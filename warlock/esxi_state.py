import os
from typing import Optional, Dict
from warlock.ssh_operator import SSHOperator


class EsxiState:
    def __init__(
            self,
            ssh_executor: SSHOperator,
            credential_dict: Optional[Dict] = None,
            fqdn: Optional[str] = None,
            username: Optional[str] = "root",
            password: Optional[str] = ""
    ):
        """
        :param ssh_executor:
        :param fqdn:
        :param username:
        :param password:
        """
        self.ssh_executor = ssh_executor
        self.credential_dict = credential_dict

        default_vcenter_ip = self.credential_dict.get('iaas', {}).get(
            'vcenter_ip', '') if self.credential_dict else ''
        default_username = self.credential_dict.get('iaas', {}).get(
            'username', '') if self.credential_dict else ''
        default_password = self.credential_dict.get('iaas', {}).get(
            'password', '') if self.credential_dict else ''

        self.fqdn = fqdn if fqdn is not None else default_vcenter_ip
        self.username = username if username is not None else default_username
        self.password = password if password is not None else default_password

    @classmethod
    def from_optional_credentials(
            cls,
            ssh_executor,
            esxi_fqdn: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """
        Constructor that creates an instance using optional credentials.

        :param ssh_executor: Instance to execute SSH commands.
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
        return cls(ssh_executor, None, esxi_fqdn.strip(), username.strip(), password.strip())

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

    def read_network_adapter(self, adapter_name="vmnic7"):
        cmd = f"esxcli network sriovnic vf list -n {adapter_name}"
        self.ssh_executor.run(self.fqdn, cmd)

    def read_network_adapters_stats(self, adapter_name="vmnic7", vf_id="0"):
        cmd = f"esxcli network sriovnic vf stats -n {adapter_name} -v {vf_id}"
        self.ssh_executor.run(self.fqdn, cmd)





