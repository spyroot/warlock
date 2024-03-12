"""
EsxiState, designed to encapsulate reading esxi state information.
i.e. whatever we need read from a system directly.  either vCenter
has no particular metric nor ESXi API provide no access.

In all cases we need to be root on the host.
EsxiState delegate all execution operation via SSH to SSHOperator.

The data we can collect from ESXi state is CPU / Network information
metric. For example if entity perform some set of test for SRIOV
we can collect sriov related metric data pkt drop / core utilization
interrupts etc.

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import os
from typing import Optional, Dict, List, Any, Union

import numpy as np

from warlock.ssh_operator import SSHOperator
import xml.etree.ElementTree as ET
import json


class InvalidESXiHostException(Exception):
    """Exception raised when the target host is not identified as an ESXi host."""

    def __init__(self, host, message="The target host does not appear to be an ESXi host."):
        self.host = host
        self.message = f"{message} Host: {host}"
        super().__init__(self.message)


class EsxiStateReader:
    INTERRUPT_INTERVAL_RANGE = 4095
    MAX_VMDQ = 16

    def __init__(
            self,
            ssh_operator: SSHOperator,
            credential_dict: Optional[Dict] = None,
            fqdn: Optional[str] = None,
            username: Optional[str] = "root",
            password: Optional[str] = ""
    ):
        """
        :param ssh_operator:  ssh operator is ssh operator that we use to connect and execute
        :param fqdn: esxi fqdn or ip address
        :param username: esxi username
        :param password: esxi password
        """
        self._ssh_operator = ssh_operator
        self.credential_dict = credential_dict

        if ssh_operator is None or not isinstance(ssh_operator, SSHOperator):
            raise ValueError(f"ssh_operator must be an instance "
                             f"of SSHOperator, got {type(ssh_operator)}")

        if not isinstance(fqdn, str):
            raise TypeError(f"esxi must be a string, got {type(fqdn)}")

        if not isinstance(username, str):
            raise TypeError(f"esxi username must be a string, got {type(username)}")

        if not isinstance(password, str):
            raise TypeError(f"esxi password must be a string, got {type(password)}")

        default_vcenter_ip = self.credential_dict.get('iaas', {}).get(
            'esxi_host', '') if self.credential_dict else ''
        default_username = self.credential_dict.get('iaas', {}).get(
            'username', '') if self.credential_dict else ''
        default_password = self.credential_dict.get('iaas', {}).get(
            'password', '') if self.credential_dict else ''

        self.fqdn = fqdn if fqdn is not None else default_vcenter_ip
        self.username = username if username is not None else default_username
        self.password = password if password is not None else default_password
        # query cache, to reduce round trip time
        self._cache = {}
        # adapter cache
        self._adapter_list_cache = None
        self._vf_list_cache = {}

        # meta data about vector
        self._pf_stats_metadata = None

    def __enter__(self):
        """
        Return the instance itself when entering the context.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ensure all connections are closed when exiting the context.
        """
        if self._ssh_operator is not None:
            self._ssh_operator.close_all_connections()
            del self._ssh_operator

    def release(self):
        """Explicitly release resources,  closing all SSH connections.
        """
        if self._ssh_operator is not None:
            self._ssh_operator.close_all_connections()
            del self._ssh_operator

    @classmethod
    def from_optional_credentials(
            cls,
            esxi_fqdn: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """
        Constructor that creates an instance using optional credentials.

        :param esxi_fqdn: Optional esxi fqdn or ip address.
        :param username: Optional esxi username.
        :param password: Optional esxi password.
        :return: An instance of EsxiState.
        """
        if not isinstance(esxi_fqdn, str):
            raise TypeError(f"esxi must be a string, got {type(esxi_fqdn)}")

        if not isinstance(username, str):
            raise TypeError(f"esxi username must be a string, got {type(username)}")

        if not isinstance(password, str):
            raise TypeError(f"esxi password must be a string, got {type(password)}")

        esxi_fqdn = esxi_fqdn or os.getenv('ESXI_IP')
        username = username or os.getenv('ESXI_USERNAME')
        password = password or os.getenv('ESXI_PASSWORD')

        ssh_operator = SSHOperator(
            remote_hosts=[esxi_fqdn],
            username=username,
            password=password,
            is_password_auth_only=True
        )

        output, exit_code, _ = ssh_operator.run(esxi_fqdn, "esxcli --version")
        _esxi_version = cls.__read_version(output)
        if _esxi_version is None:
            ssh_operator.close_all_connections()
            raise InvalidESXiHostException(esxi_fqdn)

        return cls(ssh_operator, None, esxi_fqdn.strip(), username.strip(), password.strip())

    @classmethod
    def from_optional_operator(
            cls,
            ssh_operator: SSHOperator,
            esxi_fqdn: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """
        Constructor that creates an instance using existing ssh operator.

        :param ssh_operator: Instance of ssh operator.
        :param esxi_fqdn: Optional esxi fqdn or ip address.
        :param username: Optional esxi username.
        :param password: Optional esxi password.
        :return: An instance of EsxiState.
        """
        esxi_fqdn = esxi_fqdn or os.getenv('ESXI_IP')
        username = username or os.getenv('ESXI_USERNAME')
        password = password or os.getenv('ESXI_PASSWORD')

        if not isinstance(esxi_fqdn, str):
            raise TypeError(f"esxi must be a string, got {type(esxi_fqdn)}")

        if not isinstance(username, str):
            raise TypeError(f"esxi username must be a string, got {type(username)}")

        if not isinstance(password, str):
            raise TypeError(f"esxi password must be a string, got {type(password)}")

        if esxi_fqdn:
            if not ssh_operator.has_active_connection(esxi_fqdn):
                raise ValueError(f"No active connection for host {esxi_fqdn}")
            # retrieve the ESXi version to verify the connection is to an ESXi host
            output, exit_code, _ = ssh_operator.run(esxi_fqdn, "esxcli --version")
            _esxi_version = cls.__read_version(output)
            if _esxi_version is None:
                raise InvalidESXiHostException(esxi_fqdn)

        return cls(ssh_operator, None, esxi_fqdn.strip(), username.strip(), password.strip())

    def is_active(self) -> bool:
        """
        Checks if there's an active SSH connection to the ESXi host.
        :return: True if there's an active connection, False otherwise.
        """
        return self._ssh_operator.get_active_ssh_connection(self.fqdn) is not None

    @staticmethod
    def __read_version(
            command_output: str
    ) -> Optional[str]:
        """
        Extracts the ESXi version from the command output.
        :param command_output: The output string from running `esxcli --version`.
        :return: The extracted version string or None if not found.
        """
        parts = command_output.split()
        if parts[-1].count('.') == 2:
            return parts[-1]
        return None

    def read_adapter_names(
            self
    ) -> List[str]:
        """Read all adapter VMware names and return as list  of names.

        - if failed to read it will return an empty list
          in case of SSH transport issues exception raised.

        :return: list of adapter names
        """
        if 'adapter_names' in self._cache:
            return self._cache['adapter_names']

        nic_list = self.read_adapter_list()
        if nic_list is None or len(nic_list) == 0:
            return []

        nic_list = self.read_adapter_list()
        if nic_list is None or len(nic_list) == 0:
            return []

        adapter_names = [n['Name'] for n in nic_list]
        self._cache['adapter_names'] = adapter_names
        return adapter_names

    def read_pf_adapter_names(
            self
    ) -> List[str]:
        """Method return all adapter that provide sriov pf functionality.
        :return: list of adapter names
        """
        # esxcli network sriovnic list
        if 'pf_adapter_names' in self._cache:
            return self._cache['pf_adapter_names']

        nic_list = self.read_adapter_list()
        if nic_list is None or len(nic_list) == 0:
            return []

        _pf_names = []
        pf_names = [n['Name'] for n in nic_list]
        for pf_name in pf_names:
            data = self.read_vfs(pf_adapter_name=pf_name)
            if data is not None and len(data) > 0:
                _pf_names.append(pf_name)

        self._cache['pf_adapter_names'] = _pf_names
        return _pf_names

    def read_vfs(
            self,
            pf_adapter_name: str = "vmnic0"
    ) -> List[Dict[str, Any]]:
        """Method return list of all VFs for
        particular parent network adapter (PF).
        :param pf_adapter_name: PF name of the adapter. "vmnic0" etc.
        :return: a list of VF each is dictionary
        """
        if pf_adapter_name is None:
            return []

        if pf_adapter_name in self._vf_list_cache:
            return self._vf_list_cache[pf_adapter_name]

        cmd = f"esxcli --formatter=xml network sriovnic vf list -n {pf_adapter_name}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            self._vf_list_cache[pf_adapter_name] = json.loads(EsxiStateReader.xml2json(_data))
        else:
            self._vf_list_cache[pf_adapter_name] = []

        return self._vf_list_cache[pf_adapter_name]

    def filtered_map_vm_hosts_port_ids(
            self,
            vm_names: List[str],
            vmnic_name: Dict[str, str],
            is_sriov: Optional[bool] = None,
    ):
        """
        Returns a dictionary that maps VM names to their port IDs, ESXi host,
        and port id where port id are internal id,

        VM NIC names filtered by the specified adapter name and SR-IOV flag.

        Once a VM is found on one ESXi host, it's not searched for again on another host.

        :param vm_names: List of VM names to map.
        :param vmnic_name: Dictionary of VM names to their target adapter names.
        :param is_sriov: Optional flag to filter NICs based on SR-IOV usage.
                         If True, only includes NICs with "SRIOV".
                         If False, excludes those NICs.
                         If None, includes all NICs.
        :return: Dictionary mapping VM names to their details including filtered port VM NIC names.
        """
        vm_to_port_ids = {}
        vm_port_id_map = self.read_netstats_vm_net_port_ids()

        for vm_name in vm_names:
            target_adapter = vmnic_name.get(vm_name, None)
            port_ids = []
            port_vm_nic_name = []

            for port_id, port_vm_name in vm_port_id_map.items():
                if vm_name in port_vm_name:
                    include_port = False
                    if is_sriov is None:
                        include_port = True
                    elif is_sriov and "SRIOV" in port_vm_name:
                        include_port = True
                    elif not is_sriov and "SRIOV" not in port_vm_name:
                        include_port = True

                    if include_port and (target_adapter is None or target_adapter in port_vm_name):
                        port_ids.append(port_id)
                        port_vm_nic_name.append(port_vm_name)

            if port_ids:
                vm_to_port_ids[vm_name] = {
                    'port_ids': port_ids,
                    'esxi_host': self.fqdn,
                    'port_vm_nic_name': port_vm_nic_name
                }

        return vm_to_port_ids

    def read_vm_port_stats(
            self,
            world_id: Union[int, str]
    ):
        """
        Retrieve VM port statistics using a given world ID.
        The world_id can be provided as either an integer or a string.
        :param world_id: an internal port id it should int value
        :return:
        """
        world_id_str = str(world_id)
        cmd = f"esxcli --formatter=xml network port stats get -p {world_id_str}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiStateReader.xml2json(_data))
        return []

    def read_active_vfs(
            self,
            pf_nic_name: str = "vmnic0"
    ) -> List[int]:
        """Reads and returns list of all active VF on a particular PF.
           if SRIOV not enabled and caller provided correct vmnic
           the list is empty.

        :param pf_nic_name:  PF name of the adapter. "vmnic0"
        :return: list of active VF on a particular adapter
        """
        if pf_nic_name is None:
            return []
        vfs = self.read_vfs(pf_adapter_name=pf_nic_name)
        return [vf_dict['VFID'] for vf_dict in vfs if
                'Active' in vf_dict and vf_dict['Active'] and 'VFID' in vf_dict]

    def pf_stats_metadata(self):
        """Returns metadata for the network adapter stats."""
        return self._pf_stats_metadata

    def read_pf_stats(
            self,
            adapter_name: str = "vmnic0",
            return_as_vector: bool = False
    ):
        """Read network adapter stats, if adapter name invalid
        returns empty list.

        if return_as_vector is True method return (1, 23) vector
        where each col mapped to stats metric data.

        :param adapter_name:  Name of the adapter. "vmnic0" etc.
        :param return_as_vector: If True, returns a numpy vector for all integer values.
        :return: a list of key pair stats or a numpy vector if return_numpy_vector is True.
        """
        if adapter_name is None:
            return []

        cmd = f"esxcli --formatter=xml network nic stats get -n {adapter_name}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            stats_dict = json.loads(EsxiStateReader.xml2json(_data))
            if return_as_vector and len(stats_dict) == 1:
                d = stats_dict[0]
                self._pf_stats_metadata = [key for key, value in d.items() if isinstance(value, int)]
                nd = np.array([value for key, value in d.items() if isinstance(value, int)])
                return nd.reshape(1, -1)
            else:
                return stats_dict
        return []

    def read_vf_stats(
            self,
            adapter_name: str = "vmnic0",
            vf_id: Union[str, int] = "0"
    ) -> List[Dict[str, Any]]:
        """
        Reads VF stats from the ESXi host.
        :param adapter_name:  Name of the adapter. "vmnic0"
        :param vf_id:  VF ID to read. "0" etc.
        :return: List that store stats as dictionaries
        """
        vf_id_str = str(vf_id)
        cmd = f"esxcli --formatter=xml network sriovnic vf stats -n {adapter_name} -v {vf_id_str}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiStateReader.xml2json(_data))
        return []

    def read_adapter_list(self) -> List[str]:
        """Read network adapter list and return list that hold a dicts

        Example:
        >>> with EsxiStateReader(ssh_operator, fqdn, username, password) as reader:
        >>>     adapter_list = reader.read_adapter_list()
        >>>     print(adapter_list)

        [{'AdminStatus': 'Up', 'DPUId': 'N/A', 'Description': 'Intel(R) Ethernet Controller X550', ...}, {...}]

          Data

            [
              {
                  'AdminStatus': 'Up',
                   'DPUId': 'N/A',
                   'Description': 'Intel(R) Ethernet Controller X550',
                   'Driver': 'ixgben',
                   'Duplex': 'Full',
                   'Link': 'Up',
                   'LinkStatus': 'Up',
                   'MACAddress': '78:ac:44:07:b2:c4',
                   'MTU': 1500,
                   'Name': 'vmnic0',
                   'PCIDevice': '0000:18:00.0',
               },
               // another adapter
               ]

        :return: a list of dictionaries containing all adapters
        """
        if self._adapter_list_cache is not None:
            return self._adapter_list_cache

        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, "esxcli --formatter=xml network nic list")
        if exit_code == 0 and _data is not None:
            self._adapter_list_cache = json.loads(EsxiStateReader.xml2json(_data))
        else:
            self._adapter_list_cache = []

        return self._adapter_list_cache

    def read_vm_process_list(
            self
    ) -> Dict[str, Any]:
        """
        Reads VM process list from esxi and return as json data.
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, "esxcli --formatter=xml vm process list")
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiStateReader.xml2json(_data))
        return []

    def read_dvs_list(
            self
    ) -> List[Dict[str, Any]]:
        """
        Reads vm list from esxi and return as json data.
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, "esxcli --formatter=xml network vswitch dvs vmware list")
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiStateReader.xml2json(_data))
        return []

    def read_standard_switch_list(
            self
    ) -> List[Dict[str, Any]]:
        """
        Reads vm list from esxi and return as json data
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, "esxcli --formatter=xml network vswitch standard list")
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiStateReader.xml2json(_data))
        return []

    def read_netstats_all(
            self,
            is_abs: Optional[bool] = False
    ) -> Dict[Any, Any]:
        """
        Reads all network stats from the ESXi host.
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, "net-stats -A" if is_abs else "net-stats -a -A")
        if exit_code == 0 and _data is not None:
            return json.loads(_data)
        return {}

    def read_netstats_vm_net_port_ids(
            self
    ) -> Dict[int, str]:
        """Return dictionary of port id to vm name in context net-stats vm name
        :return:
        """

        def is_number(s):
            """Checks if the input string s is a number."""
            try:
                int(s)
                return True
            except ValueError:
                return False

        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, f"net-stats -l")
        if exit_code == 0 and _data is not None:
            _data = _data.splitlines()
            data_rows = [line.strip().split() for line in _data if is_number(line[0])]
            port_to_vm_name = {int(row[0]): " ".join(row[5:]).strip() for row in data_rows if len(row) >= 5}
            return port_to_vm_name
        return {}

    def read_netstats_by_vm(
            self,
            vm_name: str,
            is_abs: Optional[bool] = False
    ):
        """Reads vm net statistics from net-stats.

        :param vm_name: is vm name accepted by net-stats i.e. SRIOVmy_vm_name.eth7
        :param is_abs:  if value caller need absolute values
        :return:  dictionary that hold all statistics.
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, f"net-stats -V {vm_name}" if is_abs else f"net-stats -a -V {vm_name}")
        if exit_code == 0 and _data is not None:
            return json.loads(_data)
        return {}

    def read_netstats_by_nic(
            self,
            nic: str = "vmnic0",
            is_abs: Optional[bool] = False,
    ):
        """Retrieves network stats for a specified port.
        :param nic:  name of network interface
        :param is_abs:  if value caller need absolute values
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, f"net-stats -N {nic}" if is_abs else f"net-stats -a -N {nic}")
        if exit_code == 0 and _data is not None:
            return json.loads(_data)
        return {}

    def read_net_sriov_stats(
            self,
            nic: str = "vmnic0"
    ) -> Dict[str, Any]:
        """
        Retrieves SR-IOV stats for a specified NIC.
        """
        command = f"vsish -r -e get /net/sriov/{nic}/stats"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, command)
        if exit_code == 0 and _data is not None:
            _data = self._convert_to_dict(_data)
            return _data
        return {}

    def read_net_adapter_capabilities(
            self,
            nic: str = "vmnic0"
    ) -> List[str]:
        """Lists hardware capabilities of a specified network adapter.
        :param nic: vmnic name that we fetch capability
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, f"vsish -e ls /net/sriov/{nic}/hwCapabilities")
        if exit_code == 0 and _data is not None:
            _cap = _data.splitlines()
            _cap = [cap.strip() for cap in _cap]
            return _cap
        return []

    def is_net_adapter_capability_on(
            self,
            nic: str = "vmnic0",
            capability: Optional[str] = "CAP_SRIOV"
    ) -> bool:
        """Return bool if a specific hardware capability enabled.
        :param nic: a string representing the name of the adapter
        :param capability: a string representing the capability CAP_SRIOV etc.
        :return: True if the enabled capability
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, f"vsish -e get /net/sriov/{nic}/hwCapabilities/{capability}")
        if exit_code == 0 and _data is not None:
            if exit_code == 0 and _data is not None:
                return _data.strip().lower() in ["1", "true", "on"]
        return False

    @staticmethod
    def _convert_to_dict(data):
        """Converts the vsish output to python dict.
        """

        def convert_value(value):
            """Converts a hexadecimal string to an integer.
            """
            if value.startswith("0x"):
                return int(value, 16)
            return value

        data = data.splitlines()
        data = [line.split(':') for line in data if ":" in line]
        data = {line[0].strip(): convert_value(line[1].strip()) for line in data}
        return data

    def read_sriov_queue_info(
            self,
            nic: str = "vmnic0"
    ) -> Dict[str, Any]:
        """ Retrieves and converts queue information for a specified NIC into JSON.
        :param nic:  a string representing the NIC to retrieve default vmnic0
        :return: a dictionary contain TX and RX queue information. (high level view)
        """
        rx_info = {}
        tx_info = {}

        command = f"vsish -r -e get /net/sriov/{nic}/rxqueues/info"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, command)
        if exit_code == 0 and _data is not None:
            rx_info = self._convert_to_dict(_data)

        command = f"vsish -r -e get /net/sriov/{nic}/txqueues/info"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, command)
        if exit_code == 0 and _data is not None:
            tx_info = self._convert_to_dict(_data)

        return {
            "rx_info": rx_info,
            "tx_info": tx_info
        }

    def write_ring_size(
            self,
            nic: str,
            tx_int: int,
            rx_int: int
    ) -> bool:
        """Update tx and rx ring size for a specified network adapter.

        :param nic:  a string representing the NIC vmnic0 etc.
        :param tx_int: ring tx size
        :param rx_int: ring rx size
        :return: a boolean indicating whether the tx and rx ring size were updated
        """

        def is_power_of_two(n):
            return n != 0 and (n & (n - 1)) == 0

        if not is_power_of_two(tx_int):
            raise ValueError(f"tx_int ({tx_int}) must be a power of 2.")
        if not is_power_of_two(rx_int):
            raise ValueError(f"rx_int ({rx_int}) must be a power of 2.")

        cmd = f"esxcli network nic ring current set -n {nic} -r {rx_int} -t {tx_int}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        return exit_code == 0

    def read_module_parameters(
            self,
            module_name: str = "icen"
    ) -> List[Any]:
        """Read kernel module parameters for a given module.
        :param module_name:  Name of the module. "icen", "en40"
        :return: a list that hold dictionary of parameters driver current uses.
        """
        if module_name is None:
            return []

        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, f"esxcli --formatter=xml system module parameters list -m {module_name}")
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiStateReader.xml2json(_data))
        return []

    def read_adapter_driver_name(
            self,
            nic: str = "vmnic0",
    ) -> Union[None, str]:
        """Read network adapter and return driver name.
        :param nic:  vmnic0
        :return: nic driver name as string
        """
        if nic is None or len(nic) == 0:
            return None

        cmd = f"esxcli --formatter=xml network nic get -n {nic}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            data = json.loads(EsxiStateReader.complex_xml2json(_data))
            if isinstance(data, list) and len(data) > 0:
                driver_info = data[0].get('DriverInfo')
                if driver_info:
                    driver = driver_info.get('Driver')
                    if driver:
                        return driver
        return None

    def read_adapter_parameters(
            self,
            nic: str = "vmnic0"
    ):
        """
        Read adapter parameters and return a list of dictionaries.
        :param nic:
        :return:
        """
        module_name = self.read_adapter_driver_name(nic=nic)
        if module_name is not None:
            return self.read_module_parameters(module_name=module_name)
        return []

    def read_available_mod_parameters(
            self,
            nic: str = "vmnic0"
    ) -> List[Dict[str, Any]]:
        """
        Reads kernel module parameters and return a list of all parameters.

        Example:

        >>> with EsxiStateReader(ssh_operator, credential_dict, fqdn, username, password)
        >>>     vf_stats = reader.read_available_mod_parameters(adapter_name="vmnic0")
        >>>     print(vf_stats)

        small example

        [
             'DRSS',
             'DevRSS',
             'QPair',
             'RSS'
        ]

        :param nic: a string representing the name of the network adapter/
        :return: a list of parameters
        """
        module_name = self.read_adapter_driver_name(nic=nic)
        if module_name is not None:
            module_params = self.read_module_parameters(module_name=module_name)
            if len(module_params) > 0:
                return [param['Name'] for param in module_params if 'Name' in param]
        return []

    def __enable_sriov(
            self,
            nic: str,
            module: str,
            num_vfs: int
    ) -> bool:
        """Enable SR-IOV on a specified network adapter with a given number
        of Virtual Functions (VFs).

        :param nic: A string representing the NIC (e.g., vmnic0).
        :param num_vfs: The number of Virtual Functions to enable for the NIC.
        :return: A boolean indicating whether SR-IOV was enabled successfully.
        """
        if not isinstance(num_vfs, int) or num_vfs <= 0:
            raise ValueError(f"num_vfs ({num_vfs}) must be a positive integer.")

        enable_sriov_cmd = "esxcli system module parameters set -m {module} -p max_vfs={num_vfs},{num_vfs},{num_vfs},{num_vfs}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, enable_sriov_cmd)

        return exit_code == 0

    @staticmethod
    def complex_xml2json(xml_data: str) -> str:
        """
        Converts XML data to JSON, handling nested structures and lists.
        """

        def parse_element(element):
            """
            Recursively parses XML elements to build a Python dict.
            """
            tag_name = element.tag.split('}', 1)[-1]
            if tag_name == 'structure':
                return {child.get('name'): parse_element(child[0]) for child in element}
            elif tag_name == 'list':
                return [parse_element(child) for child in element]
            elif tag_name == 'field':
                return parse_element(element[0])
            else:
                if tag_name == 'integer':
                    return int(element.text)
                elif tag_name == 'boolean':
                    return element.text.lower() == 'true'
                else:  # Fallback for 'string' and unrecognized tags
                    return element.text

        ns = {'esxcli': 'http://www.vmware.com/Products/ESX/5.0/esxcli'}
        root = ET.fromstring(xml_data)
        parsed_data = [parse_element(structure) for structure in root.findall('.//esxcli:structure', ns)]
        json_output = json.dumps(parsed_data, indent=4)
        return json_output

    @staticmethod
    def xml2json(
            xml_data: str
    ) -> str:
        """
        Method generic implementation data normalization
        from esxcli to JSON.

        :param xml_data: XML data as a string.
        :return: JSON representation of the XML data as string.
        """
        root = ET.fromstring(xml_data)
        data_list = []
        ns = {'esxcli': 'http://www.vmware.com/Products/ESX/5.0/esxcli'}
        for structure in root.findall('.//esxcli:list/esxcli:structure', ns):
            nic_info = {}
            for field in structure.findall('esxcli:field', ns):
                field_name = field.get('name')
                for child in field:
                    # Tag name (removing namespace)  (e.g., 'string', 'integer')
                    field_type = child.tag.split('}', 1)[-1]
                    field_value = child.text

                    if field_type == 'integer':
                        field_value = int(field_value)

                    if field_type == 'boolean':
                        field_value = True if field_value.lower() == 'true' else False

                    nic_info[field_name] = field_value
            data_list.append(nic_info)

        json_output = json.dumps(data_list, indent=4)
        return json_output

    @staticmethod
    def parse_stats_to_json(
            stats_output
    ):
        """Parse VF stats output from raw text to a JSON.
        :param stats_output:
        :return:
        """
        stats_dict = {}
        lines = stats_output.split('\n')
        for line in lines:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip().replace(' ', '_')
                value = parts[1].strip()
                try:
                    value = int(value)
                except ValueError:
                    pass
                stats_dict[key] = value
        return stats_dict

    def write_vf_trusted(
            self,
            module_name: str = "icen"
    ) -> bool:
        """Update PF trusted state. (Note not all driver/module support that)
        :param module_name: network adapter driver kernel module name
        :return: a boolean indicating whether the tx and rx ring size were updated
        """
        module_params = self.read_module_parameters(module_name=module_name)
        if len(module_params) == 0:
            raise ValueError(f"No parameters found for module {module_name}.")

        param_names = [param['Name'] for param in module_params if 'Name' in param]

        if 'trust_all_vfs' not in param_names:
            raise ValueError(f"'trust_all_vfs' parameter not available for module {module_name}.")

        cmd = f"esxcli system module parameters set -m {module_name} -p trust_all_vfs=1"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        return exit_code == 0

    def update_module_param(
            self,
            module_name: str,
            param_name: str,
            param_value: str
    ) -> bool:
        """
        Update a specific parameter for a given kernel module.

        :param module_name: The kernel module name.
        :param param_name: The name of the parameter to update.
        :param param_value: The new value for the parameter.
        :return: A boolean indicating whether the parameter was successfully updated.
        """
        module_params = self.read_module_parameters(module_name=module_name)
        if len(module_params) == 0:
            raise ValueError(f"No parameters found for module {module_name}.")

        param_names = [param['Name'] for param in module_params if 'Name' in param]
        if param_name not in param_names:
            raise ValueError(f"Parameter '{param_name}' not available for module {module_name}.")

        cmd = f"esxcli system module parameters set -m {module_name} -a -p {param_name}={param_value}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)

        if exit_code != 0:
            raise RuntimeError(f"Failed to update '{param_name}' parameter for module {module_name}.")

        return True

    def read_adapters_by_driver(
            self,
            driver_name: str
    ) -> List[str]:
        """
        Return a list of all adapter names that using particular driver.

        :param driver_name: The name of the driver to filter adapters by.
        :return: A list of adapter names that use the specified driver. Returns an empty list if none found.
        """
        nic_list = self.read_adapter_list()
        adapters_using_driver = [nic['Name'] for nic in nic_list if nic['Driver'] == driver_name]
        return adapters_using_driver

    def update_num_qps_per_vf(
            self,
            module_name: str,
            num_qps: int
    ) -> bool:
        """
        Update the NumQPsPerVF parameter for an intel  kernel module.

        :param module_name: The kernel module name.
        :param num_qps: The number of queue pairs to be allocated for each VF. Must be one of [1, 2, 4, 8, 16].
        :return: A boolean indicating whether the NumQPsPerVF parameter was successfully updated.
        """
        valid_values = [1, 2, 4, 8, 16]
        nic_list = self.read_adapters_by_driver(module_name)
        if num_qps not in valid_values:
            raise ValueError(f"num_qps ({num_qps}) must be one of {valid_values}.")

        num_qps_str = ",".join([str(num_qps) for _ in nic_list])
        return (self.update_module_param
                (module_name=module_name,
                 param_name="NumQPsPerVF",
                 param_value=str(num_qps_str))
                )

    def update_max_vfs(
            self,
            module_name: str,
            max_vfs: int
    ) -> bool:
        """
        Update max vfs parameter for a specified kernel module
        (icen, i40en etc.) for all adapter.

        :param module_name: The kernel module name.
        :param max_vfs: The number of max vf  [8, 16, 32, etc.].
        :return: A boolean indicating whether the max_vfs parameter was successfully updated.
        """
        nic_list = self.read_adapters_by_driver(module_name)
        max_vfs_str = ",".join([str(max_vfs) for _ in nic_list])
        return self.update_module_param(
            module_name=module_name,
            param_name="max_vfs",
            param_value=str(max_vfs_str)
        )

    def update_rss(
            self, module_name: str,
            enable: bool
    ) -> bool:
        """
        Update the RSS (Receive-Side Scaling) parameter for a specified
        kernel module (ice, i40en etc.) for all adapters.

        :param module_name: The kernel module name.
        :param enable: A boolean indicating whether to enable (True) or disable (False) RSS.
        :return: A boolean indicating whether the RSS parameter was successfully updated.
        """
        nic_list = self.read_adapters_by_driver(module_name)
        rss_value_str = ",".join([str(int(enable)) for _ in nic_list])
        return self.update_module_param(
            module_name=module_name,
            param_name="RSS",
            param_value=rss_value_str
        )

    def update_rx_itr(
            self, module_name: str,
            rx_itr: int
    ) -> bool:
        """
        Update the default RX interrupt interval parameter for a specified kernel module.

        :param module_name: The kernel module name.
        :param rx_itr: The RX interrupt interval in microseconds. Must be in the range [0, 4095].
        :return: A boolean indicating whether the parameter was successfully updated.
        """
        if not (0 <= rx_itr <= self.INTERRUPT_INTERVAL_RANGE):
            raise ValueError("rx_itr must be between 0 and 4095.")

        return self.update_module_param(
            module_name=module_name,
            param_name="RxITR",
            param_value=str(rx_itr)
        )

    def update_tx_itr(
            self,
            module_name: str,
            tx_itr: int
    ) -> bool:
        """ Update the default TX interrupt interval parameter for a specified kernel module.

        :param module_name:  The kernel module name.
        :param tx_itr: The TX interrupt interval in microseconds. Must be in the range [0, 4095].
        :return:  A boolean indicating whether the parameter was successfully updated.
        """
        if not (0 <= tx_itr <= self.INTERRUPT_INTERVAL_RANGE):
            raise ValueError("tx_itr must be between 0 and 4095.")

        return self.update_module_param(
            module_name=module_name,
            param_name="TxITR",
            param_value=str(tx_itr)
        )

    def update_vmdq(
            self, module_name: str,
            vmdq: int
    ) -> bool:
        """
        Update the VMDQ (Virtual Machine Device Queues) parameter
        for a specified kernel module.

        [2, 4, 8, 16, 32]

        :param module_name: The kernel module name.
        :param vmdq: The number of Virtual Machine Device Queues. Must be one of [0, 1, 2, ..., 16].
        :return: A boolean indicating whether the parameter was successfully updated.
        """
        if not (0 <= vmdq <= self.MAX_VMDQ):
            raise ValueError(f"vmdq must be between 0 and {self.MAX_VMDQ}.")

        nic_list = self.read_adapters_by_driver(module_name)
        vmdq_str = ",".join([str(vmdq) for _ in nic_list])
        return self.update_module_param(
            module_name=module_name, param_name="VMDQ", param_value=str(vmdq_str))
