import json
import os

from tests.extended_test_case import ExtendedTestCase
from tests.test_utils import (
    generate_sample_adapter_list_xml, generate_sample_vm_list
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

    def test_read_nic_list(self):
        """Tests we can parse nic list"""
        with EsxiState.from_optional_credentials(
                esxi_fqdn=self.esxi_fqdn,
                username=self.username,
                password=self.password
        ) as esxi_host_state:
            json_data = esxi_host_state.read_adapter_list()

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
            print(nic_list)

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

            json_data = esxi_host_state.read_vm_list()
            vm_list = json.loads(json_data)

            for vm in vm_list:
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
                json_data = esxi_host_state.read_network_vf_list(pf_adapter_name=pf)
                expected_keys = {
                    "Active", "OwnerWorldID", "PCIAddress", "VFID"
                }

                vf_list = json.loads(json_data)
                for vf in vf_list:
                    vf_keys = set(vf.keys())
                    missing_keys = expected_keys - vf_keys
                    self.assertTrue(not missing_keys,
                                    f"VF entry '{vf.get('DisplayName', 'Unknown')}' "
                                    f"is missing keys: {missing_keys}")
