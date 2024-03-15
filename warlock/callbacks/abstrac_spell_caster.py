from abc import abstractmethod, ABCMeta
from abc import ABC
from typing import Optional
from warlock.spell_specs import SpellSpecs
from warlock.states.spell_caster_state import SpellCasterState
# import torch.distributed as dist
# from loguru import logger


class SpellCaster(ABC, metaclass=ABCMeta):
    """
    """
    @abstractmethod
    def __init__(
            self,
            spell_spec: SpellSpecs,
            verbose: Optional[bool] = False
    ):
        """Create a new SpellCaster, each spell caster has internal state.
        encapsulate as SpellCasterState.

        In term os state is abstraction that capture spell caster state
        and observation about world around.  For example Warlock state observation
        is observation about IaaS and CaaS.

        :param spell_spec:
        :param verbose:
        """
        self.state_pods = None
        self._spell_spec = spell_spec
        self._state = SpellCasterState()
        self._state.verbose = verbose

    @abstractmethod
    def cast_spell(self):
        """Each spell caster must implement cast spell"""
        pass

    def set_verbose(self, param):
        """Set verbose level for spell caster
        :param param:
        :return:
        """
        self._state.verbose = param

    @abstractmethod
    def cast_teleport(self):
        """Cast teleport"""
        pass
