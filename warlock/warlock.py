import json
import pickle
from pathlib import Path
from typing import Optional, Callable, Union, List

from warlock.spell_specs import SpellSpecs
from warlock.callbacks.callback import BaseCallbacks, Callback
from warlock.states.warlock_state import WarlockState
from warlock.metrics.spell_metrics import SpellMetrics
from warlock.callbacks.abstrac_spell_caster import SpellCaster


class WarlockSpellCaster(SpellCaster['WarlockState']):
    def __init__(
            self,
            spell_file: Union[str, Path] = "spell.json",
            state_callbacks: Optional[List[Callback['WarlockState']]] = None,
            action_callbacks: Optional[List[Callback['WarlockState']]] = None,
            spells_specs: SpellSpecs = None,
            spell_metric: SpellMetrics = None,
            warlock_state: Optional[WarlockState] = None,
    ):
        """
        By default, Warlock reads spell from spell.json file
        state_callbacks list of spells that Warlock can cast to observer environment state.

        For example, a callback that observer pod state and iaas.
        warlock = WarlockSpellCaster(
            state_callbacks=[
                CallbackPodsOperator(spell_master_specs=master_spell),
                CallbackIaasObserver(spell_master_specs=master_spell),
            ],

        This callback will read state from pods and VMware vCenter.

        spell_file i.e. specs that describe how spell that warlock can execute to change
        the entire world or particular entity in that world.

        action_callbacks list of callback that perform action i.e. cast a spell for example
        that mutate worker node or esxi node.

        warlock_state is existing state that saved prior, this particular useful
        if we don't expect state we read prior mutated and we resume.

        consider a case when we read all state values form VMs , Worker node
        We don't expect for example a mutation that re-adjust VM specs, networking etc, hence
        we can load old state that capture snapshot of environment.


        :param spell_file: a path to a file.
        :param state_callbacks: a list of observer callback that most execute on spell beging and read state.
        :param action_callbacks: a list of callback that mutate a state and observer change made to environment.
        :param spells_specs:
        :param spell_metric:
        :param warlock_state:
        """
        # self.state.node_ips = node_ips
        # self.state.ssh_executor = ssh_executor
        # ssh_executor: SSHOperator,

        self._spell_file = spell_file
        self._spells_specs = spells_specs
        self._metric = spell_metric
        self._debug = True
        # callback that mostly focus on reading a states
        self._state_callbacks = BaseCallbacks(callbacks=state_callbacks)
        # action call , list of callback execute to perform action
        self._action_callbacks = BaseCallbacks(callbacks=state_callbacks)
        self._spells_specs = spells_specs

        self._state = warlock_state or WarlockState()
        self._state_callbacks.register_spell_caster_state(spell_caster_state=self._state)
        self._state_callbacks.register_spell_metric(spell_metric)

        self._action_callbacks.register_spell_caster_state(spell_caster_state=self._state)
        self._state_callbacks.register_spell_metric(spell_metric)

        # node_ips: List[str],
        self._build_spells()

    def _build_spells(self):
        """Build spell list if necessary,
        :return:
        """
        if self._spells_specs is None:
            self._spells_specs = SpellSpecs(self._spell_file)

    def cast_spell(self):
        """
        :return:
        """
        print(self._state)
        self._state_callbacks.on_scenario_begin()
        # node_actions = NodeActions(
        #     kube_state.node_ips(),
        #     ssh_runner,
        #     spells_specs
        # )
        # node_actions.start_environment()
        # self._callbacks.on_scenario_end()

    def cast_teleport(self):
        pass

    def show_spells(self):
        if self._spells_specs is not None:
            print(json.dumps(self._spells_specs.master_spell(), indent=4))

    def initialize_state(self) -> WarlockState:
        return WarlockState()

    def load_state_from_file(
            self,
            file_path: str
    ) -> 'WarlockState':
        """
        Loads the WarlockState from a file using pickle.

        :param file_path: The file path from where the state should be loaded.
        :return: The loaded WarlockState instance.
        """
        state = self._state.load_state_from_file(file_path)
        self.update_state(state)

    def save_state_to_file(
            self,
            file_path: str
    ):
        """

        :param file_path:
        :return:
        """
        self._state.save_state_to_file(file_path)

    def update_state(
            self,
            state: WarlockState
    ):
        """
        Sets the internal state of the WarlockSpellCaster.
        :param state: The WarlockState instance to be set as the current state.
        """
        self._state = state

    @classmethod
    def _load_state(
            cls,
            file_path: str
    ) -> WarlockState:
        """
        Loads the WarlockState from a file.
        :param file_path: The file path from where the state should be loaded.
        :return: The loaded WarlockState instance.
        """
        with open(file_path, 'rb') as file:
            return pickle.load(file)

    @classmethod
    def create_from_state(
            cls,
            state_file: str,
            spell_file: Union[str, Path] = "spell.json",
            state_callbacks: Optional[List[Callback['WarlockState']]] = None,
            action_callbacks: Optional[List[Callback['WarlockState']]] = None,
            spells_specs: SpellSpecs = None,
            spell_metric: SpellMetrics = None,
    ) -> 'WarlockSpellCaster':
        """
        Create Warlock from existing state file.

        :param state_file: The file path from where the state should be loaded.
        :param spells_specs:
        :param action_callbacks:
        :param spell_file:
        :param state_callbacks:
        :param spell_metric:
        :return: The loaded WarlockState instance.
        """
        WarlockState.load_state_from_file(state_file)
        warlock = WarlockSpellCaster(
            spell_file=spell_file,
            state_callbacks=state_callbacks,
            action_callbacks=action_callbacks,
            spells_specs=spells_specs,
            spell_metric=spell_metric,
            warlock_state=WarlockState.load_state_from_file(state_file)
        )
        return warlock
