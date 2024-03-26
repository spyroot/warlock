import collections.abc
from typing import Any
import collections
from warlock.metrics.spell_metrics import SpellMetrics
from warlock.states.spell_caster_state import SpellCasterState
from typing import Generic, TypeVar, Optional

try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections

T = TypeVar('T', bound='SpellCasterState')


class Callback(Generic[T]):
    """
    Provides a mechanism for spell caster register callbacks.
    Each callback executed at different phases and allow to extend
    spell caster to cast different type of spell on different phase.

    Note each type of Spell Caster might have own state re-presentation
    hence we use generic T so each callback know which type it
    operate on.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the callback with optional arguments for customization.
        It's intended to be linked with a spell caster for operational interactions.

        :param args:
        :param kwargs:
        """
        self.spell_metric: SpellMetrics = Optional[None]
        self.caster_state: Optional[T] = None

    def register_spell_caster_state(
            self,
            spell_caster_state: SpellCasterState
    ) -> None:
        """Associates a spell caster with this callback."""
        self.caster_state = spell_caster_state

    def register_spell_metric(self, metric: SpellMetrics) -> None:
        """Associates a metric collector with this callback."""
        self.spell_metric = metric

    def on_scenario_begin(self):
        """Callback should be called before each scenario begin"""
        pass

    def on_scenario_end(self):
        """Callback should be called before each scenario ends"""
        pass

    def on_iaas_spell_begin(self):
        """Callback should be called when we cast a spell against iaas. i.e. we mutate IaaS"""
        pass

    def on_iaas_spell_end(self):
        """Callback should be called when we cast a spell against iaas. i.e. we mutate IaaS"""
        pass

    def on_caas_spell_begin(self):
        """Callback should be called if we need mutate a caas """
        pass

    def on_caas_spell_end(self):
        """Callback should be called if we need mutate a caas """
        pass

    def on_pods_spell_begin(self):
        """Callback should be called if we need mutate a pods """
        pass

    def on_pods_spell_end(self):
        """Callback should be called if we need mutate a pods """
        pass


class BaseCallbacks(Callback[T]):
    """
    """
    def __init__(
            self,
            callbacks: collections.abc.Iterable[Callback[T]]
    ):
        super().__init__()
        self.callbacks = listify(callbacks)

    def register_spell_caster_state(
            self,
            spell_caster_state: T
    ) -> None:
        for callback in self.callbacks:
            print(f"Processing callback: {callback.__class__.__name__}")
            if not hasattr(callback, 'register_spell_caster_state'):
                raise TypeError(f"{callback.__class__.__name__} does not implement register_spell_caster")
            callback.register_spell_caster_state(spell_caster_state=spell_caster_state)

    def register_spell_metric(self, metric: SpellMetrics) -> None:
        """Associates a metric collector with all callback."""
        for callback in self.callbacks:
            callback.register_spell_metric(metric)

    def on_scenario_begin(self):
        """Callback should be called before each scenario start."""
        for callback in self.callbacks:
            callback.on_scenario_begin()

    def on_scenario_end(self):
        """Callback should be called before each scenario end."""
        for callback in self.callbacks:
            callback.on_scenario_end()

    def on_iaas_spell_begin(self):
        """Callback should be called before each scenario start."""
        for callback in self.callbacks:
            callback.on_iaas_spell_begin()

    def on_iaas_spell_end(self):
        """Callback should be called before each scenario start."""
        for callback in self.callbacks:
            callback.on_iaas_spell_end()

    def on_caas_spell_begin(self):
        """Callback should be called before each scenario start."""
        for callback in self.callbacks:
            callback.on_cast_spell_begin()

    def on_caas_spell_end(self):
        """Callback should be called before each scenario start."""
        for callback in self.callbacks:
            callback.on_cast_spell_end()

    def on_pods_spell_begin(self):
        """Callback should be called if we need mutate a pods """
        for callback in self.callbacks:
            callback.on_pods_spell_end()

    def on_pods_spell_end(self):
        """Callback should be called if we need mutate a pods """
        for callback in self.callbacks:
            callback.on_pods_spell_end()


def listify(p: Any) -> collections.abc.Iterable:
    if p is None:
        p = []
    elif not isinstance(p, collections.abc.Iterable):
        p = [p]
    return p
