import argparse
import json
import os

from warlock.vm_metric_stats import VMwareMetricCollector


def vim_state_examples() -> VMwareMetricCollector:
    return VMwareMetricCollector.from_optional_credentials(
        None, vcenter_ip=os.getenv('VCENTER_IP', 'default'),
        username=os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local'),
        password=os.getenv('VCENTER_PASSWORD', 'default')
    )


def sample_vm_name(vm_name="vf-test-np1") -> str:
    """Sample some VM based on substring
    :return:
    """
    collector = vim_state_examples()
    found_vms, found_vm_config = collector.find_vm_by_name_substring(
        vm_name
    )
    return next(iter(found_vms))


def example_read_vm_metrics():
    """Example for query for available metrics for VM
    :return:
    """
    vm_name = sample_vm_name()
    collector = vim_state_examples()
    metric_ids, metric_names = collector.read_vm_available_perf_metric(vm_name)

    VMwareMetricCollector.from_optional_credentials(
        None, vcenter_ip=os.getenv('VCENTER_IP', 'default'),
        username=os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local'),
        password=os.getenv('VCENTER_PASSWORD', 'default')
    ).read_vm_usage_mhz_metric(vm_name)

    print(json.dumps(metric_ids, indent=4, sort_keys=True))
    print(json.dumps(metric_names, indent=4))


def example_read_vm_usage_mhz_metric():
    """Example for reading usage metrics for VM in mhz
    :return:
    """
    vm_name = sample_vm_name()
    collector = vim_state_examples()
    data = collector.read_vm_usage_mhz_metric(vm_name)
    print(data)


def main():
    """Example main
    :return:
    """
    parser = argparse.ArgumentParser(description='Read VM metrics from vCenter.')
    parser.add_argument('--vcenter', required=True, help='vCenter IP address or hostname')
    parser.add_argument('--username', help='vCenter username', default='administrator@vsphere.local')
    parser.add_argument('--password', required=True, help='vCenter password')
    args = parser.parse_args()

    os.environ['VCENTER_IP'] = args.vcenter
    os.environ['VCENTER_USERNAME'] = args.username
    os.environ['VCENTER_PASSWORD'] = args.password

    example_read_vm_metrics()
    example_read_vm_usage_mhz_metric()


if __name__ == "__main__":
    main()



