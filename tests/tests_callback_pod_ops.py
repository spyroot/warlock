import json
import os

from tests.extended_test_case import ExtendedTestCase
from warlock.callback_pod_operator import CallbackPodsOperator
from warlock.callback_ring_tunner import CallbackRingTunner
from warlock.esxi_state import EsxiStateReader
from warlock.spell_generator import SpellGenerator


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

        self.spell_spec = "../spell.json"

    def tearDown(self):
        """
        :return:
        """
        pass

    def test_can_construct(self):
        """Test we can construct a callback.
        :return:
        """
        callback = CallbackPodsOperator()

    def test_on_scenario_begin(self):
        """Test we can construct a callback.
        :return:
        """
        callback = CallbackPodsOperator(self.spell_spec)
        # callback.on_scenario_begin()
