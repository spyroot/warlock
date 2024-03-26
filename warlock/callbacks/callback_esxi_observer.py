import json
import logging
import time
from collections import namedtuple
from typing import Optional, Dict, List
import threading

from warlock.callbacks.callback import Callback
from warlock.spell_specs import SpellSpecs
from warlock.states.esxi_state_reader import EsxiStateReader
from warlock.states.vm_state import VMwareVimStateReader
from warlock.callbacks.named_tuples import (
    HostVmnicInfo,
    MacAddressState, VmState
)


class CallbackEsxiObserver(Callback['WarlockState']):
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

    def _process_vm_process_state(
            self,
            esxi_state_reader: EsxiStateReader,
            vm_name: str,
            esxi_host: str
    ) -> None:
        """
        Process and collect data for a given VM from the ESXi host and update the caster state directly.

        THis method resolve VM name to WorldID and VMXCartelID hence on downstream task
        we can capture observation (cpu , netio)

        :param esxi_state_reader: An instance of EsxiStateReader connected to the ESXi host.
        :param vm_name: The name of the VM to process.
        :param esxi_host: The ESXi host being processed.
        """
        vm_process_list = esxi_state_reader.read_vm_process_list()

        for vm in vm_process_list:
            if vm['DisplayName'].strip() == vm_name.strip():
                # a  key esxi host capture data related what we see on esxi
                if esxi_host not in self.caster_state.esxi_node_states:
                    self.caster_state.esxi_node_states[esxi_host] = {}

                self.caster_state.esxi_node_states[esxi_host][vm_name] = {
                    'ConfigFile': vm.get('ConfigFile'),
                    'UUID': vm.get('UUID'),
                    'VMXCartelID': vm.get('VMXCartelID'),
                    'WorldID': vm.get('WorldID')
                }
                break

    def _process_port_ids(
            self,
            esxi_state_reader: EsxiStateReader,
            esxi_host: str,
            vm_name: str,
    ) -> None:
        """
        Process and collect port ID information for a given VM from the ESXi
        host and update the caster state directly.

        This method resolves all NICs, both SR-IOV and non-SRIOV, to internal IDs.

        :param esxi_state_reader: An instance of EsxiStateReader connected to the ESXi host.
        :param esxi_host: The ESXi host being processed.
        :param vm_name: The name of the VM to process.
        """
        self.logger.debug(f"Processing port IDs for "
                          f"VM '{vm_name}' on ESXi host '{esxi_host}'")

        if self.caster_state.esxi_node_states is None:
            self.caster_state.esxi_node_states = {}
            self.logger.debug("Initialized esxi_node_states in caster state")

        if esxi_host not in self.caster_state.esxi_node_states:
            self.caster_state.esxi_node_states[esxi_host] = {}
            self.logger.debug(f"Added ESXi host '{esxi_host}' to esxi_node_states")

        vnics_vf_to_port_ids = esxi_state_reader.filtered_map_vm_hosts_port_ids(
            vm_names=[vm_name]
        )
        if vm_name in vnics_vf_to_port_ids:
            self.caster_state.esxi_node_states[esxi_host][vm_name]['port_ids'] = vnics_vf_to_port_ids[vm_name]
        else:
            self.caster_state.esxi_node_states[esxi_host][vm_name]['port_ids'] = []

    def _process_vfs_ids(
            self,
            esxi_state_reader: EsxiStateReader,
            esxi_host: str,
            vm_name: str
    ) -> None:
        """
        Process and filter Virtual Functions (VFs) based on the WorldID of a VM.

        :param esxi_state_reader: An instance of EsxiStateReader connected to the ESXi host.
        :param esxi_host: The ESXi host being processed.
        :param vm_name: The name of the VM to process.
        """
        _vm_state = self.caster_state.iaas_state[vm_name]
        world_id = str(self.caster_state.esxi_node_states[esxi_host][vm_name]['WorldID'])
        pnic_info = _vm_state.pnic_map

        self.caster_state.esxi_node_states[esxi_host][vm_name]['active_vfs'] = {}

        for sriov_nic_name in pnic_info.sriov_vmnic:
            vfs_data = esxi_state_reader.read_vfs(pf_adapter_name=sriov_nic_name)
            active_vfs = [vf for vf in vfs_data if vf['Active'] and vf['OwnerWorldID'] == world_id]
            self.caster_state.esxi_node_states[esxi_host][vm_name]['active_vfs'] = active_vfs

    def collect_data(
            self,
            vm_name,
            spell
    ):
        """
        :param vm_name:
        :param spell:
        :return:
        """
        try:
            vm_info = self.caster_state.iaas_state[vm_name]
            esxi_host = vm_info.state['esxiHost']
            with EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=esxi_host,
                    username=spell.get('hosts_username', 'root'),
                    password=spell.get('hosts_password', '')
            ) as esxi_state_reader:
                self.logger.info(f"Collecting data from ESXi host: {esxi_host}")
                self._process_vm_process_state(esxi_state_reader, vm_name, esxi_host)
                self._process_port_ids(esxi_state_reader, esxi_host, vm_name)
                self._process_vfs_ids(esxi_state_reader, esxi_host, vm_name)

        except Exception as e:
            self.logger.error(f"Error collecting data from ESXi host {esxi_host}: {e}")

    def on_scenario_begin(self):
        """
        On scenario begin, this callback queries each ESXi host and
        reads all state values.
        """
        self.logger.info("CallbackEsxiObserver scenario begin")

        if self.caster_state.iaas_state is None or 'hosts' not in self.caster_state.iaas_state:
            self.logger.error("No ESXi hosts found in caster state.")
            return

        self.logger.info(f"ESXi host: {self.caster_state.iaas_state['hosts']}")

        spell = self._master_spell_spec.iaas_spells()
        vm_list = self.caster_state.iaas_state['vms']

        threads = []

        for vm_name in vm_list:
            thread = threading.Thread(target=self.collect_data, args=(vm_name, spell))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.logger.info("Final ESXi node states:")
        self.logger.info(json.dumps(self.caster_state.esxi_node_states, indent=2))

    def on_scenario_end(self):
        """
        :return:
        """
        self.logger.info("CallbackIaasObserver scenario end")
