#
# . Initial sketch prototype
#  - main idea the agent perform set of acton that mutate target environment
#  - the environment is kubernetes node.  The goal for the agent find optimal
#  - set of configration that maximize set of metric. We can define metric as
#  - packet per second for network, latency , storage IO etc.
#
#
import subprocess
from typing import List

import paramiko
from os.path import expanduser
import argparse

from nodes import KubernetesNodes


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
    node_names, node_ips = KubernetesNodes.get_node_names_and_ips(args.node_pool_name)
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
