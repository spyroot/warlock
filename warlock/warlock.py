import json
from abc import ABC
from pathlib import Path
from typing import Optional, Callable, Union

from warlock.callbacks.abstrac_spell_caster import SpellCaster
from warlock.callbacks.callback import BaseCallbacks
from warlock.metrics.spell_metrics import SpellMetrics
from warlock.spell_specs import SpellSpecs
from warlock.states.warlock_state import WarlockState


# from callbacks.abstrac_spell_caster import SpellCaster
# from callbacks.callback import BaseCallbacks
# from node_actions import NodeActions
# from spell_specs import SpellSpecs


class WarlockSpellCaster(SpellCaster, ABC):
    def __init__(
            self,
            spell_file: Union[str, Path] = "spell.json",
            callbacks: Optional[list[Callable]] = None,
            spells_specs: SpellSpecs = None,
            spell_metric: SpellMetrics = None,
    ):
        """
        By default, Warlock reads spell from spell.json file

        Call back are list of spells that Warlock can cast and spells_specs
        specs that describe how spell that warlock can execute to change
        the entire world or particular entity in that world.
        """
        # self.state.node_ips = node_ips
        # self.state.ssh_executor = ssh_executor
        # ssh_executor: SSHOperator,

        self._spell_file = spell_file
        self._spells_specs = spells_specs
        self._metric = spell_metric
        self._debug = True
        self._callbacks = BaseCallbacks(callbacks=callbacks)
        self._spells_specs = spells_specs

        self._state = WarlockState()
        self._callbacks.register_spell_caster_state(spell_caster_state=self._state)
        self._callbacks.register_spell_metric(spell_metric)

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
        self._callbacks.on_scenario_begin()
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
