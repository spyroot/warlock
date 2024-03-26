from collections import namedtuple

MacAddressState = namedtuple('MacAddressState', ['vnic', 'sriov'])
PnicState = namedtuple('PnicState', ['vnic', 'sriov'])
VmState = namedtuple('VmState', ['state', 'pnic_map', 'mac'])
IaaSState = namedtuple('IaaSState', ['reader', 'vm'])
HostVmnicInfo = namedtuple('HostVmnicInfo', ['host', 'vnic', 'sriov_vmnic'])

PortInfo = namedtuple(
    'PortInfo', [
        'port_id',
        'port_type',
        'subtype',
        'switch_name',
        'mac_address',
        'client_name',
        'is_sriov'
    ]
)
