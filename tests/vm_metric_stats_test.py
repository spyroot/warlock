"""
unit test for VMware VM state.

Author: Mustafa Bayramov
spyroot@gmail.com
mbayramo@stanford.edu

"""
import os
import unittest

import numpy as np

from warlock.vm_metric_stats import VMwareMetricCollector
from warlock.vm_state import (
    VMwareVimState
)


class TestVMwareVimState(unittest.TestCase):
    def setUp(self):
        """Setup initial state
        :return:
        """
        vcenter_ip = os.getenv('VCENTER_IP', 'default')
        username = os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local')
        password = os.getenv('VCENTER_PASSWORD', 'default')

        # a test VM that we know exists
        self._test_valid_vm_name = os.getenv('TEST_VM_NAME', 'default')
        self._test_valid_vm_substring = os.getenv('TEST_VMS_SUBSTRING', 'default')

        ssh_executor = None
        self.metric_stats = VMwareMetricCollector.from_optional_credentials(
            ssh_executor, vcenter_ip=vcenter_ip,
            username=username,
            password=password
        )

    def test_constructor_from_args(self):
        """Test constructor from args."""
        vcenter_ip = os.getenv('VCENTER_IP', 'default')
        username = os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local')
        password = os.getenv('VCENTER_PASSWORD', 'default')

        _obj = VMwareVimState(
            None, vcenter_ip=vcenter_ip,
            username=username,
            password=password
        )
        self.assertIsNotNone(_obj)
        self.assertEqual(_obj.ssh_executor, None)
        self.assertEqual(_obj.vcenter_ip, vcenter_ip)
        self.assertEqual(_obj.username, username)
        self.assertEqual(_obj.password, password)

    def sample_vm_name(self) -> str:
        """Sample some VM based on substring
        :return:
        """
        found_vms, found_vm_config = self.metric_stats.find_vm_by_name_substring(
            self._test_valid_vm_substring
        )
        return next(iter(found_vms))

    def sample_dvs_name(self) -> str:
        """Sample some VM based on substring
        :return:
        """
        dvs_moids, dvs_name = self.metric_stats.read_all_dvs_names()
        return next(iter(dvs_name))

    def vm_esxi_host(self) -> str:
        """Sample VM and resolve esxi host
        :return:
        """
        vm_name = self.sample_vm_name()
        return self.metric_stats.get_esxi_ip_of_vm(vm_name)

    def vm_cluster(self) -> str:
        """Sample VM and resolve its cluster name
        :return:
        """
        vm_name = self.sample_vm_name()
        c = self.metric_stats.read_cluster_by_vm_name(vm_name)
        return c.name

    def test_read_all_supported_metrics(self):
        """Test read all supported metrics
        """
        metric_types = self.metric_stats.read_all_supported_metrics()
        self.assertIsNotNone(metric_types, "read_all_metrics should not be None")
        self.assertIsInstance(metric_types, dict, "read_all_metrics should be dict")
        self.assertEqual(metric_types, self.metric_stats._vm_metrics_type,
                         "metric_stats should populate metric dict")

    def test_metrics_types(self):
        """Test we can query for all metrics types
        """
        metric_types = self.metric_stats.metrics_types()
        self.assertIsNotNone(metric_types, "read_all_metrics should not be None")
        self.assertIsInstance(metric_types, list, "metrics_types should be list")

    def test_read_vm_usage_mhz_metric(self):
        """Test vm_usage_mhz_metric method
        :return:
        """
        vm_name = self.sample_vm_name()
        metric_value = self.metric_stats.read_vm_usage_mhz_metric(vm_name)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")

        print(metric_value)

    def test_read_vm_usage_mhz_metric_interval(self):
        """Test vm_usage_mhz_metric method with interval larger > default 300
        :return:
        """
        vm_name = self.sample_vm_name()
        metric_value = self.metric_stats.read_vm_usage_mhz_metric(vm_name, interval_seconds=1200)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")

    def test_query_vm_available_perf_metrics(self):
        """Test a query available_VM perf_metrics method
        :return:
        """
        vm_name = self.sample_vm_name()
        metric_counter, metric_names = self.metric_stats.read_vm_available_perf_metric(vm_name)
        self.assertIsInstance(metric_counter, list, "return value must be list")
        self.assertIsInstance(metric_names, list, "return value must be list")
        self.assertTrue(all(isinstance(counter_id, int) for counter_id in metric_counter),
                        "Not all elements in metric_counter are integers")

        self.assertTrue(all(isinstance(name, str) for name in metric_names),
                        "Not all elements in metric_names are strings")

        self.assertEqual(len(metric_counter), len(metric_names),
                         "Lists metric_counter and metric_names should have the same length")

    def test_query_host_available_perf_metrics(self):
        """Test Query host available_perf_metrics method
        :return:
        """
        host = self.vm_esxi_host()
        host_metric_counter, host_metric_names = self.metric_stats.read_host_available_perf_metric(host)
        self.assertIsInstance(host_metric_counter, list, "return value must be list")
        self.assertIsInstance(host_metric_names, list, "return value must be list")
        self.assertTrue(all(isinstance(counter_id, int) for counter_id in host_metric_counter),
                        "Not all elements in host_metric_counter are integers")

        self.assertTrue(all(isinstance(name, str) for name in host_metric_names),
                        "Not all elements in host_metric_names are strings")

        self.assertEqual(len(host_metric_counter), len(host_metric_names),
                         "Lists host_metric_counter and host_metric_names should have the same length")

    def test_query_cluster_available_perf_metrics(self):
        """Test Query cluster available perf metrics method
        :return:
        """
        cluster = self.vm_cluster()
        cluster_metric_counter, cluster_metric_names = self.metric_stats.read_cluster_available_perf_metric(cluster)
        self.assertIsInstance(cluster_metric_counter, list, "return value must be list")
        self.assertIsInstance(cluster_metric_names, list, "return value must be list")

        self.assertTrue(all(isinstance(name, str) for name in cluster_metric_names),
                        "Not all elements in cluster_metric_names are strings")

        self.assertEqual(len(cluster_metric_counter), len(cluster_metric_names),
                         "Lists cluster_metric_counter and cluster_metric_names "
                         "should have the same length")

    def test_query_dvs_available_perf_metrics(self):
        """Test Query dvs available perf metrics method
        :return:
        """
        dvs_name = self.sample_dvs_name()
        cluster_metric_counter, cluster_metric_names = self.metric_stats.read_dvs_available_perf_metric(dvs_name)
        self.assertIsInstance(cluster_metric_counter, list, "return value must be list")
        self.assertIsInstance(cluster_metric_names, list, "return value must be list")

        self.assertTrue(all(isinstance(name, str) for name in cluster_metric_names),
                        "Not all elements in cluster_metric_names are strings")

        self.assertEqual(len(cluster_metric_counter), len(cluster_metric_names),
                         "Lists cluster_metric_counter and cluster_metric_names "
                         "should have the same length")

    def test_read_net_dvs_metrics(self):
        """
        :return:
        """
        dvs_name = self.sample_dvs_name()
        metric_value = self.metric_stats.read_net_dvs_metrics(dvs_name)
        print(metric_value)

    def test_read_core_count_metric(self):
        """ESXi host core utilization metric
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_value = self.metric_stats.read_core_utilization_metric(esxi_host)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 4, "return shape must (N, 4)")

    def test_read_cpu_latency_metric(self):
        """ESXi host core utilization metric
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_value = self.metric_stats.read_cpu_latency_metric(esxi_host)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")
        print(metric_value)

    def test_read_vm_net_usage_metric(self):
        """Test read_net_vm_usage_metric.
        :return:
        """
        vm_name = self.sample_vm_name()
        metric_values = self.metric_stats.read_net_vm_usage_metric(vm_name)
        self.assertIsInstance(metric_values, dict, "return value must be dict")
        for k in metric_values:
            metric_value = metric_values[k]
            self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
            self.assertTrue(metric_value.shape[1] == 6, "return shape must (N, 4)")
        print(metric_value)

    def test_read_host_net_usage_metric(self):
        """Test read_net_host_usage_metric.
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_values = self.metric_stats.read_net_host_usage_metric(esxi_host)
        self.assertIsInstance(metric_values, dict, "return value must be dict")
        for k in metric_values:
            metric_value = metric_values[k]
            self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
            self.assertTrue(metric_value.shape[1] == 6, "return shape must (N, 6)")
