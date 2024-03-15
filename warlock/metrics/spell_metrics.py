from abc import ABC, ABCMeta, abstractmethod
from typing import Optional

from warlock.spell_specs import SpellSpecs


class SpellMetrics(ABC, metaclass=ABCMeta):
    """
    """
    @abstractmethod
    def __init__(
            self,
            spell_spec: SpellSpecs,
            verbose: Optional[bool] = False
    ):
        """Create a new SpellMetrics, each spell caster has internal state.
        encapsulate as SpellCasterState.

        Each spell need measured and what we observed.

        :param spell_spec:
        :param verbose:
        """
        self._state = spell_spec
        self._state.verbose = verbose