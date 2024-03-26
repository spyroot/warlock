import json
import os

from tests.extended_test_case import ExtendedTestCase
from warlock.callbacks.callback_pod_operator import CallbackPodsOperator
from warlock.callbacks.named_tuples import (
    PortInfo,
    MacAddressState,
    PnicState,
    VmState,
    IaaSState,
    HostVmnicInfo
)

from warlock.spell_specs import SpellSpecs
from warlock.states.warlock_state import WarlockState, custom_serializer


class NamedTupleEncoder(json.JSONEncoder):
    def default(self, obj):
        print("called")
        if isinstance(obj, tuple) and hasattr(obj, '_asdict'):
            return obj._asdict()
        return json.JSONEncoder.default(self, obj)


def custom_serializer2(obj):
    """
    JSON serializer for objects not serializable by default json code.
    :param obj: The object to serialize.
    :return: A JSON-serializable representation of the object.
    """
    os.exit(1)

    print("custom_serializer")
    if isinstance(obj, (MacAddressState, PnicState, VmState, IaaSState, HostVmnicInfo, PortInfo)):
        print("Case one")
        print(f"Serializing {type(obj)}")
        return obj._asdict()
    elif hasattr(obj, '_asdict'):  # Additional check for namedtuples
        print("Case two")
        return obj._asdict()
    else:
        print("Case 3")
        print(f"Cannot serialize type {type(obj)}")
        raise TypeError(f"Type {type(obj)} not serializable")


class TestsWarlockState(ExtendedTestCase):

    def test_can_serialize_json(self):
        """Test we can construct a callback.
        :return:
        """
        port_info_instance = PortInfo(
            port_id="1234",
            port_type="Ethernet",
            subtype="subtype1",
            switch_name="Switch1",
            mac_address="00:11:22:33:44:55",
            client_name="Client1",
            is_sriov=True
        )
        warlock_state = WarlockState()
        warlock_state.esxi_node_states["test"] = port_info_instance
        data = warlock_state.to_json()
        print(data)
        # port_info_json = json.dumps(port_info_instance, indent=4, cls=NamedTupleEncoder)
        # print(port_info_json)
