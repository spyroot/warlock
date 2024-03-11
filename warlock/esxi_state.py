"""
EsxiState, designed to encapsulate reading esxi state information.
i.e. whatever we need read from system directly.  either vCenter
has no particular IP nor ESXi API provide no access.

In all cases we need to be root on the host.

EsxiState delegate all execution operation via SSH to SSHOperator.

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import os
from typing import Optional, Dict, List, Any, Union
from warlock.ssh_operator import SSHOperator
import xml.etree.ElementTree as ET
import json


class InvalidESXiHostException(Exception):
    """Exception raised when the target host is not identified as an ESXi host."""

    def __init__(self, host, message="The target host does not appear to be an ESXi host."):
        self.host = host
        self.message = f"{message} Host: {host}"
        super().__init__(self.message)


class EsxiState:
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
            raise ValueError(f"ssh_operator must be an instance of SSHOperator, got {type(ssh_operator)}")

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

    def __enter__(self):
        """
        Return the instance itself when entering the context.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Ensure all connections are closed when exiting the context.
        """
        if self._ssh_operator is not None:
            self._ssh_operator.close_all_connections()

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
        """Read all adapter names and return list of names
        :return: list of adapter names
        """
        nic_list = self.read_adapter_list()
        if nic_list is None or len(nic_list) == 0:
            return []
        return [n['Name'] for n in nic_list]

    def read_pf_adapter_names(
            self
    ) -> List[str]:
        """Read all adapter that provide sriov pf functionality
        :return: list of adapter names
        """
        # esxcli network sriovnic list
        nic_list = self.read_adapter_list()
        if nic_list is None or len(nic_list) == 0:
            return []

        _pf_names = []
        pf_names = [n['Name'] for n in nic_list]
        for pf_name in pf_names:
            data = self.read_network_vf_list(pf_adapter_name=pf_name)
            if data is not None and len(data) > 0:
                _pf_names.append(pf_name)

        return _pf_names

    def read_network_vf_list(
            self,
            pf_adapter_name: str = "vmnic0"
    ) -> List[Dict[str, Any]]:
        """Method return list of all VF for particular PF
        :param pf_adapter_name: PF name of the adapter. "vmnic0" etc.
        :return: a list of VF each is dictionary
        """
        cmd = f"esxcli --formatter=xml network sriovnic vf list -n {pf_adapter_name}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiState.xml2json(_data))
        return []

    def read_active_vf_list(
            self,
            pf_adapter_name: str = "vmnic0"
    ) -> List[int]:
        """
        Reads and returns list of all active vf for particular PF.
        """
        vfs = self.read_network_vf_list(pf_adapter_name=pf_adapter_name)
        return [vf_dict['VFID'] for vf_dict in vfs if
                'Active' in vf_dict and vf_dict['Active'] == 'true' and 'VFID' in vf_dict]

    def read_pf_stats(
            self,
            adapter_name: str = "vmnic0"
    ):
        """Read network adapter stats
        """
        cmd = f"esxcli --formatter=xml network nic stats get -n {adapter_name}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiState.xml2json(_data))
        return []

    def read_vf_stats(
            self,
            adapter_name: str = "vmnic0",
            vf_id: Union[str, int] = "0"
    ) -> List[Dict[str, Any]]:
        """
        Reads VF stats from the ESXi host.
        """
        vf_id_str = str(vf_id)
        cmd = f"esxcli --formatter=xml network sriovnic vf stats -n {adapter_name} -v {vf_id_str}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiState.xml2json(_data))
        return []

    def read_adapter_list(self):
        """
        Read network adapter list
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, "esxcli --formatter=xml network nic list")
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiState.xml2json(_data))
        return {}

    def read_vm_list(
            self
    ) -> Dict[str, Any]:
        """
        Reads vm list from esxi and return as json data
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, "esxcli --formatter=xml vm process list")
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiState.xml2json(_data))
        return {}

    def read_dvs_list(
            self
    ) -> List[Dict[str, Any]]:
        """
        Reads vm list from esxi and return as json data
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, "esxcli --formatter=xml network vswitch dvs vmware list")
        if exit_code == 0 and _data is not None:
            return json.loads(EsxiState.xml2json(_data))
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
            return json.loads(EsxiState.xml2json(_data))
        return []

    def read_all_net_stats(
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

    def read_vm_net_port_id(
            self
    ) -> Dict[int, str]:
        """Return dictionary of port id to vm name in context net-stats vm name
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

    def read_vm_net_stats(
            self,
            vm_name: str,
            is_abs: Optional[bool] = False
    ):
        """
        VM_FULL_NAME is net-stat name i.e.
        SRIOVmy_vm_name.eth7
        Retrieves network stats for a specified VM.
        """
        _data, exit_code, _ = self._ssh_operator.run(
            self.fqdn, f"net-stats -V {vm_name}" if is_abs else f"net-stats -a -V {vm_name}")
        if exit_code == 0 and _data is not None:
            return json.loads(_data)
        return {}

    def read_port_net_stats(
            self,
            nic: str = "vmnic0",
            is_abs: Optional[bool] = False,
    ):
        """
        Retrieves network stats for a specified port.
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
        """
        Lists hardware capabilities of a specified network adapter.
        """
        command = f"vsish -e ls /net/sriov/{nic}/hwCapabilities"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, command)
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
        """
        Gets a specific hardware capability for a specified network adapter.
        """
        command = f"vsish -e get /net/sriov/{nic}/hwCapabilities/{capability}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, command)
        if exit_code == 0 and _data is not None:
            if exit_code == 0 and _data is not None:
                return _data.strip().lower() in ["1", "true", "on"]
        return False

    @staticmethod
    def _convert_to_dict(data):
        """
        Converts the vsish output to python dict.
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
            nic="vmnic0"
    ) -> Dict[str, Any]:
        """
        Retrieves and converts queue information for a specified NIC into JSON.
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
