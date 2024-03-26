from abc import abstractmethod
from typing import Optional


class SpellCasterState:
    """
    """
    def __init__(self):
        self.verbose = False

    @abstractmethod
    def to_json(self) -> str:
        """
        Converts the state's dictionaries to a JSON string.
        This method should be implemented by all subclasses to return a JSON representation of the state.
        :return: A string representing the JSON-encoded state.
        """
        pass

    @abstractmethod
    def load_state_from_file(
            cls,
            file_path: str
    ) -> 'WarlockState':
        """
        Loads the Caster State from a file.

        :param file_path: The file path from where the state should be loaded.
        :return: The loaded WarlockState instance.
        """
        pass

    @abstractmethod
    def save_state_to_file(
            self,
            file_path: str
    ):
        """
        Saves the WarlockState to a file.
        :param file_path: The file path where the state should be saved.
        """
    pass

