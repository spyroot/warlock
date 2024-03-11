import json
import os
import random

from tests.extended_test_case import ExtendedTestCase
from tests.test_utils import (
    generate_sample_adapter_list_xml, generate_sample_vm_list, generate_vf_state_data
)
from warlock.esxi_state import EsxiState
from warlock.ssh_operator import SSHOperator


def verify_values_seq(data):
    values = list(data.values())
    numeric_values = [v for v in values if isinstance(v, int)]
    sorted_values = sorted(numeric_values)
    for i in range(len(sorted_values)):
        if sorted_values[i] != i:
            return False
    return True


class TestsEsxiState(ExtendedTestCase):

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

    def test_init_from_credentials(self):
        """Tests constructors"""

        esxi_host_state = EsxiState.from_optional_credentials(
            esxi_fqdn=self.esxi_fqdn,
            username=self.username,
            password=self.password
        )
        self.assertEqual(esxi_host_state.fqdn, self.esxi_fqdn)
        self.assertEqual(esxi_host_state.username, self.username)
        self.assertEqual(esxi_host_state.password, self.password)

        self.assertIsNotNone(esxi_host_state._ssh_operator)
        self.assertIsInstance(esxi_host_state._ssh_operator, SSHOperator)
        self.assertTrue(esxi_host_state._ssh_operator.has_active_connection(self.esxi_fqdn),
                        "remote host should be active")

    def test_failure_on_invalid_esxi_fqdn_type(self):
        """Test that object creation fails when esxi_fqdn is not a string."""
        with self.assertRaises(TypeError):
            EsxiState.from_optional_credentials(
                esxi_fqdn=None,
                username="user",
                password="pass"
            )

    def test_failure_on_invalid_username_type(self):
        """Test that object creation fails when username is not a string."""
        with self.assertRaises(TypeError):
            EsxiState.from_optional_credentials(
                esxi_fqdn="10.252.80.108",
                username=None,
                password="pass"
            )

    def test_failure_on_invalid_password_type(self):
        """Test that object creation fails when password is not a string."""
        with self.assertRaises(TypeError):
            EsxiState.from_optional_credentials(
                esxi_fqdn="10.252.80.108",
                username="user",
                password=None
            )

    def test_xml_to_json_adapter_list(self):
        """Tests we can parse nic list"""
        json_data = EsxiState.xml2json(generate_sample_adapter_list_xml())
        expected_keys = {
            "AdminStatus", "Description", "Driver",
            "Duplex", "Link", "LinkStatus", "MACAddress",
            "MTU", "Name", "PCIDevice", "Speed"
        }

        nic_list = json.loads(json_data)

        for nic in nic_list:
            nic_keys = set(nic.keys())
            missing_keys = expected_keys - nic_keys
            self.assertTrue(not missing_keys,
                            f"NIC entry {nic['Name']} "
                            f"is missing keys: {missing_keys}")

    def test_xml_to_json_vm_list(self):
        """Tests that we can parse vm list """
        json_data = EsxiState.xml2json(generate_sample_vm_list())
        expected_keys = {
            "ConfigFile", "DisplayName", "ProcessID",
            "UUID", "VMXCartelID", "WorldID"
        }
        vm_list = json.loads(json_data)
        for vm in vm_list:
            vm_keys = set(vm.keys())
            missing_keys = expected_keys - vm_keys
            self.assertTrue(not missing_keys,
                            f"VM entry '{vm.get('DisplayName', 'Unknown')}' "
                            f"is missing keys: {missing_keys}")

    def test_xml_vf_stats(self):
        """Tests that we can parse vm list """
        json_data = EsxiState.xml2json(generate_vf_state_data())
        expected_keys = {
            "ConfigFile", "DisplayName", "ProcessID",
            "UUID", "VMXCartelID", "WorldID"
        }
        vm_list = json.loads(json_data)
        for vm in vm_list:
            vm_keys = set(vm.keys())
            missing_keys = expected_keys - vm_keys
            self.assertTrue(not missing_keys,
                            f"VM entry '{vm.get('DisplayName', 'Unknown')}' "
                            f"is missing keys: {missing_keys}")

    def test_read_nic_list(self):
        """Tests we can parse nic list"""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
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

    def test_read_vm_list(self):
        """Tests we can parse vm list"""

        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            expected_keys = {
                "ConfigFile", "DisplayName", "ProcessID",
                "UUID", "VMXCartelID", "WorldID"
            }

            vm_list = esxi_host_state.read_vm_list()
            self.assertIsNotNone(vm_list, "vm_list must empty list or a list is not a None")

            for vm in vm_list:
                self.assertIsInstance(vm, dict, "vm entity should be a dict")
                vm_keys = set(vm.keys())
                missing_keys = expected_keys - vm_keys
                self.assertTrue(not missing_keys,
                                f"VM entry '{vm.get('DisplayName', 'Unknown')}' "
                                f"is missing keys: {missing_keys}")

    def test_read_adapter_name(self):
        """Tests test we can read all adapter names."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            names = esxi_host_state.read_adapter_names()
            self.assertIsNotNone(names, "list of name must empty list or a list")

    def test_read_network_pf_list(self):
        """Tests test we can read all PF adapter names.
        Note this test assume that ESXi host we test has
        adapter with SRIOV enabled.
        """
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            self.assertIsNotNone(pf_list, "list of PF adapter empty list or a list with name")
            self.assertIsInstance(pf_list, list, "return result should be a list")

    def test_read_network_vf_list(self):
        """Tests

        Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""

        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            for pf in pf_list:
                vf_list = esxi_host_state.read_network_vf_list(pf_adapter_name=pf)
                print(type(vf_list))
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
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vf_list = esxi_host_state.read_network_vf_list(pf_adapter_name="vmnic0")
            self.assertTrue([] == vf_list, "method should return empty list for bad adapter")

    def test_read_network_vf_list_bad_arg(self):
        """Tests if caller pass bad adapter name we get empty list"""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vf_list = esxi_host_state.read_network_vf_list(pf_adapter_name="bad")
            self.assertTrue([] == vf_list, "method should return empty list for bad adapter")

            vf_list = esxi_host_state.read_network_vf_list(pf_adapter_name=None)
            self.assertTrue([] == vf_list, "method should return empty list for bad adapter")

    def test_read_active_vf_list(self):
        """Tests Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            for pf in pf_list:
                vf_list = esxi_host_state.read_active_vf_list(pf_adapter_name=pf)
                self.assertIsNotNone(
                    vf_list, "list of PF adapter empty list or a list with name")

    def test_read_active_vf_list_bad_adapter(self):
        """Test on wrong PF adapter we get empty list"""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vf_list = esxi_host_state.read_active_vf_list(pf_adapter_name="vmnic0")
            self.assertIsNotNone(
                vf_list, "list of VF adapter must be empty list."
            )

    def test_read_vf_stats(self):
        """Tests Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            # sample pf , then one single vf and get stats
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            vf_list = esxi_host_state.read_active_vf_list(pf_adapter_name=random_pf)
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

    def test_read_vf_stats_bad_id(self):
        """Tests Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""
        with EsxiState.from_optional_credentials(
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

    def test_read_vf_stats_bad_id_and_pf(self):
        """Tests Note this test assume that ESXi host we test has
        adapter with SRIOV enabled."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            vf_stat = esxi_host_state.read_vf_stats(
                adapter_name="bad", vf_id=2000
            )
            self.assertTrue([] == vf_stat, "method should return empty list for bad vf")

    def test_read_pf_stats(self):
        """Tests read pf stats note it same as reading network stats."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            # sample pf , then one single vf and get stats
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            pf_stats = esxi_host_state.read_pf_stats(adapter_name=random_pf)
            self.assertIsInstance(pf_stats, list, "pf_stats should be a list")

    def test_dvs_list(self):
        """Tests dvs pf stats note it same as reading network stats."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            dvs_list = esxi_host_state.read_dvs_list()
            self.assertIsInstance(dvs_list, list, "read_dvs_list should be a list")
            print(json.dumps(dvs_list, indent=4))

    def test_read_standard_switch_list(self):
        """Tests dvs pf stats note it same as reading network stats."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            sw = esxi_host_state.read_standard_switch_list()
            self.assertIsInstance(sw, list, "read_standard_switch_list should be a list")

    def test_read_all_net_stats(self):
        """Tests we can read all net stats ."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            stats = esxi_host_state.read_all_net_stats()
            self.assertIsInstance(stats, dict, "read_all_net_stats should be a dict")
            self.assertIn('sysinfo', stats, "sysinfo should be a dict")
            self.assertIn('stats', stats, "stats should be a dict")

    def test_read_vm_net_port_id(self):
        """Tests read_vm_net_port_id """
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            port_ids = esxi_host_state.read_vm_net_port_id()
            self.assertIsInstance(port_ids, dict, "read_vm_net_port_id should be a dict")
            for port_id, vm_name in port_ids.items():
                self.assertIsInstance(port_id, int, "Port ID should be an integer")
                self.assertIsInstance(vm_name, str, "VM name should be a string")
                self.assertTrue(vm_name, "VM name should be a non-empty string")

    def test_read_vm_net_stats(self):
        """Tests dvs pf stats note it same as reading network stats."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            port_ids = esxi_host_state.read_vm_net_port_id()
            self.assertIsInstance(port_ids, dict, "read_vm_net_port_id should be a dict")
            vm_names = [name for name in port_ids.values() if 'test' in name.lower()]
            self.assertIsInstance(vm_names, list, "vm_names should be a list")
            random_vm_name = random.choice(vm_names)
            stats = esxi_host_state.read_vm_net_stats(vm_name=random_vm_name)
            self.assertIn('sysinfo', stats, "sysinfo should be a dict")
            self.assertIn('stats', stats, "stats should be a dict")

    def test_read_port_net_stats(self):
        """Tests dvs pf stats note it same as reading network stats."""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            pf_list = esxi_host_state.read_pf_adapter_names()
            random_pf = random.choice(pf_list)
            stats = esxi_host_state.read_port_net_stats(nic=random_pf)
            self.assertIn('sysinfo', stats, "sysinfo should be a dict")
            self.assertIn('stats', stats, "stats should be a dict")

    def test_read_sriov_queue_info(self):
        """Tests we can read sriov queue information """
        with EsxiState.from_optional_credentials(
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

    def test_read_net_adapter_capabilities(self):
        """Tests we can network adapter capabilities  """
        with EsxiState.from_optional_credentials(
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
        with EsxiState.from_optional_credentials(
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

    def test_read_net_sriov_stats(self):
        """Tests caller can check if capability enabled or not  """
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            random_pf = random.choice(esxi_host_state.read_pf_adapter_names())
            raw_stats = esxi_host_state.read_net_sriov_stats(nic=random_pf)
            self.assertIsInstance(raw_stats, dict, "read_net_sriov_stats should be a dict")
