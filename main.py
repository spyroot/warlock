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
import os

from warlock.callbacks.callback_esxi_observer import CallbackEsxiObserver
from warlock.callbacks.callback_iaas_observer import CallbackIaasObserver
from warlock.callbacks.callback_node_observer import CallbackNodeObserver
from warlock.callbacks.callback_node_tunner import CallbackNodeTunner
from warlock.callbacks.callback_pod_operator import CallbackPodsOperator
from warlock.callbacks.callback_ring_tunner import CallbackRingTunner
from warlock.callbacks.callback_state_printer import CallbackStatePrinter
from warlock.spell_specs import SpellSpecs
from warlock.states.kube_state_reader import KubernetesState
from warlock.warlock import WarlockSpellCaster


def configure_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
    Main function to execute the WarlockSpellCaster logic.
    """
    configure_logging()
    state_file_path = 'warlock_state.pkl'

    master_spell = SpellSpecs(cmd_args.spell_file)

    if os.path.exists(state_file_path):
        print("Loading saved state...")
        warlock = WarlockSpellCaster.create_from_state(
            state_file_path,
            state_callbacks=[
                CallbackStatePrinter(spell_master_specs=master_spell),
            ],
            spells_specs=master_spell
        )
    else:
        warlock = WarlockSpellCaster(
            state_callbacks=[
                CallbackPodsOperator(spell_master_specs=master_spell),
                CallbackIaasObserver(spell_master_specs=master_spell),
                CallbackEsxiObserver(spell_master_specs=master_spell),
                CallbackNodeObserver(spell_master_specs=master_spell),
                CallbackStatePrinter(spell_master_specs=master_spell),
            ],
            spells_specs=master_spell
        )
        warlock.save_state_to_file(state_file_path)

    warlock.cast_spell()


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
