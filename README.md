# warlock

## Instruction

```bash
conda env create -f environment.yml
conda activate warlock
conda install pytorch torchvision -c pytorch
pip install pyvmomi paramiko pyyaml
```

## Overview

Warlock is a spell-casting tool designed to combine a set of spells that mutate some environments.

Consider IaaS as a world where Caas is an entity in a castle within that world, and worker nodes are minions. Each minion can perform some work and uses PODs. For example, a minion can move magic herbs from one spot to another.

Minions can either walk (use a slow CNI) or teleport (use DPDK).

The main play here is that the Warlock needs to learn a set of spells that will make the minions more efficient.

Since the Warlock has the power to bend reality, it can mutate the entire world (IaaS).









## API

## EsxiStateReader Class

The `EsxiStateReader` class is designed to encapsulate reading ESXi state information. 
It provides methods for retrieving various metrics and data directly 
from an ESXi host via SSH.

## Constructor

### `__init__(ssh_operator: SSHOperator, fqdn: str, username: str, password: str)`

Creates an instance of the `EsxiStateReader` class.

- `ssh_operator`: An instance of the SSHOperator class used for SSH communication.
- `fqdn`: The fully qualified domain name (FQDN) or IP address of the ESXi host.
- `username`: The username for authenticating with the ESXi host.
- `password`: The password for authenticating with the ESXi host.

## Methods

### `is_active() -> bool`

Checks if there's an active SSH connection to the ESXi host.

### `read_adapter_names() -> List[str]`

Reads all adapter names from the ESXi host and returns them as a list.

### `read_pf_adapter_names() -> List[str]`

Reads all adapter names that provide SR-IOV PF functionality.

### `read_vfs(pf_adapter_name: str) -> List[Dict[str, Any]]`

Reads and returns a list of all virtual functions (VFs) for a particular parent network adapter (PF).

## Examples

```python
# Example usage of the EsxiStateReader class
with EsxiStateReader.from_optional_credentials(
        esxi_fqdn="esxi.example.com", username="root", password="password") as esxi_reader:
    adapter_names = esxi_reader.read_adapter_names()
    print("Adapter Names:", adapter_names)
    pf_adapter_names = esxi_reader.read_pf_adapter_names()
    print("SR-IOV PF Adapter Names:", pf_adapter_names)
```
 
