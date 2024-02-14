#
# . Initial sketch prototype
#  - main idea the agent perform set of acton that mutate target environment
#  - the environment is kubernetes node.  The goal for the agent find optimal
#  - set of configration that maximize set of metric. We can define metric as
#  - packet per second for network, latency , storage IO etc.
#
#
import subprocess
import paramiko
from os.path import expanduser
import argparse

from nodes import get_node_names_and_ips


# NODE_POOL_NAME = "vf-test-np1-"
# DEFAULT_UPLINK = "eth0"
# TUNED_PROFILE_NAME = "mus"
# TUNED_PROFILE_PATH = f"/usr/lib/tuned/{TUNED_PROFILE_NAME}/tuned.conf"
# setting_keys = ["default_hugepagesz", "hugepages", "intel_idle.max_cstate"]
# setting_values = ["1G", "16", "0"]
#
# node_ips = ["192.168.1.1", "192.168.1.2"]
#
#

class SshRunner:
    def __init__(self, username, password=None):
        self.username = username
        self.password = password

    def run(self, ip, command):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.load_system_host_keys()
        client.connect(ip, username=self.username, password=self.password)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8').strip()
        client.close()
        return output

    def run_local_command(command):
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return result.stdout.strip()

    def push_keys(node_ips, public_key_path, username, password=None):
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
                    print(f"SSH key is already present on {ip}. Skipping...")
                else:
                    raise Exception("Key not found")
            except Exception as e:
                print(f"SSH key not found on {ip}. Copying...")
                append_command = f'echo "{public_key}" >> ~/.ssh/authorized_keys'
                ssh_command(ip, append_command, username, password)
                print(f"SSH key successfully copied to {ip}.")

    def push_keys(self, node_ips, public_key_path):def push_keys_with_ssh_copy_id(node_ips, username):
    """
    :param node_ips:
    :param username:
    :return:
    """
    for ip in node_ips:
        print(f"Copying SSH key to {ip}...")
        subprocess.run(["ssh-copy-id", f"{username}@{ip}"])




class NodeActions:
    def __init__(self, node_ips):
        """

        :param node_ips:
        """
        self.node_ips = node_ips
        self.tuned_profile_name=""
        self.tuned_profile_path=""
        self.ssh_cmd_runner = SshRunner()

    def update_ring_buffer(self, adapter_name, username, password=None):
        """
        :param adapter_name:
        :param username:
        :param password:
        :return:
        """
        for ip in self.node_ips:
            self.ssh_cmd_runner.ssh_command(ip, f"sudo ethtool -G {adapter_name} rx 1024 tx 1024", username, password)


    def update_active_tuned(self, username, password=None):
        """Function to update the active tuned profile on remote hosts.
        :param node_ips:
        :param tuned_profile_name:
        :param tuned_profile_path:
        :param username:
        :param password:
        :return:
        """
        for ip in self.node_ips:
            profile_name = self.ssh_cmd_runner.ssh_command(ip, "sudo tuned-adm active | awk '{print $NF}'", username, password)
            print(f"Active profile on {ip}: {profile_name}")
            if profile_name != self.tuned_profile_name:
                print(f"Setting profile {self.tuned_profile_name} on {ip}...")
                self.ssh_cmd_runnerr.ssh_command(ip, f"sudo tuned-adm profile {tuned_profile_name}", username, password)
                self.ssh_cmd_runner.ssh_command(ip, "sudo reboot", username, password)
            else:
                print(f"Profile on {ip} is already set to {tuned_profile_name}. No changes made.")



#
# def update_ring_buffer(adapter_name: str, node_ips: list, tx_value, rx_value):
#     """Function update on remote host ring buffer
#     :return:
#     """
#     for ip in node_ips:
#         ssh_command(
#             ip, f"sudo ethtool -G adapter_name rx {tx_value} tx {tx_value}",
#             password="your_password")
#
#
# def update_tuned(tuned_profile_name: str, node_ips: list):
#     """Function update on remote host tuned profile
#     """
#     for ip in node_ips:
#         profile_name = ssh_command(ip, "sudo tuned-adm active | awk '{print $NF}'", password="your_password")
#         print(f"Active profile on {ip}: {profile_name}")
#         if profile_name != tuned_profile_name:
#             print(f"Setting profile tuned_profile_name on {ip}...")
#             ssh_command(ip, f"sudo tuned-adm profile {TUNED_PROFILE_NAME}", password="your_password")
#             ssh_command(ip, "sudo reboot", password="your_password")
#         else:
#             print(f"Profile on {ip} is already set to {TUNED_PROFILE_NAME}. No changes made.")
#

def main(args):
    """

    :return:
    """
    public_key_path = f"{expanduser('~')}/.ssh/id_rsa.pub"
    tuned_profile = f"/usr/lib/tuned/{args.tuned_profile_name}/tuned.conf"
    node_names, node_ips = get_node_names_and_ips(args.node_pool_name)
    print(node_names, node_ips)

    # print("Node IPs:", node_ips)
    #
    # push_keys(node_ips, public_key_path, args.username, args.password)
    # update_ring_buffer(node_ips, args.default_uplink, args.username, args.password)
    # update_tuned(node_ips, args.tuned_profile_name, f"/usr/lib/tuned/{args.tuned_profile_name}/tuned.conf",
    #              args.username, args.password)


# # Modify tuned profile configurations as needed...

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Node configuration script.")
    parser.add_argument("--node-pool-name", default="vf-test-np1-", help="Name of the node pool.")
    parser.add_argument("--default-uplink", default="eth0", help="Default network uplink.")
    parser.add_argument("--tuned-profile-name", default="mus", help="Tuned profile name.")
    parser.add_argument("--username", default="capv", help="Username for SSH.")
    parser.add_argument("--password", help="Password for SSH (optional).")
    args = parser.parse_args()
    main(args)
