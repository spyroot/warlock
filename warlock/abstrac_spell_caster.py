import pickle
from abc import abstractmethod, ABCMeta

import os
import socket
from abc import ABC
from typing import Optional


from warlock.spell_specs import SpellSpecs
from warlock.spell_caster_state import SpellCasterState
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
        """

        :param spell_spec:
        :param verbose:
        """
        # self.state = None
        self.state = SpellCasterState()
        self.state.verbose = verbose

    @abstractmethod
    def cast_spell(self):
        pass

    def set_verbose(self, param):
        """Set verbose level
        :param param:
        :return:
        """
        self.state.verbose = param

    @abstractmethod
    def cast_teleport(self):
        pass
