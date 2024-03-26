import json
import logging
import time
from collections import namedtuple
from typing import Optional, Dict, List

from warlock.callbacks.callback import Callback
from warlock.spell_specs import SpellSpecs
from warlock.states.vm_state import VMwareVimStateReader
from warlock.callbacks.named_tuples import (
    HostVmnicInfo,
    MacAddressState, VmState
)


class CallbackIaasObserver(Callback['WarlockState']):
    """
    This class is designed to adjust the RX and TX ring sizes for network adapters
    across a list of ESXi hosts. It receives a list of dictionaries detailing NICs,
    RX, and TX values for each host, and a list of EsxiStateReader objects to interact
    with the ESXi hosts.
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

    @staticmethod
    def transform_to_dict(moids, names):
        """
        Transforms two lists into a dictionary where the cluster name is the key
        and the MOID is the value.

        :param moids: List of MOIDs (Managed Object Identifiers) as strings.
        :param names: List of cluster names as strings.
        :return: Dictionary with cluster names as keys and MOIDs as values.
        """
        return dict(zip(names, moids))

    @staticmethod
    def _extract_vmnic_info_from_state(
            vm_data: Dict
    ) -> HostVmnicInfo:
        """
        Extracts VMNIC information by ESXi host,
        separating non-SRIOV and SRIOV vmnic.

        :param vm_data: The complete data structure containing VM information.
        :return: A dictionary with ESXi hosts as keys, and HostVmnicInfo named tuples as values.
        """
        for vm_name, vm_info in vm_data.items():
            esxi_host = vm_info.get('esxiHost')
            pnic_data = vm_info.get('pnic_data', {})
            sriov_adapters = vm_info.get('sriov_adapters', [])

            all_pnics = set()
            for switch_uuid, ip_data in pnic_data.items():
                for ip, vmnics in ip_data.items():
                    all_pnics.update(vmnics)

            sriov_pnics = set(adapter.get('pNIC') for adapter in sriov_adapters)
            non_sriov_vmnic = list(all_pnics - sriov_pnics)
            sriov_vmnic = list(sriov_pnics)

            return HostVmnicInfo(
                host=esxi_host,
                vnic=non_sriov_vmnic,
                sriov_vmnic=sriov_vmnic
            )

        return HostVmnicInfo(host=None, vnic=[], sriov_vmnic=[])

    def on_scenario_begin(self):
        """
        On scenario begin this callback query and resolve set of IaaS resource,
        i.e. it read current state.

        caster_state.iaas_state['reader'] hold a current state reader object created.
        Follow up, IaaS reader call back can re-use same object.

        Note most callback implemented caching to reduce RTT time for read operation.
        Thus, it preferable to re-use same reader to get reduce read time.

        If we do not mutate IaaS stata. i.e. VM run on same host, use same SRIOV
        there is no point to fetch from server since we mutate same object.

        self.caster_state.iaas_state['hosts'] store list of IaaS hosts
        that callback resolved.

        The callback uses substring to match set of VM that are target
        VM for a particular experiment.  For example in case simple two POD kubernetes
        (worker node and VM 1:1 relation) we resolve to set of ESXi host.

        "vm_template_name": "test-np1",

        self.caster_state.iaas_state['hosts']
        [
            "10.252.80.109",
            "10.252.80.107"
        ]

        Note none of callback do any validation, all spec validation must
        be done in processing state.

        :return:
        """
        self.logger.info("CallbackIaasObserver scenario begin")

        spell = self._master_spell_spec.iaas_spells()

        state_reader = VMwareVimStateReader.from_optional_credentials(
            spell['host'],
            spell['username'],
            spell['password'],
        )

        if self.caster_state.iaas_state is None:
            self.caster_state.iaas_state = {}

        self.caster_state.iaas_state['reader'] = state_reader
        self.caster_state.iaas_state['hosts'] = []
        self.caster_state.iaas_state['vms'] = []

        vms_name = state_reader.find_vm_by_name_substring(spell['vm_template_name'])

        start_time = time.time()
        self.logger.info(f"find_vm_by_name_substring took {time.time() - start_time:.2f} seconds")

        for _vm in vms_name:

            vm_name = _vm.name
            start_time = time.time()
            state = state_reader.vm_state(vm_name)

            if _vm not in self.caster_state.iaas_state:
                self.caster_state.iaas_state[vm_name] = {}

            self.logger.info(f"vm_state for {vm_name} took {time.time() - start_time:.2f} seconds")
            pnic_named = CallbackIaasObserver._extract_vmnic_info_from_state(state)

            start_time = time.time()
            _vnics = state_reader.read_vm_vnic_info(vm_name)
            self.logger.info(
                f"_extract_vmnic_from_state for {vm_name} took {time.time() - start_time:.2f} seconds")

            non_sriov_mac_addresses = [vnic['macAddress'] for vnic in _vnics if not vnic.get('is_sriov')]
            sriov_mac_addresses = [vnic['macAddress'] for vnic in _vnics if vnic.get('is_sriov')]

            self.caster_state.iaas_state[vm_name] = VmState(
                state=state[vm_name],
                pnic_map=pnic_named,
                mac=MacAddressState(
                    vnic=non_sriov_mac_addresses,
                    sriov=sriov_mac_addresses
                )
            )

            self.caster_state.iaas_state['vms'].append(vm_name)
            self.caster_state.iaas_state['hosts'].append(pnic_named.host)

    def on_scenario_end(self):
        """
        :return:
        """
        self.logger.info("CallbackIaasObserver scenario end")
