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
from typing import Optional, Dict, List
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
    def __read_version(command_output: str) -> Optional[str]:
        """
        Extracts the ESXi version from the command output.
        :param command_output: The output string from running `esxcli --version`.
        :return: The extracted version string or None if not found.
        """
        parts = command_output.split()
        if parts[-1].count('.') == 2:
            return parts[-1]
        return None

    @staticmethod
    def parse_stats_to_json(
            stats_output
    ):
        """parse VF stats output
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

    def read_adapter_names(self) -> List[str]:
        """Read all adapter names and return list
        :return:
        """
        json_data = self.read_adapter_list()
        if json_data is None or len(json_data) == 0:
            return []

        nic_list = json.loads(json_data)
        return [n['Name'] for n in nic_list]

    def read_pf_adapter_names(
            self
    ) -> List[str]:
        """Read all adapter that provide sriov pf
        :return:
        """
        json_data = self.read_adapter_list()
        if json_data is None or len(json_data) == 0:
            return []

        _pf_names = []
        nic_list = json.loads(json_data)
        pf_names = [n['Name'] for n in nic_list]
        for pf_name in pf_names:
            data = self.read_network_vf_list(pf_adapter_name=pf_name)
            if data is not None and len(data) > 0:
                _pf_names.append(pf_name)

        return _pf_names

    def read_network_vf_list(
            self,
            pf_adapter_name="vmnic7"
    ):
        """
        :param pf_adapter_name:  PF name of the adapter.
        :return: a list of VF each is dictionary
        """
        cmd = f"esxcli --formatter=xml network sriovnic vf list -n {pf_adapter_name}"
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, cmd)
        if exit_code == 0 and _data is not None:
            return EsxiState.xml2json(_data)
        return {}

    def read_network_adapters_stats(
            self,
            adapter_name="vmnic7",
            vf_id="0"
    ):
        cmd = f"esxcli network sriovnic vf stats -n {adapter_name} -v {vf_id}"
        return self._ssh_operator.run(self.fqdn, cmd)

    def read_adapter_list(self):
        """
        Read network adapter list
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, "esxcli --formatter=xml network nic list")
        if exit_code == 0 and _data is not None:
            return EsxiState.xml2json(_data)
        return {}

    def read_vm_list(self):
        """Reads vm list from esxi and return as json data
        :return:
        """
        _data, exit_code, _ = self._ssh_operator.run(self.fqdn, "esxcli --formatter=xml vm process list")
        if exit_code == 0 and _data is not None:
            return EsxiState.xml2json(_data)
        return {}

    @staticmethod
    def xml2json(
            xml_data: str
    ):
        """
        Method generic implementation data normalization
        from esxcli to JSON.

        :param xml_data: XML data as a string.
        :return: JSON representation of the XML data.
        """

        root = ET.fromstring(xml_data)
        data_list = []

        ns = {'esxcli': 'http://www.vmware.com/Products/ESX/5.0/esxcli'}

        for structure in root.findall('.//esxcli:list/esxcli:structure', ns):
            nic_info = {}
            for field in structure.findall('esxcli:field', ns):
                field_name = field.get('name')
                for child in field:
                    # Tag name (removing namespace) will be the type (e.g., 'string', 'integer')
                    field_type = child.tag.split('}', 1)[-1]
                    field_value = child.text

                    if field_type == 'integer':
                        field_value = int(field_value)

                    nic_info[field_name] = field_value
            data_list.append(nic_info)

        json_output = json.dumps(data_list, indent=4)
        return json_output
