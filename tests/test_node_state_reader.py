from tests.extended_test_case import ExtendedTestCase
from warlock.states.node_state_reader import NodeStateReader
import json
import os
import random

import numpy as np

from tests.extended_test_case import ExtendedTestCase
from tests.test_utils import (
    generate_sample_adapter_list_xml,
    generate_sample_vm_list,
    generate_nic_data
)
from warlock.operators.ssh_operator import SSHOperator


class TestsEsxiStateReader(ExtendedTestCase):

    def setUp(self):

        self.node_ip = '198.19.57.189'
        self.node_username = 'root'
        self.node_password = 'VMware1!'

        os.environ['NODE_IP'] = '198.19.57.189'
        os.environ['NODE_USERNAME'] = 'capv'
        os.environ['NODE_PASSWORD'] = 'VMware1!'

        self.node_address = '198.19.57.189'
        self.username = 'capv'
        self.password = 'VMware1!'

    def test_can_init_from_credentials(self):
        """
        Tests NodeStateReader constructors from args
        :return:
        """
        with NodeStateReader.from_optional_credentials(
                node_address=self.node_address,
                username=self.username,
                password=self.password
        ) as node_host_state:
            self.assertEqual(node_host_state.node_address, self.node_address)
            self.assertEqual(node_host_state.username, self.username)
            self.assertEqual(node_host_state.password, self.password)
            self.assertIsNotNone(node_host_state._ssh_operator)
            self.assertIsInstance(node_host_state._ssh_operator, SSHOperator)
            self.assertTrue(
                node_host_state._ssh_operator.has_active_connection(self.node_address),
                "remote host should be active"
            )
            self.assertTrue(
                len(node_host_state._ssh_operator._persistent_connections) == 1,
                "remote host should be active"
            )

    def test_can_read_pci(self):
        """
        Tests NodeStateReader constructors from args
        :return:
        """
        with NodeStateReader.from_optional_credentials(
                node_address=self.node_address,
                username=self.username,
                password=self.password
        ) as node_host_state:
            self.assertEqual(node_host_state.node_address, self.node_address)
            self.assertEqual(node_host_state.username, self.username)
            self.assertEqual(node_host_state.password, self.password)
            self.assertIsNotNone(node_host_state._ssh_operator)
            self.assertIsInstance(node_host_state._ssh_operator, SSHOperator)
            self.assertTrue(
                node_host_state._ssh_operator.has_active_connection(self.node_address),
                "remote host should be active"
            )
            self.assertTrue(
                len(node_host_state._ssh_operator._persistent_connections) == 1,
                "remote host should be active"
            )
            print(json.dumps(node_host_state.read_pci_devices(), indent=4))
