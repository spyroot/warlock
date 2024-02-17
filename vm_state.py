"""
This class represents a VMware VIM  state.  The main purpose of this class
is to read VMware object VM, host so in down stream task we can mutate.

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import json
import os
from typing import Dict, Optional, List, Tuple, Any

import pyVmomi
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import atexit
import ssl

from ssh_runner import SshRunner

VMConfigInfo = vim.vm.ConfigInfo
VirtualHardwareInfo = vim.vm.VirtualHardware
DistributedVirtualSwitch = vim.dvs.VmwareDistributedVirtualSwitch
DistributedVirtualSwitchConfig = vim.dvs.VmwareDistributedVirtualSwitch.ConfigInfo
EsxHost = vim.HostSystem


class VMwareVimStateException(Exception):
    """Custom exception for VMwareVimState class."""
    pass


class SwitchNotFound(Exception):
    def __init__(self, uuid):
        message = f"Distributed Virtual Switch with UUID '{uuid}' not found."
        super().__init__(message)


class EsxHostNotFound(Exception):
    def __init__(self, identified):
        message = f"Esxi host with identified '{identified}' not found."
        super().__init__(message)


class VMNotFoundException(Exception):
    """Exception to be raised when a VM cannot be found."""

    def __init__(self, vm_name):
        message = f"VM '{vm_name}' not found."
        super().__init__(message)


class VMwareVimState:
    def __init__(
            self, ssh_executor: SshRunner,
            test_environment_spec: Optional[Dict] = None,
            vcenter_ip: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """
        Initialize VMwareVimState with credentials and SSH executor.

        :param ssh_executor: SshRunner instance to execute SSH commands.
        :param test_environment_spec: Optional dictionary containing environment specifications.
        :param vcenter_ip: Optional vCenter IP, preferred over test_environment_spec if provided.
        :param username: Optional vCenter username, preferred over test_environment_spec if provided.
        :param password: Optional vCenter password, preferred over test_environment_spec if provided.
        """
        self.ssh_executor = ssh_executor
        self.test_environment_spec = test_environment_spec

        # Default values from test_environment_spec if it exists and specific values are not provided
        default_vcenter_ip = self.test_environment_spec.get('iaas', {}).get('vcenter_ip',
                                                                            '') if self.test_environment_spec else ''
        default_username = self.test_environment_spec.get('iaas', {}).get('username',
                                                                          '') if self.test_environment_spec else ''
        default_password = self.test_environment_spec.get('iaas', {}).get('password',
                                                                          '') if self.test_environment_spec else ''

        # Use provided values or defaults from test_environment_spec
        self.vcenter_ip = vcenter_ip if vcenter_ip is not None else default_vcenter_ip
        self.username = username if username is not None else default_username
        self.password = password if password is not None else default_password

        # cache mapping host id to hostname
        self._host_name_to_id = {}
        self._host_id_to_name = {}

        # cache mapping switch uuid to dvs
        self._dvs_uuid_to_dvs = {}

        # cache for VM searches
        self._vm_search_cache = {}

        self.esxi_host_cache = {
            'ip': {},
            'name': {},
            'uuid': {},
            'moId': {}
        }

        self.si = None

        self._vm_cache = {}

    def connect_to_vcenter(self):
        """Connect to the vCenter server and store the connection instance."""
        if not self.si:
            context = ssl._create_unverified_context()
            self.si = SmartConnect(
                host=self.vcenter_ip,
                user=self.username,
                pwd=self.password,
                sslContext=context
            )
            atexit.register(Disconnect, self.si)

    @classmethod
    def from_optional_credentials(
            cls, ssh_executor,
            vcenter_ip: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """
        Constructor that creates an instance using optional credentials.

        :param ssh_executor: Instance to execute SSH commands.
        :param vcenter_ip: Optional vCenter IP.
        :param username: Optional vCenter username.
        :param password: Optional vCenter password.
        :return: An instance of VMwareVimState.
        """
        vcenter_ip = vcenter_ip or os.getenv('VCENTER_IP')
        username = username or os.getenv('VCENTER_USERNAME')
        password = password or os.getenv('VCENTER_PASSWORD')
        return cls(ssh_executor, None, vcenter_ip, username, password)

    def _find_by_dns_name(self, vm_name):
        """
        Retrieves a virtual machine by its DNS name.

        :param vm_name: The DNS name of the VM.
        :return: The VM object if found, None otherwise.
        """
        # Check if the VM is already in the cache
        if vm_name in self._vm_cache:
            return self._vm_cache[vm_name]

        self.connect_to_vcenter()
        content = self.si.RetrieveContent()
        search_index = content.searchIndex
        vm = search_index.FindByDnsName(dnsName=vm_name, vmSearch=True)

        self._vm_cache[vm_name] = vm
        return vm

    def find_vm_by_name_substring(
            self, name_substring: str) -> Tuple[List[str], List[VMConfigInfo]]:
        """
        Find a VM by name substring in the vCenter server.

        :param name_substring: Substring of the VM name to search for.
        :return: Full name of the VM that matches the substring.
        :raises VMwareVimStateException: If the VM is not found.
        """

        if name_substring in self._vm_search_cache:
            return self._vm_search_cache[name_substring]

        self.connect_to_vcenter()
        content = self.si.RetrieveContent()

        ctx_view = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True)
        vms = ctx_view.view

        if not hasattr(ctx_view, 'view'):
            return [], []

        ctx_view.Destroy()

        found_vms = []
        found_vm_config = []

        for vm in vms:
            if name_substring in vm.name:
                found_vms.append(vm.name)
                found_vm_config.append(vm.config)

        # add to a cache
        self._vm_search_cache[name_substring] = (found_vms, found_vm_config)
        return found_vms, found_vm_config

    def get_dvs_pnics_by_switch_uuid(
            self,
            switch_uuid: str
    ) -> Dict[str, List[str]]:
        """
        Retrieves all physical NICs associated with a given Distributed Virtual Switch,
        organized by host. This method returns a dictionary where keys are host
        identifiers and values are lists of pNICs.

        {
            'x.x.x.x': ['vmnic5'],
            'x.x.x.x': ['vmnic5'],
            'x.x.x.x': ['vmnic5'],
            'x.x.x.x': ['vmnic8']
            }


        :param switch_uuid: The UUID of the Distributed Virtual Switch.
        :return: A dictionary where keys are host identifiers and values are lists of pNICs.
        """
        dvs_pnics_by_host = {}
        ctx = self.si.RetrieveContent()
        container = ctx.viewManager.CreateContainerView(
            ctx.rootFolder, [vim.DistributedVirtualSwitch], True
        )

        for dvs in container.view:
            if dvs.config.uuid == switch_uuid:
                for host_member in dvs.config.host:
                    if (hasattr(host_member, 'config')
                            and hasattr(host_member.config, 'host') and host_member.config.host):
                        host_id = host_member.config.host
                        host_name = getattr(host_member.config.host, 'name', 'Unknown Host')

                        self._host_name_to_id[host_name] = str(host_id)
                        self._host_id_to_name[str(host_id)] = host_name

                        if host_name not in dvs_pnics_by_host:
                            dvs_pnics_by_host[host_name] = []

                        # we take pnic from backing config
                        if (hasattr(host_member.config, 'backing')
                                and hasattr(host_member.config.backing, 'pnicSpec')):
                            for pnic_spec in host_member.config.backing.pnicSpec:
                                dvs_pnics_by_host[host_name].append(pnic_spec.pnicDevice)

        return dvs_pnics_by_host

    def get_dvs_by_uuid(
            self,
            dvs_uuid: str
    ) -> Tuple[
        DistributedVirtualSwitch,
        DistributedVirtualSwitchConfig
    ]:
        """
        Retrieve a Distributed Virtual Switch (DVS) by its UUID.

        :param dvs_uuid: UUID of the DVS.
        :return: The DVS object if found, otherwise None.
        :raises SwitchNotFound: If no DVS with the given UUID is found.
        """

        if dvs_uuid in self._dvs_uuid_to_dvs:
            cached_dvs = self._dvs_uuid_to_dvs[dvs_uuid]
            return cached_dvs, cached_dvs.config

        content = self.si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.DistributedVirtualSwitch], True)

        for dvs in container.view:
            if hasattr(dvs, 'uuid') and dvs.uuid == dvs_uuid:
                self._dvs_uuid_to_dvs[dvs.uuid] = dvs
                return dvs, dvs.config

        raise SwitchNotFound(dvs_uuid)

    @staticmethod
    def get_dvs_portgroup_by_key(
            dvs,
            portgroup_key: str
    ):
        """
        Retrieve a port group from a Distributed Virtual Switch (DVS) by its key.

        :param dvs: The DVS object.
        :param portgroup_key: Key of the port group.
        :return: The port group object if found, otherwise None.
        """
        for portgroup in dvs.portgroup:
            if portgroup.key == portgroup_key:
                return portgroup
        return None

    def vm_pnic_info(
            self, vm_name: str
    ):
        """
        Retrieve all pnics this vm connected to and associated. The pnics are
        all PNIC connected to a backing DVS switch.

        :param vm_name:
        :return:
        """
        self.connect_to_vcenter()
        content = self.si.RetrieveContent()
        search_index = content.searchIndex
        vm = self._find_by_dns_name(vm_name)

        processed_switches = set()
        all_vm_network_data = {}

        if vm:
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard) and \
                        isinstance(device.backing, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                    if hasattr(device.backing, 'port') and hasattr(device.backing.port, 'switchUuid'):
                        switch_uuid = device.backing.port.switchUuid
                        if switch_uuid not in processed_switches:
                            vm_network_data = self.get_dvs_pnics_by_switch_uuid(switch_uuid)
                            all_vm_network_data[switch_uuid] = vm_network_data
                            processed_switches.add(switch_uuid)

        return all_vm_network_data

    def get_esxi_ip_of_vm(
            self,
            vm_name: str
    ) -> str:
        """
        Method all retrieves the IP address of the ESXi host
        where the specified VM is running.

        :param vm_name: Name of the VM to find.
        :return: IP address of the ESXi host or a message indicating the VM/host was not found.
        """
        try:
            self.connect_to_vcenter()
            content = self.si.RetrieveContent()
            search_index = content.searchIndex
            vm = self._find_by_dns_name(vm_name)
            if vm:
                host = vm.runtime.host
                return host.summary.config.name
            else:
                return "VM not found."
        except Exception as e:
            print(f"An error occurred: {e}")
            return "Error retrieving ESXi host IP."

    def vm_sriov_devices(
            self,
            vm_name
    ):
        """
        Check if a VM is configured with SR-IOV and return details for each SR-IOV adapter.
        This method return list of SRIOV device and following keys.

        [
           {'label': 'SR-IOV network adapter 8',
           'switchUuid': '50 36 28 c6 57 2e 82 06-c0 28 b4 4a aa cd 33 de',
           'portgroupKey': 'dvportgroup-69',
           'numaNode': 0,
           'macAddress': '00:50:56:b6:a0:5f',
           'id': '0000:88:00.0'
           },
        ]

        :param vm_name: String. Name of the VM to check.
        :return: List of dictionaries, each containing details of an SR-IOV network adapter.
        """

        self.connect_to_vcenter()

        sriov_adapters = []

        ctx = self.si.RetrieveContent()
        ctx_search_idx = ctx.searchIndex
        vm = self._find_by_dns_name(vm_name)
        if not vm:
            raise VMNotFoundException(vm_name)

        esxi_host = self.get_esxi_ip_of_vm(vm_name)

        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualSriovEthernetCard):
                pci_id = device.sriovBacking.physicalFunctionBacking.id if (
                    hasattr(device.sriovBacking, 'physicalFunctionBacking')) else None
                if pci_id:
                    pci_info = self.get_pci_device_info(esxi_host, pci_id)
                    adapter_info = {
                        'label': device.deviceInfo.label,
                        'switchUuid': device.backing.port.switchUuid if hasattr(device.backing, 'port') else None,
                        'portgroupKey': device.backing.port.portgroupKey if hasattr(device.backing, 'port') else None,
                        'numaNode': device.numaNode,
                        'vf_mac': device.macAddress,
                        'id': pci_id,
                        'pf_host': esxi_host,
                        'pf_mac': pci_info.get('mac', 'Unknown'),
                        'deviceName': pci_info.get('deviceName', 'Unknown'),
                        'vendorName': pci_info.get('vendorName', 'Unknown'),
                        'pNIC': pci_info.get('pNIC', 'Unknown'),
                    }
                    sriov_adapters.append(adapter_info)

        print("DONE SRIOV")
        return sriov_adapters

    @staticmethod
    def get_vm_hardware(
            vm_config: vim.vm.ConfigInfo
    ) -> VirtualHardwareInfo:
        """
        Retrieves specific hardware information from the VM's configuration.
        :param vm_config: The configuration information of the VM.
        :return: VirtualHardwareInfo
        """
        return vm_config.hardware

    @staticmethod
    def get_vm_hardware_info(
            vm_config: vim.vm.ConfigInfo,
            key: str) -> Optional[Any]:
        """
        Retrieves specific hardware information from the VM's configuration.

        :param vm_config: The configuration information of the VM.
        :param key: The hardware attribute to retrieve (e.g., 'numCPU', 'numCoresPerSocket').
        :return: The value of the specified hardware attribute, or None if not found.
        """
        hardware = vm_config.hardware
        return getattr(hardware, key, None)

    def get_esxi_host_by_identifier(
            self, identifier: str
    ) -> EsxHost:
        """
        Retrieves an ESXi host system object by its IP address, name, UUID, or host system ID.

        :param identifier: IP address, name, UUID, or host system ID of the ESXi host.

        Examples:
        - By IP address: "192.168.1.100"
        - By name: "esxi-hostname.domain.com"
        - By UUID: "4c4c4544-004d-5010-805a-b8c04f325732"
        - By Managed Object ID (moId): "host-12"

        :return: vim.HostSystem object if found, None otherwise.
        """

        # fetch from the cache
        for cache_type in self.esxi_host_cache.values():
            if identifier in cache_type:
                return cache_type[identifier]

        self.connect_to_vcenter()
        content = self.si.RetrieveContent()

        for host in content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True).view:
            host_ip = host.summary.managementServerIp
            host_name = host.name
            host_uuid = host.summary.hardware.uuid
            host_moId = str(host.summary.host)

            # Update cache
            self.esxi_host_cache['ip'][host_ip] = host
            self.esxi_host_cache['name'][host_name] = host
            self.esxi_host_cache['uuid'][host_uuid] = host
            self.esxi_host_cache['moId'][host_moId] = host

            if identifier in [host_ip, host_name, host_uuid, host_moId]:
                return host

        raise EsxHostNotFound(identifier)

    def get_pci_device_info(
            self,
            esxi_host_ip,
            pci_device_id
    ):
        """
        Take ESXi host IP and PCI device and return a pci device
                (vim.host.PciDevice) {
                       dynamicType = <unset>,
                       dynamicProperty = (vmodl.DynamicProperty) [],
                       id = '0000:88:00.0',
                       classId = 512,
                       bus = -120,
                       slot = 0,
                       function = 0,
                       vendorId = -32634,
                       subVendorId = -32634,
                       vendorName = 'Intel(R)',
                       deviceId = 5515,
                       subDeviceId = 9,
                       parentBridge = '0000:85:02.0',
                       deviceName = 'Ethernet Controller XXV710 for 25GbE SFP28'
        }

        :param esxi_host_ip:
        :param pci_device_id:
        :return:
        """
        self.connect_to_vcenter()

        host_system = self.get_esxi_host_by_identifier(esxi_host_ip)

        if not host_system:
            return f"Host {esxi_host_ip} not found."

        pci_info = None
        for pci_device in host_system.hardware.pciDevice:
            if pci_device.id == pci_device_id:
                pci_info = pci_device
                break

        driver = ""
        if pci_info:
            pnic_info = None
            for pnic in host_system.config.network.pnic:
                if hasattr(pnic, 'pci') and pnic.pci == pci_device_id:
                    pnic_info = pnic
                    driver = pnic.driver if hasattr(pnic, 'driver') else "Unknown"
                    break

            if pnic_info:
                return {
                    "mac": pnic_info.mac,
                    "id": pci_info.id,
                    "deviceName": pci_info.deviceName,
                    "vendorName": pci_info.vendorName,
                    "pNIC": pnic_info.device,
                    "driver": driver,
                }
            else:
                return {
                    "mac": "Not found",
                    "id": pci_info.id,
                    "deviceName": pci_info.deviceName,
                    "vendorName": pci_info.vendorName,
                    "pNIC": "Not found",
                    "driver": driver,
                }
        else:
            return f"PCI device {pci_device_id} not found on host {esxi_host_ip}."

    def vm_state(self, vm_name):
        """
        Retrieves the state of VMs that match a given name substring,
        including information about their pNICs, SR-IOV adapters, and specific hardware details.

        :param vm_name: Substring of the VM name to search for.
        :return: A dictionary containing the state information for each matching VM.
        """
        vm_states = {}
        vms, vms_config = self.find_vm_by_name_substring(vm_name)

        for i, vm_name in enumerate(vms):
            vm_config = vms_config[i]
            esxi_host = self.get_esxi_ip_of_vm(vm_name)
            pnic_data = self.vm_pnic_info(vm_name)
            vm_sriov_adapters = self.vm_sriov_devices(vm_name)
            hardware_info = vm_config.hardware

            # Extract the required hardware details
            hardware_details = {
                'numCPU': hardware_info.numCPU,
                'numCoresPerSocket': hardware_info.numCoresPerSocket,
                'autoCoresPerSocket': hardware_info.autoCoresPerSocket,
                'memoryMB': hardware_info.memoryMB,
            }

            vm_states[vm_name] = {
                'esxiHost': esxi_host,
                'pnic_data': pnic_data,
                'sriov_adapters': vm_sriov_adapters,
                'hardware_details': hardware_details,
            }
        return vm_states


def test_vm_pnics():
    vcenter_ip = "vcsa.vf.vmw.run"
    username = "administrator@vsphere.local"
    password = "VMware1!"
    vm_name = "vf-test-np1"

    ssh_executor = None
    vmware_vim_state = VMwareVimState.from_optional_credentials(
        ssh_executor, vcenter_ip=vcenter_ip,
        username=username,
        password=password
    )

    vms, vms_config = vmware_vim_state.find_vm_by_name_substring(vm_name)
    vmware_vim_state.get_vm_hardware(vms_config[0])
    pnic_data = vmware_vim_state.vm_pnic_info(vms[0])

    dvs_uuids = list(pnic_data.keys())

    print(pnic_data.keys())
    print(f"VM name: {vms[0]}")
    print(vmware_vim_state.vm_pnic_info(vms[0]))
    print(vmware_vim_state.get_dvs_by_uuid(dvs_uuids[0]))


def test_vms_backend_host():
    vcenter_ip = "vcsa.vf.vmw.run"
    username = "administrator@vsphere.local"
    password = "VMware1!"
    vm_name = "vf-test-np1"

    ssh_executor = None
    vmware_vim_state = VMwareVimState.from_optional_credentials(
        ssh_executor, vcenter_ip=vcenter_ip,
        username=username,
        password=password
    )

    vms, vms_config = vmware_vim_state.find_vm_by_name_substring(vm_name)
    esxi_host = vmware_vim_state.get_esxi_ip_of_vm(vms[0])
    print(esxi_host)

    esxi_host = vmware_vim_state.get_esxi_ip_of_vm(vms[1])
    print(esxi_host)


def vm_config_to_dict(vm_config):
    """
    Convert a vim.vm.ConfigInfo object to a dictionary.
    Adjust attributes as needed based on what you want to include.
    """
    config_dict = {
        "name": vm_config.name,
        "guestFullName": vm_config.guestFullName,
        # Add more attributes here
    }
    return config_dict


def test_vms_sriov_nics():
    vcenter_ip = "vcsa.vf.vmw.run"
    username = "administrator@vsphere.local"
    password = "VMware1!"
    vm_name = "vf-test-np1"

    ssh_executor = None
    vmware_vim_state = VMwareVimState.from_optional_credentials(
        ssh_executor, vcenter_ip=vcenter_ip,
        username=username,
        password=password
    )

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


def test_vms_state():
    vcenter_ip = "vcsa.vf.vmw.run"
    username = "administrator@vsphere.local"
    password = "VMware1!"
    vm_sub_name = "vf-test-np1"

    ssh_executor = None
    vmware_vim_state = VMwareVimState.from_optional_credentials(
        ssh_executor, vcenter_ip=vcenter_ip,
        username=username,
        password=password
    )

    vms_state = vmware_vim_state.vm_state(vm_sub_name)
    print(json.dumps(vms_state, indent=4))


test_vms_state()
