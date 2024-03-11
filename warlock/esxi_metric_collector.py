import json
from typing import List, Dict, Union
from warlock.esxi_state import EsxiState


class EsxiMetricCollector:

    def __init__(
            self,
            esxi_states: List[EsxiState],
    ):
        self.esxi_state_reader = esxi_states

    def map_vm_hosts_port_ids(
            self, vm_names: List[str]):
        """
        Returns a dictionary mapping VM names to their port IDs and ESXi host.
        Once a VM is found on one ESXi host, it's not searched for again on another host.

        Example output:
        {
            'vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k9jcm': {
                'port_ids': [67108902, 100663326, 100663327, 100663333, 134217757, 134217760, 134217761, 134217762],
                'esxi_host': '10.252.80.107'
            },
            'vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k6mdx': {
                'port_ids': [67112135, 100666566, 100666638, 100666639, 134221065, 134221066, 134221067, 134221068],
                'esxi_host': '10.252.80.109'
            }
        }
        """
        vm_to_port_ids = {}
        remaining_vm_names = set(vm_names)

        for esxi_state in self.esxi_state_reader:
            if not remaining_vm_names:
                break

            vm_port_id_map = esxi_state.read_vm_net_port_id()
            found_vm_names = []
            for vm_name in remaining_vm_names:
                port_ids = [port_id for port_id, port_vm_name in vm_port_id_map.items()
                            if vm_name in port_vm_name]
                port_vm_nic_name = [port_vm_name for port_id, port_vm_name in vm_port_id_map.items()
                                    if vm_name in port_vm_name]
                if port_ids:
                    vm_to_port_ids[vm_name] = {
                        'port_ids': port_ids,
                        'esxi_host': esxi_state.fqdn,
                        'port_vm_nic_name': port_vm_nic_name
                    }
                    found_vm_names.append(vm_name)

            # remove found VMs
            remaining_vm_names -= set(found_vm_names)

        return vm_to_port_ids

    def filtered_map_vm_hosts_port_ids(
            self, vm_names: List[str], vmnic_name: Dict[str, str]):
        """
        Returns a dictionary mapping VM names to their port IDs, ESXi host, and port VM NIC names filtered
        by the specified adapter name.

        Once a VM is found on one ESXi host, it's not searched for again on another host.

        :param vm_names: List of VM names to map.
        :param vmnic_name: Dictionary of VM names to their target adapter names.
        :return: Dictionary mapping VM names to their details including filtered port VM NIC names.
        """
        vm_to_port_ids = {}
        remaining_vm_names = set(vm_names)

        for esxi_state in self.esxi_state_reader:
            if not remaining_vm_names:
                break

            vm_port_id_map = esxi_state.read_vm_net_port_id()
            found_vm_names = []
            for vm_name in remaining_vm_names:
                target_adapter = vmnic_name.get(vm_name, None)
                port_ids = []
                port_vm_nic_name = []

                for port_id, port_vm_name in vm_port_id_map.items():
                    if vm_name in port_vm_name and (target_adapter is None or target_adapter in port_vm_name):
                        port_ids.append(port_id)
                        port_vm_nic_name.append(port_vm_name)

                if port_ids:
                    vm_to_port_ids[vm_name] = {
                        'port_ids': port_ids,
                        'esxi_host': esxi_state.fqdn,
                        'port_vm_nic_name': port_vm_nic_name
                    }
                    found_vm_names.append(vm_name)

            # Remove found VMs
            remaining_vm_names -= set(found_vm_names)

        return vm_to_port_ids

    def get_esxi_state(
            self, esxi_fqdn: str
    ) -> Union[None, EsxiState]:
        """
        Returns the EsxiState object for the given ESXi host FQDN.
        """
        for esxi_state in self.esxi_state_reader:
            if esxi_state.fqdn == esxi_fqdn:
                return esxi_state
        return None

    @staticmethod
    def analyze_pps_and_drops(data):
        for stat in data['stats']:
            for port in stat['ports']:
                name = port['name']
                txpps = port.get('txpps', 0)
                rxpps = port.get('rxpps', 0)
                txdrops = port.get('txdisc', 0)

                drop_by_burst_q = port.get('dropsByBurstQ', 0)
                drop_by_q = port.get('droppedbyQueuing', 0)
                interrupts = port.get('intr', {}).get('count', 0)

                print(f"Port: {name}, TX PPS: {txpps}, RX PPS: {rxpps}, TX Drops: {txdrops}, "
                      f"Drops by Burst Q: {drop_by_burst_q}, Drops by Queuing: {drop_by_q}, "
                      f"Interrupts: {interrupts}")

    def collect_vm_port_metrics(
            self,
            vm_names: List[str],
            vmnic_name: Dict[str, str],
            is_sriov: bool = False
    ):
        """
        Collects VM port metrics filtered by VM NIC names
        and optionally filters out SRIOV NIC names.
        Note net-stat ESXi for same eth0 might return two names

        ['vm_name.eth0', 'SRIOVvm_name.eth0']

        if caller need vnic is_sriov must false otherwise if true method will collect
        stats for VF

        """
        if not all(vm_name in vmnic_name for vm_name in vm_names) or not all(
                key in vm_names for key in vmnic_name.keys()):
            raise ValueError("vmnic_name must contain the same keys as the list of VM names provided.")

        vm_to_port_ids = self.filtered_map_vm_hosts_port_ids(vm_names, vmnic_name)
        for vm_name, vm_data in vm_to_port_ids.items():
            esxi_state = self.get_esxi_state(vm_data['esxi_host'])
            if esxi_state:
                # Filter NIC names based on is_sriov flag
                filtered_adapter_names = [nic_name for nic_name in vm_data['port_vm_nic_name']
                                          if ("SRIOV" not in nic_name) or (is_sriov and "SRIOV" in nic_name)]
                filtered_adapter_name = filtered_adapter_names[0]
                stats = esxi_state.read_vm_net_stats(filtered_adapter_name)
                print(json.dumps(stats, indent=4))

        return {}


