import json

import numpy as np

from tests.extended_test_case import ExtendedTestCase
from tests.test_utils import (
    sample_vm_stats
)
from warlock.metrics.esxi_metric_collector import EsxiMetricCollector
from warlock.states.esxi_state_reader import EsxiStateReader


class TestsEsxiMetric(ExtendedTestCase):

    def setUp(self):
        self.esxi_fqdns = [
            '10.252.80.107',
            '10.252.80.109'
        ]

        self.username = 'root'
        self.password = 'VMware1!'
        # test expect this substring in test vm on different hosts
        self.test_vms_substring = 'test-np'
        self.test_default_adapter_name = 'eth0'

    def test_init_from_list(self):
        """Tests constructors"""
        esxi_states = []
        try:
            for esxi_fqdn in self.esxi_fqdns:
                esxi_states.append(EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=esxi_fqdn,
                    username=self.username,
                    password=self.password
                ))

            for esxi_state in esxi_states:
                self.assertTrue(esxi_state.is_active(), f"should be active after initialization")

            esxi_collector = EsxiMetricCollector(esxi_states)
            self.assertEqual(len(esxi_collector.esxi_state_reader), len(self.esxi_fqdns))

        finally:
            for esxi_state in esxi_states:
                esxi_state.release()
                self.assertFalse(esxi_state.is_active(), f"{esxi_state.fqdn} should not be active after release")

    def sample_vm_names(self):
        """Utility method return VM names"""
        esxi_states = []
        try:
            for esxi_fqdn in self.esxi_fqdns:
                esxi_states.append(EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=esxi_fqdn,
                    username=self.username,
                    password=self.password
                ))

            test_vm_names = []
            for esxi_state in esxi_states:
                vm_pids = esxi_state.read_vm_process_list()
                if vm_pids and len(vm_pids) > 0:
                    names = [v['DisplayName'] for v in vm_pids if 'DisplayName'
                             in v and self.test_vms_substring in v['DisplayName']]
                    test_vm_names.extend(names)

            return test_vm_names

        finally:
            for esxi_state in esxi_states:
                esxi_state.release()
                self.assertFalse(esxi_state.is_active(), f"{esxi_state.fqdn} should not be active after release")

    def test_vm_port_ids_map(self):
        """Tests constructors"""
        esxi_states = []
        try:
            for esxi_fqdn in self.esxi_fqdns:
                esxi_states.append(EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=esxi_fqdn,
                    username=self.username,
                    password=self.password
                ))

            for esxi_state in esxi_states:
                self.assertTrue(esxi_state.is_active(), f"should be active after initialization")

            esxi_collector = EsxiMetricCollector(esxi_states)
            self.assertEqual(len(esxi_collector.esxi_state_reader), len(self.esxi_fqdns))

            test_vm_names = self.sample_vm_names()
            self.assertIsInstance(test_vm_names, list, "test_vm_names should return a list")
            self.assertTrue(len(test_vm_names) > 0, "test_vm_names should not be empty")

            _data = esxi_collector.map_vm_hosts_port_ids(test_vm_names)
            self.assertIsInstance(_data, dict, "vm_port_ids_map should return a dictionary")

            for vm_name in test_vm_names:
                self.assertIn(vm_name, _data, f"{vm_name} should be a key in the result")
                self.assertIn('port_ids', _data[vm_name], "'port_ids' should be a key in each VM's data")
                self.assertIn('esxi_host', _data[vm_name], "'esxi_host' should be a key in each VM's data")
                self.assertIsInstance(_data[vm_name]['port_ids'], list, "'port_ids' should be a list")
                self.assertIsInstance(_data[vm_name]['esxi_host'], str, "'esxi_host' should be a string")
                self.assertTrue(_data[vm_name]['port_ids'], "The list of 'port_ids' should not be empty")
                self.assertTrue(_data[vm_name]['esxi_host'], "The 'esxi_host' should not be empty")

        finally:
            for esxi_state in esxi_states:
                esxi_state.release()
                self.assertFalse(esxi_state.is_active(),
                                 f"{esxi_state.fqdn} should not be active after release")

    def test_collect_vm_port_metrics(self):
        """Tests constructors"""
        esxi_states = []
        try:
            for esxi_fqdn in self.esxi_fqdns:
                esxi_states.append(EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=esxi_fqdn,
                    username=self.username,
                    password=self.password
                ))

            esxi_collector = EsxiMetricCollector(esxi_states)
            vm_names = self.sample_vm_names()
            self.assertIsInstance(vm_names, list, "test_vm_names should return a list")
            self.assertTrue(len(vm_names) > 0, "test_vm_names should not be empty")
            self.assertEqual(len(esxi_collector.esxi_state_reader), len(self.esxi_fqdns))

            args_dict = {vm_name: self.test_default_adapter_name for vm_name in vm_names}
            stats_data = esxi_collector.collect_vm_port_metrics(vm_names, args_dict)
            print(stats_data)

        finally:
            for esxi_state in esxi_states:
                esxi_state.release()
                self.assertFalse(esxi_state.is_active(), f"{esxi_state.fqdn} should not be active after release")

    def test_metric_parse(self):
        """
        Test the parsing
        :return:
        """
        data = sample_vm_stats()
        json_data = json.loads(data)
        data = EsxiMetricCollector.vectorize_data(json_data, vm_index=7)
        np.set_printoptions(linewidth=160)
        self.assertTrue(data.shape[0] == 2, "vectorize_data should 2, 8")
        self.assertTrue(data.shape[1] == 8, "vectorize_data should 2, 8")
        self.assertTrue(np.all(data[:, 0] == 7), "data invalid")

    def test_collect_vm_port_metrics_n_samples(self):
        """Tests constructors"""
        esxi_states = []
        try:
            for esxi_fqdn in self.esxi_fqdns:
                esxi_states.append(EsxiStateReader.from_optional_credentials(
                    esxi_fqdn=esxi_fqdn,
                    username=self.username,
                    password=self.password
                ))

            esxi_collector = EsxiMetricCollector(esxi_states)
            vm_names = self.sample_vm_names()
            self.assertIsInstance(vm_names, list, "test_vm_names should return a list")
            self.assertTrue(len(vm_names) > 0, "test_vm_names should not be empty")
            self.assertEqual(len(esxi_collector.esxi_state_reader), len(self.esxi_fqdns))

            args_dict = {vm_name: self.test_default_adapter_name for vm_name in vm_names}
            stats_data = esxi_collector.collect_vm_port_metrics(vm_names, args_dict, num_sample=2)
            np.set_printoptions(linewidth=160)
            print(stats_data)

        finally:
            for esxi_state in esxi_states:
                esxi_state.release()
                self.assertFalse(esxi_state.is_active(), f"{esxi_state.fqdn} should not be active after release")



