import json
import logging
import time
from collections import namedtuple
from typing import Optional, Dict, List
import threading

from warlock.callbacks.callback import Callback
from warlock.spell_specs import SpellSpecs
from warlock.states.esxi_state_reader import EsxiStateReader
from warlock.states.node_state_reader import NodeStateReader
from warlock.states.vm_state import VMwareVimStateReader
from warlock.callbacks.named_tuples import (
    HostVmnicInfo,
    MacAddressState, VmState
)


class CallbackNodeObserver(Callback['WarlockState']):
    """
    """
    def __init__(
            self,
            spell_master_specs: SpellSpecs,
            dry_run: Optional[bool] = True,
            logger: Optional[logging.Logger] = None,
            reuse_existing: Optional[bool] = False,
    ):
        """
        Create Pod Operator
        :param spell_master_specs:
        :param dry_run:
        :param logger:
        :param reuse_existing:
        """
        super().__init__()
        self.logger = logger if logger else logging.getLogger(__name__)
        self._master_spell_spec = spell_master_specs

        self.is_dry_run = dry_run
        self.dry_run_plan = []
        self._abs_dir = self._master_spell_spec.absolute_dir

        # re-use exiting won't delete pod and re-use existing pods
        self._reuse_existing = reuse_existing
        # default wait time
        self._timeout = 30
        self._default_timeout = self._timeout

    def _log_dry_run_operation(
            self,
            ops: str,
    ):
        """
        Log an operation that would be executed during a dry run.
        """
        operation = {
            "operation": ops,
        }
        self.dry_run_plan.append(operation)

    def get_dry_run_plan(self):
        """
        Retrieve the plan of operations
        that would be executed during a dry run.
        :return: A list of planned operations.
        """
        return self.dry_run_plan

    def on_scenario_begin(self):
        """
        On scenario begin, this callback read information
        from all worker node.
        """
        self.logger.info("CallbackNodeObserver scenario begin")
        spell = self._master_spell_spec.caas_spells()
        for k, pod_state in self.caster_state.k8s_pods_states.items():
            if 'node_ip' not in pod_state or pod_state['node_ip'] is None:
                continue

            node_address = pod_state['node_ip']
            with NodeStateReader.from_optional_credentials(
                        node_address=node_address,
                        username=spell['username'],
                        password=spell['password']) as node_host_reader:
                pci_device_dict = node_host_reader.read_pci_devices()
                self.logger.info(f"connecting to a node {node_address} "
                                 f"username {spell['username']} password {spell['password']}")
                self.caster_state.k8s_node_states[node_address] = pci_device_dict



