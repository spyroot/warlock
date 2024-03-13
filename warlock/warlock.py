import argparse
from abc import ABC
from pathlib import Path
from typing import List, Optional, Callable

from warlock.abstrac_spell_caster import SpellCaster
from warlock.callback import BaseCallbacks
from warlock.kube_state import KubernetesState
from warlock.node_actions import NodeActions
from warlock.ssh_operator import SSHOperator
from warlock.inference import (
    iperf_tcp_json_to_np, plot_tcp_perf
)

import json


class WarlockSpellCaster(SpellCaster, ABC):
    def __init__(
            self,
            callbacks: Optional[list[Callable]] = None,
            spells_specs=None
    ):
        """
        Call back are spells that Warlock can cast and spells_specs
        specs that describe how spell that warlock can execute to change
        the entire world or particular entity in that world.

        :param node_ips: A list of IP addresses for the  kubernetes nodes.
        :param ssh_executor: An object responsible for executing SSH commands.
        :param test_environment_spec: The test environment specification including configurations for the test.
        """
        # self.node_ips = node_ips
        # self.ssh_executor = ssh_executor

        # ssh_executor: SSHOperator,

        # Set test environment specification directly from the provided argument
        if spells_specs is not None:
            self.tun_value = spells_specs
        else:
            # If no spec is provided, fallback to loading from the default file (optional)
            self.tun_value_file = "../spell.json"
            with open(self.tun_value_file, 'r') as file:
                self.tun_value = json.load(file)

        self.debug = True
        self._callbacks = BaseCallbacks(callbacks=callbacks)
        print(self._callbacks.callbacks)

        # self._callbacks.register_spell_caster(self)
        # self._callbacks.register_metric(self.metric)
        # node_ips: List[str],


    def cast_spell(self):
        self._callbacks.on_scenario_begin()
        self._callbacks.on_scenario_end()

    def cast_teleport(self):
        pass
