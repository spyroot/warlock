"""
unit test for VMware VM state.

Author: Mustafa Bayramov
spyroot@gmail.com
mbayramo@stanford.edu

"""
import json
import os
import unittest
import time

from warlock.vm_state import VMwareVimState, SwitchNotFound, EsxHostNotFound, VMNotFoundException


class TestVMwareVimState(unittest.TestCase):
    def setUp(self):
        """

        :return:
        """
        vcenter_ip = os.getenv('VCENTER_IP', 'default')
        username = os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local')
        password = os.getenv('VCENTER_PASSWORD', 'default')
        self._test_vm_name = os.getenv('TEST_VM_NAME', 'default')
        self._test_vm_substring = os.getenv('TEST_VMS_SUBSTRING', 'default')

        ssh_executor = None
        self.vmware_vim_state = VMwareVimState.from_optional_credentials(
            ssh_executor, vcenter_ip=vcenter_ip,
            username=username,
            password=password
        )

    def test_find_by_dns_name_returns_none(self):
        """Basic test for _find_by_dns_name to ensure
        it returns a VM and caches it correctly.
        :return:
        """
        _vm = self.vmware_vim_state._find_by_dns_name("")
        self.assertIsNone(
            _vm,
            "The VM object returned by _find_by_dns_name should be None"
        )

    def test_find_by_dns_name_returns_vm(self):
        """Basic test for _find_by_dns_name to ensure
        it returns a VM and caches it correctly.
        :return:
        """
        _vm = self.vmware_vim_state._find_by_dns_name(self._test_vm_name)
        self.assertIsNotNone(
            _vm,
            "The VM object returned by _find_by_dns_name should not be None"
        )
        self.assertIn(
            self._test_vm_name,
            self.vmware_vim_state._vm_cache,
            f"The key '{self._test_vm_name}' should be in the _vm_cache"
        )
        self.assertIsNotNone(
            self.vmware_vim_state._vm_cache[self._test_vm_name],
            f"The object in _vm_cache for key '{self._test_vm_name}' should not be None"
        )

    def test_cached_find_by_dns_name_returns_vm(self):
        """Basic test for _find_by_dns_name to ensure it returns a VM
        from caches and measures execution time.
        :return:
        """

        self.vmware_vim_state._vm_cache.pop(self._test_vm_name, None)
        start_time_first_call = time.time()
        first_vm = self.vmware_vim_state._find_by_dns_name(self._test_vm_name)
        end_time_first_call = time.time()

        self.assertIsNotNone(
            first_vm,
            "The VM object returned by _find_by_dns_name should not be None after the first call"
        )
        self.assertIn(
            self._test_vm_name, self.vmware_vim_state._vm_cache,
            f"The key '{self._test_vm_name}' should be in the _vm_cache after the first call"
        )

        self.assertIsNotNone(
            self.vmware_vim_state._vm_cache[self._test_vm_name],
            f"The object in _vm_cache for key '{self._test_vm_name}' should not be None")

        start_time_second_call = time.time()
        second_vm = self.vmware_vim_state._find_by_dns_name(self._test_vm_name)
        end_time_second_call = time.time()

        self.assertIsNotNone(
            second_vm,
            "The VM object returned by _find_by_dns_name should not be None after the second call"
        )
        self.assertEqual(
            first_vm, second_vm,
            "The VM object returned should be the same for both calls"
        )

        self.assertTrue(
            (end_time_second_call - start_time_second_call) < (end_time_first_call - start_time_first_call),
            "Second call should be faster due to caching"
        )

    def test_vm_uuid(self):
        """Basic test for find_by_dns_name
        :return:
        """
        _vm_uuid = self.vmware_vim_state.read_vm_uuid(self._test_vm_name)
        self.assertIsNotNone(
            _vm_uuid,
            "The VM object returned by read_vm_uuid should not be None"
        )

        uuid_pattern = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
        self.assertIsNotNone(
            _vm_uuid, "The vm_uuid method should return a UUID string, not None"
        )
        self.assertRegex(
            _vm_uuid, uuid_pattern,
            "The returned UUID does not match the expected format"
        )

    def test_vm_not_found_empty(self):
        """Basic test for find_by_dns_name
        :return:
        """
        _vm_uuid = self.vmware_vim_state.read_vm_uuid("")
        self.assertIsNone(
            _vm_uuid,
            "The VM object should be None"
        )

    def test_read_vm_numa_not_found(self):
        """Basic test for find_by_dns_name
        :return:
        """
        _vm_numa_info = self.vmware_vim_state.read_vm_numa_info(self._test_vm_name)
        self.assertIsNotNone(
            _vm_numa_info,
            "The VM numa info returned by read_vm_numa_info should not be None"
        )
        d = self.vmware_vim_state.vmware_obj_as_json(_vm_numa_info)
        self.assertIn(
            'coresPerNumaNode',
            d, "'coresPerNumaNode' key should be present in the VM NUMA info"
        )

    def test_read_vm_extra_config(self):
        """Basic test for find_by_dns_name
        :return:
        """
        _vm_extra_config = self.vmware_vim_state.read_vm_extra_config(self._test_vm_name)
        self.assertIsNotNone(
            _vm_extra_config,
            "The VM extra info returned by read_vm_extra_config should not be None"
        )
        d = self.vmware_vim_state.vim_obj_to_dict(
            _vm_extra_config, no_dynamics=True
        )
        self.assertIsInstance(d, list, "'d' should be a list")
        for item in d:
            self.assertIsInstance(item, dict, "Each item in 'd' should be a dictionary")
            self.assertIn('key', item, "The item should have a 'key'")
            self.assertIn('value', item, "The item should have a 'value'")

    def test_find_by_substr(self):
        """Basic test to find vms by some string
        :return:
        """
        found_vms, found_vm_config = self.vmware_vim_state.find_vm_by_name_substring(self._test_vm_substring)
        self.assertIsNotNone(
            found_vms,
            "found VMs should not be None"
        )
        self.assertIsNotNone(
            found_vm_config,
            "found VMs confing should not be None"
        )

        cache_result = self.vmware_vim_state._vm_search_cache[self._test_vm_substring]
        self.assertIsNotNone(
            cache_result,
            "Search result should be cached"
        )
        self.assertIsInstance(
            cache_result, tuple,
            "Cached search result should be a tuple"
        )

        self.assertEqual(
            (found_vms, found_vm_config), cache_result,
            "The method's return value should match the cache result exactly"
        )

    def test_find_by_substr_result_from_cache(self):
        """Basic test to find vms by some string
        :return:
        """

        self.vmware_vim_state._vm_search_cache = {}
        start_time_first_call = time.time()
        found_vms, found_vm_config = self.vmware_vim_state.find_vm_by_name_substring(self._test_vm_substring)
        end_time_first_call = time.time()

        self.assertIsNotNone(
            found_vms,
            "found VMs should not be None"
        )
        self.assertIsNotNone(
            found_vm_config,
            "found VMs confing should not be None"
        )

        start_time_second_call = time.time()
        found_cache_vms, found_cached_vms_config = self.vmware_vim_state.find_vm_by_name_substring(
            self._test_vm_substring)
        end_time_second_call = time.time()

        self.assertIsNotNone(
            found_vms,
            "found VMs should not be None"
        )
        self.assertIsNotNone(
            found_vm_config,
            "found VMs confing should not be None"
        )

        self.assertTrue(
            (end_time_second_call - start_time_second_call) < (end_time_first_call - start_time_first_call),
            "Second call should be faster due to caching"
        )

        self.assertEqual(
            found_vms, found_cache_vms,
            "The method's return value should match the cache result exactly"
        )

    def test_read_all_dvs_specs(self):
        """Basic test to read all dvs and check that cache populated
        :return:
        """
        dvs_list = self.vmware_vim_state.read_all_dvs_specs()
        self.assertEqual(len(dvs_list), len(self.vmware_vim_state._dvs_uuid_to_dvs),
                         "The length of the returned DVS list should match the cache size.")

    def test_find_dvs_by_uuid(self):
        """Test return dvs by DVS uuid
        :return:
        """
        dvs_list = self.vmware_vim_state.read_all_dvs_specs()
        self.assertEqual(len(dvs_list), len(self.vmware_vim_state._dvs_uuid_to_dvs),
                         "The length of the returned DVS list should match the cache size.")

        for dvs_uuid in dvs_list:
            dvs_spec, dvs_config = self.vmware_vim_state.get_dvs_by_uuid(dvs_uuid)
            self.assertIsNotNone(
                dvs_spec,
                "dvs spec should not be None"
            )
            self.assertIsNotNone(
                dvs_config,
                "dvs config should not be None"
            )

    def test_find_dvs_by_uuid_not_found(self):
        """Test return dvs by DVS uuid
        :return:
        """
        with self.assertRaises(SwitchNotFound):
            _, _ = self.vmware_vim_state.get_dvs_by_uuid("test_not_found")

    def test_read_esxi_hosts(self):
        """Tests a read ESXI hosts method
        :return:
        """
        esxi_hosts = self.vmware_vim_state.read_esxi_hosts()
        self.assertEqual(
            len(self.vmware_vim_state.esxi_host_cache['uuid']),
            len(esxi_hosts),
            "The length of the returned esxi host list should match the cache size.")

    def test_read_esxi_mgmt_address(self):
        """Tests a read ESXI hosts method
        :return:
        """
        esxi_mgmt_address = self.vmware_vim_state.read_esxi_mgmt_address()
        self.assertIsInstance(esxi_mgmt_address, dict, "Expected a dictionary of ESXi management addresses.")
        for host, ips in esxi_mgmt_address.items():
            self.assertIsInstance(host, str, "Host identifier should be a string.")
            self.assertIsInstance(ips, list, f"Expected a list of IP addresses for {host}, got {type(ips)} instead.")
            for ip in ips:
                self.assertIsInstance(
                    ip, str,
                    f"Expected IP address to be a string "
                    f"for {host}, found {type(ip)} instead.")

    def test_read_esxi_host(self):
        """Tests a read ESXI hosts method
        :return:
        """
        esxi_hosts = self.vmware_vim_state.read_esxi_hosts()
        self.assertEqual(
            len(self.vmware_vim_state.esxi_host_cache['uuid']),
            len(esxi_hosts),
            "The length of the returned esxi host list should match the cache size.")

        for uuid, host in esxi_hosts.items():
            esxi_host = self.vmware_vim_state.read_esxi_host(uuid)
            self.assertEqual(esxi_host, host,
                             f"The ESXi host retrieved by UUID {uuid} "
                             f"should match the cached version.")

    def test_read_esxi_host_pnic(self):
        """Tests a read esxi pnic information
        :return:
        """
        esxi_hosts = self.vmware_vim_state.read_esxi_hosts()
        self.assertEqual(
            len(self.vmware_vim_state.esxi_host_cache['uuid']),
            len(esxi_hosts),
            "The length of the returned esxi host "
            "list should match the cache size.")

        for uuid, host in esxi_hosts.items():
            data = self.vmware_vim_state.read_esxi_host_pnic(uuid)
            self.assertIsInstance(data, dict, "'host pnic' should be a Dictionary")
            for pnic in data.values():
                self.assertIn('pci', pnic, "pNIC data should include 'pci'")
                self.assertIn('mac', pnic, "pNIC data should include 'mac'")
                self.assertIn('driver', pnic, "pNIC data should include 'driver'")
                self.assertIn('driver_version', pnic, "pNIC data should include 'driver_version'")
                self.assertIn('driver_firmware', pnic, "pNIC data should include 'driver_firmware'")

    def test_read_esxi_host_pnic_not_found(self):
        """Tests a read esxi pnic host not found exception
        :return:
        """
        with self.assertRaises(EsxHostNotFound):
            data = self.vmware_vim_state.read_esxi_host_pnic("not found")

    def test_find_esxi_host_pnic(self):
        """Tests a find esxi pnic by on pci device id
        :return:
        """
        esxi_hosts = self.vmware_vim_state.read_esxi_hosts()
        self.assertEqual(
            len(self.vmware_vim_state.esxi_host_cache['uuid']),
            len(esxi_hosts),
            "The length of the returned esxi host "
            "list should match the cache size.")

        for uuid, host in esxi_hosts.items():
            all_pnic_data = self.vmware_vim_state.read_esxi_host_pnic(uuid)
            self.assertIsInstance(all_pnic_data, dict, "'host pnic' should be a Dictionary")
            for pnic_info in all_pnic_data.values():
                self.assertIn('pci', pnic_info, "pNIC data should include 'pci'")
                found_pnic = self.vmware_vim_state.find_esxi_host_pnic(uuid, pnic_info['pci'])
                self.assertIsInstance(found_pnic, tuple, "find_esxi_host_pnic should return a tuple")
                vmnic_name, pnic_data = found_pnic
                self.assertEqual(
                    pnic_data, pnic_info,
                    "Found pNIC should match the pNIC data read for the host"
                )

    def test_find_esxi_host_pnic_not_found(self):
        """Tests a find esxi pnic by on pci device id
        :return:
        """
        esxi_hosts = self.vmware_vim_state.read_esxi_hosts()
        self.assertEqual(
            len(self.vmware_vim_state.esxi_host_cache['uuid']),
            len(esxi_hosts),
            "The length of the returned esxi host "
            "list should match the cache size.")

        for uuid, host in esxi_hosts.items():
            x, y = self.vmware_vim_state.find_esxi_host_pnic(uuid, "")
            self.assertIsNone(x, "find_esxi_host_pnic should return None")
            break

    def test_read_dvs_backend_pnics(self):
        """Tests a find esxi pnic by on pci device id
        :return:
        """
        dvs_spec = self.vmware_vim_state.read_all_dvs_specs()
        dvs_uuid = list(dvs_spec.keys())[0]
        dvs_pnic_data = self.vmware_vim_state.read_dvs_pnics_by_switch_uuid(dvs_uuid)
        self.assertIsNotNone(dvs_pnic_data, "read_dvs_pnics_by_switch_uuid should not return None")
        self.assertIsInstance(dvs_pnic_data, dict, "'host pnic' should be a Dictionary")

    def test_read_vm_pnic_info(self):
        """Tests a read vm's  pnic information
        :return:
        """
        vm_pnic_data = self.vmware_vim_state.read_vm_pnic_info(self._test_vm_name)
        self.assertIsNotNone(vm_pnic_data, "read_vm_pnic_info should not return None")
        self.assertIsInstance(vm_pnic_data, dict, "'host pnic' should be a Dictionary")

    def test_read_vm_pnic_info_not_found(self):
        """Tests a read vm's  pnic information
        :return:
        """
        with self.assertRaises(VMNotFoundException):
            _ = self.vmware_vim_state.read_vm_pnic_info("not found")

    def test_resolve_esxi_of_vm(self):
        """Tests a read vm's  pnic information
        :return:
        """
        vm_pnic_data = self.vmware_vim_state.get_esxi_ip_of_vm(self._test_vm_name)
        self.assertIsNotNone(vm_pnic_data, "get_esxi_ip_of_vm should not return None")

    def test_read_pci_devices(self):
        """Tests a read vm's  pnic information
        :return:
        """
        pci_devices = self.vmware_vim_state.read_pci_devices(self._test_vm_name)
        self.assertIsNotNone(pci_devices, "read_pci_devices should not return None")
        print(pci_devices)