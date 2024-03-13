import collections.abc

from typing import Any, Optional

import collections

from warlock.abstrac_spell_caster import SpellCaster

try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections


class Metrics:
    pass


class Callback(object):
    """
    Metric Concrete type , late maybe to abstract
    """
    def __init__(self, *args, **kwargs):
        self.metric: Metrics = Optional[None]
        self.spell_caster: SpellCaster = Optional[None]

    def register_spell_caster(self, spell_caster):
        self.spell_caster = spell_caster

    def register_metric(self, metric):
        self.metric = metric

    def on_test_begin(self):
        pass

    def on_test_end(self):
        pass

    def on_scenario_begin(self):
        pass

    def on_scenario_end(self):
        pass

    def on_iaas_mutate_begin(self):
        pass

    def on_iaas_mutate_end(self):
        pass

    def on_cast_spell_begin(self):
        pass

    def on_cast_spell_end(self):
        pass

    def on_after_backward(self):
        pass

    def validation_start(self):
        pass

    def validation_end(self):
        pass


class BaseCallbacks(Callback):
    """
    """
    def __init__(self, callbacks):
        super().__init__()
        self.callbacks = listify(callbacks)

    def register_spell_caster(self, state):
        for callback in self.callbacks:
            callback.register_spell_caster(state)

    def register_metric(self, state):
        for callback in self.callbacks:
            callback.register_metric(state)

    def on_test_begin(self):
        for callback in self.callbacks:
            callback.on_test_begin()

    def on_test_end(self):
        for callback in self.callbacks:
            callback.on_test_end()

    def on_scenario_begin(self):
        for callback in self.callbacks:
            callback.on_scenario_begin()

    def on_scenario_end(self):
        for callback in self.callbacks:
            callback.on_scenario_end()

    def on_iaas_mutate_begin(self):
        for callback in self.callbacks:
            callback.on_iaas_mutate_begin()

    def on_iaas_mutate_end(self):
        for callback in self.callbacks:
            callback.on_iaas_mutate_end()

    def on_cast_spell_begin(self):
        for callback in self.callbacks:
            callback.on_cast_spell_begin()

    def on_cast_spell_end(self):
        for callback in self.callbacks:
            callback.on_cast_spell_end()

    def on_after_backward(self):
        for callback in self.callbacks:
            callback.on_after_backward()

    def validation_start(self):
        for callback in self.callbacks:
            callback.validation_start()

    def validation_end(self):
        for callback in self.callbacks:
            callback.validation_end()


def listify(p: Any) -> collections.abc.Iterable:
    if p is None:
        p = []
    elif not isinstance(p, collections.abc.Iterable):
        p = [p]
    return p