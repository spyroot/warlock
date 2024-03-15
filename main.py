#
# . Initial sketch prototype
#  - main idea the agent perform set of acton that mutate target environment
#  - the environment is kubernetes node.  The goal for the agent find optimal
#  - set of configration that maximize set of metric. We can define metric as
#  - packet per second for network, latency , storage IO etc.
#
#
import argparse
import logging

from warlock.callbacks.callback_pod_operator import CallbackPodsOperator
from warlock.spell_specs import SpellSpecs
from warlock.states.kube_state_reader import KubernetesState
from warlock.warlock import WarlockSpellCaster


def configure_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
    configure_logging()

    master_spell = SpellSpecs(cmd_args.spell_file)
    warlock = WarlockSpellCaster(
        callbacks=[CallbackPodsOperator(
            spell_master_specs=master_spell)
        ],
        spells_specs=master_spell
    )
    warlock.show_spells()
    warlock.cast_spell()

    # cast_spell(self):
    # kube_state = KubernetesState()
    # nodes = kube_state.fetch_nodes_uuid_ip(args.node_pool_name)
    # test_environment_spec = prepare_environment(kube_state, cmd_args.test_spec)
    #
    # vcenter_ip = os.getenv('VCENTER_IP', 'default')
    # username = os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local')
    # password = os.getenv('VCENTER_PASSWORD', 'default')
    #
    # # a test VM that we know exists
    # self._test_valid_vm_name = os.getenv('TEST_VM_NAME', 'default')
    # self._test_valid_vm_substring = os.getenv('TEST_VMS_SUBSTRING', 'default')
    #
    # ssh_executor = None
    # self.vmware_vim_state = VMwareVimState.from_optional_credentials(
    #     ssh_executor, vcenter_ip=vcenter_ip,
    #     username=username,
    #     password=password
    # )

    # node_ips = kube_state.node_ips()
    # print(node_ips)
    # print(test_environment_spec)

    #
    # ssh_runner = SSHOperator(kube_state.node_ips(), username="capv", password="VMware1!")
    # node_actions = NodeActions(
    #     kube_state.node_ips(),
    #     ssh_runner,
    #     test_environment_spec
    # )
    #
    # # mutate environment
    # node_actions.update_ring_buffer()
    # node_actions.update_active_tuned()
    # # run experiment
    # test_result = node_actions.start_environment()
    #
    # # vectorize and save result
    # iperf_tcp_json_to_np(test_result)
    # plot_tcp_perf(test_result, "bps", "plots", "bps_per_core_ring_size4096.png")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Node configuration script.")
    # parser.add_argument("--node-pool-name", default="vf-test-np1-", help="Name of the node pool.")
    # parser.add_argument("--default-uplink", default="eth0", help="Default network uplink.")
    # parser.add_argument("--tuned-profile-name", default="mus", help="Tuned profile name.")
    # parser.add_argument("--username", default="capv", help="Username for SSH.")
    # parser.add_argument("--password", help="Password for SSH (optional).")
    parser.add_argument("--spell_file", default="spell.json", help="a master spell warlock will read")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")

    args = parser.parse_args()
    main(args)
