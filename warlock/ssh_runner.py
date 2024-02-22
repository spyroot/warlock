#
import subprocess
from pathlib import Path
from typing import List
import paramiko
from os.path import expanduser
import time


class SshRunner:
    def __init__(
            self,
            remote_hosts: List[str],
            username: str = "capv",
            password=None,
            public_key_path=None,
    ):
        """
        :param username:
        :param password:
        """
        self._remote_hosts = remote_hosts
        self.username = username
        self.password = password
        self._is_pubkey_authenticated = False

        # default path
        self.public_key_path = f"{expanduser('~')}/.ssh/id_rsa.pub"
        if public_key_path is not None:
            self.public_key_path = public_key_path

        self.initial_auth()
        self.persistent_connections = {}

    def __enter__(self):
        """
        Return the instance itself when entering the context.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Ensure all connections are closed when exiting the context.
        """
        print("closing connections")
        self.close_all_connections()

    def close_all_connections(self):
        """Close all connections to remote host
        :return:
        """
        for ip, client in self.persistent_connections.items():
            client.close()
        self.persistent_connections.clear()

    def get_ssh_connection(self, ip):
        """
        :param ip:
        :return:
        """
        if ip not in self.persistent_connections:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.load_system_host_keys()
            client.connect(ip, username=self.username, password=self.password)
            self.persistent_connections[ip] = client

        return self.persistent_connections[ip]

    def run(self, ip, command):
        """Run cmd on remote host
        :param ip:
        :param command:
        :return:
        """
        client = self.get_ssh_connection(ip)

        print("executing command {} on a host {}".format(command, ip))
        start_time = time.time()
        stdin, stdout, stderr = client.exec_command(command)
        # This blocks until the command finishes
        stdout.channel.recv_exit_status()

        end_time = time.time()
        output = stdout.read().decode('utf-8').strip()
        execution_time = end_time - start_time
        exit_code = stdout.channel.exit_status

        return output, exit_code, execution_time

    def initial_auth(self):
        """Initial authentication
        :return:
        """
        self.push_keys()
        if self.password:
            self._is_pubkey_authenticated = False
        else:
            self._is_pubkey_authenticated = True

    @staticmethod
    def run_command(cmd):
        """
        :param cmd:
        :return:
        """
        result = subprocess.run(
            cmd, capture_output=True, text=True, shell=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        else:
            raise Exception(f"Command '{cmd}' failed with error: {result.stderr.strip()}")

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

    def push_keys(self):
        """For initial connection we copy ssh key to remote nodes by leveraging
        ssh-copy-id all follow up ssh connection will use key authentication.
        Note it assume server accept that.

        :return:
        """
        pub_key_path = Path(self.public_key_path)
        if not pub_key_path.exists():
            print("Not found {}".format(pub_key_path))
            print("Please generate public key first. run ssh-keygen")
            return

        with open(self.public_key_path, "r") as file:
            public_key = file.read().strip()

            for ip in self._remote_hosts:
                print(f"Copying SSH key to {ip}...")
                subprocess.run(["ssh-copy-id", f"{self.username}@{ip}"])

    def release_connection(self, ip):
        """
        Closes the SSH connection for a specific host
        and removes it from the persistent connections.

        :param ip: IP address of the host whose connection should be released.
        """
        # Check if the connection exists for the given IP
        if ip in self.persistent_connections:
            self.persistent_connections[ip].close()
            del self.persistent_connections[ip]

