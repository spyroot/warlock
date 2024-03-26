"""
VMwareVimState, is designed to encapsulate the state of virtual machines (VMs) within a
VMware vSphere environment, providing an abstraction layer for managing and retrieving detailed
information about VMs. The state information includes details such as the ESXi host on which a
VM is running, NUMA node allocation, various configuration parameters, and network attachment
details including SR-IOV Virtual

Functions (VFs), Physical Functions (PFs), network interface cards (NICs),
 and their respective  drivers and firmware versions.


Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import json
import logging
import os
from collections import defaultdict, namedtuple
from enum import Enum
from typing import (
    Dict,
    Optional,
    List,
    Tuple,
    Any, Union
)

from pyVim.connect import (
    SmartConnect,
    Disconnect
)

from contextlib import contextmanager
from pyVmomi import vim
import atexit
import ssl
import time
from pyVmomi import vim, vmodl

from warlock.operators.ssh_operator import SSHOperator

VMConfigInfo = vim.vm.ConfigInfo
VirtualHardwareInfo = vim.vm.VirtualHardware
VMwareDistributedVirtualSwitch = vim.dvs.VmwareDistributedVirtualSwitch
VMwareDistributedVirtualSwitchConfig = vim.dvs.VmwareDistributedVirtualSwitch.ConfigInfo
VMwareDvsBackingInfo = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo

EsxHost = vim.HostSystem
VmwareContainerView = vim.view.ContainerView
VMwarePciDevice = vim.host.PciDevice
VMwareVirtualMachine = vim.VirtualMachine
VmwareVirtualNumaInfo = vim.vm.VirtualNumaInfo
VmwareAffinityInfo = vim.vm.AffinityInfo
VmwareVgpuProfileInfo = vim.vm.VgpuProfileInfo
VmwareSriovInfo = vim.vm.SriovInfo
VmwareVcpuConfig = vim.vm.VcpuConfig
VMwareInvalidLogin = vim.fault.InvalidLogin
VMwareClusterComputeResource = vim.ClusterComputeResource
VMwareResourcePool = vim.ResourcePool
VMwareManagedEntity = vim.ManagedEntity
VMwareDatastore = vim.Datastore
VMwareContex = vim.view.ContainerView
VMwareFolder = vim.Folder
VmUuid = namedtuple('VmUuid', ['uuid', 'name', 'moid'])
VMwareHost = namedtuple('VMwareHost', ['uuid', 'host', 'moid'])


class PciDeviceClass(Enum):
    """
    """
    UNDEFINED = 0x00
    MASS_STORAGE_CONTROLLER = 0x01
    NETWORK_CONTROLLER = 0x02
    DISPLAY_CONTROLLER = 0x03


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


class DatastoreNotFoundException(Exception):
    """Exception to be raised when datastore cannot be found."""

    def __init__(self, datastore_name):
        message = f"Datastore '{datastore_name}' not found."
        super().__init__(message)


class ClusterNotFoundException(Exception):
    """Exception to be raised when cluster cannot be found."""

    def __init__(self, cluster_name):
        message = f"Cluster '{cluster_name}' not found."
        super().__init__(message)


class VMNotFoundException(Exception):
    """Exception to be raised when a VM cannot be found."""

    def __init__(self, vm_name):
        message = f"VM '{vm_name}' not found."
        super().__init__(message)


class UnknownEntity(Exception):
    """Exception to be raised when unknown managed entity requested."""

    def __init__(self, entity_name):
        message = f"Unknown '{entity_name}' entity."
        super().__init__(message)


class ResourcePoolNotFoundException(Exception):
    """Exception to be raised when a Resource Pool cannot be found."""

    def __init__(self, r_name):
        message = f"Resource pool '{r_name}' not found."
        super().__init__(message)


class PciDeviceNotFound(Exception):
    """Exception to be raised when a PCI device cannot be found."""

    def __init__(self, pci_dev_id):
        message = f"pci device '{pci_dev_id}' not found."
        super().__init__(message)


class VAppNotFoundException(Exception):
    """Exception to be raised when a Resource Pool cannot be found."""

    def __init__(self, vpp_name):
        message = f"VAPP '{vpp_name}' not found."
        super().__init__(message)


class FolderNotFoundException(Exception):
    """Exception to be raised when a Folder cannot be found."""

    def __init__(self, folder_name):
        message = f"Folder '{folder_name}' not found."
        super().__init__(message)


class VMwareVimStateReader:
    def __init__(
            self,
            iaas_spec: Optional[Dict] = None,
            vcenter_ip: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None,
            logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize VMwareVimStateReader with credentials and SSH executor.

        :param iaas_spec: Optional dictionary containing environment specifications.
        :param vcenter_ip: Optional vCenter IP, preferred over test_environment_spec if provided.
        :param username: Optional vCenter username, preferred over test_environment_spec if provided.
        :param password: Optional vCenter password, preferred over test_environment_spec if provided.
        """
        self.iaas_spec = iaas_spec
        self.logger = logger if logger else logging.getLogger(__name__)

        # Default values from test_environment_spec if it exists
        # and specific values are not provided.
        default_vcenter_ip = self.iaas_spec.get('iaas', {}).get(
            'vcenter_ip', '') if self.iaas_spec else ''
        default_username = self.iaas_spec.get('iaas', {}).get(
            'username', '') if self.iaas_spec else ''
        default_password = self.iaas_spec.get('iaas', {}).get(
            'password', '') if self.iaas_spec else ''

        # Use provided values or defaults from test_environment_spec
        self.vcenter_ip = vcenter_ip if vcenter_ip is not None else default_vcenter_ip
        self.username = username if username is not None else default_username
        self.password = password if password is not None else default_password

        # cache mapping host id to hostname
        self._sriov_device_cache = {}
        self._none_sriov_device_cache = {}

        self._host_name_to_id = {}
        self._host_id_to_name = {}
        self._esxi_host = {}
        self._dvs_uuid_to_dvs = {}

        # cache for VM searches
        #  name cache store key to name mapping,  including substring
        self._vm_name_cache = {}
        # store vm name to vm object
        self._vm_cache = {}

        # cache for esxi lookup by
        self.esxi_host_cache = {
            'ip': {},
            'name': {},
            'uuid': {},
            'moId': {}
        }

        # pci device cache
        self._pci_dev_cache = {}

        # esxi host pnic, key is esxi identifier
        self._host_device_pnic = {}

        # vc
        self.si = None

        #
        self._debug = True

        self._all_vms_cache = None
        self._cache_timestamp = None
        self._cache_timeout = 300
        self._obj_cache = {}
        self._dvs_cache = {}

    def connect_to_vcenter(self):
        """Connect to the vCenter server and store the connection instance."""
        if not self.si:
            context = ssl._create_unverified_context()
            try:
                self.si = SmartConnect(
                    host=self.vcenter_ip,
                    user=self.username,
                    pwd=self.password,
                    sslContext=context,
                    disableSslCertValidation=True
                )
            except VMwareInvalidLogin as e:
                print(f"Failed to login to {self.vcenter_ip} vCenter server. Please check your credentials.")
                raise e

            atexit.register(Disconnect, self.si)

    @classmethod
    def from_optional_credentials(
            cls,
            vcenter_ip: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """
        Constructor that creates an instance using optional credentials.

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

    @contextmanager
    def _dvs_container_view(
            self
    ) -> VmwareContainerView:
        """Return dvs container view for DVS
        :return:
        """
        self.connect_to_vcenter()
        ctx = self.si.RetrieveContent()
        container = ctx.viewManager.CreateContainerView(
            ctx.rootFolder, [vim.DistributedVirtualSwitch], True)
        try:
            yield container
        finally:
            container.Destroy()

    @contextmanager
    def _container_view(
            self,
            obj_type: [vim.ManagedEntity]
    ) -> VmwareContainerView:
        """Return  container view.
        :param obj_type: VMware API object
        :return: container view
        """
        # if isinstance(obj_type, list):
        #     cache_key = "_".join([ot.__name__ for ot in obj_type])
        # else:
        #     cache_key = obj_type.__name__
        #
        # if cache_key in self._obj_cache:
        #     yield self._obj_cache[cache_key]
        #     return

        self.connect_to_vcenter()
        content = self.si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, obj_type, True)
        try:
            # self._obj_cache[cache_key] = container
            yield container

        finally:
            container.Destroy()

    def read_vm_uuid(
            self,
            vm_name: str
    ) -> Union[str, None]:
        """Return VM UUID for given VM name, where name is name in VC inventory.
        :param vm_name: virtual machine name
        :return: UUID for given VM or None if VM does not exist
        """
        _vm = self._find_by_dns_or_uuid(vm_name)
        if (_vm is not None and hasattr(_vm, 'config')
                and hasattr(_vm.config, 'uuid')):
            return _vm.config.uuid
        else:
            return None

    def read_vm_numa_info(
            self,
            vm_name: str
    ) -> VmwareVirtualNumaInfo | None:
        """Return VM UUID for given VM name, where name is name in VC inventory.
        :param vm_name: virtual machine name
        :return: VM Numa information for given VM or None if VM does not exist
        """
        _vm = self._find_by_dns_or_uuid(vm_name)
        if (_vm is not None and hasattr(_vm, 'config')
                and hasattr(_vm.config, 'numaInfo')):
            return _vm.config.numaInfo
        else:
            return None

    def read_vm_extra_config(
            self,
            vm_name: str
    ):
        """Return VM UUID for given VM name, where name is name in VC inventory.

        :param vm_name:
        :return:
        """
        _vm = self._find_by_dns_or_uuid(vm_name)
        if (_vm is not None and hasattr(_vm, 'config')
                and hasattr(_vm.config, 'extraConfig')):
            return _vm.config.extraConfig
        else:
            return None

    def _find_by_uuid_name(
            self,
            uuid: str
    ) -> VMwareVirtualMachine:
        """
        :param uuid: is VM UUID, 4236d5ce-6fe8-725c-2429-954c402d660c
        :return:
        """
        if uuid in self._vm_cache:
            return self._vm_cache[uuid]

        start_time = time.time()
        content = self.si.RetrieveContent()
        vm = content.searchIndex.FindByUuid(None, uuid, True, False)
        if vm:
            self._vm_cache[uuid] = vm
            self._vm_cache[vm.name] = vm

        self.logger.debug(f"content.searchIndex.FindByUuid took {time.time() - start_time:.2f} seconds")
        return vm

    def _find_by_dns_or_uuid(
            self,
            vm_name: str
    ) -> VMwareVirtualMachine:
        """
        Retrieves a virtual machine by its DNS name,

        if vm name cached before in named cache, it also stores uuid hence
        we find by UUID ( faster path )

        :param vm_name: The DNS name of the VM.
        :return: The VM object if found, None otherwise.
        """

        vm_obj = None
        start_time = time.time()
        if vm_name in self._vm_cache:
            return self._vm_cache[vm_name]

        if vm_name in self._vm_name_cache:
            vm_tuple = self._vm_name_cache[vm_name][0]
            vm_obj = self._find_by_uuid_name(vm_tuple.uuid)
        else:
            self.connect_to_vcenter()
            content = self.si.RetrieveContent()
            search_index = content.searchIndex
            vm_obj = search_index.FindByDnsName(
                dnsName=vm_name, vmSearch=True
            )

        if vm_obj is not None:
            self._vm_cache[vm_name] = vm_obj

        self.logger.debug(f"_find_by_dns_name for {vm_name} took {time.time() - start_time:.2f} seconds")
        return vm_obj

    def _fetch_all_vms(self):
        """
        Fetches all virtual machines from vCenter and returns them.

        :return: A list of all virtual machines in vCenter.
        """
        start_time = time.time()
        self.connect_to_vcenter()
        content = self.si.RetrieveContent()
        ctx_view = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True)
        try:
            vms = ctx_view.view
            self.logger.debug(f"_fetch_all_vms took {time.time() - start_time:.2f} seconds")
            return vms
        finally:
            ctx_view.Destroy()

    def get_all_vms(self):
        """
        :return:
        """
        if self._all_vms_cache is None or (time.time() - self._cache_timestamp) > self._cache_timeout:
            self._all_vms_cache = self._fetch_all_vms()
            self._cache_timestamp = time.time()

        return self._all_vms_cache

    def find_vm_by_name_substring2(
            self,
            name_substring: str
    ) -> Tuple[
        List[str],
        List[VMConfigInfo]
    ]:
        """
        Find a VM by name substring in the vCenter server.

        :param name_substring: Substring of the VM name to search for.
        :return: Full name of the VM that matches the substring.
        :raises VMwareVimStateException: If the VM is not found.
        """
        start_time = time.time()
        if name_substring in self._vm_name_cache:
            return self._vm_name_cache[name_substring]

        vms = self.get_all_vms()
        found_vms_with_config = [(vm.name, vm.config) for vm in vms if name_substring in vm.name]
        found_vms, found_vm_config = zip(*found_vms_with_config) if found_vms_with_config else ([], [])
        found_vms = list(found_vms)
        found_vm_config = list(found_vm_config)

        self._vm_name_cache[name_substring] = (found_vms, found_vm_config)

        # add all found VM
        for vm_name in found_vms:
            self._vm_name_cache[vm_name] = (found_vms, found_vm_config)

        self.logger.debug(
            f"find_vm_by_name_substring for {name_substring} , took {time.time() - start_time:.2f} seconds")
        return found_vms, found_vm_config

    def read_all_dvs_specs(
            self
    ) -> Dict[
        str, vim.DistributedVirtualSwitch
    ]:
        """
        Retrieve all Distributed Virtual Switch (DVS).
        :return: a dictionary of all dvs where key is DVS uuid string.
        """
        if self._dvs_uuid_to_dvs and len(self._dvs_uuid_to_dvs) > 0:
            return self._dvs_uuid_to_dvs

        with self._dvs_container_view() as ctx:
            for dvs in ctx.view:
                self._dvs_uuid_to_dvs[dvs.uuid] = dvs

        return self._dvs_uuid_to_dvs

    def read_dvs_pnics_by_switch_uuid(
            self,
            switch_uuid: str
    ) -> Dict[
        str,
        List[str]
    ]:
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
        :raises SwitchNotFound: If no DVS with the given UUID is found.
        """
        start_time = time.time()
        if switch_uuid in self._dvs_cache:
            self.logger.debug(
                f"read_dvs_pnics_by_switch_uuid for {switch_uuid}, "
                f"cache took {time.time() - start_time:.2f} seconds")
            return self._dvs_cache[switch_uuid]

        dvs_pnics_by_host = {}
        start_time = time.time()
        _dvs = self.get_dvs_by_uuid(switch_uuid)
        if _dvs.config.host is None:
            raise ValueError("DVS has no host associated with.")

        _dvs_hosts = _dvs.config.host
        for host_member in _dvs_hosts:
            if (hasattr(host_member, 'config')
                    and hasattr(host_member.config, 'host') and host_member.config.host):
                _dvs_host_member = getattr(host_member.config.host, 'name', 'Unknown Host')
                if _dvs_host_member not in dvs_pnics_by_host:
                    dvs_pnics_by_host[_dvs_host_member] = []

                # we take pnic from backing config
                if (hasattr(host_member.config, 'backing')
                        and hasattr(host_member.config.backing, 'pnicSpec')):

                    dvs_pnics_by_host[_dvs_host_member] = [
                        pnic_spec.pnicDevice for pnic_spec in host_member.config.backing.pnicSpec
                    ]

        self._dvs_cache[switch_uuid] = dvs_pnics_by_host
        self.logger.debug(
            f"read_dvs_pnics_by_switch_uuid - {switch_uuid} "
            f"took {time.time() - start_time:.2f} seconds")

        return dvs_pnics_by_host

    def get_dvs_by_uuid(
            self,
            dvs_uuid: str
    ) -> VMwareDistributedVirtualSwitch:
        """
        Retrieve a Distributed Virtual Switch (DVS) by its UUID.

        :param dvs_uuid: UUID of the DVS.
        :return: The DVS object if found, otherwise None.
        :raises SwitchNotFound: If no DVS with the given UUID is found.
        """
        start_time = time.time()
        if dvs_uuid in self._dvs_uuid_to_dvs:
            return self._dvs_uuid_to_dvs[dvs_uuid]

        self.connect_to_vcenter()
        content = self.si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.DistributedVirtualSwitch],
            True
        )

        try:
            obj = None
            for dvs in container.view:
                if hasattr(dvs, 'uuid'):
                    self._dvs_uuid_to_dvs[dvs.uuid] = dvs
                    if dvs.uuid == dvs_uuid:
                        obj = dvs

            self.logger.debug(
                f"get_dvs_by_uuid, took {time.time() - start_time:.2f} seconds")

            if obj is None:
                raise SwitchNotFound(dvs_uuid)
            else:
                return obj

        finally:
            container.Destroy()

    @staticmethod
    def read_dvs_portgroup_by_key(
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

    def read_vm_vnic_info(
            self,
            vm_name: str
    ) -> List[Dict[str, str]]:
        """
        Retrieve information about all virtual NICs (vNICs)
        associated with a given virtual machine.

        :param vm_name: The name of the virtual machine.
        :return: A list of dictionaries, where each dictionary contains details about a vNIC.
        """
        self.connect_to_vcenter()

        vm = self._find_by_dns_or_uuid(vm_name)
        if not vm:
            raise VMNotFoundException("VM '{}' not found".format(vm_name))

        vnic_info = []

        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                is_sriov = False
                if hasattr(device, 'sriovBacking'):
                    is_sriov = True
                    sriov_backing = device.sriovBacking
                    pf_info = sriov_backing.physicalFunctionBacking
                    vf_info = sriov_backing.virtualFunctionBacking

                vnic_detail = {
                    'label': device.deviceInfo.label,
                    'summary': device.deviceInfo.summary,
                    'macAddress': device.macAddress,
                    'key': device.key,
                    'backing': type(device.backing).__name__,
                    'network': None,
                    'is_sriov': is_sriov
                }

                if hasattr(device.backing, 'network'):
                    network_ref = device.backing.network
                    if isinstance(network_ref, vim.Network):
                        vnic_detail['network'] = network_ref.name
                    elif isinstance(network_ref, vim.dvs.DistributedVirtualPortgroup):
                        vnic_detail['network'] = network_ref.name
                    elif isinstance(network_ref, vim.OpaqueNetwork):
                        vnic_detail['network'] = network_ref.summary.name

                vnic_info.append(vnic_detail)

        return vnic_info

    def read_vm_pnic_info(
            self,
            vm_name: str
    ):
        """
        Retrieve all pnics this vm connected to and associated. The pnics are
        all PNIC connected to a backing DVS switch.

        :param vm_name: virtual machine name
        :raises VMNotFoundException: if the virtual machine not found
        :return:
        """
        start_time = time.time()
        self.connect_to_vcenter()
        vm = self._find_by_dns_or_uuid(vm_name)
        if not vm:
            raise VMNotFoundException("VM '{}' not found".format(vm_name))

        processed_switches = set()
        all_vm_network_data = {}

        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard) and \
                    isinstance(device.backing, VMwareDvsBackingInfo):
                if hasattr(device.backing, 'port') and hasattr(device.backing.port, 'switchUuid'):
                    switch_uuid = device.backing.port.switchUuid
                    if switch_uuid not in processed_switches:
                        vm_network_data = self.read_dvs_pnics_by_switch_uuid(switch_uuid)
                        all_vm_network_data[switch_uuid] = vm_network_data
                        processed_switches.add(switch_uuid)

        self.logger.debug(
            f"read_vm_pnic_info, took {time.time() - start_time:.2f} seconds")

        return all_vm_network_data

    def _add_to_host_cache(
            self,
            obj: vim.HostSystem,
            esxi_host_id: VMwareHost):

        """
        We cache 3 primary query.

        - moid to HostSystem
        - host uuid to HostSystem
        - host (ip address or FQDN) to HostSystem.

        :param obj:
        :return:
        """
        self.esxi_host_cache[esxi_host_id.uuid] = obj
        self.esxi_host_cache[esxi_host_id.host] = obj
        self.esxi_host_cache[esxi_host_id.moid] = obj

    def get_esxi_ip_of_vm(
            self,
            vm_name: str
    ) -> VMwareHost:
        """
        Method return an esxi host that runs a particular VM.
        :param vm_name: Name of the VM used to search esxi hosts.
        :return: IP address of the ESXi host or a message indicating the VM/host was not found.
        """
        if vm_name in self.esxi_host_cache:
            return self.esxi_host_cache[vm_name]

        try:
            self.connect_to_vcenter()
            vm = self._find_by_dns_or_uuid(vm_name)
            if vm:
                if vm.runtime is not None and vm.runtime.host is not None:
                    host = vm.runtime.host
                    host_info = VMwareHost(uuid=host.summary.hardware.uuid,
                                           host=host.summary.config.name,
                                           moid=host.summary.host)
                    self._add_to_host_cache(host, host_info)
                    self.esxi_host_cache[vm_name] = host_info
                    return host_info
            else:
                return "VM not found."

        except Exception as e:
            print(f"An error occurred: {e}")
            return "Error retrieving ESXi host IP."

    @staticmethod
    def decode_pci_address(pci_slot_number):
        """Decode pci device address. ( Vanilla method VMware use different semantics)
        Best way to use slot id and resolve in VM slot id.
        :param pci_slot_number:
        :return:
        """
        bus_number = pci_slot_number >> 8
        device_number = (pci_slot_number >> 3) & 0x1F
        function_number = pci_slot_number & 0x07
        return f"{bus_number:02x}:{device_number:02x}.{function_number}"

    def vm_adapters_and_sriov_devices(
            self,
            vm_name
    ):
        """
        Check if a VM is configured with SR-IOV and return details for each SR-IOV adapter.
        This method return list of SRIOV device and following keys.

        [
           {
           'label': 'SR-IOV network adapter 8',
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
        cache_key = f"vm_sriov_devices_{vm_name}"
        if cache_key in self._sriov_device_cache:
            return self._sriov_device_cache[cache_key]

        self.connect_to_vcenter()

        sriov_adapters = []
        none_sriov_pci_devices = []
        vm = self._find_by_dns_or_uuid(vm_name)
        if not vm:
            raise VMNotFoundException(vm_name)

        _esxi_host = self.get_esxi_ip_of_vm(vm_name)

        start_time = time.time()
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualSriovEthernetCard):
                pci_id = device.sriovBacking.physicalFunctionBacking.id if (
                    hasattr(device.sriovBacking, 'physicalFunctionBacking')) else None
                if pci_id:
                    pci_info = self.read_pci_net_device_info(_esxi_host.host, pci_id)
                    adapter_info = {
                        'label': device.deviceInfo.label,
                        'switchUuid': device.backing.port.switchUuid if hasattr(device.backing, 'port') else None,
                        'portgroupKey': device.backing.port.portgroupKey if hasattr(device.backing, 'port') else None,
                        'device_id': device.key,
                        'numaNode': device.numaNode,
                        'vf_mac': device.macAddress,
                        'id': pci_id,
                        'pf_host': _esxi_host.host,
                        'pf_host_uuid': _esxi_host.uuid,
                        'pf_mac': pci_info.get('mac', 'Unknown'),
                        'deviceName': pci_info.get('deviceName', 'Unknown'),
                        'vendorName': pci_info.get('vendorName', 'Unknown'),
                        'pNIC': pci_info.get('pNIC', 'Unknown'),
                        "pci_slot_number": device.slotInfo.pciSlotNumber if device.slotInfo is not None else None,
                        "type": "sriov",
                        "connected": device.connectable.connected if hasattr(device.connectable,
                                                                             'connected') else False,
                    }
                    sriov_adapters.append(adapter_info)
            else:
                if isinstance(device, vim.vm.device.VirtualVmxnet3):
                    none_sriov_pci_devices.append({
                        'label': device.deviceInfo.label,
                        'switchUuid': device.backing.port.switchUuid if hasattr(device.backing, 'port') else None,
                        'portgroupKey': device.backing.port.portgroupKey if hasattr(device.backing, 'port') else None,
                        'numaNode': device.numaNode,
                        'device_id': device.key,
                        'device_mac': device.macAddress,
                        "pci_slot_number": device.slotInfo.pciSlotNumber if device.slotInfo is not None else None,
                        "type": "vmxnet3",
                        "connected": device.connectable.connected if hasattr(device.connectable,
                                                                             'connected') else False,
                    })

        self.logger.debug(
            f"vm_sriov_devices, took {time.time() - start_time:.2f} seconds")

        result_tuple = (sriov_adapters, none_sriov_pci_devices)
        self._sriov_device_cache[cache_key] = result_tuple
        return result_tuple

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
            key: str
    ) -> Optional[Any]:
        """
        Retrieves specific hardware information from the VM's configuration.

        :param vm_config: The configuration information of the VM.
        :param key: The hardware attribute to retrieve (e.g., 'numCPU', 'numCoresPerSocket').
        :return: The value of the specified hardware attribute, or None if not found.
        """
        hardware = vm_config.hardware
        return getattr(hardware, key, None)

    def read_esxi_hosts(
            self
    ) -> Dict[str, vim.HostSystem]:
        """
        Retrieves all ESXi host information.
        :return: Dict of vim.HostSystem object.
        """

        start_time = time.time()
        if self.esxi_host_cache['moId']:
            return self.esxi_host_cache['moId']

        self.connect_to_vcenter()
        content = self.si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem],
            True
        )

        try:
            for host in container.view:
                self.esxi_host_cache['name'][host.name] = host
                self.esxi_host_cache['uuid'][host.summary.hardware.uuid] = host
                self.esxi_host_cache['moId'][str(host.summary.host)] = host

        finally:
            container.Destroy()

        self.logger.debug(
            f"read_esxi_hosts, took {time.time() - start_time:.2f} seconds")

        return self.esxi_host_cache['moId']

    def read_esxi_host(
            self,
            identifier: str
    ) -> vim.HostSystem:
        """
        Retrieves an ESXi host system object by its IP address,
        name, UUID, or host system ID.

        :param identifier: IP address, name, UUID, or
        host system ID of the ESXi host.

        :Examples:
        - By IP address: "192.168.1.100"
        - By name: "esxi-hostname.domain.com"
        - By UUID: "4c4c4544-004d-5010-805a-b8c04f325732"
        - By Managed Object ID (moId): "host-12"

        :return: vim.HostSystem object if found, None otherwise.
        """
        start_time = time.time()
        # fetch from the cache
        if identifier in self.esxi_host_cache:
            return self.esxi_host_cache[identifier]

        self.connect_to_vcenter()
        content = self.si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem],
            True
        )

        try:
            for host in container.view:
                host_name = host.name
                host_uuid = host.summary.hardware.uuid
                host_moid = str(host.summary.host)

                host_info = VMwareHost(uuid=host_uuid,
                                       host=host_name,
                                       moid=str(host.summary.host))
                self._add_to_host_cache(host, host_info)
                if identifier in [host_name, host_uuid, host_moid]:
                    self.logger.debug(
                        f"read_esxi_host for {identifier}, took {time.time() - start_time:.2f} seconds")
                    return host
        finally:
            container.Destroy()

        raise EsxHostNotFound(f"ESXi host with identifier {identifier} not found.")

    def read_esxi_mgmt_address(
            self
    ) -> Dict[str, List[str]]:
        """ Read all esxi host mgmt address.
        .. code-block:: python
          vim_state = warlock.VMwareVimState.from_optional_credentials(
                    ssh_executor=None,
                    vcenter_ip=os.getenv('VCENTER_IP', 'default_vcenter_ip'),
                    username=os.getenv('VCENTER_USERNAME', 'administrator@vsphere.local'),
                    password=os.getenv('VCENTER_PASSWORD', 'default_password')
                )
            esxi_mgmt_address = vim_state.read_esxi_mgmt_address()
            print(esxi_mgmt_address)
            {
                "'vim.HostSystem:host-12'": ['10.252.80.79', '198.19.56.239'],
                "'vim.HostSystem:host-15'": ['10.252.80.107', '198.19.56.200']
             }
             ..
        :return:
        """
        start_time = time.time()
        esxi_hosts = self.read_esxi_hosts()
        host_address = {}
        for h in esxi_hosts:
            ip_address = [v.spec.ip.ipAddress for
                          v in esxi_hosts[h].config.network.vnic]
            host_address[h] = ip_address

        self.logger.debug(
            f"read_esxi_mgmt_address, took {time.time() - start_time:.2f} seconds")
        return host_address

    def read_pci_devices(
            self,
            esxi_host_identifier: Optional[str] = None,
            filter_class: Optional[PciDeviceClass] = None,
    ) -> Dict[str, VMwarePciDevice]:
        """Read  all PCI device info from some ESXi if esxi_host_identifier arg supplied
          where  we find based on identifier. i.e. esxi managed object id, uuid.
          if identifies is none then method will read PCI devices for all ESXi hosts.

         filter applied in case client need to filter particular PCI device id
         class.

        :param esxi_host_identifier: Optional; ESXi managed object id, uuid. If None, read from all hosts.
        :param filter_class: Optional; A PCI device class.
        :return:  a dictionary of PCI device where a key is a PCI device id
        :raise EsxHostNotFound: if ESXi host with identifier not found
        """

        start_time = time.time()
        if esxi_host_identifier and esxi_host_identifier in self._pci_dev_cache:
            return self._pci_dev_cache[esxi_host_identifier]

        self.connect_to_vcenter()
        if esxi_host_identifier:
            host_system = self.read_esxi_host(esxi_host_identifier)
            if not host_system:
                raise EsxHostNotFound(f"ESXi host {esxi_host_identifier} not found")
            hosts = {esxi_host_identifier: host_system}
        else:
            hosts = self.read_esxi_hosts()

        for k in hosts:
            host_system = hosts[str(k)]
            self._pci_dev_cache[k] = {}
            for pci_device in host_system.hardware.pciDevice:
                if filter_class is None or (pci_device.classId >> 8) == filter_class.value:
                    self._pci_dev_cache[str(k)][pci_device.id] = pci_device

        self.logger.debug(f"read_pci_devices for {esxi_host_identifier}, took {time.time() - start_time:.2f} seconds")
        return self._pci_dev_cache

    def find_pci_device(
            self,
            esxi_host_identifier: str,
            pci_device_id: str
    ) -> Union[None, VMwarePciDevice]:
        """Find a PCI device by PCI identifier. If no PCI device is found
        return none and if esxi host found will raise EsxHostNotFound.

        All PCI device added to internal cache, and follow-up request
        to a same device return from a cache.
        :return:VMwarePciDevice
        :raises EsxHostNotFound if ESX host not found
        """
        start_time = time.time()
        if (esxi_host_identifier in self._pci_dev_cache
                and pci_device_id in self._pci_dev_cache[esxi_host_identifier]):
            return self._pci_dev_cache[esxi_host_identifier][pci_device_id]

        self.connect_to_vcenter()
        host_system = self.read_esxi_host(esxi_host_identifier)
        if not host_system:
            raise EsxHostNotFound(
                f"ESXi host {esxi_host_identifier} not found")

        for pci_device in host_system.hardware.pciDevice:
            if pci_device.id == pci_device_id:
                if esxi_host_identifier not in self._pci_dev_cache:
                    self._pci_dev_cache[esxi_host_identifier] = {}
                self._pci_dev_cache[esxi_host_identifier][pci_device_id] = pci_device
                self.logger.debug(
                    f"find_pci_device for {esxi_host_identifier} took {time.time() - start_time:.2f} seconds")
                return pci_device

        return None

    def read_esxi_host_pnic(
            self,
            esxi_identifier: str
    ) -> Dict[str, Dict[str, str]]:
        """Reads esxi host pnic information.

        The dictionary returned contains the following information:

        :Examples:

        "vmnic0": {
                "pci": "0000:1a:00.0",
                "mac": "e4:43:4b:62:e9:fc",
                "driver": "ixgben",
                "driver_version": "1.15.1.0",
                "driver_firmware": "3.30 0x800014a5, 20.5.13"
        }

        :param esxi_identifier: esxi host identifier. (UUID, name etc.)
        :return: dictionary where key is esxi host identified
        :raises EsxHostNotFound: If the ESXi host is not found.
        """
        if esxi_identifier in self._host_device_pnic:
            return self._host_device_pnic[esxi_identifier]
        else:
            self._host_device_pnic[esxi_identifier] = {}

        self.connect_to_vcenter()
        host_system = self.read_esxi_host(esxi_identifier)

        for pnic in host_system.config.network.pnic:
            self._host_device_pnic[esxi_identifier][pnic.device] = {
                "pci": pnic.pci,
                'mac': pnic.mac,
                "driver": pnic.driver,
                "driver_version": pnic.driverVersion,
                "driver_firmware": pnic.firmwareVersion,
                "speed": pnic.linkSpeed.speedMb if pnic.linkSpeed else None,
                "is_connected": True if pnic.linkSpeed else False
            }

        return self._host_device_pnic[esxi_identifier]

    def find_esxi_host_pnic(
            self,
            esxi_host_identified: str,
            pci_device: str
    ) -> Union[
        Tuple[None, None],
        Tuple[str, Dict[str, str]]
    ]:
        """Method search for a pnic device based on pci device id.
        Example of return data

        :Examples:

        "vmnic0",
        {
            "pci": "0000:1a:00.0",
            "mac": "e4:43:4b:62:e9:fc",
            "driver": "ixgben",
            "driver_version": "1.15.1.0",
            "driver_firmware": "3.30 0x800014a5, 20.5.13",
            "speed": 10000,
            "is_connected": true
        }

        :param esxi_host_identified: an esxi host identifier.
        :param pci_device:  a pci device id
        :return: dictionary where key is pnic name
        """
        if esxi_host_identified not in self._host_device_pnic:
            host_pnic_dict = self.read_esxi_host_pnic(esxi_host_identified)
        else:
            host_pnic_dict = self._host_device_pnic[esxi_host_identified]

        for pnic in host_pnic_dict:
            pnic_dict = host_pnic_dict[pnic]
            if 'pci' in pnic_dict and pnic_dict['pci'] == pci_device:
                return pnic, pnic_dict

        return None, None

    def read_pci_net_device_info(
            self,
            esxi_host_identified: str,
            pci_device_id: str
    ) -> Dict:
        """
        Retrieve detailed information for a specified PCI Network device on a given ESXi host.
        This method returns a dictionary containing the following keys and their associated values:

        - "deviceName": The name of the device (e.g., "Ethernet Controller X550").
        - "driver": The name of the driver (e.g., "ixgben").
        - "driver_firmware": Firmware version of the driver (e.g., "3.30 0x800014a5, 20.5.13").
        - "driver_version": Version of the driver (e.g., "1.15.1.0").
        - "id": PCI device ID (e.g., "0000:1a:00.0").
        - "is_connected": Boolean indicating if the device is connected (true or false).
        - "mac": MAC address of the device (e.g., "e4:43:4b:62:e9:fc").
        - "pNIC": Physical NIC associated with the PCI device (e.g., "vmnic0").
        - "pnic_vendor": Vendor information for the pNIC (e.g., "0000:1a:00.0 - Intel(R) Ethernet Controller X550").
        - "speed": Speed of the connection in Mbps (e.g., 10000).
        - "vendorName": Name of the device vendor (e.g., "Intel(R)").

        :param esxi_host_identified: string an esxi host IP or UUID or moid
        :param pci_device_id: pci device.
        :raise EsxHostNotFound: if host not found.
        :raise PciDeviceNotFound: if pci device not found
        :return: Dictionary
        """
        if not isinstance(esxi_host_identified, str):
            raise TypeError(f"esxi_host_identified must be a string, got {type(esxi_host_identified)}")

        if not isinstance(pci_device_id, str):
            raise TypeError(f"pci_device_id must be a string, got {type(pci_device_id)}")

        pci_info = self.find_pci_device(
            esxi_host_identified, pci_device_id
        )

        if pci_info is None:
            raise PciDeviceNotFound(pci_device_id)

        pci_device_vendor_and_dev = f"{pci_info.id} - {pci_info.vendorName} {pci_info.deviceName}"
        pnic_name, pnic_info_dict = self.find_esxi_host_pnic(esxi_host_identified, pci_device_id)
        pnic_info_dict["pnic_vendor"] = pci_device_vendor_and_dev

        pci_pnic_info = {
            "mac": pnic_info_dict.get("mac", "Not found"),
            "id": pci_info.id,
            "deviceName": pci_info.deviceName,
            "vendorName": pci_info.vendorName,
            "pNIC": pnic_name,
            "driver": pnic_info_dict.get("driver", "Unknown"),
            "driver_version": pnic_info_dict.get("driver_version", "Unknown"),
            "driver_firmware": pnic_info_dict.get("driver_firmware", "Unknown"),
            "speed": pnic_info_dict.get("speed", 0),
            "is_connected": pnic_info_dict.get("is_connected", False),
            "pnic_vendor": f"{pci_info.id} - {pci_info.vendorName} {pci_info.deviceName}"
        }

        return pci_pnic_info

    def read_all_datastores(
            self
    ) -> List[VMwareDatastore]:
        """
        Reads all datastore's and return as a list of VMware Datastore
        :return: List of VMwareClusterComputeResource.
        """
        with self._container_view([vim.Datastore]) as container:
            return [d for d in container.datastores]

    def read_datastore_by_name(
            self,
            datastore_name: str
    ) -> Optional[VMwareDatastore]:
        """
        Retrieves a datastore by its name.

        :param datastore_name: The name of the datastore.
        :return: The datastore object if found, None otherwise.
        """
        with self._container_view([vim.Datastore]) as container:
            for datastore in container.view:
                if (datastore.name == datastore_name
                        or str(datastore) == datastore_name):
                    return datastore
        return None

    def read_all_dvs(self) -> Optional[List[vim.DistributedVirtualSwitch]]:
        """
        Reads all Distributed Virtual Switches (DVS) and returns them as a list of DVS Switch objects.
        :return: List of VMwareDistributedVirtualSwitch.
        """
        with self._container_view([vim.DistributedVirtualSwitch]) as container:
            return [dvs for dvs in container.view]

    def read_all_dvs_names(
            self
    ) -> Tuple[List[str], List[str]]:
        """
        Reads all Distributed Virtual Switch (DVS) names and returns them as strings.

        Example:
        ["vim.DistributedVirtualSwitch:dvs-100"]

        :return: A tuple containing two lists: the first list contains
                 the managed object reference strings,
                 and the second list contains the human-readable names of the DVSs.
        """
        dvss = self.read_all_dvs()
        if dvss is not None:
            return ([str(d) for d in dvss],
                    [d.name for d in dvss])
        else:
            return [], []

    def read_dvs_by_name(
            self,
            dvs_name: str
    ) -> Optional[VMwareDistributedVirtualSwitch]:
        """
        Reads a Distributed Virtual Switch (DVS) by its name
        or managed object id and returns it.

        :param dvs_name: The name of the DVS or managed object id string.
        :return: The DVS object if found, None otherwise.
        """
        start_time = time.time()
        with self._container_view([vim.DistributedVirtualSwitch]) as container:
            for dvs in container.view:
                if (dvs.name == dvs_name
                        or str(dvs) == dvs_name):
                    self.logger.debug(f"read_dvs_by_name took {time.time() - start_time:.2f} seconds")
                    return dvs
        return None

    def read_all_cluster(
            self
    ) -> Optional[List[VMwareClusterComputeResource]]:
        """
        Reads all cluster and return as a list of VMware Cluster ComputeResources.

        :return: List of VMwareClusterComputeResource.
        """
        with self._container_view([vim.ClusterComputeResource]) as container:
            clusters = [cluster for cluster in container.view]
            return clusters

    def read_all_cluster_names(
            self
    ) -> Tuple[List[str], List[str]]:
        """
        Reads all cluster name and return as string,
        each tuple entry moid, name

        Example
        ["vim.ClusterComputeResource:domain-c8"]

        :return: The cluster string name
        """
        clusters = self.read_all_cluster()
        if clusters is not None:
            return ([str(c) for c in clusters],
                    [c.name for c in clusters])
        else:
            return [], []

    def read_cluster(
            self,
            cluster_name: str
    ) -> Optional[VMwareClusterComputeResource]:
        """
        Reads a cluster by its name or managed object id and returns them as
        list of VMware Cluster ComputeResource

        :param cluster_name: The name of the cluster or managed object id string.
        :return: The cluster object if found, None otherwise.
        """
        with self._container_view([vim.ClusterComputeResource]) as container:
            for cluster in container.view:
                if cluster.name == cluster_name or str(cluster) == cluster_name:
                    return cluster
        return None

    def read_cluster_by_vm_name(
            self,
            vm_name: str
    ) -> Union[VMwareManagedEntity, None]:
        """
        Reads the cluster that contains a specified virtual machine by the VM's name.

        :param vm_name: The name of the virtual machine.
        :return: The cluster object if found, None otherwise.
        :raise: VMNotFoundException if the virtual machine not found
        """
        vm = self._find_by_dns_or_uuid(vm_name)
        if vm is None:
            raise VMNotFoundException("VM '{}' not found".format(vm_name))

        try:
            resource_pool = vm.resourcePool
            while hasattr(resource_pool, 'parent') and resource_pool.parent is not None:
                if isinstance(resource_pool.parent, vim.ClusterComputeResource):
                    return resource_pool.parent
                resource_pool = resource_pool.parent
        except AttributeError:
            return None

        return None

    def read_all_resource_pools(
            self
    ) -> Optional[List[VMwareResourcePool]]:
        """
        Reads all resource pools and returns them as a list
        of VMware ResourcePool objects.

        :return: List of VMwareResourcePool objects.
        """
        with self._container_view([vim.ResourcePool]) as container:
            resource_pools = [resource_pool for resource_pool in container.view]
            return resource_pools

    def read_all_resource_pool_names(
            self
    ) -> Tuple[List[str], List[str]]:
        """
        Reads all resource pool names and returns them as strings.

        Example:
        ["vim.ResourcePool:resgroup-100"]

        :return: A tuple containing two lists: the first list contains the managed object reference strings,
                 and the second list contains the human-readable names of the resource pools.
        """
        resource_pools = self.read_all_resource_pools()
        if resource_pools is not None:
            return ([str(rp) for rp in resource_pools],
                    [rp.name for rp in resource_pools])
        else:
            return [], []

    def read_resource_pool_by_name(
            self,
            resource_pool_name: str
    ) -> Optional[vim.ResourcePool]:
        """
        Retrieves a resource pool by its name.

        :param resource_pool_name: The name of the resource pool.
        :return: The resource pool object if found, None otherwise.
        """
        with self._container_view([vim.ResourcePool]) as container:
            for resource_pool in container.view:
                if (resource_pool.name == resource_pool_name or
                        str(resource_pool) == resource_pool_name):
                    return resource_pool
        return None

    def read_vapp_by_name(
            self, vapp_name: str
    ) -> Optional[vim.VirtualApp]:
        """
        Retrieves a vApp (Virtual Application) by its name.

        :param vapp_name: The name of the vApp.
        :return: The vApp object if found, None otherwise.
        """
        with self._container_view([vim.VirtualApp]) as container:
            for vapp in container.view:
                if vapp.name == vapp_name or str(vapp) == vapp_name:
                    return vapp
        return None

    def read_folder_by_name(
            self, folder_name: str
    ) -> Optional[vim.Folder]:
        """
        Retrieves a folder by its name.

        :param folder_name: The name of the folder.
        :return: The folder object if found, None otherwise.
        """
        with self._container_view([vim.Folder]) as container:
            for folder in container.view:
                if folder.name == folder_name or str(folder) == folder_name:
                    return folder
        return None

    @staticmethod
    def get_numa_node_by_pci_device(
            pci_device,
            numa_topology
    ):
        """
        topology must be in format
        {
            'cpu': {
                <numa_node_id>: [<cpu_id_1>, <cpu_id_2>, ...],
                ...
            },
            'pci': {
                <numa_node_id>: [<pci_device_id_1>, <pci_device_id_2>, ...],
                ...
            }
        }
        :param pci_device:
        :param numa_topology:
        :return:
        """
        for node_id, devices in numa_topology['pci'].items():
            if pci_device in devices:
                return node_id
        return None

    def vm_state(
            self,
            vm_name: str
    ) -> Dict[str, Any]:
        """
        Retrieves the state of VMs that match a given name substring,
        including information about their pNICs, SR-IOV adapters, and vmxnet3 adapters
        and specific hardware details and vm config object.

        The return dict contains  following keys

        {
                'esxiHost': esxi host ip
                'esxiHostUuid': host uuid,
                'pnic_data':  pnic data related to VM
                'sriov_adapters': list of dict that hold sriov data,
                'vmxnet_adapters': list of dict that hold vmxnet3 adapters data.
                'hardware_details': hardware details,
                'vm_config': a dict that hold vm config state.
        }

        :param vm_name: Substring of the VM name to search for.
        :return: A dictionary containing the state information for each matching VM.
        """
        vm_states = {}
        vms = self.find_vm_by_name_substring(vm_name)

        for i, vm in enumerate(vms):
            vm_ = self._find_by_dns_or_uuid(vm.name)
            hardware_info = vm_.config.hardware

            _vm_extra_config = self.read_vm_extra_config(vm.name)
            _vm_extra_dict = self.vim_obj_to_dict(
                _vm_extra_config, no_dynamics=True
            )

            hardware_details = {
                'numCPU': hardware_info.numCPU,
                'numCoresPerSocket': hardware_info.numCoresPerSocket,
                'autoCoresPerSocket': hardware_info.autoCoresPerSocket,
                'memoryMB': hardware_info.memoryMB,
            }

            host = self.get_esxi_ip_of_vm(vm.name)
            host_data = self.read_esxi_host(host.host)

            numa_info = None
            if host_data and host_data.hardware:
                numa_info = host_data.hardware.numaInfo

            numa_topology = {
                'cpu': {numa_node.typeId: [str(cpu).replace('(short)', '').strip()
                                           for cpu in numa_node.cpuID] for numa_node in numa_info.numaNode},

                'pci': {numa_node.typeId: [pci.replace('\n', '').strip()
                                           for pci in numa_node.pciId] for numa_node in numa_info.numaNode}
            } if numa_info else {'cpu': None, 'pci': None}

            _sriov_adapters, _vmx_net_adapters = self.vm_adapters_and_sriov_devices(vm.name)

            vm_states[vm_name] = {
                'esxiHost': host.host,
                'numa_nodes': numa_info.numNodes,
                'numa_topology': numa_topology,
                'esxiHostUuid': host.uuid,
                'pnic_data': self.read_vm_pnic_info(vm.name),
                'sriov_adapters': _sriov_adapters,
                'vmxnet_adapters': _vmx_net_adapters,
                'hardware_details': hardware_details,
                'vm_config': _vm_extra_dict
            }

        return vm_states

    def get_managed_entities(self, entity_name: str, entity_type: str):
        """
        Retrieves a managed entity by its name and type.

        :param entity_name: The name of the entity to retrieve.
        :param entity_type: The type of the entity (e.g., vm, host, datastore, cluster, dvs, resourcepool, vapp).
        :return: The requested entity if found.
        :raises: Specific exception if the entity is not found or the entity type is unknown.
        """
        entity = None
        if entity_type == "vm":
            entity = self._find_by_dns_or_uuid(entity_name)
            if entity is None:
                raise VMNotFoundException(f"VM '{entity_name}' not found")
        elif entity_type == "host":
            entity = self.read_esxi_host(entity_name)
            if entity is None:
                raise EsxHostNotFound(f"Host '{entity_name}' not found")
        elif entity_type == "datastore":
            entity = self.read_datastore_by_name(entity_name)
            if entity is None:
                raise DatastoreNotFoundException(f"Datastore '{entity_name}' not found")
        elif entity_type == "cluster":
            entity = self.read_cluster(entity_name)
            if entity is None:
                raise ClusterNotFoundException(f"Cluster '{entity_name}' not found")
        elif entity_type == "dvs":
            entity = self.read_dvs_by_name(entity_name)
            if entity is None:
                raise SwitchNotFound(f"Distributed switch '{entity_name}' not found")
        elif entity_type == "resourcepool":
            entity = self.read_resource_pool_by_name(entity_name)
            if entity is None:
                raise ResourcePoolNotFoundException(f"Resource Pool '{entity_name}' not found")
        elif entity_type == "vapp":
            entity = self.read_vapp_by_name(entity_name)
            if entity is None:
                raise VAppNotFoundException(f"vApp '{entity_name}' not found")
        elif entity_type == "folder":
            entity = self.read_folder_by_name(entity_name)
            if entity is None:
                raise FolderNotFoundException(f"Folder '{entity_name}' not found")
        else:
            raise UnknownEntity(f"Unknown entity type '{entity_type}'")

        return entity

    @staticmethod
    def vim_obj_to_dict(
            vim_obj,
            no_dynamics: Optional[bool] = False
    ):
        """
        Recursively converts a VIM API object into a dictionary.
        It takes a VMware Object return by API and covert to native Dict

        Example.

        ```
        (vim.option.OptionValue) [
               (vim.option.OptionValue) {
                  dynamicType = <unset>,
                  dynamicProperty = (vmodl.DynamicProperty) [],
                  key = 'sched.cpu.latencySensitivity',
                  value = 'high'
               },
               (vim.option.OptionValue) {
                  dynamicType = <unset>,
                  dynamicProperty = (vmodl.DynamicProperty) [],
                  key = 'tools.guest.desktop.autolock',
                  value = 'TRUE'
               }
        ]

            {
                "dynamicProperty": [],
                "key": "sched.cpu.latencySensitivity",
                "value": "high"
            },
            {
                "dynamicProperty": [],
                "key": "tools.guest.desktop.autolock",
                "value": "TRUE"
            },

        :param vim_obj: is pyVmomi object
        :param no_dynamics:  remove dynamicProperty
        :return:
        """
        if not vim_obj:
            return None

        # infer if something we can iterate or it a python list
        if isinstance(vim_obj, list) or hasattr(vim_obj, '__iter__'):
            return [VMwareVimStateReader.vim_obj_to_dict(item, no_dynamics=no_dynamics) for item in vim_obj]

        output = {}
        for attr in dir(vim_obj):
            if attr.startswith('_') or callable(getattr(vim_obj, attr)):
                continue
            attr_value = getattr(vim_obj, attr)
            # case list recurse
            if isinstance(attr_value, list):
                if no_dynamics and attr == "dynamicProperty":
                    continue
                output[attr] = [
                    VMwareVimStateReader.vim_obj_to_dict(el, no_dynamics=no_dynamics)
                    if not isinstance(el, (int, str, bool, float)) else el for el in attr_value
                ]
            # case native dtype
            elif not isinstance(attr_value, (int, str, bool, float)):
                if attr_value is not None:
                    output[attr] = VMwareVimStateReader.vim_obj_to_dict(attr_value, no_dynamics=no_dynamics)
            else:
                output[attr] = attr_value

        return output

    @staticmethod
    def vmware_obj_as_json(
            vim_obj,
            no_dynamics: Optional[bool] = False
    ) -> str:
        """ Converts a VIM API object to JSON format.
        see vim_obj_to_dict

        :param vim_obj: is pyVmomi object
        :param no_dynamics:  remove dynamicProperty
        :return: JSON as string
        """
        dict_obj = VMwareVimStateReader.vim_obj_to_dict(vim_obj, no_dynamics=no_dynamics)
        return json.dumps(dict_obj, indent=4)

    def read_vmware_object(self, root, vim_type):
        """
        :param root:
        :param vim_type:
        :return:
        """
        self.connect_to_vcenter()
        container = self.si.content.viewManager.CreateContainerView(
            root, vim_type, True)
        view = container.view
        container.Destroy()
        return view

    def filter_spec(
            self,
            ctx: VMwareContex,
            obj_type,
            path: list
    ):
        traverse_spec = vmodl.query.PropertyCollector.TraversalSpec()
        traverse_spec.name = 'traverseEntries'
        traverse_spec.path = 'view'
        traverse_spec.skip = False
        traverse_spec.type = vim.view.ContainerView

        obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = ctx
        obj_spec.skip = True
        obj_spec.selectSet.append(traverse_spec)

        prop_spec = vmodl.query.PropertyCollector.PropertySpec()
        prop_spec.type = obj_type
        prop_spec.pathSet = path
        return vmodl.query.PropertyCollector.FilterSpec(propSet=[prop_spec], objectSet=[obj_spec])

    def _unpack_result(
            self,
            result, objects
    ):
        """Unpack result from properties collector
        :param result: a result from properties collector
        :param objects: a list of objects returned by properties collector
        :return:
        """
        for o in result.objects:
            for p in o.propSet:
                objects[o.obj][p.name] = p.val

    def collect_properties(
            self,
            root_view: VMwareFolder,
            vim_type,
            props: List[str]
    ):
        """
        Collect properties where root context view , object type and list of properties we collect.
        Note this more desired query since it produce much faster queries.
        :param root_view: root folder view
        :param vim_type: an object type
        :param props:  list of properties to collect
        :return:
        """

        self.connect_to_vcenter()
        objects = defaultdict(dict)
        start_time = time.time()
        view_mgr = self.si.content.viewManager
        ctx = view_mgr.CreateContainerView(root_view, [vim_type], True)
        self.logger.debug(f"CreateContainerView took {time.time() - start_time:.2f} seconds")

        try:
            filter_spec = self.filter_spec(
                ctx, vim_type, props
            )
            start_time = time.time()
            self.logger.debug(
                f"vmodl.query.PropertyCollector.RetrieveOptions took {time.time() - start_time:.2f} seconds")

            pc = self.si.content.propertyCollector
            start_time = time.time()
            result = pc.RetrievePropertiesEx([filter_spec], vmodl.query.PropertyCollector.RetrieveOptions())

            self.logger.debug(f"RetrievePropertiesEx took {time.time() - start_time:.2f} seconds")
            self._unpack_result(result, objects)

            while result.token is not None:
                result = pc.ContinueRetrievePropertiesEx(result.token)
                self._unpack_result(result, objects)

        finally:
            ctx.Destroy()

        return objects

    def find_vm_by_name_substring(
            self,
            name_substring: str
    ) -> List[VmUuid]:
        """
        :param name_substring:
        :return:
        """
        if name_substring in self._vm_name_cache:
            return self._vm_name_cache[name_substring]

        start_time = time.time()
        self.connect_to_vcenter()
        self.logger.debug(f"connect_to_vcenter took {time.time() - start_time:.2f} seconds")
        vms = self.collect_properties(
            self.si.content.rootFolder, vim.VirtualMachine, ['name', 'config.uuid'])
        vms = [VmUuid(*v.values(), k) for k, v in vms.items() if name_substring in v['name']]
        self._vm_name_cache[name_substring] = vms
        for vm in vms:
            self._vm_name_cache[vm.name] = [vm]
            self._vm_name_cache[vm.uuid] = [vm]

        return vms
