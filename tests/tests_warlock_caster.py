import os

from tests.extended_test_case import ExtendedTestCase
from warlock.callbacks.callback_dummy import DummyCallback
from warlock.callbacks.callback_pod_operator import CallbackPodsOperator
from warlock.callbacks.callback_ring_tunner import CallbackRingTunner
from warlock.states.esxi_state_reader import EsxiStateReader
from warlock.generators.spell_generator import SpellGenerator
from warlock.warlock import WarlockSpellCaster


class TestWarlockPower(ExtendedTestCase):

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

    def test_can_construct_spell_caster(self):
        """
        :return:
        """
        callback1 = CallbackRingTunner(self.args, self.esxi_states)
        callback2 = DummyCallback()
        callback3 = CallbackPodsOperator()
        callbacks = [callback1, callback2]
        warlock = WarlockSpellCaster(callbacks=callbacks)
        warlock.cast_spell()
