import json
import os
from ipaddress import ip_address
import unittest
from unittest.mock import patch

from tests.custom_unit_test import CustomTestCase
from tests.test_utils import (
    write_temp_kubeconfig,
    write_bad_temp_kubeconfig,
    sample_control_node,
    sample_worker_node
)
from warlock.kube_state import KubernetesState


class TestKubernetesState(CustomTestCase):
    def setUp(self):
        """
        :return:
        """
        self.k_state = KubernetesState()

    @patch('subprocess.run')
    def test_run_command_json_success(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"key": "value"})
        mock_run.return_value.returncode = 0
        result = self.k_state.run_command_json("echo 'dummy command'")
        expected_output = {"key": "value"}
        self.assertEqual(result, expected_output)
        mock_run.assert_called_once_with("echo 'dummy command'", capture_output=True, text=True, shell=True)

    @patch('subprocess.run')
    def test_run_command_json_error_code(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"key": "value"})
        mock_run.return_value.returncode = 100
        with self.assertRaises(Exception):
            _ = self.k_state.run_command_json("echo 'dummy command'")
        mock_run.assert_called_once_with("echo 'dummy command'", capture_output=True, text=True, shell=True)

    @patch('subprocess.run')
    def test_run_command_json_error_code_stdout(self, mock_run):
        # Simulate subprocess.run returning a failure
        mock_run.return_value.stdout = "Command failed with error: something went wrong"
        mock_run.return_value.stderr = "Command failed with error: something went wrong"
        mock_run.return_value.returncode = 100

        # Assert that the correct exception is raised for a failed command execution
        with self.assertRaises(Exception) as context:
            _ = self.k_state.run_command_json("echo 'dummy command'")

        self.assertIn("Command 'echo 'dummy command'' failed with error:", str(context.exception))
        mock_run.assert_called_once_with("echo 'dummy command'", capture_output=True, text=True, shell=True)

    @patch('subprocess.run')
    def test_run_command_error(self, mock_run):
        """Test if subprocess return error
        """
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Command failed with error"

        with self.assertRaises(Exception) as context:
            _ = self.k_state.run_command("echo 'This will fail'")

        self.assertIn("Command failed with error", str(context.exception))
        mock_run.assert_called_once_with("echo 'This will fail'", capture_output=True, text=True, shell=True)

    @patch('subprocess.run')
    def test_is_kubectl_installed_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        result = KubernetesState.is_kubectl_installed()
        self.assertFalse(result)
        mock_run.assert_called_once_with(
            ["kubectl", "version", "--client"],
            capture_output=True, check=True
        )

    @patch('subprocess.run')
    def test_run_command_json_unparseable_json(self, mock_run):
        """Test case if json corrupted
        :param mock_run:
        :return:
        """
        mock_run.return_value.stdout = "This is not JSON"
        mock_run.return_value.returncode = 0

        #  JSONDecodeError should be raised for unparseable JSON output
        with self.assertRaises(json.JSONDecodeError):
            _ = self.k_state.run_command_json("echo 'This is not JSON'")

        mock_run.assert_called_once_with("echo 'This is not JSON'", capture_output=True, text=True, shell=True)

    @patch('subprocess.run')
    def test_run_command_with_empty_string(
            self, mock_subprocess_run
    ):
        os.environ['SKIP_KUBECONFIG_VALIDATE'] = "true"
        mock_subprocess_run.return_value.stdout = ''
        mock_subprocess_run.return_value.returncode = 0
        instance = KubernetesState()
        result = instance.run_command('any command')
        self.assertEqual([""], result)
        del os.environ['SKIP_KUBECONFIG_VALIDATE']

    def test_generate_custom_path(self):
        """Test custom config generated in tmp loc
        :return:
        """
        path_to_generated_kubeconfig = write_temp_kubeconfig()
        self.assertCanRead(path_to_generated_kubeconfig, "failed to write temp config")

    def test_write_temp_kubeconfig_bad_path(self):
        self.assertCannotRead("wrong", "failed to write temp config")

    def test_custom_kubeconfig(self):
        """Test we can create KubernetesState class from custom kubeconfig
        :return:
        """
        path_to_generated_kubeconfig = write_temp_kubeconfig()
        os.environ['SKIP_KUBE_SERVER_CHECK'] = "true"
        state = KubernetesState(path_to_generated_kubeconfig)
        kube_config = state.read_kube_config()
        self.assertIsNotNone(kube_config, "read_kube_config should not be None")
        self.assertIn('clusters', kube_config, "'clusters' key should exist in kube_config")
        self.assertIn('contexts', kube_config, "'contexts' key should exist in kube_config")
        self.assertIn('users', kube_config, "'users' key should exist in kube_config")
        cluster_names = [cluster['name'] for cluster in kube_config.get('clusters', [])]
        self.assertIn('test-test', cluster_names, "'test-test' cluster should exist in kube_config")
        del os.environ['SKIP_KUBE_SERVER_CHECK']

        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

    def test_custom_kubeconfig_not_found(self):
        """Test we can create KubernetesState class from bad path
        :return:
        """
        with self.assertRaises(FileNotFoundError):
            state = KubernetesState("bad_path")

        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

    def test_custom_kubeconfig_correctness(self):
        """Test we can create KubernetesState class from custom kubeconfig
        :return:
        """
        os.environ['SKIP_KUBE_SERVER_CHECK'] = "true"
        path_to_generated_kubeconfig = write_temp_kubeconfig()
        state = KubernetesState(path_to_generated_kubeconfig)
        kube_config = state.read_kube_config()
        self.assertIsNotNone(kube_config, "read_kube_config should not be None")
        self.assertIn('clusters', kube_config, "'clusters' key should exist in kube_config")
        self.assertIn('contexts', kube_config, "'contexts' key should exist in kube_config")
        self.assertIn('users', kube_config, "'users' key should exist in kube_config")

        expected_cluster_username = "kubernetes-admin"
        cluster_username = state.read_cluster_username()
        self.assertEqual(cluster_username, expected_cluster_username,
                         f"Expected cluster username to be '{expected_cluster_username}', got '{cluster_username}'")

        expected_cluster_context = "kubernetes-admin@test-test"
        cluster_context = state.read_cluster_context()
        self.assertEqual(cluster_context, expected_cluster_context,
                         f"Expected cluster context to be '{expected_cluster_context}', got '{cluster_context}'")

        expected_cluster_name = "test-test"
        cluster_name = state.read_cluster_name()
        self.assertEqual(cluster_name, expected_cluster_name,
                         f"Expected cluster name to be '{expected_cluster_name}', got '{cluster_name}'")

        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

        del os.environ["SKIP_KUBE_SERVER_CHECK"]

    def test_from_kubeconfig(self):
        """Test we can create KubernetesState class from custom kubeconfig
        :return:
        """
        os.environ['SKIP_KUBE_SERVER_CHECK'] = "true"
        path_to_generated_kubeconfig = write_temp_kubeconfig()
        state = KubernetesState.from_kubeconfig(path_to_generated_kubeconfig)
        kube_config = state.read_kube_config()
        self.assertIsNotNone(kube_config, "read_kube_config should not be None")
        self.assertIn('clusters', kube_config, "'clusters' key should exist in kube_config")
        self.assertIn('contexts', kube_config, "'contexts' key should exist in kube_config")
        self.assertIn('users', kube_config, "'users' key should exist in kube_config")

        expected_cluster_username = "kubernetes-admin"
        cluster_username = state.read_cluster_username()
        self.assertEqual(cluster_username, expected_cluster_username,
                         f"Expected cluster username to "
                         f"be '{expected_cluster_username}', got '{cluster_username}'")

        expected_cluster_context = "kubernetes-admin@test-test"
        cluster_context = state.read_cluster_context()
        self.assertEqual(cluster_context, expected_cluster_context,
                         f"Expected cluster context to be '{expected_cluster_context}', got '{cluster_context}'")

        expected_cluster_name = "test-test"
        cluster_name = state.read_cluster_name()
        self.assertEqual(cluster_name, expected_cluster_name,
                         f"Expected cluster name to be '{expected_cluster_name}', got '{cluster_name}'")

        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

        del os.environ["SKIP_KUBE_SERVER_CHECK"]

    def test_read_config_twice(self):
        """Test we can create KubernetesState class from custom kubeconfig
        :return:
        """
        os.environ["SKIP_KUBE_SERVER_CHECK"] = "true"

        path_to_generated_kubeconfig = write_temp_kubeconfig()
        state = KubernetesState.from_kubeconfig(path_to_generated_kubeconfig)
        kube_config = state.read_kube_config()
        self.assertIsNotNone(kube_config, "read_kube_config should not be None")
        self.assertIn('clusters', kube_config, "'clusters' key should exist in kube_config")
        self.assertIn('contexts', kube_config, "'contexts' key should exist in kube_config")
        self.assertIn('users', kube_config, "'users' key should exist in kube_config")

        expected_cluster_username = "kubernetes-admin"
        cluster_username = state.read_cluster_username()
        self.assertEqual(cluster_username, expected_cluster_username,
                         f"Expected cluster username to "
                         f"be '{expected_cluster_username}', got '{cluster_username}'")

        expected_cluster_context = "kubernetes-admin@test-test"
        cluster_context = state.read_cluster_context()
        self.assertEqual(cluster_context, expected_cluster_context,
                         f"Expected cluster context to be '{expected_cluster_context}', got '{cluster_context}'")

        expected_cluster_name = "test-test"
        cluster_name = state.read_cluster_name()
        self.assertEqual(cluster_name, expected_cluster_name,
                         f"Expected cluster name to be '{expected_cluster_name}', got '{cluster_name}'")

        kube_config = state.read_kube_config()
        self.assertIsNotNone(kube_config, "read_kube_config should not be None")
        self.assertIn('clusters', kube_config, "'clusters' key should exist in kube_config")
        self.assertIn('contexts', kube_config, "'contexts' key should exist in kube_config")
        self.assertIn('users', kube_config, "'users' key should exist in kube_config")

        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

        del os.environ["SKIP_KUBE_SERVER_CHECK"]

    def test_kube_config_without_read(self):
        """Read config twice it should return from state
        :return:
        """
        os.environ["SKIP_KUBE_SERVER_CHECK"] = "true"
        state1 = KubernetesState.from_kubeconfig(write_temp_kubeconfig())
        expected_cluster_username = "kubernetes-admin"
        cluster_username = state1.read_cluster_username()
        self.assertEqual(cluster_username, expected_cluster_username,
                         f"Expected cluster username to "
                         f"be '{expected_cluster_username}', got '{cluster_username}'")

        state2 = KubernetesState.from_kubeconfig(write_temp_kubeconfig())
        expected_cluster_context = "kubernetes-admin@test-test"
        cluster_context = state2.read_cluster_context()
        self.assertEqual(cluster_context, expected_cluster_context,
                         f"Expected cluster context to be '{expected_cluster_context}', got '{cluster_context}'")

        state3 = KubernetesState.from_kubeconfig(write_temp_kubeconfig())
        expected_cluster_name = "test-test"
        cluster_name = state3.read_cluster_name()
        self.assertEqual(cluster_name, expected_cluster_name,
                         f"Expected cluster name to be '{expected_cluster_name}', got '{cluster_name}'")

        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']
        del os.environ["SKIP_KUBE_SERVER_CHECK"]

    def test_validate_kubeconfig_bad_config(self):
        """Test fetching k8s networks
        :return:
        """
        with self.assertRaises(Exception):
            config = write_bad_temp_kubeconfig("contexts")
            state = KubernetesState(path_to_kubeconfig=config)

    def test_read_kube_config(self):
        """Test fetching k8s networks
        :return:
        """
        kube_config = self.k_state.read_kube_config()
        self.assertIsNotNone(kube_config, "read_kube_config should not be None")
        self.assertIn('clusters', kube_config, "'clusters' key should exist in kube_config")
        self.assertIn('contexts', kube_config, "'contexts' key should exist in kube_config")
        self.assertIn('users', kube_config, "'users' key should exist in kube_config")

    def test_is_kubectl_installed(self):
        """Test fetching k8s networks
        :return:
        """
        is_installed = self.k_state.is_kubectl_installed()
        self.assertIsNotNone(is_installed, "is_kubectl_installed should not be None")

    def test_read_cluster_context(self):
        """Test fetching k8s networks
        :return:
        """
        kube_context = self.k_state.read_cluster_context()
        s = kube_context.split("@")
        self.assertTrue(len(s) == 2,
                        f"The kube_context '{kube_context}' "
                        f"does not match the expected format 'string@string'.")

    def test_read_cluster_username(self):
        """Test fetching k8s networks
        :return:
        """
        cluster_username = self.k_state.read_cluster_username()
        self.assertIsNotNone(cluster_username, "read_cluster_username() should not return None")
        self.assertTrue(len(cluster_username) > 0, "cluster_username should not be empty string")

    def test_constructor_custom_path(self):
        path_to_generated_kubeconfig = write_temp_kubeconfig()
        print(path_to_generated_kubeconfig)

    def assertPodInfoValidity(self, pod_data, expected_ns=None):
        self.assertIsNotNone(pod_data, "pod_node_ns_names should not be None")
        self.assertIsInstance(pod_data, dict, "pod_node_ns_names should be a dict")
        for pod_name, pod_info in pod_data.items():
            self.assertIsNotNone(pod_name, f"Pod name is None for pod_info: {pod_info}")
            self.assertIsInstance(pod_info, dict, f"Pod info for {pod_name} should be a dict")
            self.assertIn('node', pod_info, f"'node' key missing in pod info for {pod_name}")
            self.assertIn('ns', pod_info, f"'ns' key missing in pod info for {pod_name}")
            self.assertIsNotNone(pod_info['node'], f"'node' value is None in pod info for {pod_name}")
            self.assertIsNotNone(pod_info['ns'], f"'ns' value is None in pod_info for {pod_name}")
            if expected_ns:
                self.assertEqual(pod_info['ns'], expected_ns, f"'ns' value for {pod_name} is not '{expected_ns}'")

    def test_pod_node_ns_names(self):
        pod_data = self.k_state.pod_node_ns_names()
        self.assertPodInfoValidity(pod_data)

    def test_pod_node_valid_ns(self):
        pod_data = self.k_state.pod_node_ns_names(ns="default")
        self.assertPodInfoValidity(pod_data, expected_ns="default")

    def test_pod_node_invalid_ns(self):
        pod_data = self.k_state.pod_node_ns_names(ns="invalid")
        self.assertEqual(pod_data, {}, "pod_data should be an empty dictionary for an invalid namespace")

    def test_pod_node_ns_all(self):
        pod_data = self.k_state.pod_node_ns_names(ns="all")
        self.assertPodInfoValidity(pod_data)

    def test_pod_node_kube_system(self):
        ns_to_test = "kube-system"
        pod_data = self.k_state.pod_node_ns_names(ns=ns_to_test)
        self.assertPodInfoValidity(pod_data, expected_ns=ns_to_test)

    def test_namespaces(self):
        namespace_data = self.k_state.namespaces()
        self.assertIsNotNone(namespace_data, "namespaces() should not be None")
        self.assertIsInstance(namespace_data, list, "namespaces() should be list")

    @patch('warlock.kube_state.KubernetesState.run_command')
    def test_namespaces_no_result(self, mock_run_command):
        """
        Test if namespace return empty resul
        :param mock_run_command:
        :return:
        """
        mock_run_command.return_value = ''
        k_state = KubernetesState()
        result = k_state.namespaces()
        self.assertEqual(result, [])

    def test_pods_name(self):
        pod_names = self.k_state.pods_name()
        self.assertIsNotNone(pod_names, "pods_name() should not be None")
        self.assertIsInstance(pod_names, list, "pods_name() should be list")

    def test_node_names(self):
        node_names = KubernetesState()._fetch_and_update_nodes()
        self.assertIsNotNone(node_names, "_fetch_and_update_nodes() should not be None")
        self.assertIsInstance(node_names, dict, "_fetch_and_update_nodes() should be dict")

    def test_update_nodes_uuid_ip(self):
        node_names = KubernetesState().update_nodes_uuid_ip_view()
        self.assertIsNotNone(node_names, "_fetch_and_update_nodes() should not be None")
        self.assertIsInstance(node_names, dict, "_fetch_and_update_nodes() should be dict")

    def test_is_control_plane_node(self):
        self.assertTrue(KubernetesState.is_control_plane_node(json.loads(sample_control_node())),
                        "is_control_plane_node() should Return True")

    def test_is_control_plane_node_false(self):
        self.assertFalse(KubernetesState.is_control_plane_node(json.loads(sample_worker_node())),
                         "is_control_plane_node() should Return False")

    def test_read_worker_node_specs_(self):
        """Test reads worker node specs. node specs should return only worker node specs
        :return:
        """
        node_specs = KubernetesState().node_specs()
        for node_name, node_spec in node_specs.items():
            self.assertFalse(KubernetesState.is_control_plane_node(node_spec),
                             f"Control plane node {node_name} was included in the output")

    def test_all_node_specs(self):
        """Test reads all node specs.  node specs should return all node specs
        :return:
        """
        # read all worker node only
        worker_node_specs = KubernetesState().node_specs()
        for node_name, node_spec in worker_node_specs.items():
            self.assertFalse(KubernetesState.is_control_plane_node(node_spec),
                             f"Control plane node {node_name} was included in the output")

        # read all nodes
        all_node_specs = KubernetesState().node_specs(is_worker_node_only=False)
        self.assertTrue(len(all_node_specs) > len(worker_node_specs),
                        "node_specs should return all nodes when is_worker_node_only is False")

        # pop all worker node and check each is control plane node
        for worker_node_name in worker_node_specs.keys():
            all_node_specs.pop(worker_node_name, None)

        for node_name, node_spec in all_node_specs.items():
            self.assertTrue(KubernetesState.is_control_plane_node(node_spec),
                            f"Expected control plane node {node_name} not identified as such")

    def test_read_all_node_specs(self):
        """Test reads all node specs.  node specs should return all node specs
        :return:
        """
        # read all worker node only
        worker_node_specs = KubernetesState().read_all_node_specs()
        for node_name, node_spec in worker_node_specs.items():
            self.assertFalse(KubernetesState.is_control_plane_node(node_spec),
                             f"Control plane node {node_name} was included in the output")

        # read all nodes
        all_node_specs = KubernetesState().node_specs(is_worker_node_only=False)
        self.assertTrue(len(all_node_specs) > len(worker_node_specs),
                        "node_specs should return all nodes when is_worker_node_only is False")

        # pop all worker node and check each is control plane node
        for worker_node_name in worker_node_specs.keys():
            all_node_specs.pop(worker_node_name, None)

        for node_name, node_spec in all_node_specs.items():
            self.assertTrue(KubernetesState.is_control_plane_node(node_spec),
                            f"Expected control plane node {node_name} not identified as such")

    def sample_node_name_from_specs(self):
        """return work node name, note kubeconfig must have nodes for this test"""
        worker_node_specs = KubernetesState().node_specs()
        self.assertTrue(len(worker_node_specs) > 0, "No worker nodes found.")
        return list(worker_node_specs.keys())[0]

    def sample_n_node_specs(self, num_workers=2):
        """Return a specified number of worker node names.
        Note that the kubeconfig must have nodes for this test.
        :param num_workers: The number of worker node names to return.
        :return: A list of worker node names.
        """
        worker_node_specs = KubernetesState().node_specs()
        available_workers = list(worker_node_specs.keys())
        self.assertTrue(len(available_workers) >= num_workers,
                        f"Requested {num_workers} workers, but only {len(available_workers)} available.")
        return available_workers[:num_workers]

    def sample_control_plane_specs(self):
        """sample some control plane node """
        nodes = KubernetesState().node_specs(is_worker_node_only=False)
        for node_name, node_spec in nodes.items():
            if KubernetesState.is_control_plane_node(node_spec):
                return node_name
        return None

    def test_node_specs_with_args(self):
        """Test node specs return correct node spec by name
        :return:
        """
        sample_node_name = self.sample_node_name_from_specs()
        worker_node_specs = KubernetesState().node_specs(node_name=sample_node_name)
        self.assertIsNotNone(worker_node_specs, "node_specs should not be none")
        self.assertTrue(len(worker_node_specs) == 1, "node_specs should return only one worker node")
        self.assertIn(sample_node_name, worker_node_specs, "node_specs should return same worker node name as key")

        spec = worker_node_specs[sample_node_name]
        self.assertTrue('apiVersion' in spec, "'apiVersion' key should exist in node specs")
        self.assertTrue('kind' in spec, "'kind' key should exist in node specs")
        self.assertEqual(spec['kind'], 'Node', "'kind' should be 'Node'")

    def test_node_specs_not_found(self):
        """Test node specs return correct node spec by name
        :return:
        """
        worker_node_specs = KubernetesState().node_specs(node_name="notfound")
        self.assertEqual(worker_node_specs, {}, "not node found should return empty dict")

    def test_node_specs_with_args_cached(self):
        """
        Test node specs cache
        :return:
        """
        sample_node_name = self.sample_node_name_from_specs()

        # first lookup
        k_state = KubernetesState()
        worker_node_specs = k_state.node_specs(node_name=sample_node_name)
        self.assertIsNotNone(worker_node_specs, "node_specs should not be none")
        self.assertTrue(len(worker_node_specs) == 1, "node_specs should return only one worker node")
        self.assertIn(sample_node_name, worker_node_specs, "node_specs should return same worker node name as key")
        spec = worker_node_specs[sample_node_name]
        self.assertTrue('apiVersion' in spec, "'apiVersion' key should exist in node specs")
        self.assertTrue('kind' in spec, "'kind' key should exist in node specs")
        self.assertEqual(spec['kind'], 'Node', "'kind' should be 'Node'")

        self.assertIn(sample_node_name,
                      k_state._node_state, "node spec should cached")

        # follow up
        worker_node_specs = k_state.node_specs(node_name=sample_node_name)
        self.assertIsNotNone(worker_node_specs, "node_specs should not be none")
        self.assertTrue(len(worker_node_specs) == 1, "node_specs should return only one worker node")
        self.assertIn(sample_node_name, worker_node_specs, "node_specs should return same worker node name as key")

        spec = worker_node_specs[sample_node_name]
        self.assertTrue('apiVersion' in spec, "'apiVersion' key should exist in node specs")
        self.assertTrue('kind' in spec, "'kind' key should exist in node specs")
        self.assertEqual(spec['kind'], 'Node', "'kind' should be 'Node'")

        self.assertTrue('metadata' in spec, "'metadata' key should exist in node specs")
        self.assertTrue('spec' in spec, "'spec' key should exist in node specs")

    def test_two_node_specs_with_args_n_cached(self):
        """
        Test node specs cache
        :return:
        """
        sample_node_name = self.sample_n_node_specs()
        self.assertTrue(len(sample_node_name) == 2, "sample_n_node_specs should return two node")

        k_state = KubernetesState()
        for n in sample_node_name:
            worker_node_specs = k_state.node_specs(node_name=n)
            self.assertTrue(len(worker_node_specs) == 1, "node_specs should return only one worker node")
            self.assertIn(n, worker_node_specs, "node_specs should return same worker node name as key")
            spec = worker_node_specs[n]
            self.assertTrue('apiVersion' in spec, "'apiVersion' key should exist in node specs")
            self.assertTrue('kind' in spec, "'kind' key should exist in node specs")
            self.assertEqual(spec['kind'], 'Node', "'kind' should be 'Node'")
            self.assertIn(n, k_state._node_state, "node spec should cached")

        self.assertEqual(len(k_state._node_state), 2, "two node should cached")
        node_keys = list(k_state._node_state.keys())
        self.assertEqual(sample_node_name, node_keys, "node_specs must cache all results")

    def test_should_not_return_control(self):
        """
        Test node specs cache
        :return:
        """
        ctl_node_name = self.sample_control_plane_specs()
        self.assertIsNotNone(ctl_node_name, "cluster must have control plane")

        k_state = KubernetesState()
        node_spec = k_state.node_specs(node_name=ctl_node_name)
        self.assertIsNotNone(node_spec)
        self.assertEqual(node_spec, {}, "node_specs() by default should return {} for control plane")
        self.assertEqual(len(k_state._node_state), 0, "node_spec() should not cache control plane")

    def test_node_specs_with_customer_bad_config(self):
        """Test we can create KubernetesState class from custom kubeconfig
        :return:
        """
        path_to_generated_kubeconfig = write_temp_kubeconfig()
        with self.assertRaises(Exception):
            k_state = KubernetesState(path_to_generated_kubeconfig).node_specs()

        if 'KUBECONFIG' in os.environ:
            del os.environ['KUBECONFIG']

    def test_fetch_networks(self):
        """Test fetching k8s networks
        :return:
        """
        k_state = KubernetesState()
        k_networks = KubernetesState.fetch_networks()
        self.assertIsNotNone(k_networks, "fetch_networks should not be None")
        self.assertIsInstance(k_networks, list, "fetch_networks should be list")
        self.assertTrue(all(isinstance(n, str) for n in k_networks),
                        "all elements must string")

        self.assertIsNotNone(self.k_state._cache_networks)

    def test_fetch_networks_with_wrong_ns(self):
        """Test we can create KubernetesState class from custom kubeconfig
        :return:
        """
        k_networks = KubernetesState().fetch_networks(ns_name="test")
        self.assertIsNotNone(k_networks, "fetch_networks should not be None")
        self.assertIsInstance(k_networks, list, "fetch_networks should be list")
        self.assertTrue([] == k_networks, "for invalid namespace return should be empty list")

    def test_node_ips(self):
        """Test we get a list of ip address
        :return:
        """
        node_ips = KubernetesState().node_ips()
        self.assertTrue(all(isinstance(int(ip_address(addr)), int) for addr in node_ips),
                        "All addresses should convert without error")

    def test_fetch_nodes_uuid_ip(self):
        """Test fetch_nodes_uuid_ip
        :return:
        """
        node_name = self.sample_node_name_from_specs()
        node_ips = KubernetesState().fetch_nodes_uuid_ip(node_name)
        self.assertIsNotNone(node_ips, "fetch_nodes_uuid_ip should not be None")
        self.assertTrue(len(node_ips) == 1, "fetch_nodes_uuid_ip should return single entry")
        self.assertTrue(all(isinstance(int(ip_address(addr)), int) for addr in node_ips),
                        "All addresses should convert without error")

    def test_fetch_nodes_uuid_ip(self):
        """Test fetch_nodes_uuid_ip
        :return:
        """
        node_name = self.sample_node_name_from_specs()
        node_ips = KubernetesState().fetch_nodes_uuid_ip(node_name)
        self.assertIsNotNone(node_ips, "fetch_nodes_uuid_ip should not be None")
        self.assertTrue(len(node_ips) == 1, "fetch_nodes_uuid_ip should return single entry")
        self.assertTrue(all(isinstance(int(ip_address(addr)), int) for addr in node_ips),
                        "All addresses should convert without error")

    def test_read_node_metadata(self):
        """Test read_esxi_metadata
        :return:
        """
        node_name = self.sample_node_name_from_specs()
        node_metadata = KubernetesState().read_node_metadata(node_name)
        self.assertIsNotNone(node_metadata, "read_node_metadata should not return None")
        self.assertIsInstance(node_metadata, dict, "read_node_metadata should be a dict")
        print(json.dumps(node_metadata, indent=4))

    def test_read_node_metadata_not_found(self):
        """Test read_esxi_metadata
        :return:
        """
        node_name = self.sample_node_name_from_specs()
        node_metadata = KubernetesState().read_node_metadata(node_name)
        self.assertIsNotNone(node_metadata, "read_node_metadata should not return None")
        self.assertIsInstance(node_metadata, dict, "read_node_metadata should be a dict")
        self.assertTrue(len(node_metadata) == 0, "read_node_metadata not found should empty dict")

    def test_read_node_labels(self):
        """Test read_esxi_metadata
                "telco.vmware.com/nodepool": "np1"
        :return:
        """
        node_name = self.sample_node_name_from_specs()
        node_metadata = KubernetesState().read_node_metadata("vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k9jcm")
        self.assertIsNotNone(node_metadata, "read_esxi_metadata should not be None")
        print(json.dumps(node_metadata, indent=4))

    def test_read_node_pool_name(self):
        """Test read_esxi_metadata
                "telco.vmware.com/nodepool": "np1"
        :return:
        """
        node_name = self.sample_node_name_from_specs()
        node_metadata = KubernetesState().read_node_pool_name("vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k9jcm")
        self.assertIsNotNone(node_metadata, "read_esxi_metadata should not be None")
        print(json.dumps(node_metadata, indent=4))
