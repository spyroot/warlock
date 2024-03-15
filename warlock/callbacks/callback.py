import collections.abc
from typing import Any, Optional
import collections
from warlock.callbacks.abstrac_spell_caster import SpellCaster
from warlock.metrics.spell_metrics import SpellMetrics
from warlock.states.spell_caster_state import SpellCasterState

try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections


class Callback(object):
    """
    Provides a mechanism for spell caster register callbacks.
    Each callback executed at different phases and allow to extend
    spell caster to cast different type of spell on different phase.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the callback with optional arguments for customization.
        It's intended to be linked with a spell caster for operational interactions.

        :param args:
        :param kwargs:
        """
        self.spell_metric: SpellMetrics = Optional[None]
        self.caster_state: SpellCasterState = Optional[None]

    def register_spell_caster_state(
            self,
            spell_caster_state: SpellCasterState
    ) -> None:
        """Associates a spell caster with this callback."""
        print("Registering spell caster state", spell_caster_state)
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


class BaseCallbacks(Callback):
    """
    """
    def __init__(self, callbacks):
        super().__init__()
        self.callbacks = listify(callbacks)

    def register_spell_caster_state(
            self,
            spell_caster_state: SpellCasterState
    ) -> None:
        print("Registering spell caster with callbacks:", self.callbacks)
        for callback in self.callbacks:
            print(f"Processing callback: {callback.__class__.__name__}")
            if not hasattr(callback, 'register_spell_caster_state'):
                raise TypeError(f"{callback.__class__.__name__} does not implement register_spell_caster")
            callback.register_spell_caster_state(spell_caster_state=spell_caster_state)
            print(f"Spell caster registered with: {callback.__class__.__name__}")

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
