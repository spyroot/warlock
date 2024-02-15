#
# . Initial sketch prototype
#  - main idea the agent perform set of acton that mutate target environment
#  - the environment is kubernetes node.  The goal for the agent find optimal
#  - set of configration that maximize set of metric. We can define metric as
#  - packet per second for network, latency , storage IO etc.
#
#
import json
import subprocess
from pathlib import Path
from typing import List

import paramiko
from os.path import expanduser
import argparse

from kube_state import KubernetesState
from node_actions import NodeActions
from ssh_runner import SshRunner


def main(cmd_args):
    """

    :return:
    """
    kube_state = KubernetesState()
    nodes = kube_state.fetch_nodes_uuid_ip(args.node_pool_name)

    print(kube_state.node_names())
    print(kube_state.pod_node_ns_names(ns="all"))
    print(kube_state.pods_name())
    print(kube_state.read_kube_config())
    print(kube_state.read_cluster_name())

    print(cmd_args.test_spec)
    with open(cmd_args.test_spec, 'r') as file:
        test_spec = json.load(file)
        server_config = test_spec.get('environment', {}).get('server', {})
        client_config = test_spec.get('environment', {}).get('client', {})
        server_pod_spec = Path(server_config.get('pod_spec')).resolve().absolute()
        client_pod_spec = Path(client_config.get('pod_spec')).resolve().absolute()
        node_output = KubernetesState.run_command(f"kubectl apply -f {server_pod_spec}")
        node_output = KubernetesState.run_command(f"kubectl apply -f {client_pod_spec}")

    #
    # ssh_runner = SshRunner(kube_state.node_ips(), username="capv", password="VMware1!")
    # node_actions = NodeActions(kube_state.node_ips(), ssh_runner)
    #
    # node_actions.update_ring_buffer()
    # node_actions.update_active_tuned()
    # node_actions.run_iperf_test()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Node configuration script.")
    parser.add_argument("--node-pool-name", default="vf-test-np1-", help="Name of the node pool.")
    parser.add_argument("--default-uplink", default="eth0", help="Default network uplink.")
    parser.add_argument("--tuned-profile-name", default="mus", help="Tuned profile name.")
    parser.add_argument("--username", default="capv", help="Username for SSH.")
    parser.add_argument("--password", help="Password for SSH (optional).")
    parser.add_argument("--test_spec", default="mutate.json", help="test scenarion")

    args = parser.parse_args()
    main(args)