```json
{
    "vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k6mdx": {
        "esxiHost": "10.252.80.109",
        "pnic_data": {
            "50 36 69 7a d3 44 2d 5b-2d 9a 62 87 5e 09 35 18": {
                "10.252.80.79": [
                    "vmnic5"
                ],
                "10.252.80.107": [
                    "vmnic5"
                ],
                "10.252.80.109": [
                    "vmnic5"
                ],
                "10.252.80.96": [
                    "vmnic8"
                ]
            },
            "50 36 28 c6 57 2e 82 06-c0 28 b4 4a aa cd 33 de": {
                "10.252.80.79": [
                    "vmnic6"
                ],
                "10.252.80.107": [
                    "vmnic6"
                ],
                "10.252.80.109": [
                    "vmnic6"
                ],
                "10.252.80.96": [
                    "vmnic9"
                ]
            },
            "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7": {
                "10.252.80.79": [
                    "vmnic7"
                ],
                "10.252.80.107": [
                    "vmnic7"
                ],
                "10.252.80.109": [
                    "vmnic7"
                ]
            }
        },
        "sriov_adapters": [
            {
                "label": "SR-IOV network adapter 8",
                "switchUuid": "50 36 28 c6 57 2e 82 06-c0 28 b4 4a aa cd 33 de",
                "portgroupKey": "dvportgroup-69",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:a0:5f",
                "id": "0000:88:00.0",
                "pf_host": "10.252.80.109",
                "pf_mac": "40:a6:b7:3d:b2:50",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic6"
            },
            {
                "label": "SR-IOV network adapter 7",
                "switchUuid": "50 36 28 c6 57 2e 82 06-c0 28 b4 4a aa cd 33 de",
                "portgroupKey": "dvportgroup-69",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:88:34",
                "id": "0000:88:00.0",
                "pf_host": "10.252.80.109",
                "pf_mac": "40:a6:b7:3d:b2:50",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic6"
            },
            {
                "label": "SR-IOV network adapter 5",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:89:ed",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.109",
                "pf_mac": "40:a6:b7:3d:b2:51",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 4",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:d0:80",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.109",
                "pf_mac": "40:a6:b7:3d:b2:51",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 3",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:d0:d2",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.109",
                "pf_mac": "40:a6:b7:3d:b2:51",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 2",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:20:df",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.109",
                "pf_mac": "40:a6:b7:3d:b2:51",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 1",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:be:5f",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.109",
                "pf_mac": "40:a6:b7:3d:b2:51",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 9",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:9a:66",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.109",
                "pf_mac": "40:a6:b7:3d:b2:51",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            }
        ],
        "hardware_details": {
            "numCPU": 32,
            "numCoresPerSocket": 32,
            "autoCoresPerSocket": false,
            "memoryMB": 65536
        }
    },
    "vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k9jcm": {
        "esxiHost": "10.252.80.107",
        "pnic_data": {
            "50 36 69 7a d3 44 2d 5b-2d 9a 62 87 5e 09 35 18": {
                "10.252.80.79": [
                    "vmnic5"
                ],
                "10.252.80.107": [
                    "vmnic5"
                ],
                "10.252.80.109": [
                    "vmnic5"
                ],
                "10.252.80.96": [
                    "vmnic8"
                ]
            },
            "50 36 28 c6 57 2e 82 06-c0 28 b4 4a aa cd 33 de": {
                "10.252.80.79": [
                    "vmnic6"
                ],
                "10.252.80.107": [
                    "vmnic6"
                ],
                "10.252.80.109": [
                    "vmnic6"
                ],
                "10.252.80.96": [
                    "vmnic9"
                ]
            },
            "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7": {
                "10.252.80.79": [
                    "vmnic7"
                ],
                "10.252.80.107": [
                    "vmnic7"
                ],
                "10.252.80.109": [
                    "vmnic7"
                ]
            }
        },
        "sriov_adapters": [
            {
                "label": "SR-IOV network adapter 9",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:4a:df",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.107",
                "pf_mac": "40:a6:b7:35:6e:31",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 8",
                "switchUuid": "50 36 28 c6 57 2e 82 06-c0 28 b4 4a aa cd 33 de",
                "portgroupKey": "dvportgroup-69",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:73:f1",
                "id": "0000:88:00.0",
                "pf_host": "10.252.80.107",
                "pf_mac": "40:a6:b7:35:6e:30",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic6"
            },
            {
                "label": "SR-IOV network adapter 7",
                "switchUuid": "50 36 28 c6 57 2e 82 06-c0 28 b4 4a aa cd 33 de",
                "portgroupKey": "dvportgroup-69",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:d7:3e",
                "id": "0000:88:00.0",
                "pf_host": "10.252.80.107",
                "pf_mac": "40:a6:b7:35:6e:30",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic6"
            },
            {
                "label": "SR-IOV network adapter 5",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:24:e5",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.107",
                "pf_mac": "40:a6:b7:35:6e:31",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 4",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:81:16",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.107",
                "pf_mac": "40:a6:b7:35:6e:31",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 3",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:2f:ff",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.107",
                "pf_mac": "40:a6:b7:35:6e:31",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 2",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:07:a5",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.107",
                "pf_mac": "40:a6:b7:35:6e:31",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            },
            {
                "label": "SR-IOV network adapter 1",
                "switchUuid": "50 36 9d e2 45 9e 28 c0-81 8b 0b 75 e8 e1 5b d7",
                "portgroupKey": "dvportgroup-2051",
                "numaNode": 0,
                "vf_mac": "00:50:56:b6:ba:c5",
                "id": "0000:88:00.1",
                "pf_host": "10.252.80.107",
                "pf_mac": "40:a6:b7:35:6e:31",
                "deviceName": "Ethernet Controller XXV710 for 25GbE SFP28",
                "vendorName": "Intel(R)",
                "pNIC": "vmnic7"
            }
        ],
        "hardware_details": {
            "numCPU": 32,
            "numCoresPerSocket": 32,
            "autoCoresPerSocket": false,
            "memoryMB": 65536
        }
    }
}

```