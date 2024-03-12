"""
EsxiMetricCollector, designed to collect and vectorize metric
from esxi hosts

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import json
from typing import List, Dict, Union, Tuple, Any, Optional
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from warlock.esxi_state import EsxiStateReader


class EsxiMetricCollector:

    def __init__(
            self,
            esxi_states: List[EsxiStateReader],
    ):
        self.esxi_state_reader = esxi_states

    def map_vm_hosts_port_ids(
            self,
            vm_names: List[str]
    ):
        """
        Returns a dictionary mapping VM names to their port IDs and ESXi host.
        Once a VM is found on one ESXi host, it's not searched for again on another host.

        Example output:
        {
            'my-test-np1-h5mtj-9cf8fdcf6xcfln5-k9jcm': {
                'port_ids': [67108902, 100663326, 100663327, 100663333, 134217757, 134217760, 134217761, 134217762],
                'esxi_host': '10.x.x.x'
            },
            'my-test-np1-h5mtj-9cf8fdcf6xcfln5-k6mdx': {
                'port_ids': [67112135, 100666566, 100666638, 100666639, 134221065, 134221066, 134221067, 134221068],
                'esxi_host': '10.x.x.x'
            }
        }
        """
        vm_to_port_ids = {}
        remaining_vm_names = set(vm_names)

        for esxi_state in self.esxi_state_reader:
            if not remaining_vm_names:
                break

            vm_port_id_map = esxi_state.read_netstats_vm_net_port_ids()
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
            self,
            vm_names: List[str],
            vmnic_name: Dict[str, str]
    ):
        """
        Returns a dictionary mapping VM names to their port IDs, ESXi host,
        and port VM NIC names filtered by the specified adapter name.

        Once a VM is found on one ESXi host, it's not searched
        for again on another host.

        vm_names is list of VM that we want resolve
        vmnic_name is dict where key is VM name and adapter name.

        :param vm_names: List of VM names to map.
        :param vmnic_name: Dictionary of VM names to their target adapter names.
        :return: Dictionary mapping VM names to their details including filtered port VM NIC names.
        """
        vm_to_port_ids = {}
        remaining_vm_names = set(vm_names)

        for esxi_state in self.esxi_state_reader:
            if not remaining_vm_names:
                break

            vm_port_id_map = esxi_state.read_netstats_vm_net_port_ids()
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
            self,
            esxi_fqdn: str
    ) -> Union[None, EsxiStateReader]:
        """Returns the EsxiState object for the given ESXi host (FQDN or IP).
        :param esxi_fqdn: IP or hostname address of the ESXi
        :return:  EsxiState object
        """
        for esxi_state in self.esxi_state_reader:
            if esxi_state.fqdn == esxi_fqdn:
                return esxi_state
        return None

    @staticmethod
    def vectorize_data(
            data: dict,
            vm_index: int
    ) -> np.ndarray:
        """Take data stats and vectorized set of values that we use in downstream task
        :param data:  Dictionary is dictionary object hold sample
        :param vm_index:  Index of the VM.
        :return:
        """
        temp_data = []
        for stat in data['stats']:
            for port in stat['ports']:
                temp_data.append((
                    vm_index,
                    port.get('id', 0),
                    port.get('txpps', 0),
                    port.get('rxpps', 0),
                    port.get('txdisc', 0),
                    port.get('dropsByBurstQ', 0),
                    port.get('droppedbyQueuing', 0),
                    port.get('intr', {}).get('count', 0)
                ))
        return np.array(temp_data)

    def __fetch_and_vectorize_data(
            self,
            esxi_state,
            vm_data,
            vm_index,
            is_sriov: bool = False
    ):
        filtered_adapter_names = [
            nic_name for nic_name in vm_data['port_vm_nic_name']
            if ("SRIOV" not in nic_name) or (is_sriov and "SRIOV" in nic_name)
        ]
        filtered_adapter_name = filtered_adapter_names[0]
        stats = esxi_state.read_netstats_by_vm(filtered_adapter_name)
        return self.vectorize_data(stats, vm_index)

    def collect_vm_port_metrics(
            self,
            vm_names: List[str],
            vmnic_name: Dict[str, str],
            is_sriov: bool = False,
            num_sample: int = 1,
            interval: int = 10
    ) -> np.ndarray:
        """This method take list of VM and dictionary of adapter name.
        and collect metrics.

        For example vm_names=["vm1", "vm2"]
        vmnic_name={"vm1": "eth0", "vm2": "eth1"}

        This method will collect the metrics for vm1 , eth0 adapters
        and then collect the metrics for vm2 , eth1.

        The data vectorized where first col is index of VM and second index
        is index of VMNIC/VNIC.

        :param vm_names:  a list of VM names
        :param vmnic_name:  a dictionary of adapter name
        :param is_sriov:    whether to collect metrics for sriov or vmxnet3
        :param num_sample: number of samples to collect
        :param interval:    how often
        :return:
        """
        vm_to_port_ids = self.filtered_map_vm_hosts_port_ids(vm_names, vmnic_name)
        indices_map = {vm_name: index for index, vm_name in enumerate(vm_names)}

        all_vectorized_data = []

        with ThreadPoolExecutor(max_workers=len(vm_names)) as executor:
            futures = []
            for _ in range(num_sample):
                for vm_name, vm_data in vm_to_port_ids.items():
                    esxi_state = self.get_esxi_state(vm_data['esxi_host'])
                    if esxi_state:
                        futures.append(
                            executor.submit(
                                self.__fetch_and_vectorize_data,
                                esxi_state,
                                vm_data,
                                indices_map[vm_name],
                                is_sriov
                            )
                        )

                for future in as_completed(futures):
                    all_vectorized_data.append(future.result())

                if _ < num_sample - 1:
                    time.sleep(interval)

        if all_vectorized_data:
            return np.concatenate(all_vectorized_data)

        return np.array([])