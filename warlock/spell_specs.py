"""
A Spell Spec is a framework that encapsulates what is termed a "Master Spell."
This Master Spell is essentially an aggregation of several spells which together
create a comprehensive strategy.

These spells, when cast by a Spell Caster, are applied to various environments
to achieve specific objectives, such as optimization tasks.

The objective is to learn a powerful Master Spell upon acting on environment
producing maximizing desired behavior.

The framework is designed to be abstract, using terms like IaaS,
CaaS, and pods metaphorically,  rather than referring to actual infrastructure components.

The system categorizes spells into three primary types alongside additional, optional spells:

IaaS Spells: Aimed at transforming what is conceptually represented as IaaS.
CaaS Spells: Focus on altering what is analogously understood as CaaS.
Pods Spells: These are theoretical entities used to evaluate the effectiveness
of a Master Spell, not direct references to Kubernetes pods or similar technologies.

Author: Mustafa Bayramov
spyroot@gmail.com
mbayramo@stanford.edu
"""
import json
import logging
import os
from enum import Enum, auto
from pathlib import Path
from typing import Union, Dict, Any, List, Optional

import yaml


class InvalidSpellSpec(Exception):
    """Raised if spell spec has problem, mandatory key, invalid path etc."""
    def __init__(self, msg):
        super().__init__(msg)


class InvalidPodSpec(Exception):
    """Raised if pod spell has duplicate name"""
    def __init__(self, msg):
        super().__init__(msg)


class SpellType(Enum):
    IAAS = auto()
    CAAS = auto()
    PODS = auto()
    POD = auto()
    METRICS = auto()
    METRIC = auto()

    def to_string(self):
        """Return the enum member's name as a string.
        """
        return self.name

    def __str__(self):
        """
        Return the enum member's name in lowercase when converted to string.
        """
        return self.name.lower()


class IaasSType(Enum):
    VMWARE = auto()
    GCP = auto()

    def to_string(self):
        """Return the enum member's name as a string.
        """
        return self.name

    def __str__(self):
        """Return the  member's name in lowercase when converted to string.
        """
        return self.name.lower()


class PodTypes(Enum):
    SERVER = auto()
    CLIENT = auto()

    def to_string(self):
        """Return the enum member's name as a string.
        """
        return self.name

    def __str__(self):
        """Return the  member's name in lowercase when converted to string.
        """
        return self.name.lower()


