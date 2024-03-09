#
# . Initial sketch prototype
#  - main idea the agent perform set of acton that mutate target environment
#  - the environment is kubernetes node.  The goal for the agent find optimal
#  - set of configration that maximize set of metric. We can define metric as
#  - packet per second for network, latency , storage IO etc.
#
#
import argparse
from pathlib import Path

from warlock.kube_state import KubernetesState
from warlock.node_actions import NodeActions
from warlock.ssh_operator import SSHOperator
from warlock.inference import (
    iperf_tcp_json_to_np, plot_tcp_perf
)

import json


def prepare_environment(
        kube_state: KubernetesState,
        scenario_file: str,
):
    """Read scenario from a json file and kubernetes pods used to evaluate
    a result.  i.e. we mutate a node, and we use pod to observer a result.

    After pod create we update scenario file and add pod IP address.

    :return:
    """
    with open(scenario_file, 'r') as file:
        test_spec = json.load(file)
        server_config = test_spec.get('environment', {}).get('server', {})
        client_config = test_spec.get('environment', {}).get('client', {})

        server_pod_spec = Path(server_config.get('pod_spec')).resolve().absolute()
        client_pod_spec = Path(client_config.get('pod_spec')).resolve().absolute()

        server_pod_name = server_config.get('pod_name')
        client_pod_name = client_config.get('pod_name')

        node_output = KubernetesState.run_command(f"kubectl apply -f {server_pod_spec}")
        server_pod_spec = kube_state.read_pod_spec(server_pod_name)
        server_pod_ip = server_pod_spec.get('status', {}).get('podIPs', [])[0].get('ip')

        node_output = KubernetesState.run_command(f"kubectl apply -f {client_pod_spec}")
        server_pod_spec = kube_state.read_pod_spec(server_pod_name)
        client_pod_ip = server_pod_spec.get('status', {}).get('podIPs', [])[0].get('ip')

        server_config['ip'] = server_pod_ip
        client_config['ip'] = client_pod_ip

    return test_spec


def debug_info(kube_state: KubernetesState):
    """

    :param kube_state:
    :return:
    """
    print(kube_state.node_names())
    print(kube_state.pod_node_ns_names(ns="all"))
    print(kube_state.pods_name())
    print(kube_state.read_kube_config())
    print(kube_state.read_cluster_name())


def main(cmd_args):
    """
    :return:
    """
    kube_state = KubernetesState()
    nodes = kube_state.fetch_nodes_uuid_ip(args.node_pool_name)

    test_environment_spec = prepare_environment(kube_state, cmd_args.test_spec)
    print(test_environment_spec)

    ssh_runner = SSHOperator(kube_state.node_ips(), username="capv", password="VMware1!")
    node_actions = NodeActions(
        kube_state.node_ips(),
        ssh_runner,
        test_environment_spec
    )

    # mutate environment
    node_actions.update_ring_buffer()
    node_actions.update_active_tuned()
    # run experiment
    test_result = node_actions.start_environment()

    # vectorize and save result
    iperf_tcp_json_to_np(test_result)
    plot_tcp_perf(test_result, "bps", "plots", "bps_per_core_ring_size4096.png")


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
