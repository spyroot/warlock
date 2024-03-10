"""
Test SSHOperator.

Note it create local container and test against that ssh operator.
also it has test that manipulate ssh pub key.

Note that SSH Operator for public authentication method first time
need to push key hence make sure you have sshpass.

brew install sshpass

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import os
import shutil
import subprocess
from unittest.mock import patch
import paramiko
from paramiko.ssh_exception import SSHException
from unittest.mock import patch, MagicMock

from tests.containerized_test_case import (
    ContainerizedTestCase
)

from warlock.ssh_operator import (
    SSHOperator,
    PublicKeyNotFound,
    CommandNotFound
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
        with SSHOperator(remote_hosts=["127.0.0.1"],
                         username="root",
                         password="pass", is_password_auth_only=True) as ssh_operator:
            self.assertIsNotNone(ssh_operator, "ssh runner should be none")
            self.assertEqual(ssh_operator._username, "root", "username should be capv")
            self.assertEqual(ssh_operator._password, "pass", "username should be capv")
            self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

    def test_init_ssh_key_auth(self):
        """Test construct for ssh key auth"""
        with SSHOperator(
                remote_hosts=[f"127.0.0.1:{self.ssh_port}"],
                username=self.ssh_user,
                password=self.ssh_pass,
                is_password_auth_only=False
        ) as ssh_operator:
            self.assertIsNotNone(ssh_operator, "ssh runner should be none")
            self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
            self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
            self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")

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
        """Tests initial procedure to add public key """

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

        with SSHOperator(
                remote_hosts=[_host],
                username=self.ssh_user,
                password=self.ssh_pass,
                is_password_auth_only=False
        ) as ssh_operator:
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

        with SSHOperator(
                remote_hosts=[_host],
                username=self.ssh_user,
                password=self.ssh_pass,
                is_password_auth_only=False
        ) as ssh_operator:
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

        with SSHOperator(
            remote_hosts=[_host],
            username=self.ssh_user,
            password=self.ssh_pass,
            is_password_auth_only=False
        ) as ssh_operator:

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

        with SSHOperator(
                remote_hosts=[_host],
                username=self.ssh_user,
                password=self.ssh_pass,
                is_password_auth_only=False
        ) as ssh_operator:
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

        with SSHOperator(
                remote_hosts=[_host],
                username=self.ssh_user,
                password=self.ssh_pass,
                is_password_auth_only=False
        ) as ssh_operator:
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
        """Test bad pass """
        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"
        with self.assertRaises(paramiko.ssh_exception.AuthenticationException):
            with SSHOperator(
                    remote_hosts=[_host],
                    username=self.ssh_user,
                    password="bad",
                    is_password_auth_only=False
            ) as ssh_operator:
                pass

    def test_execute_cmd_and_timeout_after(self):
        """Test execute cmd and timeout ssh  """

        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host = f"127.0.0.1:{self.ssh_port}"

        with SSHOperator(
                remote_hosts=[_host],
                username=self.ssh_user,
                password=self.ssh_pass,
                is_password_auth_only=False
        ) as ssh_operator:
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

    def test_connect_concurrently(self):
        """
        Test concurrent execution
        """
        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host1 = f"127.0.0.1:{self.ssh_port}"
        _host2 = f"localhost:{self.ssh_port}"

        with SSHOperator(
                remote_hosts=[_host1, _host2],
                username=self.ssh_user,
                password=self.ssh_pass,
                is_password_auth_only=False
        ) as ssh_operator:
            self.assertIsNotNone(ssh_operator, "ssh runner should be none")
            self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
            self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
            self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")
            self.assertEqual(len(ssh_operator._persistent_connections), 2, "SSHOperator should open two connection.")

            docker_command = f"docker exec {self.container_id} netstat -an | grep 22 | grep ESTABLISHED | wc -l"
            result = subprocess.run(docker_command, shell=True, capture_output=True, text=True)
            self.assertIsNotNone(result, "docker should return some result")
            self.assertEqual(2, int(result.stdout.strip()), f"server should have two connection")

    def test_execute_concurrently(self):
        """
        Test concurrent execution
        """
        self.assertIsNotNone(self.ssh_port, "Test expect ssh port")
        self.assertIsNotNone(self.container_id, "Test expect ssh port")

        _host1 = f"127.0.0.1:{self.ssh_port}"
        _host2 = f"localhost:{self.ssh_port}"

        with SSHOperator(
                remote_hosts=[_host1, _host2],
                username=self.ssh_user,
                password=self.ssh_pass,
                is_password_auth_only=False
        ) as ssh_operator:
            self.assertIsNotNone(ssh_operator, "SSHOperator should be none")
            self.assertEqual(ssh_operator._username, self.ssh_user, f"username should be {self.ssh_user}")
            self.assertEqual(ssh_operator._password, self.ssh_pass, f"password should be {self.ssh_pass}")
            self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")
            self.assertEqual(len(ssh_operator._persistent_connections), 2, "SSHOperator should open two connection.")

            docker_command = f"docker exec {self.container_id} netstat -an | grep 22 | grep ESTABLISHED | wc -l"
            result = subprocess.run(docker_command, shell=True, capture_output=True, text=True)
            self.assertIsNotNone(result, "docker should return some result")
            self.assertEqual(2, int(result.stdout.strip()), f"server should have two connection")
            output_dict = ssh_operator.broadcast("echo 'test'")

    def test_init_with_none_remote_hosts(self):
        """Test SSHOperator initialization with remote_hosts set to None."""
        with self.assertRaises(ValueError) as context:
            SSHOperator(remote_hosts=None, username="test_user", password="test_pass")

        self.assertTrue("remote_hosts cannot be None" in str(context.exception))

    def test_init_without_password_for_password_auth(self):
        """Test SSHOperator initialization without password for password authentication."""
        with self.assertRaises(ValueError) as context:
            SSHOperator(remote_hosts=["127.0.0.1"], username="test_user", password=None, is_password_auth_only=True)

        self.assertTrue("password is required for password authentication" in str(context.exception))

    @patch('paramiko.SSHClient')
    def test_get_ssh_connection_reuses_existing_connection(self, mock_ssh_client):
        """Test that get_ssh_connection reuses an existing connection."""
        # Mock the behavior of an SSHClient instance
        mock_client_instance = MagicMock()
        mock_ssh_client.return_value = mock_client_instance

        # Initialize SSHOperator with a dummy host key
        with SSHOperator(remote_hosts=["127.0.0.1"],
                         username="test_user", password="test_pass") as operator:

            host_key = "127.0.0.1:22"
            first_connection = operator.get_ssh_connection(host_key)
            self.assertEqual(first_connection, mock_client_instance)
            self.assertTrue(mock_ssh_client.called)
            mock_ssh_client.assert_called_once()
            mock_ssh_client.reset_mock()

            second_connection = operator.get_ssh_connection(host_key)
            self.assertEqual(second_connection, first_connection)
            mock_ssh_client.assert_not_called()

    @patch('paramiko.SSHClient')
    def test_handling_of_network_errors(self, mock_ssh_client):
        """Test handling of network errors like timeouts and connection resets."""
        mock_client_instance = MagicMock()
        mock_client_instance.connect.side_effect = Exception("Network error")
        mock_ssh_client.return_value = mock_client_instance

        operator = SSHOperator(remote_hosts=["127.0.0.1"],
                               username="test_user",
                               password="test_pass")
        host_key = "127.0.0.1:22"

        with self.assertRaises(Exception) as context:
            operator.get_ssh_connection(host_key)

        self.assertIn("Network error", str(context.exception))

    @patch('paramiko.SSHClient')
    def test_context_manager_establishes_and_closes_connections(
            self, mock_ssh_client):
        """Test that the context manager establishes and closes connections properly."""
        mock_client_instance = MagicMock()
        mock_ssh_client.return_value = mock_client_instance

        with SSHOperator(remote_hosts=["127.0.0.1:22"], username="test_user", password="test_pass") as operator:
            operator.get_ssh_connection("127.0.0.1:22")
            mock_client_instance.connect.assert_called_once()

        mock_client_instance.close.assert_called_once()

    def test_password_and_cmd(self):
        """Test Construct for pass auth"""
        live_host = "10.252.80.107"
        with SSHOperator(remote_hosts=[live_host],
                         username="root",
                         password="VMware1!",
                         is_password_auth_only=True) as ssh_operator:
            self.assertIsNotNone(ssh_operator, "ssh runner should be none")
            self.assertEqual(ssh_operator._username, "root", "username should be root")
            self.assertEqual(ssh_operator._password, "VMware1!", "username should be VMware1!")
            self.assertFalse(ssh_operator._is_pubkey_authenticated, "_is_pubkey_authenticated should be false")
            output, exit_code, _ = ssh_operator.run(live_host, "esxcli --version")
            self.assertIsNotNone(output, "Output should be None")
            self.assertEqual(0, exit_code, "exit code should be 0")