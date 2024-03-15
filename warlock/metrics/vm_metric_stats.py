"""
VMwareMetricCollector, is designed to encapsulate VC API related
the performance metrics.   In context warlock it used to cross
correlated.

All metric value return as ndarray.

Most of the docs related to counter and interpretation
can be found here
https://vdc-repo.vmware.com/vmwb-repository/dcr-public/d1902b0e-d479-46bf-8ac9-cee0e31e8ec0/07ce8dbd-db48-4261-9b8f-c6d3ad8ba472/network_counters.html

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import os
import warnings
from functools import lru_cache
from typing import Optional, Dict, List, Tuple, Any

import numpy as np

from warlock.states.vm_state import (
    VMwareVimState
)

from pyVmomi import vim
from datetime import datetime, timedelta

VMwareMetricSeries = vim.PerformanceManager.MetricSeries
VMwareMetricIntSeries = vim.PerformanceManager.IntSeries
VMwarePerformanceManager = vim.PerformanceManager


class UpdateIntervalNotFound(Exception):
    def __init__(self, entity_name):
        message = f"Performance Update interval '{entity_name}' not found."
        super().__init__(message)


class VMwareMetricCollectorError(Exception):
    def __init__(self, msg):
        message = f"Metric Collector Error Update: '{msg}'."
        super().__init__(message)


class VMwareMetricCollector(VMwareVimState):
    """
     vSphere Aggregates metric information

    This level includes basic performance metrics that are averaged over the collection interval.
    It's suitable for general monitoring of key performance indicators.

    Entities Covered: CPU, Memory, Disk, Network, System Uptime, System Heartbeat, and DRS.
    Rollup Type: Average.
    Exclusions: Does not include device-specific counters.
    Example: Average CPU usage percentage, average memory usage, average disk I/O,
             and average network throughput.

    Counters with “average,” “summation,” and “latest” Rollup Types

    This level provides a more detailed view by including summation and latest rollup types,
    offering insights into total accumulations over the interval and the most recent values, respectively.

    Entities Covered: Same as above, with the addition of "summation" and "latest" metrics.
    Rollup Types: Average, Summation, Latest.
    Exclusions: Does not include device-specific counters.
    Example: Total bytes transmitted over the network during the interval (summation),
    the latest memory usage at the end of the interval.
    """
    def __init__(self,
                 environment_spec: Optional[Dict] = None,
                 vcenter_ip: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        :param environment_spec: is some dictionary where we get VC Sphere information.
        :param vcenter_ip: optional in case caller manually provide vCenter FQDN
        :param username: optional in case caller manually provide username
        :param password: optional in case caller manually provide
        """
        super().__init__(
            None,
            test_environment_spec=environment_spec,
            vcenter_ip=vcenter_ip,
            username=username,
            password=password
        )

        # store metric counter id to name and reverse mapping
        self._vm_type_to_name = {}
        self._vm_metrics_type = {}

    @classmethod
    def from_optional_credentials(
            cls,
            ssh_executor,
            vcenter_ip: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """Constructor that creates an instance using optional credentials.

        :param ssh_executor: Instance to execute SSH commands.
        :param vcenter_ip: Optional vCenter IP.
        :param username: Optional vCenter username.
        :param password: Optional vCenter password.
        :return: An instance of VMwareVimState.
        """
        if not isinstance(vcenter_ip, str):
            raise TypeError(f"vcenter_ip must be a string, got {type(vcenter_ip)}")

        if not isinstance(username, str):
            raise TypeError(f"vcenter username must be a string, got {type(username)}")

        if not isinstance(password, str):
            raise TypeError(f"vcenter password must be a string, got {type(password)}")

        vcenter_ip = vcenter_ip or os.getenv('VCENTER_IP')
        username = username or os.getenv('VCENTER_USERNAME')
        password = password or os.getenv('VCENTER_PASSWORD')
        return cls(None, vcenter_ip.strip(), username.strip(), password.strip())

    def _get_perf_manager(
            self
    ) -> VMwarePerformanceManager:
        """
        Retrieve the PerformanceManager object from vCenter.
        :return: VMwarePerformanceManager
        :raises VMwareMetricCollectorError if failed to retrieve performance manager.
        """
        if not self.si:
            self.connect_to_vcenter()

        p = self.si.content.perfManager
        if p is None:
            raise VMwareMetricCollectorError("Failed get performance manager.")

        return p

    def _read_available_perf_metrics(
            self,
            entity
    ):
        """Reads available performance metrics for a given VMware entity.

        :param entity: The managed entity object (e.g., VirtualMachine, HostSystem) to query metrics for.
        :return:  A list of available performance metrics for the entity.
        """
        if len(self._vm_metrics_type) == 0:
            self.read_all_supported_metrics()

        entity_metric = self._get_perf_manager().QueryAvailablePerfMetric(entity=entity)
        if entity_metric is None:
            raise VMwareMetricCollectorError("Failed fetch entity metric.")

        return entity_metric

    def read_entity_metric(
            self,
            entity_name: str,
            entity_type: str,
            metric_indices: List[int],
            interval_seconds: Optional[int] = 6000,
            max_sample: Optional[int] = 30,
            metric_instance: str = "",
    ) -> np.ndarray:
        """
        Retrieve metric counters for a given VM over the specified interval,
        where metrix_indices is list of metrics

        :param metric_instance:
        :param entity_name: VMware's entity name
        :param entity_type: VMware's managed entity type
        :param metric_indices:
        :param interval_seconds: The time interval in seconds to calculate samples.
        :param max_sample: number of samples returned.
        :return: numpy array of metric values with shape (max_sample, num_metrics)
        """

        max_sample = max(1, max_sample)
        interval_seconds = max(60, interval_seconds)

        perf_manager = self._get_perf_manager()
        entity = self.get_managed_entities(entity_name, entity_type)

        metric_ids = [vim.PerformanceManager.MetricId(
            counterId=idx, instance=metric_instance) for idx in metric_indices]

        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=interval_seconds)
        query = vim.PerformanceManager.QuerySpec(
            entity=entity,
            metricId=metric_ids,
            startTime=start_time,
            endTime=end_time,
            maxSample=max_sample
        )

        stats = perf_manager.QueryPerf(querySpec=[query])

        if stats:
            metric_values = {}
            for metric_id, series in zip(metric_indices, stats[0].value):
                metric_values[metric_id] = [vv for vv in series.value]

            if len(metric_values) == 0:
                warnings.warn(f"No usage data found for host {entity_name}, metrics {str(metric_indices)}")
                return np.array([], dtype=np.float32).reshape(0, len(metric_indices))

            num_samples = min(len(v) for v in metric_values.values())
            np_values = np.zeros((num_samples, len(metric_indices)), dtype=np.float32)
            for i, metric_id in enumerate(metric_indices):
                np_values[:, i] = metric_values[metric_id][:num_samples]

            return np_values
        else:
            warnings.warn(f"No usage data found for {entity_name}, metrics {str(metric_indices)}")
            return np.array([], dtype=np.float32).reshape(0, len(metric_indices))

    def read_vm_usage_mhz_metric(
            self,
            vm_name: str,
            interval_seconds: Optional[int] = 300,
            max_sample: Optional[int] = 30,
    ) -> np.ndarray:
        """Collect CPU usage metrics for a given virtual machine.

        :param vm_name: Name of the VM instance
        :param interval_seconds: Number of seconds in past to collect
        :param max_sample: Maximum number of samples to collect per time frame
        :raises VMNotFoundException if the VM does not exist
        :return: np.ndarray: Numpy array containing the CPU usage metrics.
        """
        metric_indices = [
            self.metric_index("cpu.usagemhz.average"),
            self.metric_index("cpu.usagemhz.minimum"),
            self.metric_index("cpu.usagemhz.maximum"),
        ]
        return self.read_entity_metric(vm_name, "vm", metric_indices, interval_seconds, max_sample)

    def read_host_mhz_metric(
            self,
            esxi_host: str,
            interval_seconds: Optional[int] = 300,
            max_sample: Optional[int] = 30,
    ) -> np.ndarray:
        """Collect CPU usage metrics for a given virtual machine.

        :param esxi_host: Name of the esxi_host instance
        :param interval_seconds: Number of seconds in past to collect
        :param max_sample: Maximum number of samples to collect per time frame
        :raises VMNotFoundException if the VM does not exist
        :return: np.ndarray: Numpy array containing the CPU usage metrics.
        """
        metric_indices = [
            self.metric_index("cpu.usagemhz.average"),
            self.metric_index("cpu.usagemhz.minimum"),
            self.metric_index("cpu.usagemhz.maximum"),
        ]
        return self.read_entity_metric(esxi_host, "host", metric_indices, interval_seconds, max_sample)

    def read_net_vm_usage_metric(
            self,
            vm_name: str,
            interval_seconds: Optional[int] = 300,
            max_sample: Optional[int] = 30,
    ) -> Dict[str, np.ndarray]:
        """Method reads vm net usage metrics. It resolves
        VM virtual nic adapters and return result as dict where a key is network
        adapter identifier and the value is np.ndarray

        (N, 0) - packetsTx
        (N, 1) - packetsRx
        (N, 2) - droppedTx
        (N, 3) - droppedRx
        (N, 4) - received is average in kb/sec
        (N, 5) - transmitted is average in kb/sec

        :param vm_name: Name of the VM instance
        :param interval_seconds: Number of seconds in past to collect
        :param max_sample: Maximum number of samples to collect per time frame
        :return:
        """
        vnic_info = self.read_vm_vnic_info(vm_name)
        vnic_labels = [vnic['key'] for vnic in vnic_info if vnic["is_sriov"] is False]

        metric_indices = [
            self.metric_index("net.packetsTx.summation"),
            self.metric_index("net.packetsRx.summation"),
            self.metric_index("net.droppedTx.summation"),
            self.metric_index("net.droppedRx.summation"),
            self.metric_index("net.received.average"),
            self.metric_index("net.transmitted.average"),
        ]

        vnic_stats = {
            vnic_key: self.read_entity_metric(
                vm_name, "vm",
                metric_indices,
                interval_seconds,
                max_sample,
                metric_instance=str(vnic_key)
            ) for vnic_key in vnic_labels
        }

        return vnic_stats

    def read_net_host_usage_metric(
            self,
            host_name: str,
            interval_seconds: Optional[int] = 300,
            max_sample: Optional[int] = 30,
    ) -> Dict[str, np.ndarray]:
        """Collect vmnic net stats for ESXi host .

        The return shape is (N, 6)
        Where
        col 0 net.packetsTx.summation
        col 1 net.packetsRx.summation
        col 2 net.droppedTx.summation
        col 3 net.droppedRx.summation
        col 4 net.received.average
        col 5 net.transmitted.average

        net.received.average units kiloBytesPerSecond
        net.transmitted.average units kiloBytesPerSecond

        :param host_name: Name of the VM instance
        :param interval_seconds: Number of seconds in past to collect
        :param max_sample: Maximum number of samples to collect per time frame
        :return:
        """

        vmnic_dict = self.read_esxi_host_pnic(host_name)
        _vmnics = list(vmnic_dict.keys())

        metric_indices = [
            self.metric_index("net.packetsTx.summation"),
            self.metric_index("net.packetsRx.summation"),
            self.metric_index("net.droppedTx.summation"),
            self.metric_index("net.droppedRx.summation"),
            self.metric_index("net.received.average"),
            self.metric_index("net.transmitted.average"),
        ]

        vmnic_stats = {}
        # we're passing vmnic0, vmnic1 etc
        for _vmnic in _vmnics:
            vmnic_stats[_vmnic] = self.read_entity_metric(
                host_name, "host",
                metric_indices,
                interval_seconds,
                max_sample,
                metric_instance=_vmnic
            )

        return vmnic_stats

    def read_core_utilization_metric(
            self,
            host_name: str,
            interval_seconds: Optional[int] = 300,
            max_sample: Optional[int] = 30,
    ) -> np.ndarray:
        """Collect core utilization metrics, CPU usage as a percent during the interval.

        coreUtilization
        average unit a percentage

        (minimum)
        (maximum)
        (none)

        :param host_name: Name of the VM instance
        :param interval_seconds: Number of seconds in past to collect
        :param max_sample: Maximum number of samples to collect per time frame
        :return:
        """
        metric_indices = [
            self.metric_index("cpu.coreUtilization.average"),
            self.metric_index("cpu.coreUtilization.minimum"),
            self.metric_index("cpu.coreUtilization.maximum"),
            self.metric_index("cpu.coreUtilization.none"),
        ]

        return self.read_entity_metric(
            host_name, "host",
            metric_indices,
            interval_seconds,
            max_sample
        )

    def read_cpu_latency_metric(
            self,
            host_name: str,
            interval_seconds: Optional[int] = 300,
            max_sample: Optional[int] = 30,
    ) -> np.ndarray:
        """Collect core latency , readiness and wait metrics.

        latency , unit percent
        readiness, percent , unit percent
        cpu.wait.summation - CPU time spent waiting for swap-in.

        :param host_name: Name of the VM instance
        :param interval_seconds: Number of seconds in past to collect
        :param max_sample: Maximum number of samples to collect per time frame
        :return:
        """

        metric_indices = [
            self.metric_index("cpu.latency.average"),
            self.metric_index("cpu.readiness.average"),
            self.metric_index("cpu.wait.summation"),
        ]
        return self.read_entity_metric(host_name, "host", metric_indices, interval_seconds, max_sample)

    def read_net_dvs_metrics(
            self,
            dvs_name: str,
            interval_seconds: Optional[int] = 300,
            max_sample: Optional[int] = 30,
    ) -> np.ndarray:
        """Collect dvs net count metrics.

        :param dvs_name: Name of the VM instance
        :param interval_seconds: Number of seconds in past to collect
        :param max_sample: Maximum number of samples to collect per time frame
        :return:
        """
        metric_ids, metric_names = self.read_dvs_available_perf_metric(dvs_name)

        metric_indices = [
            self.metric_index("net.throughput.vds.pktsTx.average"),
            self.metric_index("net.throughput.vds.pktsRx.average"),
            self.metric_index("net.throughput.vds.droppedTx.average"),
            self.metric_index("net.throughput.vds.droppedRx.average"),
        ]

        return self.read_entity_metric(dvs_name, "dvs", metric_indices, interval_seconds, max_sample)

    def read_net_dvs_log_metrics(
            self,
            dvs_name: str,
            interval_seconds: Optional[int] = 600,
            max_sample: Optional[int] = 30,
    ) -> np.ndarray:
        """Collect dvs net count log metrics.
        :param dvs_name: Name of the VM instance
        :param interval_seconds: Number of seconds in past to collect
        :param max_sample: Maximum number of samples to collect per time frame
        :return:
        """

        metric_ids, metric_names = self.read_dvs_available_perf_metric(dvs_name)

        metric_indices = [
            self.metric_index("net.throughput.vds.lagTx.average"),
            self.metric_index("net.throughput.vds.lagRx.average"),
            self.metric_index("net.throughput.vds.lagDropTx.average"),
            self.metric_index("net.throughput.vds.lagDropRx.average"),
        ]

        return self.read_entity_metric(dvs_name, "dvs", metric_indices, interval_seconds, max_sample)

    def metrics_types(self) -> List[str]:
        """Returns a list of all available metrics types
        :return:
        """
        if len(self._vm_metrics_type) == 0:
            self.read_all_supported_metrics()
        return list(self._vm_metrics_type.keys())

    def metric_index(
            self,
            metric_type: str
    ) -> int:
        """Return metric counter id based metric type (string)
        cpu.usagemhz.average etc.

        :param metric_type: metric type (string)
        :return: metric counter id based metric type (string)
        """
        if len(self._vm_metrics_type) == 0:
            self.read_all_supported_metrics()
        return self._vm_metrics_type[metric_type]

    def resolve_metric_names(
            self, counter_ids: List[int]
    ) -> List[str]:
        """Resolves metric counter IDs to their names.

        :param counter_ids: List of metric counter IDs.
        :return: List of metric names.
        """
        if len(self._vm_metrics_type) == 0:
            self.read_all_supported_metrics()

        return [self._vm_type_to_name.get(cid, f"Unknown Metric ID: {cid}") for cid in counter_ids]

    @lru_cache(maxsize=None)
    def read_all_supported_metrics(
            self,
    ) -> Dict[str, int]:
        """Retrieve list of all available metrics and return Dict
        mapping metric name to counter id.

        :return: Dict mapping metric name to counter id
        """
        perf_manager = self._get_perf_manager()
        perf_counters = perf_manager.perfCounter
        if perf_manager is None:
            raise VMwareMetricCollectorError("perfCounter is None")

        for counter in perf_counters:
            counter_full = f"{counter.groupInfo.key}.{counter.nameInfo.key}.{counter.rollupType}"
            self._vm_metrics_type[counter_full] = counter.key
            self._vm_type_to_name[counter.key] = counter_full

        return self._vm_metrics_type

    def read_available_perf_metrics(
            self,
            entity_name: str,
            entity_type: str,
    ) -> Tuple[List[Any], List[str]]:
        """Reads available performance metrics for a given VMware entity.

        :param entity_type:
        :param entity_name: The managed entity object (e.g., VirtualMachine, HostSystem) to query metrics for.
        :return:  A list of available performance metrics for the entity.
        """
        entity = self.get_managed_entities(entity_name, entity_type)
        metric_ids = self._read_available_perf_metrics(entity)
        counter_ids = [metric.counterId for metric in metric_ids]
        metric_names = self.resolve_metric_names(counter_ids)
        return counter_ids, metric_names

    def read_vm_available_perf_metric(
            self,
            vm_name: str
    ) -> Tuple[List[Any], List[str]]:
        """Reads available performance metric for VM object
        :param vm_name:
        :raise VMNotFoundException: if a VM not found
        :return list available of counter id and name of metric VM entity supports.
        """
        return self.read_available_perf_metrics(vm_name, "vm")

    def read_host_available_perf_metric(
            self,
            host: str
    ) -> Tuple[List[Any], List[str]]:
        """Reads available performance metric for ESXi host object
        :param host: esxi host identifier
        :return: return list available of counter id and name of metric esxi host entity supports.
        """
        return self.read_available_perf_metrics(host, "host")

    def read_cluster_available_perf_metric(
            self,
            host: str
    ) -> Tuple[List[Any], List[str]]:
        """Reads available performance metric for VMware Cluster object.
        :param host: cluster name identifier
        :return: return list available of counter id and name of metric cluster entity supports.
        """
        return self.read_available_perf_metrics(host, "cluster")

    def read_dvs_available_perf_metric(
            self,
            dvs_name: str
    ) -> Tuple[List[Any], List[str]]:
        """Reads available performance metric for VMware DVS object.
        :param dvs_name: dvs name identifier
        :return: return list available of counter id and name of metric dvs entity supports.
        """
        return self.read_available_perf_metrics(dvs_name, "dvs")

    def update_perf_intervals(
            self,
            interval_id: int,
            enabled: Optional[bool] = None,
            length: Optional[int] = None,
            sampling_period: Optional[int] = None
    ):
        """
        Update the performance collection interval settings to a x-second sampling period.
        by default, we update to default value 300.

        Default intervals
        https://developer.vmware.com/apis/vi-json/latest/sdk/vim25/release/PerformanceManager/moId/UpdatePerfInterval/post/

        :param interval_id: The ID of the interval to update.
        :param enabled: Whether the interval is enabled (True or False).
        :param length: The length of the interval in seconds.
        :param sampling_period: The new sampling period in seconds. Set to 60 for this example.
        """

        perf_manager = self._get_perf_manager()
        current_intervals = perf_manager.historicalInterval
        if current_intervals is None:
            raise VMwareMetricCollectorError("Historical interval is None.")

        interval = next((i for i in current_intervals if i.key == interval_id), None)
        if not interval:
            raise UpdateIntervalNotFound(interval_id)

        if enabled is not None:
            interval.enabled = enabled
        if length is not None:
            interval.length = length
        if sampling_period is not None:
            interval.samplingPeriod = sampling_period

        try:
            perf_manager.UpdatePerfInterval(interval)
        except Exception as e:
            raise VMwareMetricCollectorError(
                f"Failed to update interval {interval_id}: {str(e)}")

    def read_update_intervals(
            self
    ) -> Dict[Any, Any]:
        """
        Return all historical update intervals as dict
        The collection level for the historical intervals can be changed.
        https://developer.vmware.com/apis/vi-json/latest/sdk/vim25/release/PerformanceManager/moId/UpdatePerfInterval/post/

        :return: a dict with all updated intervals
        :raise VMwareMetricCollectorError if failed get performance manager object
        """

        perf_manager = self._get_perf_manager()
        current_intervals = perf_manager.historicalInterval
        if current_intervals is None:
            raise VMwareMetricCollectorError("Historical interval is None.")

        interval_dict = {
            interval.key: {
                'samplingPeriod': interval.samplingPeriod,
                'name': interval.name,
                'length': interval.length,
                'level': interval.level,
                'enabled': interval.enabled
            } for interval in current_intervals
        }
        return interval_dict
