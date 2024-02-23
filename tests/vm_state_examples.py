import json
import os
from warlock.vm_state import VMwareVimState


def vim_state_examples():
    return VMwareVimState.from_optional_credentials(
        None, vcenter_ip=os.getenv('VCENTER_IP', 'default'),
        username=os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local'),
        password=os.getenv('VCENTER_PASSWORD', 'default')
    )


def example_vm_pnics(vm_name="vf-test-np1"):
    """
    :return:
    """
    vm_name = "vf-test-np1"
    vmware_vim_state = vim_state_examples()

    vms, vms_config = vmware_vim_state.find_vm_by_name_substring(vm_name)
    vmware_vim_state.get_vm_hardware(vms_config[0])
    pnic_data = vmware_vim_state.read_vm_pnic_info(vms[0])

    dvs_uuids = list(pnic_data.keys())

    print(pnic_data.keys())
    print(f"VM name: {vms[0]}")
    print(vmware_vim_state.read_vm_pnic_info(vms[0]))
    print(vmware_vim_state.get_dvs_by_uuid(dvs_uuids[0]))


def example_vms_backend_host(vm_name="vf-test-np1"):
    """
    :return:
    """
    vm_name = "vf-test-np1"
    vmware_vim_state = VMwareVimState.from_optional_credentials(
        None,
        vcenter_ip=os.getenv('VCENTER_IP', 'default'),
        username=os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local'),
        password=os.getenv('VCENTER_PASSWORD', 'default')
    )

    vms, vms_config = vmware_vim_state.find_vm_by_name_substring(vm_name)
    esxi_host = vmware_vim_state.get_esxi_ip_of_vm(vms[0])
    print(esxi_host)

    esxi_host = vmware_vim_state.get_esxi_ip_of_vm(vms[1])
    print(esxi_host)


def example_vms_sriov_nics(vm_name="vf-test-np1"):
    """
    :return:
    """
    vmware_vim_state = vim_state_examples()

    vms, vms_config = vmware_vim_state.find_vm_by_name_substring(vm_name)
    esxi_host = vmware_vim_state.get_esxi_ip_of_vm(vms[0])
    print(esxi_host)

    esxi_host = vmware_vim_state.get_esxi_ip_of_vm(vms[1])
    print(esxi_host)

    vm_sriov_adapters = vmware_vim_state.vm_sriov_devices(vms[0])
    # vms_config_dicts = [vm_config_to_dict(vm_config) for vm_config in vms_config]

    # Now you can serialize vms_config_dicts to JSON
    print(json.dumps(vm_sriov_adapters, indent=4))

    vms, vms_config = vmware_vim_state.find_vm_by_name_substring(vm_name)
    esxi_host = vmware_vim_state.get_esxi_ip_of_vm(vms[0])
    pci_info = vmware_vim_state.get_pci_device_info(esxi_host, '0000:88:00.0')
    print("Pnic INFO")
    print(pci_info)


def example_vms_state():
    """
    :return:
    """
    vm_sub_name = "vf-test-np1"
    vmware_vim_state = vim_state_examples()
    vms_state = vmware_vim_state.vm_state(vm_sub_name)
    print(json.dumps(vms_state, indent=4))
