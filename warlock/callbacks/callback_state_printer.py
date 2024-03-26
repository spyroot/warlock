import logging
from typing import Optional

from warlock.callbacks.callback import Callback
from warlock.spell_specs import SpellSpecs


class CallbackStatePrinter(
    Callback['WarlockState']
):
    """
    This class is responsible for printing the state of the application to a specified output,
    which can be stdout, a file, or the logging system. This functionality is primarily used
    for debugging purposes to ensure the correct state is captured at various points in the
    application's execution.

    Attributes:
        spell_master_specs (SpellSpecs): Configuration and specifications for the spell master.
        dry_run (bool, optional): Indicates if the operations should be executed or just simulated.
        logger (logging.Logger, optional): Logger instance for logging messages.
        output (str): The output destination type ('stdout', 'file', or 'log').
        output_file (str, optional): The file path where the state should be written if output is 'file'.
    """

    def __init__(
            self,
            spell_master_specs: SpellSpecs,
            dry_run: Optional[bool] = True,
            logger: Optional[logging.Logger] = None,
            output: str = 'stdout',
            output_file: Optional[str] = None,
    ):
        """
        Initializes the CallbackStatePrinter with specified parameters for spell master specs,
        operation mode, logger, output destination, and output file path.

        :param spell_master_specs: Spell specifications and configurations.
        :param dry_run: If True, no actual operations will be performed (default is True).
        :param logger: Logger instance to use for logging purposes. If None, a default logger will be used.
        :param output: The type of output destination ('stdout', 'file', or 'log').
        :param output_file: The file path to write to if the output is set to 'file'. If None,
                            a default 'state_output.json' file will be used.
        """
        super().__init__()
        self.logger = logger if logger else logging.getLogger(__name__)
        self._master_spell_spec = spell_master_specs
        self.is_dry_run = dry_run
        self._output = output
        self._output_file = output_file if output_file else 'state_output.json'

    def on_scenario_begin(self):
        """Called at the beginning of a scenario.
        This method prints the state to the specified output.
        Depending on the output type, the state can be printed to stdout, written to a file, or logged.
        """
        self.logger.info("CallbackStatePrinter scenario begin")
        state_json = self.caster_state.to_json()

        if self._output == 'stdout':
            print(state_json)
        elif self._output == 'file':
            with open(self._output_file, 'w') as file:
                file.write(state_json)
        elif self._output == 'log':
            self.logger.info(f"State: {state_json}")
        else:
            raise ValueError(f"Unsupported output type: {self._output}")
