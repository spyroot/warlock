import os
import shutil
import subprocess
from unittest.mock import patch
import paramiko
from paramiko.ssh_exception import SSHException


from tests.containerized_test_case import (
    ContainerizedTestCase
)

from warlock.ssh_operator import (
    SSHOperator,
    PublicKeyNotFound
)


class TesSshRunner(ContainerizedTestCase):

    def backup_ssh_pub_key(self):
        """Back up the existing SSH public key within the same directory.
        i.e. default pub key"""
        self.default_pub_key_path = os.path.expanduser('~/.ssh/id_rsa.pub')
        self.backup_pub_key_path = f"{self.default_pub_key_path}.backup"

        if os.path.exists(self.default_pub_key_path) and not os.path.exists(self.backup_pub_key_path):
            shutil.copy2(self.default_pub_key_path, self.backup_pub_key_path)

    def restore_ssh_pub_key(self):
        """Restore the SSH public key back to its default location."""
        if os.path.exists(self.backup_pub_key_path):
            shutil.copy2(self.backup_pub_key_path, self.default_pub_key_path)
            os.remove(self.backup_pub_key_path)
        elif os.path.exists(self.default_pub_key_path):
            pass
        else:
            # Handle the case where both the original and backup keys are missing.
            pass

    def setUp(self):
        """Set up the environment for the tests."""
        self.backup_ssh_pub_key()

    def tearDown(self):
        """Clean up after tests."""
        self.restore_ssh_pub_key()

    def test_init_from_defaults(self):
        """Test construct from default"""
        runner = SSHOperator(remote_hosts=["127.0.0.1"], password="test")
        self.assertEqual(runner._username, "capv", "username should be capv")
        self.assertEqual(runner._password, "test", "password should be test")
        self.assertFalse(runner._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

    def test_init_password_auth(self):
        """Test Construct for pass auth"""
        runner = SSHOperator(remote_hosts=["127.0.0.1"],
                             username="root", password="pass", is_password_auth_only=True)
        self.assertIsNotNone(runner, "ssh runner should be none")
        self.assertEqual(runner._username, "root", "username should be capv")
        self.assertEqual(runner._password, "pass", "username should be capv")
        self.assertFalse(runner._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

    def test_init_ssh_key_auth(self):
        """Test construct for ssh key auth"""
        runner = SSHOperator(
            remote_hosts=[f"127.0.0.1:{self.ssh_port}"],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        )
        self.assertIsNotNone(runner, "ssh runner should be none")
        self.assertEqual(runner._username, self.ssh_user, f"username should be {self.ssh_user}")
        self.assertEqual(runner._password, self.ssh_pass, f"password should be {self.ssh_pass}")
        self.assertFalse(runner._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

    def test_init_ssh_key_auth_no_key_error(self):
        """Test simulate a case if no public key present"""
        self.backup_ssh_pub_key()
        if os.path.exists(self.default_pub_key_path):
            os.remove(self.default_pub_key_path)
        try:
            with self.assertRaises(PublicKeyNotFound):
                _ = SSHOperator(
                    remote_hosts=["127.0.0.1"],
                    username="test", password="test",
                    is_password_auth_only=False
                )
        finally:
            self.restore_ssh_pub_key()

    def test_initial_ssh_key_auth_prompt(self):
        """Test does initial ssh pub key copy """

        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        runner = SSHOperator(
            remote_hosts=[f"127.0.0.1:{self.ssh_port}"],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        )

        self.assertIsNotNone(runner, "ssh runner should be none")
        self.assertEqual(runner._username, self.ssh_user, f"username should be {self.ssh_user}")
        self.assertEqual(runner._password, self.ssh_pass, f"password should be {self.ssh_pass}")
        self.assertFalse(runner._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

        # we check server side
        docker_command = f"docker exec {self.container_id} ls /home/{self.ssh_user}/.ssh/"
        result = subprocess.run(docker_command, shell=True, capture_output=True, text=True)
        self.assertIn('id_rsa', result.stdout, "id_rsa file should be present")
        self.assertIn('id_rsa.pub', result.stdout, "id_rsa.pub file should be present")

    def test_connect_and_check_state(self):
        """Test does initial ssh pub key copy """
        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"

        ssh_operator = SSHOperator(
            remote_hosts=[_host],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        )

        self.assertIsNotNone(ssh_operator, "ssh runner should be none")
        self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
        self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
        self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

        self.assertIn(_host, ssh_operator._persistent_connections)
        self.assertIsInstance(ssh_operator._persistent_connections[_host], paramiko.SSHClient)

    def test_reuse_existing(self):
        """Test check that we re-use existing"""
        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"

        ssh_operator = SSHOperator(
            remote_hosts=[_host],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        )

        self.assertIsNotNone(ssh_operator, "ssh runner should be none")
        self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
        self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
        self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

        self.assertIn(_host, ssh_operator._persistent_connections)
        self.assertIsInstance(ssh_operator._persistent_connections[_host], paramiko.SSHClient)

        connection = ssh_operator.get_ssh_connection(_host)
        self.assertIs(connection, ssh_operator._persistent_connections[_host], "Connection should be reused")
        connection2 = ssh_operator.get_ssh_connection(_host)
        self.assertIs(connection2, ssh_operator._persistent_connections[_host], "Connection should be reused")
        self.assertIs(connection2, connection, "Connection should be reused")

    def test_push_and_execute_cmd(self):
        """Test does initial ssh pub key copy """

        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"

        ssh_operator = SSHOperator(
            remote_hosts=[_host],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        )

        self.assertIsNotNone(ssh_operator, "ssh runner should be none")
        self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
        self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
        self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

        output, exit_code, _ = ssh_operator.run(_host, "echo 'test'")
        self.assertEqual(output, 'test', f"output should be test")
        self.assertEqual(exit_code, 0, f"exit code should be 0")

        output, exit_code, execution_time = ssh_operator.run(_host, "non_existing_command")
        self.assertEqual(output, "", "Output should be empty")
        self.assertNotEqual(exit_code, 0, "Exit code should not be zero")
        self.assertGreater(execution_time, 0, "Execution time should be greater than zero")

    def test_push_and_execute_complex(self):
        """Test does initial ssh pub key copy """
        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"

        ssh_operator = SSHOperator(
            remote_hosts=[_host],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        )

        self.assertIsNotNone(ssh_operator, "ssh runner should be none")
        self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
        self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
        self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

        command = 'echo "complex command with pipe symbol" | grep "pipe"'
        output, exit_code, execution_time = ssh_operator.run(_host, command)
        self.assertIn("pipe", output, "Output should contain 'pipe'")
        self.assertEqual(exit_code, 0, "Exit code should be zero")
        self.assertGreater(execution_time, 0, "Execution time should be greater than zero")

    def test_push_and_execute_complex2(self):
        """Test does initial ssh pub key copy """
        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"

        ssh_operator = SSHOperator(
            remote_hosts=[_host],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        )

        self.assertIsNotNone(ssh_operator, "ssh runner should be none")
        self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
        self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
        self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

        command = 'echo "complex command with pipe symbol" | grep "pipe"'
        output, exit_code, execution_time = ssh_operator.run(_host, command)
        self.assertIn("pipe", output, "Output should contain 'pipe'")
        self.assertEqual(exit_code, 0, "Exit code should be zero")
        self.assertGreater(execution_time, 0, "Execution time should be greater than zero")

        command = 'echo "$PATH"'
        output, exit_code, execution_time = ssh_operator.run(_host, command)
        self.assertIsNotNone(output, "Output should not be None")
        self.assertIn("/", output, "Output should contain '/' symbols")
        self.assertEqual(exit_code, 0, "Exit code should be zero")
        self.assertGreater(execution_time, 0, "Execution time should be greater than zero")

        script_content = '''\
        #!/bin/bash

        echo "Received arguments:"
        for arg in "$@"; do
            echo "$arg"
        done
        '''

        script_file_path = '/tmp/mock.sh'
        echo_command = f'echo "{script_content}" > {script_file_path}'
        ssh_operator.run(_host, echo_command)
        self.assertEqual(exit_code, 0, "Exit code for > should be zero")

        chmod_command = f'chmod +x {script_file_path}'
        ssh_operator.run(_host, chmod_command)
        self.assertEqual(exit_code, 0, "Exit code should be zero for chmod")

        # arguments passed via '--'
        command_with_args = '/tmp/mock.sh -v this_prog_args -- -c'
        output, exit_code, execution_time = ssh_operator.run(_host, command_with_args)
        self.assertIsNotNone(output, "Output should not be None")
        self.assertEqual(exit_code, 0, "Exit code should be zero")
        self.assertGreater(execution_time, 0, "Execution time should be greater than zero")

    def test_bad_pass(self):
        """Test does initial ssh pub key copy """
        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"
        with self.assertRaises(paramiko.ssh_exception.AuthenticationException):
            _ = SSHOperator(
                remote_hosts=[_host],
                username=self.ssh_user,
                password="bad",
                is_password_auth_only=False
            )

    def test_execute_cmd_and_timeout_after(self):
        """Test does initial ssh pub key copy """

        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"

        ssh_operator = SSHOperator(
            remote_hosts=[_host],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        )

        self.assertIsNotNone(ssh_operator, "ssh runner should be none")
        self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
        self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
        self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

        output, exit_code, _ = ssh_operator.run(_host, "echo 'test'")
        self.assertEqual(output, 'test', f"output should be test")
        self.assertEqual(exit_code, 0, f"exit code should be 0")

        with patch('paramiko.SSHClient.exec_command') as mock_exec_command:
            mock_exec_command.side_effect = SSHException("Simulated timeout")
            output, exit_code, _ = ssh_operator.run(_host, "echo 'test'")
            self.assertEqual(output, '', f"output should be empty due to timeout")
            self.assertNotEqual(exit_code, 0, f"exit code should not be 0 due to timeout")


