"""
WarlockState represents the shared state within the Warlock framework,
encapsulating the state information for IaaS, ESXi, Pods, and Kubernetes.

Each callback updates the shared state based on the data it retrieves.
For example, the IaaS callback discovers all VMs and updates the state with

VM configurations and resources, including UUIDs, virtual switches, NUMA and CPU mappings,
vmnic, and the ESXi host details.

The ESXi state reader extracts information directly from the ESXi host, including
word IDs, internal port IDs, and other internal identifiers necessary for metric collection.

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import json
import pickle

from warlock.states.spell_caster_state import SpellCasterState
from warlock.callbacks.named_tuples import (
    HostVmnicInfo,
    MacAddressState,
    PnicState,
    VmState,
    IaaSState, PortInfo
)


# class NamedTupleEncoder(json.JSONEncoder):
#     def default(self, obj):
#         print("called")
#         if isinstance(obj, tuple) and hasattr(obj, '_asdict'):
#             return obj._asdict()
#         return json.JSONEncoder.default(self, obj)
#
# def custom_serializer(obj):
#     """
#     :param obj:
#     :return:
#     """
#     if isinstance(obj, (MacAddressState,
#                         PnicState,
#                         VmState,
#                         IaaSState,
#                         HostVmnicInfo,
#                         PortInfo)
#                   ):
#         return obj._asdict()
#     raise TypeError(f"Type {type(obj)} not serializable")

#
def custom_serializer(obj):
    """
    JSON serializer for objects not serializable by default json code.
    :param obj: The object to serialize.
    :return: A JSON-serializable representation of the object.
    """
    print("custom_serializer")
    if isinstance(obj, (MacAddressState, PnicState, VmState, IaaSState, HostVmnicInfo, PortInfo)):
        print("Case one")
        print(f"Serializing {type(obj)}")
        return obj._asdict()
    elif hasattr(obj, '_asdict'):
        print("Case two")
        return obj._asdict()
    else:
        print("Case 3")
        print(f"Cannot serialize type {type(obj)}")
        raise TypeError(f"Type {type(obj)} not serializable")


class NamedTupleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, tuple) and hasattr(obj, '_asdict'):
            return obj._asdict()
        return json.JSONEncoder.default(self, obj)


class WarlockState(SpellCasterState):
    def __init__(self):
        """WarlockState represents the shared state within the Warlock framework,
        encapsulating the state information for IaaS, ESXi, Pods, and Kubernetes.
        Each callback updates the shared state based on the data it retrieves.
        For example, the IaaS callback discovers all VMs and updates the state with
        VM configurations and resources, including UUIDs, virtual switches, NUMA and CPU mappings,
        vmnic, and the ESXi host details.

        The ESXi state reader extracts information directly from the ESXi host, including
        word IDs, internal port IDs, and other internal identifiers necessary for metric collection.

        """
        super().__init__()
        self.verbose = False
        # k8s worker node state where key is ip address
        self.k8s_node_states = {}
        # k8s pod state is state read from kubernetes
        # it include 'ip', 'phase', 'node_ip', 'pod_state'
        # where pod state is state read from kubernetes
        self.k8s_pods_states = {}
        # esxi node state is state read from each esxi host
        self.esxi_node_states = {}
        # iaas state is state read from particular iaas.
        # in case VMWare it vCenter
        self.iaas_state = None

    def __str__(self):
        """To string warlock state
        :return:
        """
        state_str = [
            f"verbose: {self.verbose}",
            f"k8s_node_states: {self.k8s_node_states}",
            f"k8s_pods_states: {self.k8s_pods_states}",
            f"esxi_node_states: {self.esxi_node_states}",
        ]

        if self.iaas_state is not None:
            state_str.append(f"iaas_state: {self.iaas_state}")
        else:
            state_str.append("iaas_state: None")
        return "\n".join(state_str)

    def to_json(self) -> str:
        """
        Converts the state's content to a JSON string, excluding certain keys
        that should not be serialized.
        :return: A string representing the JSON-encoded state.
        """
        state_dict = {
            "verbose": self.verbose,
            "k8s_node_states": self.k8s_node_states,
            "k8s_pods_states": self.k8s_pods_states,
            "esxi_node_states": self.esxi_node_states,
            "iaas_state": self.iaas_state
        }

        # we skip 'reader' key
        if self.iaas_state is not None:
            if 'iaas_state' in state_dict and 'reader' in state_dict['iaas_state']:
                del state_dict['iaas_state']['reader']

        return json.dumps(state_dict, cls=NamedTupleEncoder, indent=4)

    @classmethod
    def load_state_from_file(
            cls,
            file_path: str
    ) -> 'WarlockState':
        """
        Loads the WarlockState from a file using pickle.

        :param file_path: The file path from where the state should be loaded.
        :return: The loaded WarlockState instance.
        """
        with open(file_path, 'rb') as file:
            state = pickle.load(file)
        return state

    def save_state_to_file(
            self,
            file_path: str
    ):
        """
        Saves the WarlockState to a file using pickle.

        :param file_path: The file path where the state should be saved.
        """
        with open(file_path, 'wb') as file:
            pickle.dump(self, file)
