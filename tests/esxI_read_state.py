import json
import os
from ipaddress import ip_address
import unittest
from unittest.mock import patch

from tests.extended_test_case import ExtendedTestCase
from tests.test_utils import (
    write_temp_kubeconfig,
    write_bad_temp_kubeconfig,
    sample_control_node,
    sample_worker_node
)
from warlock.esxi_state import EsxiState
from warlock.ssh_operator import SSHOperator


def verify_values_seq(data):
    values = list(data.values())
    numeric_values = [v for v in values if isinstance(v, int)]
    sorted_values = sorted(numeric_values)
    for i in range(len(sorted_values)):
        if sorted_values[i] != i:
            return False
    return True


class TestsEsxiState(ExtendedTestCase):
    def setUp(self):
        """
        :return:
        """
    def test_init_from_defaults(self):
        runner = SSHOperator(remote_hosts=["127.0.0.1"])
        self.assertEqual(runner._username, "capv", "username should be capv")
        self.assertIsNone(runner._password, "password should be none")
        self.assertFalse(runner._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

    def test_init_password_auth(self):
        runner = SSHOperator(remote_hosts=["127.0.0.1"], username="root", password="pass", is_password_auth_only=True)
        self.assertIsNotNone(runner, "ssh runner should be none")
        self.assertEqual(runner._username, "root", "username should be capv")
        self.assertEqual(runner._password, "pass", "username should be capv")
        self.assertFalse(runner._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

    def test_init_ssh_key_auth(self):
        runner = SSHOperator(remote_hosts=["127.0.0.1"], username="root", password="pass", is_password_auth_only=False)
        self.assertIsNotNone(runner, "ssh runner should be none")
        self.assertEqual(runner._username, "root", "username should be capv")
        self.assertEqual(runner._password, "pass", "username should be capv")
        self.assertFalse(runner._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")
