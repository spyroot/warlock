"""
Unit tests for vm_metric_stats.py

Author: Mustafa Bayramov
spyroot@gmail.com
mbayramo@stanford.edu

"""
import os
import unittest
import numpy as np
import time

from warlock.metrics.vm_metric_stats import VMwareMetricCollector
from warlock.states.vm_state import (
    VMwareVimStateReader, VMNotFoundException, EsxHostNotFound
)


class TestVMwareVimState(unittest.TestCase):
    """
    """
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

        _obj = VMwareVimStateReader(
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
        """Unit test util , sample some VM based on substring
        :return:
        """
        found_vms, found_vm_config = self.metric_stats.find_vm_by_name_substring(
            self._test_valid_vm_substring
        )
        return next(iter(found_vms))

    def sample_dvs_name(self) -> str:
        """Unit test util, sample some VM based on substring
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
        self.assertTrue(all(isinstance(k, str) for k in metric_types),
                        "all elements must string")

        self.assertTrue(all(isinstance(v, int) for v in metric_types.values()),
                        "all values must ints")

    def test_metrics_types(self):
        """Test we can query for all metrics types
        """
        metric_types = self.metric_stats.metrics_types()
        self.assertIsNotNone(metric_types, "metrics_types should not be None")
        self.assertIsInstance(metric_types, list, "metrics_types should be list")
        self.assertTrue(all(isinstance(k, str) for k in metric_types),
                        "all elements must string")

    def test_query_vm_available_perf_metrics(self):
        """Test a query read_vm_available_perf_metric method
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
        """Test Query host read_host_available_perf_metric method
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

    def test_read_vm_usage_mhz_metric(self):
        """Test read_vm_usage_mhz_metric method.
        :return:
        """
        vm_name = self.sample_vm_name()
        metric_value = self.metric_stats.read_vm_usage_mhz_metric(vm_name)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")

    def test_read_host_mhz_metric(self):
        """Test read_host_mhz_metric method.
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_value = self.metric_stats.read_host_mhz_metric(esxi_host)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")

    def test_read_vm_usage_mhz_metric_not_found(self):
        """Test read_vm_usage_mhz_metric should throw exception if vm not found.
        :return:
        """
        with self.assertRaises(VMNotFoundException):
            _ = self.metric_stats.read_vm_usage_mhz_metric("bad")

    def test_read_vm_usage_mhz_metric_interval(self):
        """Test read_vm_usage_mhz_metric method with interval larger > default 300
        :return:
        """
        vm_name = self.sample_vm_name()
        metric_value = self.metric_stats.read_vm_usage_mhz_metric(vm_name, interval_seconds=1200)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")

    def test_read_vm_usage_mhz_metric_interval_n_sample(self):
        """Test read_vm_usage_mhz_metric method with interval larger > default 300
        :return:
        """
        vm_name = self.sample_vm_name()
        metric_value = self.metric_stats.read_vm_usage_mhz_metric(
            vm_name, max_sample=1, interval_seconds=1200)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")
        self.assertTrue(metric_value.shape[0] == 1, "return shape must (1, 3)")

    def test_read_core_utilization_metric(self):
        """ESXi host core utilization metric
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_value = self.metric_stats.read_core_utilization_metric(esxi_host)
        self.assertIsNotNone(metric_value, "return value must be not None")
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 4, "return shape must (N, 4)")

    def test_read_core_utilization_metric_not_found(self):
        """ESXi host core utilization metric
        :return:
        """
        with self.assertRaises(EsxHostNotFound):
            metric_value = self.metric_stats.read_core_utilization_metric("bad")

    def test_read_core_utilization_large_interval(self):
        """ESXi host core utilization metric
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_value = self.metric_stats.read_core_utilization_metric(esxi_host, interval_seconds=1200)
        self.assertIsNotNone(metric_value, "return value must be not None")
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 4, "return shape must (N, 4)")
        self.assertTrue(metric_value.shape[0] > 1, "first dim should > 1")

    def test_read_core_utilization_short_interval(self):
        """Tests ESXi host core utilization metric
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_value = self.metric_stats.read_core_utilization_metric(esxi_host, interval_seconds=0)
        self.assertIsNotNone(metric_value, "return value must be not None")
        self.assertEqual(metric_value.size, 0, "For a short interval, expected return value is an empty np.ndarray")

    def test_read_cpu_latency_metric(self):
        """Test ESXi host core utilization metric
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_value = self.metric_stats.read_cpu_latency_metric(esxi_host)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")

    def test_read_cpu_latency_metric_not_found(self):
        """Test ESXi host core utilization metric, host not found case
        :return:
        """
        with self.assertRaises(EsxHostNotFound):
            _ = self.metric_stats.read_cpu_latency_metric("bad")

    def test_read_vm_net_usage_metric(self):
        """Test read_net_vm_usage_metric
        :return:
        """
        vm_name = self.sample_vm_name()
        metric_values = self.metric_stats.read_net_vm_usage_metric(vm_name)
        self.assertIsInstance(metric_values, dict, "return value must be dict")
        for k in metric_values:
            metric_value = metric_values[k]
            self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
            self.assertTrue(metric_value.shape[1] == 6, "return shape must (N, 4)")

    def test_read_host_net_usage_metric(self):
        """Test read net host usage metric.
        :return:
        """
        esxi_host = self.vm_esxi_host()
        metric_values = self.metric_stats.read_net_host_usage_metric(esxi_host)
        self.assertIsInstance(metric_values, dict, "return value must be dict")
        for k in metric_values:
            metric_value = metric_values[k]
            self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
            self.assertTrue(metric_value.shape[1] == 6, "return shape must (N, 6)")

    def test_read_all_perf_intervals(self):
        """Test read all performance intervals."""

        intervals = self.metric_stats.read_update_intervals()
        self.assertIsInstance(intervals, dict, "return value must be dict")

        expected_keys = [1, 2, 3, 4]
        expected_sub_keys = ['samplingPeriod', 'name', 'length', 'level', 'enabled']

        for key in expected_keys:
            self.assertIn(key, intervals, f"Expected key {key} not found in intervals")

            interval_info = intervals[key]
            self.assertIsInstance(interval_info, dict, f"Interval info for key {key} must be a dict")

            for sub_key in expected_sub_keys:
                self.assertIn(sub_key, interval_info,
                              f"Expected sub-key {sub_key} not found in interval info for key {key}")

            self.assertIsInstance(interval_info['samplingPeriod'], int, "samplingPeriod should be an int")
            self.assertIsInstance(interval_info['name'], str, "name should be a string")
            self.assertIsInstance(interval_info['length'], int, "length should be an int")
            self.assertIsInstance(interval_info['level'], int, "level should be an int")
            self.assertIsInstance(interval_info['enabled'], bool, "enabled should be a bool")

    def test_update_interval(self):
        """Test read all performance intervals."""
        interval_info = self.metric_stats.read_update_intervals()
        initial_sampling_period = interval_info[1]['samplingPeriod']

        # read and check
        self.metric_stats.update_perf_intervals(1, sampling_period=60)
        updated_intervals = self.metric_stats.read_update_intervals()
        updated_sampling_period = updated_intervals[1]['samplingPeriod']

        self.assertNotEqual(initial_sampling_period, updated_sampling_period,
                            "The initial and updated sampling periods should not be equal.")

        self.assertEqual(updated_sampling_period, 60,
                         "The updated sampling period should be 60 seconds.")

        # reset the interval back to its original state
        self.metric_stats.update_perf_intervals(1, sampling_period=300)

    def test_update_collect_reset_back(self):
        """
        This test update collect interval sleep and check number of samples
        returned
        :return:
        """
        interval_info = self.metric_stats.read_update_intervals()
        initial_sampling_period = interval_info[1]['samplingPeriod']

        # 1) update to 60 second and check it updated
        self.metric_stats.update_perf_intervals(1, sampling_period=60)
        updated_intervals = self.metric_stats.read_update_intervals()
        updated_sampling_period = updated_intervals[1]['samplingPeriod']

        self.assertNotEqual(initial_sampling_period, updated_sampling_period,
                            "The initial and updated sampling periods should not be equal.")

        self.assertEqual(updated_sampling_period, 60,
                         "The updated sampling period should be 60 seconds.")

        # we sleep for 2 minutes and check how many sample we get
        time.sleep(120)
        vm_name = self.sample_vm_name()
        metric_value = self.metric_stats.read_vm_usage_mhz_metric(vm_name, interval_seconds=360, max_sample=60)
        self.assertIsInstance(metric_value, np.ndarray, "return value must be np.ndarray")
        self.assertTrue(metric_value.shape[1] == 3, "return shape must (N, 3)")
        self.assertTrue(metric_value.shape[0] > 0, "Should collect more than 0 samples")


        # reset the interval back to its original state
        self.metric_stats.update_perf_intervals(1, sampling_period=300)