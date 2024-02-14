#
import subprocess
from typing import List

import paramiko
from os.path import expanduser
import argparse

from nodes import KubernetesNodes

class SshRunner:
    def __init__(self, remote_hosts, username, password=None):
        """
        :param username:
        :param password:
        """
        self.remote_hosts = remote_hosts
        self.username = username
        self.password = password
        self._is_pubkey_authenticated = False

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

    def check_key(self, node_ips, public_key_path, username, password=None):
        """Function to push SSH keys to remote hosts , all follow ssh command executed
         with key based authentication
        :param node_ips:  list of node ip
        :param public_key_path: a path to public key
        :param username: initial username
        :param password: initial password
        :return:
        """
        with open(public_key_path, "r") as file:
            public_key = file.read().strip()

        for ip in node_ips:
            print(f"Checking if SSH key is already present on {ip}...")
            try:
                authorized_keys = ssh_command(ip, "cat ~/.ssh/authorized_keys", username, password)
                if public_key in authorized_keys:
                    print(f"SSH key is already present on remote node: {ip}. Skipping...")
                else:
                    raise Exception("Key not found")
            except Exception as e:
                print(f"SSH key not found on {ip}. Copying...")
                append_command = f'echo "{public_key}" >> ~/.ssh/authorized_keys'
                ssh_command(ip, append_command, username, password)
                print(f"SSH key successfully copied to {ip}.")

    def push_keys(self, nodes: List[str], public_key_path):
        """Copy ssh key to remote nodes
        :param nodes:
        :return:
        """
        for ip in nodes:
            print(f"Copying SSH key to {ip}...")
            subprocess.run(["ssh-copy-id", f"{self.username}@{ip}"])
