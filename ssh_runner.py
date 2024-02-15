#
import subprocess
from pathlib import Path
from typing import List
import paramiko
from os.path import expanduser


class SshRunner:
    def __init__(
            self,
            remote_hosts: List[str],
            username: str,
            password=None
    ):
        """
        :param username:
        :param password:
        """
        self.remote_hosts = remote_hosts
        self.username = username
        self.password = password
        self._is_pubkey_authenticated = False

        # default path
        self.public_key_path = f"{expanduser('~')}/.ssh/id_rsa.pub"
        self.initial_auth()

    def run(self, ip, command):
        """Run cmd on remote host
        :param ip:
        :param command:
        :return:
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        client.connect(ip, username=self.username, password=self.password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        client.close()
        return output

    def initial_auth(self):
        """Initial authentication
        :return:
        """
        self.push_keys()
        if self.password:
            self._is_pubkey_authenticated = False
        else:
            self._is_pubkey_authenticated = True

    def run_local_command(self, cmd):
        """Run local command
        :param cmd:
        :return:
        """
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        return result.stdout.strip()

    # def check_key(self, node_ips, public_key_path, username, password=None):
    #     """Function to push SSH keys to remote hosts , all follow ssh command executed
    #      with key based authentication
    #     :param node_ips:  list of node ip
    #     :param public_key_path: a path to public key
    #     :param username: initial username
    #     :param password: initial password
    #     :return:
    #     """
    #     with open(public_key_path, "r") as file:
    #         public_key = file.read().strip()
    #
    #     for ip in node_ips:
    #         print(f"Checking if SSH key is already present on {ip}...")
    #         try:
    #             authorized_keys = ssh_command(ip, "cat ~/.ssh/authorized_keys", username, password)
    #             if public_key in authorized_keys:
    #                 print(f"SSH key is already present on remote node: {ip}. Skipping...")
    #             else:
    #                 raise Exception("Key not found")
    #         except Exception as e:
    #             print(f"SSH key not found on {ip}. Copying...")
    #             append_command = f'echo "{public_key}" >> ~/.ssh/authorized_keys'
    #             ssh_command(ip, append_command, username, password)
    #             print(f"SSH key successfully copied to {ip}.")

    def push_keys(self, nodes: List[str]):
        """For initial connection we copy ssh key to remote nodes by leveraging
        ssh-copy-id all follow up ssh connection will use key authentication.
        Note it assume server accept that.

        :param nodes:
        :return:
        """

        pub_key_path = Path(self.public_key_path)
        if not pub_key_path.exists():
            print("Found not found {}".format(pub_key_path))
            print("Please generate public key first. run ssh-keygen")
            return

        with open(self.public_key_path, "r") as file:
            public_key = file.read().strip()

            for ip in nodes:
                print(f"Copying SSH key to {ip}...")
                subprocess.run(["ssh-copy-id", f"{self.username}@{ip}"])