class SpellSpecs:

    def __init__(
            self, spell_file: Union[str, Path],
            logger: Optional[logging.Logger] = None):
        """
        Constructor spell from a master spell file.
        A master spell file must contain mandatory ingredients of spell
        iaas_spell, caas_spell, pods_spell

        Example:  spell.json
        {

              "working_dir": "$HOME/dev/warlock",
              "iaas_spell": "spell_iaas.json",
              "caas_spell": "spell_caas.json",
              "pods_spell": "spell_pods.json"
        }
        :param spell_file: a path to master spell.
        """
        self.spell_file = spell_file
        self.spell_spec_file = None
        self.absolute_dir = None
        self.logger = logger or logging.getLogger(__name__)

        self.__mandatory_spells = ['iaas_spell', 'caas_spell', 'pods_spell']
        self.__optional_spells = ['metrics_spell']

        # list of all validator applied for each spell type
        self.spell_validators = {
            SpellType.IAAS: SpellSpecs.validate_iaas_config,
            SpellType.CAAS: SpellSpecs.validate_caas_config,
            SpellType.PODS: SpellSpecs.validate_pods_config,
        }
        self._read_spell_file()
        self._pod_names = set()

    def _read_spell_file(
            self
    ) -> None:
        """Reads and validates master spell and all child spells.
        Internally we keep track absolute root dir where all spells specs files,
        pods spec file located.
        :return:
        """
        with open(self.spell_file, 'r') as file:
            spell_spec_file = json.load(file)

        self.spell_spec_file = spell_spec_file
        self._validate_master_spell_file()
        self.update_absolute_dir()
        self._load_referenced_files()
        return spell_spec_file

    def _validate_master_spell_file(self):
        """Validates that the master spell file contains all mandatory keys.
           Raises an exception if any mandatory key is missing.
        :return:
        """
        mandatory_keys = ['working_dir', 'iaas_spell', 'caas_spell', 'pods_spell']
        missing_keys = [key for key in mandatory_keys if key not in self.spell_spec_file]

        if missing_keys:
            raise ValueError(
                f"Master spell file is missing mandatory keys: {', '.join(missing_keys)}")

    def update_absolute_dir(self):
        """Resolve the absolute dir and update absolute_dir.
        :return:
        """
        if self.spell_spec_file is None:
            self._read_spell_file()

        if self.absolute_dir is None:
            working_dir = self.spell_spec_file.get("working_dir", "")
            expanded_dir = os.path.expandvars(working_dir)
            self.absolute_dir = Path(expanded_dir).resolve()

    def _load_referenced_files(
            self
    ) -> None:
        """
        Loads the mandatory spells referenced JSON files
        (iaas_spell, caas_spell, pods_spell) each spell has a type
        'type' and we infer from spell type it key.

        field within each file, and updates the spell_spec_file dictionary to include these
        configurations under keys that match their specified type.
        """
        if self.absolute_dir is None:
            working_dir = self.spell_spec_file.get("working_dir", "")
            expanded_dir = os.path.expandvars(working_dir)
            self.absolute_dir = Path(expanded_dir).resolve()

        for key in self.__mandatory_spells:
            referenced_file_path = self.spell_spec_file.get(key)
            if referenced_file_path:
                file_path = self.absolute_dir / referenced_file_path
                if file_path.exists():
                    with file_path.open('r') as file:
                        content = json.load(file)
                        if 'type' not in content:
                            raise InvalidSpellSpec(f"No valid 'type' specified in {file_path}, file ignored.")
                        config_type = content.get("type")
                        if config_type.upper() in SpellType.__members__:
                            _config_type = SpellType[config_type.upper()]
                            validator = self.spell_validators.get(_config_type)
                            if validator:
                                validator(content, self.absolute_dir)
                                self.spell_spec_file[config_type] = content
                            else:
                                raise InvalidSpellSpec(f"No validator found for type '{config_type}'")
                            self.spell_spec_file[config_type] = content
                        else:
                            raise InvalidSpellSpec(f"No valid 'type' specified in {file_path}, file ignored.")
                else:
                    raise InvalidSpellSpec(f"Referenced spell file {file_path} not found.")

    def get_referenced_config(
            self,
            config_name: str
    ) -> Dict[str, Any]:
        """Retrieves a configuration dictionary for the specified config_name.
        """
        return self.spell_spec_file.get(config_name, {})

    def master_spell(
            self
    ) -> Dict[str, Any]:
        """Returns master spells
        :return:a Dictionary of master spells that hols spec for all spells.
        """
        self.update_absolute_dir()
        return self.spell_spec_file

    def caas_spells(
            self
    ) -> Dict[str, Any]:
        """Returns pod spells
        :return: a Dictionary of master spells that hols spec for all spells.
        """
        if self.spell_spec_file is None:
            self.master_spell()

        return self.spell_spec_file.get('caas', {})

    def iaas_spells(
            self
    ) -> Dict[str, Any]:
        """Returns iaas spell specification
        :return: a Dictionary of master spells that hols spec for all spells.
        """
        if self.spell_spec_file is None:
            self.master_spell()

        return self.spell_spec_file.get('iaas', {})

    def pods_spells(
            self
    ) -> Dict[str, Any]:
        """Method return pod specification
        :return:
        """
        if self.spell_spec_file is None:
            self.master_spell()

        return self.spell_spec_file.get('pods', {})

    def pods_file(self) -> List[str]:
        """
        Method returns list of pod spec files that part of pods spell.
        :return: A list containing pod specifications.
        """
        if self.spell_spec_file is None:
            self._read_spell_file()

        pods_config = self.get_referenced_config('pods')
        pod_specs_files = []
        for key, config in pods_config.items():
            if isinstance(config, dict) and config.get("type") == "pod":
                if 'pod_spec_file' in config and self.absolute_dir:
                    pod_spec_path = (self.absolute_dir / config['pod_spec_file']).resolve()
                    pod_specs_files.append(str(pod_spec_path))

        return pod_specs_files

    @staticmethod
    def validate_iaas_config(
            iaas_config: Dict[str, Any],
            base_path: Union[str, Path]
    ) -> None:
        """
        Validates the IaaS configuration based on the specified IaaS type.
        Specifically, for VMware IaaS type, it checks for the presence of
        'host', 'username', and 'password' keys.

        :param iaas_config: The IaaS configuration dictionary.
        :param base_path:
        :raises ValueError: If the required keys are missing for the specified IaaS type.
        """
        iaas_type = iaas_config.get("iaas_type", "").upper()
        try:
            iaas_type_enum = IaasSType[iaas_type]
        except KeyError:
            raise ValueError(f"Unsupported IaaS type: {iaas_type}")

        if iaas_type_enum == IaasSType.VMWARE:
            required_keys = ['host', 'username', 'password']
            missing_keys = [k for k in required_keys if k not in iaas_config]
            if missing_keys:
                raise ValueError(f"VMware IaaS config is missing mandatory keys: {', '.join(missing_keys)}")
        else:
            raise ValueError(f"Unknown iaas type spell")

    @staticmethod
    def validate_caas_config(
            content: Dict[str, Any],
            base_path: Union[str, Path]
    ) -> None:
        """
        Validates the caas configuration based on the specified CaaS type.
        Specifically, for VMware IaaS type, it checks for the presence of
        'host', 'username', and 'password' keys.

        :param base_path:
        :param content: The IaaS configuration dictionary.
        :raises ValueError: If the required keys are missing for the specified IaaS type.
        """
        required_keys = ['username', 'password']
        missing_keys = [k for k in required_keys if k not in content]
        if missing_keys:
            raise ValueError(
                "CaaS config is missing mandatory keys: {', '.join(missing_keys)}")

    @staticmethod
    def validate_pods_config(
            content: Dict[str, Any],
            base_path: Union[str, Path]
    ) -> None:
        """Validates the pods spell specs.
        :param content: The pods configuration dictionary.
        :param base_path: The base path for resolving relative file paths.
        :raises ValueError: If the required keys are missing for the specified IaaS type.
        """
        _pod_names = set()
        for k in content:
            if (isinstance(content[k], dict) and 'type'
                    in content[k] and content[k]['type'] == "pod"):
                if "pod_name" not in content[k]:
                    raise InvalidSpellSpec(f"Pod config is missing mandatory keys: pod_name")
                pod_name = content[k].get("pod_name")
                if pod_name in _pod_names:
                    raise InvalidSpellSpec(f"Duplicate 'pod_name' found: {pod_name}")
                SpellSpecs.validate_pod_config(content[k], base_path)
                _pod_names.add(pod_name)

    @staticmethod
    def update_pod_yaml(
            pod_spec_file: Union[str, Path],
            pod_config: Dict[str, Any]
    ):
        """
        Updates the 'metadata.name' field in a Kubernetes pod YAML file
        based on the 'pod_name' specified in the pod_config.

        :param pod_spec_file: Path to the Kubernetes pod spec YAML file.
        :param pod_config: The pod configuration dictionary from the spell spec.
        """
        try:
            with pod_spec_file.open('r') as file:
                pod_yaml = yaml.safe_load(file)

            pod_yaml['metadata']['name'] = pod_config['pod_name']
            with pod_spec_file.open('w') as file:
                yaml.safe_dump(pod_yaml, file)

        except yaml.YAMLError as exc:
            raise ValueError(f"Error updating YAML file {pod_spec_file}: {exc}")

    @staticmethod
    def validate_pod_config(
            pod_spell: Dict[str, Any],
            base_path: Union[str, Path]
    ) -> None:
        """
        Validates a single pod configuration.

        :param pod_spell: The pod configuration dictionary.
        :param base_path: The base path for resolving relative file paths.
        :raises InvalidSpellSpec: If required keys are missing or the YAML file is invalid.
        :raises InvalidPodSpec: If pod spec point to an invalid kubernetes POD spec file.
        """
        required_keys = ['pod_spec_file', 'pod_name', 'type', 'role']
        missing_keys = [key for key in required_keys if key not in pod_spell]
        if missing_keys:
            raise InvalidSpellSpec(f"Pod config is missing mandatory keys: {', '.join(missing_keys)}")

        pod_spec_file = base_path / pod_spell['pod_spec_file']
        if not pod_spec_file.exists():
            raise InvalidSpellSpec(f"Pod spec file does not exist: {pod_spec_file}")

        # update
        SpellSpecs.update_pod_yaml(pod_spec_file, pod_spell)

        try:
            with pod_spec_file.open('r') as file:
                logging.debug("Validating file", pod_spec_file)
                pod_yaml = yaml.safe_load(file)
                if pod_yaml.get("kind") != "Pod":
                    raise InvalidPodSpec(
                        f"The file {pod_spec_file} is not a valid Pod spec file. "
                        f"'kind: Pod' is expected.")
        except yaml.YAMLError as exc:
            raise InvalidSpellSpec(f"Error parsing YAML file {pod_spec_file}: {exc}")