import json

from warlock.states.spell_caster_state import SpellCasterState


class WarlockState(SpellCasterState):
    def __init__(self):
        super().__init__()
        self.verbose = False
        self.k8s_node_states = {}
        self.k8s_pods_states = {}
        self.esxi_node_states = {}

    def __str__(self):
        """
        Provides a string representation of the WarlockState instance,
        detailing its internal dictionaries.
        """
        state_str = [
            f"verbose: {self.verbose}",
            f"k8s_node_states: {self.k8s_node_states}",
            f"k8s_pods_states: {self.k8s_pods_states}",
            f"esxi_node_states: {self.esxi_node_states}",
        ]
        return "\n".join(state_str)

    def to_json(self) -> str:
        """Converts the state's dictionaries to a JSON string.
        :return:  A string representing the JSON-encoded state.
        """
        state_dict = {
            "verbose": self.verbose,
            "k8s_node_states": self.k8s_node_states,
            "k8s_pods_states": self.k8s_pods_states,
            "esxi_node_states": self.esxi_node_states,
        }
        return json.dumps(state_dict, indent=4)

