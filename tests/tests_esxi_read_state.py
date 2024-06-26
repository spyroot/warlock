"""
Tests for reading state values from VMware Esxi

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""

import json
import os
import random

import numpy as np

from tests.extended_test_case import ExtendedTestCase
from tests.test_utils import (
    generate_sample_adapter_list_xml,
    generate_sample_vm_list,
    generate_nic_data
)
from warlock.states.esxi_state_reader import EsxiStateReader
from warlock.operators.ssh_operator import SSHOperator


def verify_values_seq(data):
    values = list(data.values())
    numeric_values = [v for v in values if isinstance(v, int)]
    sorted_values = sorted(numeric_values)
    for i in range(len(sorted_values)):
        if sorted_values[i] != i:
            return False
    return True


class TestsEsxiStateReader(ExtendedTestCase):

    def setUp(self):
        self.esxi_ip = '10.252.80.107'
        self.esxi_username = 'root'
        self.esxi_password = 'VMware1!'

        os.environ['ESXI_IP'] = '10.252.80.107'
        os.environ['ESXI_USERNAME'] = 'root'
        os.environ['ESXI_PASSWORD'] = 'VMware1!'

        self.esxi_fqdn = '10.252.80.107'
        self.username = 'root'
        self.password = 'VMware1!'
        self.test_vms_substring = 'test-np'
        self.test_default_adapter_name = 'eth0'

    def test_can_init_from_credentials(self):
        """Tests EsxiState constructors from args """

        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            self.assertEqual(esxi_host_state.fqdn, self.esxi_fqdn)
            self.assertEqual(esxi_host_state.username, self.username)
            self.assertEqual(esxi_host_state.password, self.password)
            self.assertIsNotNone(esxi_host_state._ssh_operator)
            self.assertIsInstance(esxi_host_state._ssh_operator, SSHOperator)
            self.assertTrue(
                esxi_host_state._ssh_operator.has_active_connection(self.esxi_fqdn),
                "remote host should be active"
            )
            self.assertTrue(
                len(esxi_host_state._ssh_operator._persistent_connections) == 1,
                "remote host should be active"
            )

    def test_failure_on_invalid_esxi_fqdn_type(self):
        """Test that object creation fails when esxi_fqdn is not a string."""
        with self.assertRaises(TypeError):
            with EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=None,
                    username="user",
                    password="pass"
            ) as esxi_host_state:
                self.assertIsNone(esxi_host_state._ssh_operator)

    def test_failure_on_invalid_username_type(self):
        """Test that object creation fails when username is not a string."""
        with self.assertRaises(TypeError):
            with EsxiStateReader.from_optional_credentials(
                    esxi_fqdn="10.252.80.108",
                    username=None,
                    password="pass"
            ) as esxi_host_state:
                self.assertIsNone(esxi_host_state._ssh_operator)

    def test_failure_on_invalid_password_type(self):
        """Test that object creation fails when password is not a string."""
        with self.assertRaises(TypeError):
            EsxiStateReader.from_optional_credentials(
                esxi_fqdn="10.252.80.108",
                username="user",
                password=None
            )

    def test_xml_to_json_adapter_list(self):
        """Tests we can parse nic list"""
        json_data = EsxiStateReader.xml2json(generate_sample_adapter_list_xml())
        expected_keys = {
            "AdminStatus", "Description", "Driver",
            "Duplex", "Link", "LinkStatus", "MACAddress",
            "MTU", "Name", "PCIDevice", "Speed"
        }

        nic_list = json.loads(json_data)

        for nic in nic_list:
            nic_keys = set(nic.keys())
            missing_keys = expected_keys - nic_keys
            self.assertTrue(
                not missing_keys,
                f"NIC entry {nic['Name']} is missing keys: {missing_keys}")

    def test_xml_nic_data(self):
        """Tests parser nic list"""
        json_data = EsxiStateReader.complex_xml2json(generate_nic_data())
        self.assertIsNotNone(json_data, "json_data must not be None")
        self.assertIsInstance(json_data, str, "json_data must be a string")

    def test_xml_to_json_vm_list(self):
        """Tests that we can parse vm list """
        json_data = EsxiStateReader.xml2json(generate_sample_vm_list())
        expected_keys = {
            "ConfigFile",
            "DisplayName",
            "ProcessID",
            "UUID",
            "VMXCartelID",
            "WorldID"
        }
        vm_list = json.loads(json_data)
        for vm in vm_list:
            vm_keys = set(vm.keys())
            missing_keys = expected_keys - vm_keys
            self.assertTrue(
                not missing_keys,
                f"VM entry '{vm.get('DisplayName', 'Unknown')}' "
                f"is missing keys: {missing_keys}")

    def test_can_read_nic_list(self):
        """
        Tests can we read nic list from esxi
        :return:
        """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password) as esxi_host_state:
            nic_list = esxi_host_state.read_adapter_list()
            expected_keys = {
                "AdminStatus", "Description", "Driver",
                "Duplex", "Link", "LinkStatus", "MACAddress",
                "MTU", "Name", "PCIDevice", "Speed"
            }

            for nic in nic_list:
                nic_keys = set(nic.keys())
                missing_keys = expected_keys - nic_keys
                self.assertTrue(not missing_keys,
                                f"NIC entry {nic['Name']} "
                                f"is missing keys: {missing_keys}")

    def test_can_read_module_parameters(
            self, module_names=None):
        """Tests test we can read driver/module parameters
        """
        if module_names is None:
            module_names = ['icen', 'i40en', 'ixgben', 'bad', None]

        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            for module_name in module_names:
                with self.subTest(module_name=module_name):
                    module_parameters = esxi_host_state.read_module_parameters(module_name=module_name)
                    self.assertIsNotNone(
                        module_parameters,
                        f"read_module_parameters must return a list for {module_name}.")
                    self.assertIsInstance(
                        module_parameters, list, f"Module name {module_name} should return list.")
                    for param in module_parameters:
                        for key in param.keys():
                            self.assertTrue(
                                isinstance(key, str),
                                f"Key '{key}' in module {module_name} is not a string."
                            )

    def test_can_read_available_mod_parameters(self):
        """Tests test we can read driver/module parameters t"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            # for default adapter.
            m = esxi_host_state.read_available_mod_parameters()
            self.assertIsNotNone(m, "must empty list or a list is not a None")
            self.assertIsInstance(m, list, "should return a list")

            #  repeat for all adapters.
            nic_names = esxi_host_state.read_adapter_names()
            for nic in nic_names:
                mp = esxi_host_state.read_available_mod_parameters(nic=nic)
                self.assertIsNotNone(mp, "must empty list or a list is not a None")
                self.assertIsInstance(mp, list, "should return a list")

    def test_cannot_read_module_parameters(self):
        """Tests test we can read driver/module parameters t"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            module_parameters = esxi_host_state.read_module_parameters(module_name="bad")
            self.assertTrue(
                [] == module_parameters, "for bad module name should return empty list")

            module_parameters = esxi_host_state.read_module_parameters(module_name=None)
            self.assertTrue(
                [] == module_parameters, "for bad module name should return empty list")

    def test_can_read_adapter_driver_name(self):
        """Tests can read adapter driver name."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            d = esxi_host_state.read_adapter_driver_name()
            self.assertIsNotNone(d, "read_adapter_driver should return string")
            self.assertTrue(len(d) > 0, "read_adapter_driver should return module name")
            nic_names = esxi_host_state.read_adapter_names()
            for nic in nic_names:
                n = esxi_host_state.read_adapter_driver_name(nic=nic)
                self.assertIsNotNone(n, "should return driver name")

    def test_can_read_nic_adapter_parameters(self):
        """Tests caller can read adapter parameters."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            module_param = esxi_host_state.read_adapter_parameters(nic="vmnic0")
            self.assertIsNotNone(module_param, "read_adapter_parameters should return string")
            self.assertIsInstance(module_param, list, "read_adapter_parameters should return string")
            for record in module_param:
                self.assertIn("Description", record, "data should contain 'Description'")
                self.assertIn("Name", record, "data should contain 'Name'")
                self.assertIn("Type", record, "data should contain 'Type'")
                self.assertIn("Value", record, "data should contain 'Value'")

            module_param = esxi_host_state.read_adapter_parameters(nic=None)
            self.assertIsNotNone(module_param, "must return list for None")
            self.assertTrue(module_param == [], "must return list for None")

    def test_can_read_vm_pid_list(self):
        """Tests we can parse vm list"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            expected_keys = {
                "ConfigFile", "DisplayName", "ProcessID",
                "UUID", "VMXCartelID", "WorldID"
            }

            vm_list = esxi_host_state.read_vm_process_list()
            self.assertIsNotNone(vm_list, "vm_list must empty list or a list is not a None")

            for vm in vm_list:
                self.assertIsInstance(vm, dict, "vm entity should be a dict")
                vm_keys = set(vm.keys())
                missing_keys = expected_keys - vm_keys
                self.assertTrue(not missing_keys,
                                f"VM entry '{vm.get('DisplayName', 'Unknown')}' "
                                f"is missing keys: {missing_keys}")

    def test_can_read_adapter_name(self):
        """Tests test we can read all adapter names."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            names = esxi_host_state.read_adapter_names()
            self.assertIsNotNone(names, "list of name must empty list or a list")
            self.assertTrue('adapter_names' in esxi_host_state._cache, "Adapter names were not cached")
            self.assertEqual(names, esxi_host_state._cache['adapter_names'],
                             "Cached adapter names do not match the fetched names")

    def test_read_network_pf_list(self):
        """Tests test we can read all PF adapter names.
        Note this test assume that ESXi host we test has
        adapter with SRIOV enabled.
        """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            self.assertIsNotNone(pf_list, "list of PF adapter empty list or a list with name")
            self.assertIsInstance(pf_list, list, "return result should be a list")
            self.assertTrue('pf_adapter_names' in esxi_host_state._cache, "pf name were not cached")

    def test_read_network_vf_list(self):
        """Tests

        Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""

        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            for pf in pf_list:
                vf_list = esxi_host_state.read_vfs(pf_adapter_name=pf)
                expected_keys = {
                    "Active", "OwnerWorldID", "PCIAddress", "VFID"
                }
                for vf in vf_list:
                    vf_keys = set(vf.keys())
                    missing_keys = expected_keys - vf_keys
                    self.assertTrue(not missing_keys,
                                    f"VF entry '{vf.get('DisplayName', 'Unknown')}' "
                                    f"is missing keys: {missing_keys}")

    def test_read_network_vf_list_bad_pf(self):
        """Tests if caller pass bad adapter name we get empty list."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vf_list = esxi_host_state.read_vfs(pf_adapter_name="vmnic0")
            self.assertTrue([] == vf_list, "method should return empty list for bad adapter")

    def test_read_network_vf_list_bad_arg(self):
        """Tests if caller pass bad adapter name we get empty list"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vf_list = esxi_host_state.read_vfs(pf_adapter_name="bad")
            self.assertTrue([] == vf_list, "method should return empty list for bad adapter")

            vf_list = esxi_host_state.read_vfs(pf_adapter_name=None)
            self.assertTrue([] == vf_list, "method should return empty list for bad adapter")

    def test_read_active_vf_list(self):
        """Tests Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            for pf in pf_list:
                vf_list = esxi_host_state.read_active_vfs(pf_nic_name=pf)
                self.assertIsNotNone(
                    vf_list, "list of PF adapter empty list or a list with name")

    def test_read_active_vf_list_bad_adapter(self):
        """Test on wrong PF adapter we get empty list"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vf_list = esxi_host_state.read_active_vfs(pf_nic_name="vmnic0")
            self.assertIsNotNone(
                vf_list, "list of VF adapter must be empty list."
            )

    def test_can_read_vf_stats(self):
        """Tests Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            vf_list = esxi_host_state.read_active_vfs(pf_nic_name=random_pf)

            self.assertIsNotNone(vf_list, "VF list is None for PF adapter: {}".format(random_pf))
            self.assertTrue(len(vf_list) > 0, "VF list is empty for PF adapter: {}".format(random_pf))
            random_vf_id = random.choice(vf_list)

            data = esxi_host_state.read_vf_stats(
                adapter_name=random_pf, vf_id=random_vf_id
            )

            expected_keys = {
                "NICName", "RxBroadcastBytes", "RxBroadcastPkts", "RxErrordrops",
                "RxLROBytes", "RxLROPkts", "RxMulticastBytes", "RxMulticastPkts",
                "RxOutofBufferdrops", "RxUnicastBytes", "RxUnicastPkt", "TxBroadcastBytes",
                "TxBroadcastPkts", "TxDiscards", "TxErrors", "TxMulticastBytes",
                "TxMulticastPkts", "TxTSOBytes", "TxTSOPkts", "TxUnicastBytes", "TxUnicastPkt",
                "VFID"
            }

            for vf_data in data:
                vf_data_keys = set(vf_data.keys())
                missing_keys = set(expected_keys) - vf_data_keys
                self.assertTrue(not missing_keys,
                                f"VF entry '{vf_data.get('DisplayName', 'Unknown')}' "
                                f"is missing keys: {missing_keys}")

    def test_cannot_read_vf_stats_bad_id(self):
        """Tests Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            vf_stat = esxi_host_state.read_vf_stats(
                adapter_name=random_pf, vf_id=2000
            )
            self.assertTrue([] == vf_stat, "method should return empty list for bad vf")

    def test_cannot_read_vf_stats_bad_id_and_pf(self):
        """Tests Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vf_stat = esxi_host_state.read_vf_stats(
                adapter_name="bad", vf_id=2000
            )
            self.assertTrue([] == vf_stat, "method should return empty list for bad vf")

    def test_can_read_pf_stats(self):
        """Tests read pf stats note it same as reading network stats."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            pf_stats = esxi_host_state.read_pf_stats(adapter_name=random_pf)
            self.assertIsInstance(pf_stats, list, "pf_stats should be a list")

            expected_keys = [
                'Broadcastpacketsreceived', 'Broadcastpacketssent', 'Bytesreceived',
                'Bytessent', 'Multicastpacketsreceived', 'Multicastpacketssent',
                'NICName', 'Packetsreceived', 'Packetssent', 'ReceiveCRCerrors',
                'ReceiveFIFOerrors', 'Receiveframeerrors', 'Receivelengtherrors',
                'Receivemissederrors', 'Receiveovererrors', 'Receivepacketsdropped',
                'Totalreceiveerrors', 'Totaltransmiterrors', 'TransmitFIFOerrors',
                'Transmitabortederrors', 'Transmitcarriererrors',
                'Transmitheartbeaterrors', 'Transmitpacketsdropped',
                'Transmitwindowerrors'
            ]

            for stat in pf_stats:
                self.assertCountEqual(expected_keys, stat.keys(), "Keys mismatch")
                for key, value in stat.items():
                    if key == 'NICName':
                        self.assertIsInstance(value, str, f"Value for key '{key}' should be a string")
                    else:
                        self.assertIsInstance(value, int, f"Value for key '{key}' should be an integer")

    def test_can_read_pf_stats_as_np(self):
        """Tests read pf stats note it same as reading network stats."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            pf_stats = esxi_host_state.read_pf_stats(adapter_name=random_pf, return_as_vector=True)
            self.assertIsInstance(pf_stats, np.ndarray, "pf_stats is not a numpy array")
            pf_stats_metadata = esxi_host_state.pf_stats_metadata()
            self.assertTrue(len(pf_stats_metadata) == pf_stats.shape[1], "Metadata columns count mismatch")

    def test_dvs_list(self):
        """Tests dvs pf stats note it same as reading network stats."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            dvs_list = esxi_host_state.read_dvs_list()
            self.assertIsInstance(dvs_list, list, "read_dvs_list should be a list")

    def test_read_standard_switch_list(self):
        """Tests dvs pf stats note it same as reading network stats."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            sw = esxi_host_state.read_standard_switch_list()
            self.assertIsInstance(sw, list, "read_standard_switch_list should be a list")

    def test_read_all_net_stats(self):
        """Tests we can read all net stats ."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            stats = esxi_host_state.read_netstats_all()
            self.assertIsInstance(stats, dict, "read_all_net_stats should be a dict")
            self.assertIn('sysinfo', stats, "sysinfo should be a dict")
            self.assertIn('stats', stats, "stats should be a dict")

    def test_read_vm_net_port_id(self):
        """Tests read internal port ids """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            port_ids = esxi_host_state.read_netstats_vm_net_port_ids()
            self.assertIsInstance(port_ids, dict, "should be a dict")
            for port_id, vm_name in port_ids.items():
                self.assertIsInstance(port_id, int, "Port ID should be an integer")
                self.assertIsInstance(vm_name, str, "VM name should be a string")
                self.assertTrue(vm_name, "VM name should be a non-empty string")

    def test_can_read_vm_net_stats(self):
        """Tests dvs pf stats note it same as reading network stats."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            port_ids = esxi_host_state.read_netstats_vm_net_port_ids()
            self.assertIsInstance(port_ids, dict, "read_vm_net_port_id should be a dict")
            vm_names = [name for name in port_ids.values() if 'test' in name.lower()]
            self.assertIsInstance(vm_names, list, "vm_names should be a list")
            random_vm_name = random.choice(vm_names)
            stats = esxi_host_state.read_netstats_by_vm(vm_name=random_vm_name)
            self.assertIn('sysinfo', stats, "sysinfo should be a dict")
            self.assertIn('stats', stats, "stats should be a dict")

    def test_can_read_port_net_stats(self):
        """Tests can read stats from pfname ."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            stats = esxi_host_state.read_netstats_by_nic(nic=random_pf)
            self.assertIn('sysinfo', stats, "sysinfo should be a dict")
            self.assertIn('stats', stats, "stats should be a dict")

    def test_can_read_sriov_queue_info(self):
        """Tests we can read sriov queue information """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            queue_info = esxi_host_state.read_sriov_queue_info(nic=random_pf)
            self.assertIsInstance(queue_info, dict, "read_sriov_queue_info should be a dict")
            self.assertIn("rx_info", queue_info, "read_sriov_queue_info should have rx_info key")
            self.assertIn("tx_info", queue_info, "read_sriov_queue_info should have tx_info key")

    def test_can_read_net_adapter_capabilities(self):
        """Tests we can network adapter capabilities  """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            cap = esxi_host_state.read_net_adapter_capabilities(nic=random_pf)
            self.assertIsInstance(cap, list, "read_net_adapter_capabilities should be a list of capabilities")

    def test_is_net_adapter_capability_on(self):
        """Tests caller can check if capability enabled or not  """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            random_pf = random.choice(esxi_host_state.read_pf_adapter_names())
            cap_list = esxi_host_state.read_net_adapter_capabilities(nic=random_pf)
            is_cap = esxi_host_state.is_net_adapter_capability_on(
                nic=random_pf, capability=random.choice(cap_list)
            )
            self.assertIsNotNone(is_cap, "should be boolean value")

    def test_can_read_net_sriov_stats(self):
        """Tests caller can check if capability enabled or not  """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            random_pf = random.choice(esxi_host_state.read_pf_adapter_names())
            raw_stats = esxi_host_state.read_net_sriov_stats(nic=random_pf)
            self.assertIsInstance(raw_stats, dict, "read_net_sriov_stats should be a dict")

    def test_can_update_ring_size(self):
        """Tests ring size can be updated"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            random_pf = random.choice(esxi_host_state.read_pf_adapter_names())
            ok = esxi_host_state.write_ring_size(random_pf, 4096, 4096)
            self.assertTrue(
                ok, "write_ring_size should be able update ring size"
            )

    def test_update_ring_siz_should_fail(self):
        """Tests write_ring_size should return false for bad adapter name"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            ok = esxi_host_state.write_ring_size("bad", 4096, 4096)
            self.assertFalse(
                ok, "write_ring_size should be able update ring size"
            )

    def test_update_ring_siz_bad_ring(self):
        """Tests write_ring_size should return false for bad adapter name"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            # Test with tx_int not a power of 2
            with self.assertRaises(ValueError):
                esxi_host_state.write_ring_size("vmnic0", 4091, 1024)

            # Test with rx_int not a power of 2
            with self.assertRaises(ValueError):
                esxi_host_state.write_ring_size("vmnic0", 1024, 4091)

            # Test with both tx_int and rx_int not powers of 2
            with self.assertRaises(ValueError):
                esxi_host_state.write_ring_size("vmnic0", 4091, 4091)

            # 0
            with self.assertRaises(ValueError):
                esxi_host_state.write_ring_size("vmnic0", 0, 4091)

            # 0
            with self.assertRaises(ValueError):
                esxi_host_state.write_ring_size("vmnic0", 1024, 0)

    def test_can_nic_from_driver_name(self):
        """Tests write_ring_size should return false for bad adapter name"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            nic = esxi_host_state.read_adapters_by_driver("i40en")
            self.assertIsInstance(nic, list, "NIC should be a list")

    def test_no_card_driver_name_num_queue(self):
        """Tests write_ring_size should return false for bad adapter name"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            nic = esxi_host_state.read_adapters_by_driver("bogus_driver")
            self.assertIsInstance(nic, list, "NIC should be a list")
            self.assertTrue(nic == [], "NIC should be empty list")

    def test_can_set_trusted(self):
        """Tests write_ring_size should return false for bad adapter name"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            esxi_host_state.write_vf_trusted("icen")

    def test_can_update_num_queue(self):
        """Tests write_ring_size should return false for bad adapter name"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            esxi_host_state.update_num_qps_per_vf("icen", 16)

    def test_cannot_update_num_queue_en40(self):
        """Tests num queue, en40 has no  num qps should fail"""
        with self.assertRaises(ValueError):
            with EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=self.esxi_fqdn,
                    username=self.username,
                    password=self.password
            ) as esxi_host_state:
                esxi_host_state.update_num_qps_per_vf("i40en", 16)

    def test_can_update_max_vfs_from_array_en40(self):
        """Tests check we can update max vfs"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:

            max_vfs = 16
            esxi_host_state.update_max_vfs("i40en", max_vfs)
            module_parameters = esxi_host_state.read_module_parameters(module_name="i40en")
            nic_list = esxi_host_state.read_adapters_by_driver("i40en")
            num_max_vfs = ",".join([str(max_vfs) for _ in nic_list])

            for param in module_parameters:
                if param.get('Name') == 'max_vfs':
                    max_vfs_value = param.get('Value')
                    break

            self.assertIsNotNone(max_vfs_value, "max_vfs parameter not found.")
            self.assertEqual(max_vfs_value, num_max_vfs, "max_vfs parameter value is not as expected.")

    def test_can_update_rss_vfs_from_array_en40(self):
        """Tests validate that we can update RSS """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:

            esxi_host_state.update_rss("i40en", True)
            module_parameters = esxi_host_state.read_module_parameters(module_name="i40en")
            nic_list = esxi_host_state.read_adapters_by_driver("i40en")
            rss_value_str = ",".join([str(int(True)) for _ in nic_list])

            for param in module_parameters:
                if param.get('Name') == 'RSS':
                    rss_vfs_value = param.get('Value')
                    break

            self.assertIsNotNone(rss_vfs_value, "max_vfs parameter not found.")
            self.assertEqual(rss_vfs_value, rss_value_str, "max_vfs parameter value is not as expected.")

    def test_can_update_rx_itr(self):
        """Tests that we can update the RxITR parameter
        from default 100 microseconds."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn, username=self.username,
                password=self.password) as esxi_host_state:
            esxi_host_state.update_rx_itr("i40en", 106)
            module_parameters = esxi_host_state.read_module_parameters(module_name="i40en")

            rx_itr_value = None
            for param in module_parameters:
                if param.get('Name') == 'RxITR':
                    rx_itr_value = param.get('Value')
                    break

            self.assertIsNotNone(rx_itr_value, "RxITR parameter not found.")
            self.assertEqual(rx_itr_value, "106", "RxITR parameter value is not as expected.")

    def test_cannot_update_rx_itr(self):
        """Tests that we can update the TxITR parameter.
        from default 50 microseconds """
        with self.assertRaises(ValueError):
            with EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=self.esxi_fqdn, username=self.username,
                    password=self.password) as esxi_host_state:
                esxi_host_state.update_rx_itr("i40en", 100000)

    def test_can_update_tx_itr(self):
        """Tests that we can update the TxITR parameter.
        from default 50 microseconds """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn, username=self.username,
                password=self.password) as esxi_host_state:
            esxi_host_state.update_tx_itr("i40en", 40)
            module_parameters = esxi_host_state.read_module_parameters(module_name="i40en")

            tx_itr_value = None
            for param in module_parameters:
                if param.get('Name') == 'TxITR':
                    tx_itr_value = param.get('Value')
                    break

            self.assertIsNotNone(tx_itr_value, "TxITR parameter not found.")
            self.assertEqual(tx_itr_value, "40", "TxITR parameter value is not as expected.")

    def test_cannot_update_tx_itr(self):
        """Tests that we can update the TxITR parameter.
        from default 50 microseconds """
        with self.assertRaises(ValueError):
            with EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=self.esxi_fqdn, username=self.username,
                    password=self.password) as esxi_host_state:
                esxi_host_state.update_tx_itr("i40en", 100000)

    def test_can_update_vmdq(self):
        """Tests that we can update the VMDQ parameter.
        from default 8 to 16"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn, username=self.username,
                password=self.password) as esxi_host_state:

            esxi_host_state.update_vmdq("i40en", 16)
            module_parameters = esxi_host_state.read_module_parameters(module_name="i40en")

            nic_list = esxi_host_state.read_adapters_by_driver("i40en")
            rss_value_str = ",".join([str(16) for _ in nic_list])

            vmdq_value = None
            for param in module_parameters:
                if param.get('Name') == 'VMDQ':
                    vmdq_value = param.get('Value')
                    break

            self.assertIsNotNone(vmdq_value, "VMDQ parameter not found.")
            self.assertEqual(rss_value_str, vmdq_value, "VMDQ parameter value is not as expected.")

    def test_can_update_bad_vmdq(self):
        """Tests do not accept bad value the VMDQ parameter"""
        with self.assertRaises(ValueError):
            with EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=self.esxi_fqdn, username=self.username,
                    password=self.password) as esxi_host_state:
                esxi_host_state.update_vmdq("i40en", 128)

    def test_can_update_vmdq_rss(self):
        """Tests that we can update the VMDQ parameter.
        from default 8 to 16"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn, username=self.username,
                password=self.password) as esxi_host_state:

            # we update the VMDQ and RSS parameters
            esxi_host_state.update_vmdq("i40en", 16)
            esxi_host_state.update_rss("i40en", True)

            module_parameters = esxi_host_state.read_module_parameters(module_name="i40en")
            nic_list = esxi_host_state.read_adapters_by_driver("i40en")
            rss_value_str = ",".join([str(16) for _ in nic_list])

            vmdq_value = None
            for param in module_parameters:
                if param.get('Name') == 'VMDQ':
                    vmdq_value = param.get('Value')
                    break

            # check vmdq update
            self.assertIsNotNone(vmdq_value, "VMDQ parameter not found.")
            self.assertEqual(rss_value_str, vmdq_value, "VMDQ parameter value is not as expected.")

            # check rss update
            rss_value_str = ",".join([str(int(True)) for _ in nic_list])
            for param in module_parameters:
                if param.get('Name') == 'RSS':
                    rss_vfs_value = param.get('Value')
                    break

            self.assertIsNotNone(rss_vfs_value, "max_vfs parameter not found.")
            self.assertEqual(rss_vfs_value, rss_value_str, "max_vfs parameter value is not as expected.")

    def test_can_filtered_map_vm_hosts_port_ids(self):
        """Tests read_vm_port_stats """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            test_vm_names = []
            vm_pids = esxi_host_state.read_vm_process_list()
            if vm_pids and len(vm_pids) > 0:
                names = [v['DisplayName'] for v in vm_pids if 'DisplayName'
                         in v and self.test_vms_substring in v['DisplayName']]
                test_vm_names.extend(names)

            args_dict = {vm_name: self.test_default_adapter_name for vm_name in test_vm_names}
            world_id_map = esxi_host_state.filtered_map_vm_hosts_port_ids(test_vm_names, args_dict)
            self.assertIsInstance(world_id_map, dict, "filtered_map_vm_hosts_port_ids should be a dict")
            for vm_name in test_vm_names:
                self.assertIn(vm_name, world_id_map, f"{vm_name} should be a key in the result")
                self.assertIn('port_ids', world_id_map[vm_name], "'port_ids' should be a key in each VM's data")
                self.assertIn('esxi_host', world_id_map[vm_name], "'esxi_host' should be a key in each VM's data")
                self.assertIsInstance(world_id_map[vm_name]['port_ids'], list, "'port_ids' should be a list")
                self.assertIsInstance(world_id_map[vm_name]['esxi_host'], str, "'esxi_host' should be a string")
                self.assertTrue(world_id_map[vm_name]['port_ids'], "The list of 'port_ids' should not be empty")
                self.assertTrue(world_id_map[vm_name]['esxi_host'], "The 'esxi_host' should not be empty")
                self.assertIsInstance(world_id_map[vm_name]['port_vm_nic_name'], list, "'port_ids' should be a list")

    def test_can_filtered_vnic_map_vm_hosts_port_ids(self):
        """Tests  filtered_map_vm_hosts_port_ids with vnic name"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            test_vm_names = []
            vm_pids = esxi_host_state.read_vm_process_list()
            if vm_pids and len(vm_pids) > 0:
                names = [v['DisplayName'] for v in vm_pids if 'DisplayName'
                         in v and self.test_vms_substring in v['DisplayName']]
                test_vm_names.extend(names)

            args_dict = {vm_name: self.test_default_adapter_name for vm_name in test_vm_names}
            world_id_map = esxi_host_state.filtered_map_vm_hosts_port_ids(
                test_vm_names,
                args_dict,
                is_sriov=False
            )

            self.assertIsInstance(world_id_map, dict, "filtered_map_vm_hosts_port_ids should be a dict")
            for vm_name in test_vm_names:
                self.assertIn(vm_name, world_id_map, f"{vm_name} should be a key in the result")
                self.assertIn('port_ids', world_id_map[vm_name], "'port_ids' should be a key in each VM's data")
                self.assertIn('esxi_host', world_id_map[vm_name], "'esxi_host' should be a key in each VM's data")
                self.assertIsInstance(world_id_map[vm_name]['port_ids'], list, "'port_ids' should be a list")
                self.assertIsInstance(world_id_map[vm_name]['esxi_host'], str, "'esxi_host' should be a string")
                self.assertTrue(world_id_map[vm_name]['port_ids'], "The list of 'port_ids' should not be empty")
                self.assertTrue(world_id_map[vm_name]['esxi_host'], "The 'esxi_host' should not be empty")
                self.assertIsInstance(world_id_map[vm_name]['port_vm_nic_name'], list, "'port_ids' should be a list")

                self.assertTrue(len(world_id_map[vm_name]['port_ids']) == 1,
                                "filtering by sriov should return one world id")

                self.assertTrue(len(world_id_map[vm_name]['port_vm_nic_name']) == 1,
                                "filtering by sriov should return one world id")

    def test_can_filtered_sriov_map_vm_hosts_port_ids(self):
        """Tests filtered_map_vm_hosts_port_ids """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            test_vm_names = []
            vm_pids = esxi_host_state.read_vm_process_list()
            if vm_pids and len(vm_pids) > 0:
                names = [v['DisplayName'] for v in vm_pids if 'DisplayName'
                         in v and self.test_vms_substring in v['DisplayName']]
                test_vm_names.extend(names)

            args_dict = {vm_name: self.test_default_adapter_name for vm_name in test_vm_names}
            world_id_map = esxi_host_state.filtered_map_vm_hosts_port_ids(
                test_vm_names,
                args_dict,
                is_sriov=True
            )

            self.assertIsInstance(world_id_map, dict, "filtered_map_vm_hosts_port_ids should be a dict")
            for vm_name in test_vm_names:
                self.assertIn(vm_name, world_id_map, f"{vm_name} should be a key in the result")
                self.assertIn('port_ids', world_id_map[vm_name], "'port_ids' should be a key in each VM's data")
                self.assertIn('esxi_host', world_id_map[vm_name], "'esxi_host' should be a key in each VM's data")
                self.assertIsInstance(world_id_map[vm_name]['port_ids'], list, "'port_ids' should be a list")
                self.assertIsInstance(world_id_map[vm_name]['esxi_host'], str, "'esxi_host' should be a string")
                self.assertTrue(world_id_map[vm_name]['port_ids'], "The list of 'port_ids' should not be empty")
                self.assertTrue(world_id_map[vm_name]['esxi_host'], "The 'esxi_host' should not be empty")
                self.assertIsInstance(world_id_map[vm_name]['port_vm_nic_name'], list, "'port_ids' should be a list")

                # we assert so adapter has SRIOV
                for nic_name in world_id_map[vm_name]['port_vm_nic_name']:
                    self.assertIn("SRIOV", nic_name, f"The NIC name '{nic_name}' should include 'SRIOV'")

                self.assertTrue(len(world_id_map[vm_name]['port_ids']) == 1,
                                "filtering by sriov should return one world id")

                self.assertTrue(len(world_id_map[vm_name]['port_vm_nic_name']) == 1,
                                "filtering by sriov should return one world id")

    def sample_vm_names(self):
        """Utilit function to get sampled VM names"""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            test_vm_names = []
            vm_pids = esxi_host_state.read_vm_process_list()
            if vm_pids and len(vm_pids) > 0:
                names = [v['DisplayName'] for v in vm_pids if 'DisplayName'
                         in v and self.test_vms_substring in v['DisplayName']]
                test_vm_names.extend(names)
            return test_vm_names

    def test_can_read_sriov_vm_port_stats(self):
        """Tests first world id based  VM Name and adapter name
        and fetch stats """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:

            vm_names = self.sample_vm_names()
            world_id_map = esxi_host_state.filtered_map_vm_hosts_port_ids(
                vm_names,
                {vm_name: self.test_default_adapter_name for vm_name in vm_names},
                is_sriov=True
            )
            for vm_name in vm_names:
                self.assertIn(vm_name, world_id_map, f"{vm_name} should be a key in the result")
                world_ids = world_id_map[vm_name]['port_ids']
                for world_id in world_ids:
                    port_stats = esxi_host_state.read_vm_port_stats(world_id)
                    self.assertIsInstance(port_stats, list, "read_vm_port_stats should be a dict")
                    if port_stats:
                        stats = port_stats[0]
                        self.assertEqual(stats['PortID'], world_id, f"PortID should be {world_id}")
                        self.assertIn('Transmitpacketsdropped', stats,
                                      "'Transmitpacketsdropped' should be a key in the stats")
                        self.assertIsInstance(stats['Transmitpacketsdropped'], int,
                                              "'Transmitpacketsdropped' should be an int")
                        self.assertIn('Receivepacketsdropped', stats,
                                      "'Receivepacketsdropped' should be a key in the stats")
                        self.assertIsInstance(stats['Receivepacketsdropped'], int,
                                              "'Receivepacketsdropped' should be an int")
                        print(json.dumps(port_stats, indent=4, sort_keys=True))
                    else:
                        self.fail("No port stats returned")

    def test_can_read_vnic_vm_port_stats(self):
        """Tests first world id based  VM Name and adapter name
        and fetch stats """
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vm_names = self.sample_vm_names()
            args_dict = {vm_name: self.test_default_adapter_name for vm_name in vm_names}
            world_id_map = esxi_host_state.filtered_map_vm_hosts_port_ids(
                vm_names,
                args_dict,
                is_sriov=False
            )

            for vm_name in vm_names:
                self.assertIn(vm_name, world_id_map, f"{vm_name} should be a key in the result")
                world_ids = world_id_map[vm_name]['port_ids']
                for world_id in world_ids:
                    port_stats = esxi_host_state.read_vm_port_stats(world_id)
                    self.assertIsInstance(port_stats, list, "read_vm_port_stats should be a dict")
                    if port_stats:
                        stats = port_stats[0]
                        self.assertEqual(stats['PortID'], world_id, f"PortID should be {world_id}")

                        self.assertIn('Transmitpacketsdropped', stats,
                                      "'Transmitpacketsdropped' should be a key in the stats")

                        self.assertIsInstance(stats['Transmitpacketsdropped'], int,
                                              "'Transmitpacketsdropped' should be an int")

                        self.assertIn('Receivepacketsdropped', stats,
                                      "'Receivepacketsdropped' should be a key in the stats")

                        self.assertIsInstance(stats['Receivepacketsdropped'], int,
                                              "'Receivepacketsdropped' should be an int")
                    else:
                        self.fail("No port stats returned")

    def test_read_ring_size(self):
        """Tests we can read all net stats ."""
        with EsxiStateReader.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            expected_keys = ["RX", "RXJumbo", "RXMini", "TX"]
            data = esxi_host_state.read_ring_size(adapter_name="vmnic7")
            self.assertIsInstance(data, list, "Returned data should be a list")
            self.assertTrue(len(data) == 1, "Returned list should contain one dictionary")
            ring_size_dict = data[0]
            self.assertIsInstance(ring_size_dict, dict, "Dictionary expected in the list")
            self.assertEqual(set(ring_size_dict.keys()), set(expected_keys),
                             "Keys in the returned dictionary should match expected keys")


