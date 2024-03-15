import json
import os

from tests.extended_test_case import ExtendedTestCase
from warlock.callbacks.callback_ring_tunner import CallbackRingTunner
from warlock.states.esxi_state_reader import EsxiStateReader
from warlock.generators.spell_generator import SpellGenerator


class TestsCallbackRingTunner(ExtendedTestCase):

    def setUp(self):
        """

        :return:
        """
        test_esxi_fqdn_env = os.getenv('ESXI_FQDNS')
        if test_esxi_fqdn_env:
            self.esxi_fqdns = test_esxi_fqdn_env.split(',')
        else:
            self.esxi_fqdns = [
                '10.252.80.107',
                '10.252.80.109'
            ]

        self.username = 'root'
        self.password = 'VMware1!'
        self.test_vms_substring = 'test-np'
        self.test_default_adapter_name = 'eth0'

        # we expect two hosts in env or we use
        # defaults
        self.args = [
            {
                self.esxi_fqdns[0]: [
                    {"nic": "vmnic0", "RX": 1024, "TX": 1024},
                    {"nic": "vmnic1", "RX": 1024, "TX": 1024},
                ],
                self.esxi_fqdns[1]: [
                    {"nic": "vmnic2", "RX": 1024, "TX": 1024},
                    {"nic": "vmnic3", "RX": 1024, "TX": 1024},
                ],
            },

            {
                self.esxi_fqdns[0]: [
                    {"nic": "vmnic0", "RX": 4096, "TX": 4096},
                    {"nic": "vmnic1", "RX": 4096, "TX": 4096},
                ],
                self.esxi_fqdns[1]: [
                    {"nic": "vmnic0", "RX": 4096, "TX": 4096},
                    {"nic": "vmnic1", "RX": 4096, "TX": 4096},
                ],
            },
        ]

        nic_configs = [
            {"nics": ["vmnic0", "vmnic1"], "RX": 1024, "TX": 1024},
            {"nics": ["vmnic0", "vmnic1"], "RX": 4096, "TX": 4096},
        ]

        self.generated_spec = SpellGenerator(hosts=self.esxi_fqdns).generate_ring_spec(nic_configs)

        self.esxi_states = []
        for esxi_fqdn in self.esxi_fqdns:
            self.esxi_states.append(EsxiStateReader.from_optional_credentials(
                esxi_fqdn=esxi_fqdn,
                username=self.username,
                password=self.password
            ))

        for esxi_state in self.esxi_states:
            self.assertTrue(esxi_state.is_active(), f"should be active after initialization")

    def tearDown(self):
        """
        :return:
        """
        for esxi_state in self.esxi_states:
            esxi_state.release()
        self.esxi_states = []

    def test_can_construct(self):
        """Test we can construct a callback.
        :return:
        """

        callback = CallbackRingTunner(self.args, self.esxi_states)
        self.assertEqual(callback.nic_rx_tx_map, self.args,
                         "nic_rx_tx_map should be initialized with provided args")

        # esxi_states_readers is correctly assigned
        self.assertEqual(callback.esxi_states_readers, self.esxi_states,
                         "esxi_states_readers should be initialized "
                         "with the provided EsxiStateReader instances")

        #  _sample_index is initialized as expected
        self.assertEqual(callback._sample_index, 0, "_sample_index should be initialized to 0")

        #  _initial_ring_size is an empty dictionary
        self.assertEqual(callback._initial_ring_size, {},
                         "_initial_ring_size should be initialized as an empty dictionary")

    def test_can_accept_spec_generated(self):
        """Test we can construct a callback form generated specs.
        :return:
        """

        callback = CallbackRingTunner(self.args, self.esxi_states)
        self.assertEqual(callback.nic_rx_tx_map, self.args,
                         "nic_rx_tx_map should be initialized with provided args")
        self.assertEqual(callback.esxi_states_readers, self.esxi_states,
                         "esxi_states_readers should be initialized "
                         "with the provided EsxiStateReader instances")
        self.assertEqual(callback._sample_index, 0, "_sample_index should be initialized to 0")
        self.assertEqual(callback._initial_ring_size, {},
                         "_initial_ring_size should be initialized as an empty dictionary")

    def test_constructor_edge_cases(self):
        """Test construction of CallbackRingTunner with edge case inputs."""
        # Attempt construction with empty lists
        try:
            callback = CallbackRingTunner([], [])
            self.assertIsInstance(callback, CallbackRingTunner, "Should handle empty lists without error.")
        except Exception as e:
            self.fail(f"Construction with empty lists should not raise an exception, but got: {e}")

        try:
            callback = CallbackRingTunner(None, None)
            self.fail("Construction with None should raise an exception.")
        except TypeError:
            pass  # we expected
        except Exception as e:
            self.fail(f"Construction with None should raise TypeError, but got: {e}")

    def test_edge_case_key_wrong(self):
        """
        Test construct valid esxi state reader but spec uses wrong host keys.
        Callback should raise an exception

        :return:
        """
        bad_args = [
            {
                "10.252.80.x": [
                    {"nic": "vmnic0", "RX": 1024, "TX": 1024},
                    {"nic": "vmnic1", "RX": 1024, "TX": 1024},
                ],
                "10.252.80.x": [
                    {"nic": "vmnic2", "RX": 1024, "TX": 1024},
                    {"nic": "vmnic3", "RX": 1024, "TX": 1024},
                ],
            },

            {
                "10.252.80.x": [
                    {"nic": "vmnic0", "RX": 4096, "TX": 4096},
                    {"nic": "vmnic1", "RX": 4096, "TX": 4096},
                ],
                "10.252.80.x": [
                    {"nic": "vmnic0", "RX": 4096, "TX": 4096},
                    {"nic": "vmnic1", "RX": 4096, "TX": 4096},
                ],
            },
        ]

        with self.assertRaises(ValueError):
            _ = CallbackRingTunner(bad_args, self.esxi_states)

    def test_on_iaas_prepare(self):
        """
        Test on prepare we memorize old value.
        :return:
        """
        expected_nics_by_host = {
            self.esxi_fqdns[0]: {"vmnic0", "vmnic1"},
            self.esxi_fqdns[1]: {"vmnic0", "vmnic1", "vmnic2", "vmnic3"}
        }

        callback = CallbackRingTunner(self.args, self.esxi_states)
        callback.on_iaas_prepare()

        for host, expected_nics in expected_nics_by_host.items():
            recorded_nics = callback._initial_ring_size.get(host, [])
            self.assertEqual(len(recorded_nics), len(expected_nics),
                             f"Host {host} does not have the expected "
                             f"number of NIC configurations.")

            for nic_tuple in recorded_nics:
                self.assertIn(nic_tuple[0], expected_nics,
                              f"NIC {nic_tuple[0]} for host {host} was not expected.")
                self.assertIsInstance(nic_tuple[1], int,
                                      f"RX value for NIC {nic_tuple[0]} "
                                      f"in host {host} is not an integer.")
                self.assertIsInstance(nic_tuple[2], int,
                                      f"TX value for NIC {nic_tuple[0]}"
                                      f" in host {host} is not an integer.")

    def test_can_sample_value(self):
        """
        Test construct valid esxi state reader but spec uses wrong host keys.

        Callback should raise an exception

        :return:
        """

        expected_nics_by_host = {
            self.esxi_fqdns[0]: {"vmnic0", "vmnic1"},
            self.esxi_fqdns[1]: {"vmnic0", "vmnic1", "vmnic2", "vmnic3"}
        }

        expected_values_first_cycle = [
            {
                '10.252.80.107': [('vmnic0', 1024, 1024), ('vmnic1', 1024, 1024)],
                '10.252.80.109': [('vmnic2', 1024, 1024), ('vmnic3', 1024, 1024)]},

            {
                '10.252.80.107': [('vmnic0', 4096, 4096), ('vmnic1', 4096, 4096)],
                '10.252.80.109': [('vmnic0', 4096, 4096), ('vmnic1', 4096, 4096)]
            }
        ]

        callback = CallbackRingTunner(self.args, self.esxi_states)

        for expected in expected_values_first_cycle:
            value_for_mutate = callback.sample_value()
            self.assertEqual(value_for_mutate, expected)

        # keep going sine we restart
        for expected in expected_values_first_cycle:
            value_for_mutate = callback.sample_value()
            self.assertEqual(value_for_mutate, expected)

    def test_empty_configuration_list(self):
        """Test that the class handles an empty configuration list without errors.
        """
        callback = CallbackRingTunner([], self.esxi_states)
        sampled_value = callback.sample_value()
        self.assertEqual(sampled_value, {},
                         "Expected sample_value to return an empty"
                         "dictionary for empty configuration.")

    def test_can_iaas_mutate_begin(self):
        """Test can mutate env
        """
        callback = CallbackRingTunner(self.args, self.esxi_states)
        callback.on_iaas_spell_begin()
        exec_plan = callback.get_dry_run_plan()

    def test_on_release(self):
        """Test can mutate env
        """
        callback = CallbackRingTunner(self.args, self.esxi_states)
        callback.on_iaas_spell_begin()
        callback.on_iaas_release()

    def test_full_cycle(self):
        """
        :return:
        """
        callback = CallbackRingTunner(self.args, self.esxi_states)
        callback.on_iaas_prepare()
        # run each scenario
        for _ in self.args:
            callback.on_iaas_spell_begin()
        callback.on_iaas_release()
        exec_plan = callback.get_dry_run_plan()
        print(json.dumps(exec_plan, indent=4))





