import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Union, Optional

import yaml

from tests.extended_test_case import ExtendedTestCase
from tests.test_utils import remove_key_from_pod_spec
from warlock.spell_specs import SpellSpecs, InvalidSpellSpec, InvalidPodSpec


class TestSpellFileReader(ExtendedTestCase):

    def update_value_in_place(
            self,
            file_path: Union[str, Path],
            key: str,
            new_value: any,
            sub_key: Optional[str] = None,
    ) -> None:
        """For test routine we need mutate , create incorrect spell spec files.
         Update or remove a specific key in a JSON file, in place.
         If new_value is None, the key is removed from the JSON structure.
         Otherwise, the key is updated with the new value.

        :param sub_key:  we don't do full recurse search ,so it second layer in json key.
        :param file_path: Path to the JSON file.
        :param key: The key in the JSON file to update.
        :param new_value: The new value to assign to the key.
        """
        with open(file_path, 'r+') as file:
            spell_data = json.load(file)
            if sub_key:
                if sub_key not in spell_data:
                    raise ValueError(f"Sub-key '{sub_key}' not found in the file.")
                nested_data = spell_data[sub_key]
                if new_value is None:
                    nested_data.pop(key, None)
                else:
                    nested_data[key] = new_value
            else:
                if new_value is None:
                    spell_data.pop(key, None)
                else:
                    spell_data[key] = new_value

            file.seek(0)
            json.dump(spell_data, file, indent=4)
            file.truncate()

        # we check that we updated correct value
        with open(file_path, 'r') as file:
            updated_data = json.load(file)
            if sub_key:
                if sub_key not in updated_data:
                    self.fail(f"Sub-key '{sub_key}' not found after update.")
                updated_data = updated_data[sub_key]

            if new_value is None:
                self.assertFalse(key in updated_data,
                                 f"Expected '{key}' "
                                 f"to be removed from '{sub_key}' section, but it is still present.")
            else:
                updated_value = updated_data.get(key, None)
                self.assertEqual(updated_value, new_value,
                                 f"Expected '{key}' in '{sub_key}' "
                                 f"section to be updated to {new_value}, but found {updated_value}")

    def create_temp_specs(self):
        """Create copy of original valid spec in temp dir, so we can
        mutate.
        :return:
        """

        self.temp_dir = Path(tempfile.mkdtemp()).resolve().absolute()

        self.original_spell_files = [
            Path("../spell.json").resolve().absolute(),
            Path("../spell_caas.json").resolve().absolute(),
            Path("../spell_iaas.json").resolve().absolute(),
            Path("../spell_pods.json").resolve().absolute(),
        ]

        self.original_pod_specs_dir = Path("../pod_spec").resolve().absolute()
        for spell_file in self.original_spell_files:
            shutil.copy(spell_file, self.temp_dir)

        temp_pod_specs_dir = (self.temp_dir / "pod_spec").resolve().absolute()
        shutil.copytree(self.original_pod_specs_dir, temp_pod_specs_dir)

        self.update__spell_file = self.temp_dir / "spell.json"
        self.update_value_in_place(
            self.update__spell_file, key="working_dir", new_value=str(self.temp_dir))

        self._test_spell_iaas_file = (self.temp_dir / "spell_iaas.json").resolve().absolute()
        self._test_spell_caas_file = (self.temp_dir / "spell_caas.json").resolve().absolute()
        self._test_spell_pods_file = (self.temp_dir / "spell_pods.json").resolve().absolute()

    def setUp(self):
        """
        :return:
        """
        self.spell_spec = "../spell.json"
        self.temp_dir = Path(tempfile.mkdtemp()).resolve().absolute()
        self.create_temp_specs()

    def tearDown(self):
        """
        :return:
        """
        abs_tmp_dir = Path(self.temp_dir).resolve().absolute()
        # os.rmdir(abs_tmp_dir)

    def create_spell_file(self, content):
        """Helper function to create a temporary spell file."""
        temp_spell_file_path = os.path.join(self.temp_dir, 'temp_spell.json')
        with open(temp_spell_file_path, 'w') as temp_spell_file:
            json.dump(content, temp_spell_file)
        return temp_spell_file_path

    def test_missing_mandatory_keys(self):
        """Test handling when mandatory keys are missing in the master spell file."""
        content = {
            # Omitting 'working_dir', 'iaas_spell', 'caas_spell', 'pods_spell'
        }
        spell_file_path = self.create_spell_file(content)
        self.assertTrue(Path(spell_file_path).exists(), "file should be created")
        with self.assertRaises(ValueError) as context:
            _ = SpellSpecs(spell_file_path)

        self.assertTrue("missing mandatory keys" in str(context.exception))

    def test_can_construct(self):
        """Test we can construct a from default location.
        :return:
        """
        spell_spec = SpellSpecs(self.spell_spec)
        spell_spec.update_absolute_dir()
        self.assertTrue(spell_spec.absolute_dir.is_absolute(), "The path is not absolute.")
        self.assertTrue(spell_spec.absolute_dir.exists(), "The path does not exist.")
        self.assertTrue(spell_spec.absolute_dir.is_dir(), "The path is not a directory.")

    def test_init_bad_path(self):
        """Test we can construct a from default location.
        :return:
        """
        with self.assertRaises(FileNotFoundError):
            _ = SpellSpecs("bad_path")

    def test_can_construct_custom_path(self):
        """Test we can construct from custom temp working dir.
        :return:
        """
        spell_spec = SpellSpecs(self.update__spell_file)
        spell_spec.update_absolute_dir()
        self.assertTrue(spell_spec.absolute_dir.is_absolute(), "The path is not absolute.")
        self.assertTrue(spell_spec.absolute_dir.exists(), "The path does not exist.")
        self.assertTrue(spell_spec.absolute_dir.is_dir(), "The path is not a directory.")
        spells_spec = spell_spec.master_spell()
        mandatory_keys = ["working_dir", "pods", "iaas", "caas"]
        for k in mandatory_keys:
            self.assertIn(k, spells_spec, f"The '{k}' configuration should be present")

    def test_can_parse_master_spell(self):
        """Test we parse all files from custom dir.
        :return:
        """
        spell_spec = SpellSpecs(self.spell_spec)
        data = spell_spec.master_spell()
        self.assertIn('pods', data, "The 'pods' configuration should be present")
        self.assertIn('iaas', data, "The 'iaas' configuration should be present")
        self.assertIn('caas', data, "The 'caas' configuration should be present")

    def test_can_resolve_working_dir(self):
        """Test we can construct a callback.
        :return:
        """
        spell_spec = SpellSpecs(self.update__spell_file)
        data = spell_spec.master_spell()
        self.assertIn('pods', data, "The 'pods' configuration should be present")
        self.assertIn('iaas', data, "The 'iaas' configuration should be present")
        self.assertIn('caas', data, "The 'caas' configuration should be present")
        self.assertIn('working_dir', data, "The 'working_dir' configuration should be present")
        self.assertTrue(data['working_dir'] == str(self.temp_dir), "invalid data")

    def test_can_read_iaas_spell(self):
        """Test we can construct a callback.
        :return:
        """
        files = [self.spell_spec, self.update__spell_file]
        for f in files:
            spell_spec = SpellSpecs(f)
            data = spell_spec.iaas_spells()
            self.assertIn('type', data, "The 'type' configuration should be present")
            self.assertIn('username', data, "The 'username' configuration should be present")
            self.assertIn('host', data, "The 'host' configuration should be present")

    def test_can_read_caas_spell(self):
        """Test we can construct a callback.
        :return:
        """
        files = [self.spell_spec, self.update__spell_file]
        for f in files:
            spell_spec = SpellSpecs(f)
            spell = spell_spec.caas_spells()
            self.assertIn('type', spell, "The 'type' configuration should be present")
            self.assertIn('username', spell, "The 'username' configuration should be present")
            self.assertIn('password', spell, "The 'host' configuration should be present")
            self.assertIn('tuned_profile', spell, "The 'tuned_profile' configuration should be present")

    def test_can_read_pods_spell(self):
        """Test we can construct a callback.
        :return:
        """
        spell_spec = SpellSpecs(self.spell_spec)
        spell = spell_spec.pods_spells()
        self.assertIn('type', spell, "The 'type' configuration should be present")

    def test_can_parse_pod_spell_files(self):
        """Test that the pods_file method returns correct pod specification files."""
        spell_spec = SpellSpecs(self.spell_spec)
        spell_files = spell_spec.pods_file()

        self.assertEqual(len(spell_files), 2, "Expected two entries in the pod spec files list.")
        expected_server_spec = os.path.join(spell_spec.absolute_dir, 'pod_spec/iperf_server.yaml')
        expected_client_spec = os.path.join(spell_spec.absolute_dir, 'pod_spec/iperf_client.yaml')
        normalized_spell_files = [os.path.normpath(path) for path in spell_files]
        expected_server_spec = os.path.normpath(expected_server_spec)
        expected_client_spec = os.path.normpath(expected_client_spec)

        self.assertIn(expected_server_spec, normalized_spell_files, "Server pod spec file is missing from the list.")
        self.assertIn(expected_client_spec, normalized_spell_files, "Client pod spec file is missing from the list.")

    def test_edge_case_no_iaas_spell(self):
        """Test validates master spell should have iaas_spell.
        :return:
        """
        self.update_value_in_place(self.update__spell_file, "iaas_spell", None)
        with self.assertRaises(ValueError) as _:
            _ = SpellSpecs(self.update__spell_file)

    def test_edge_case_no_caas_spell(self):
        """Test validates master spell should have caas_spell.
        :return:
        """
        self.update_value_in_place(self.update__spell_file, "caas_spell", None)
        with self.assertRaises(ValueError) as _:
            _ = SpellSpecs(self.update__spell_file)

    def test_edge_case_no_pods_spell(self):
        """Test validates master spell should have pods_spell.
        :return:
        """
        self.update_value_in_place(self.update__spell_file, "pods_spell", None)
        with self.assertRaises(ValueError) as _:
            _ = SpellSpecs(self.update__spell_file)

    def test_missing_iaas_key(self):
        """Test validates iaas spell should have set of mandatory keys
        and optional keys.
        :return:
        """
        required_keys = ['host', 'username', 'password']
        for k in required_keys:
            # create copy , pop key,
            self.create_temp_specs()
            self.update_value_in_place(self._test_spell_iaas_file, k, None)
            with self.assertRaises(ValueError) as _:
                _ = SpellSpecs(self.update__spell_file)

    def test_ignore_iaas_bad_type(self):
        """Test validates iaas spell should have a type.
        :return:
        """
        self.create_temp_specs()
        self.update_value_in_place(self._test_spell_iaas_file, "type", "bad")
        with self.assertRaises(InvalidSpellSpec) as _:
            _ = SpellSpecs(self.update__spell_file)

    def test_missing_caas_key(self):
        """Test validates caas spell file, in case if mandatory missing keys
        should raise an exception.
        :return:
        """
        required_keys = ['username', 'password']
        for k in required_keys:
            # create copy , pop key,
            self.create_temp_specs()
            self.update_value_in_place(self._test_spell_caas_file, k, None)
            with self.assertRaises(ValueError) as _:
                _ = SpellSpecs(self.update__spell_file)

    def test_missing_pod_spec_key(self):
        """Test validates pod spell file, in case if mandatory missing keys
        should raise an exception.
        :return:
        """
        required_keys = ['pod_spec_file', 'pod_name', 'role']
        for k in required_keys:
            # at each iteration we copy master ( valid , pop key and check)
            self.create_temp_specs()
            self.update_value_in_place(self._test_spell_pods_file, k, None, sub_key="client01")
            with self.assertRaises(InvalidSpellSpec,
                                   msg=f"mandatory key {k} is missing, must raise an exception") as _:
                _ = SpellSpecs(self.update__spell_file)

    def test_bad_pod_spec_file(self):
        """Test validates pod spell file, in case if mandatory missing keys
        should raise an exception.
        :return:
        """
        self.update_value_in_place(
            self._test_spell_pods_file, "pod_spec_file", "/bad/file", sub_key="client01")

        with self.assertRaises(InvalidSpellSpec):
            _ = SpellSpecs(self.update__spell_file)

    def test_duplicate_pod_names(self):
        """Test validates pod spell file, with duplicate pod names
        :return:
        """
        self.update_value_in_place(
            self._test_spell_pods_file, "pod_name", "test", sub_key="client01")
        self.update_value_in_place(
            self._test_spell_pods_file, "pod_name", "test", sub_key="server01")

        with self.assertRaises(InvalidSpellSpec):
            _ = SpellSpecs(self.update__spell_file)

    def test_bad_pod_yaml_file(self):
        """Test validates pod spell point to valid kubernetes pod spec.
        :return:
        """
        self.create_temp_specs()
        spec = SpellSpecs(self.update__spell_file)
        pod_files = spec.pods_file()
        remove_key_from_pod_spec(Path(pod_files[0]), "kind")

        # try to load again
        with self.assertRaises(InvalidPodSpec):
            _ = SpellSpecs(self.update__spell_file)