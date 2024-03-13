from warlock.callback import Callback


class DummyCallback(Callback):
    def __init__(self):
        super().__init__()

    def on_scenario_begin(self):
        print("DummyCallback on_scenario_begin")

    def on_scenario_end(self):
        print("DummyCallback on_scenario_end")
