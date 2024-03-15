"""
This class represents a kubernetes state.  The main purpose of this class
is to read kubernetes object node , pod , networks so in downstream
code we can use that data for something.

All data fetched once and cached is stored in states.  Caller can do force read
in case it need constantly update a state of particular object

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""

import os
import json
import subprocess
from typing import Dict, List, Optional, Any


class KubernetesState:

    def __init__(
            self,
            path_to_kubeconfig: str = None
    ):
        """
        :param path_to_kubeconfig:
        """
        # store a node state information
        self._node_state: Dict[str, Dict] = {}
        # cache store a node ip address as key and node name
        self._cache_addr2node = None
        self._cache_node2addr = None

        # pods name, node name, ns
        self._cache_pods_names: Dict[str, Dict[str, str]] = {}
        # networks
        self._cache_networks = None
        # current cluster config
        self.kube_config = None

        # namespaces cache
        self._namespaces = None

        if self.is_kubectl_installed() is False:
            raise Exception("kubectl is not installed. Please install kubectl to proceed.")

        if path_to_kubeconfig:
            if not os.path.exists(path_to_kubeconfig):
                raise FileNotFoundError(f"Kubeconfig file not found at '{path_to_kubeconfig}'")
            if not os.path.isfile(path_to_kubeconfig):
                raise Exception(f"The path '{path_to_kubeconfig}' is not a file.")
            if not os.access(path_to_kubeconfig, os.R_OK):
                raise PermissionError(f"The file '{path_to_kubeconfig}' is not readable.")
            os.environ['KUBECONFIG'] = path_to_kubeconfig

        try:
            if "SKIP_KUBECONFIG_VALIDATE" not in os.environ:
                self.validate_kubeconfig()
        except Exception as e:
            if 'KUBECONFIG' in os.environ:
                del os.environ['KUBECONFIG']
            raise e

    @classmethod
    def from_kubeconfig(
            cls,
            path_to_kubeconfig: str
    ):
        """
        Constructor KubernetesState from custom path to kubeconfig
        :return: An instance of VMwareVimState.
        """
        return cls(path_to_kubeconfig=path_to_kubeconfig)

    @staticmethod
    def run_command(cmd):
        """Run k8s command.
        :param cmd:
        :return:
        """
        result = subprocess.run(
            cmd, capture_output=True, text=True, shell=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        else:
            raise Exception(f"Command '{cmd}' failed with error: {result.stderr.strip()}")

    @staticmethod
    def run_command_json(
            cmd: str, expect_error: str = None) -> Dict:
        """
        Execute a shell command that should return a JSON and parse the output to a Python dict.

        If an expected error substring is provided and encountered,
        return an empty dictionary instead of raising an exception.

        :param cmd: Command to execute.
        :param expect_error: Substring of the error message that, if found, will not raise an exception but return an empty dict.
        :return: A dictionary with the command output or an empty dictionary for expected errors.
        """
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            # json.JSONDecodeError propagated up
            return json.loads(result.stdout)
        else:
            error_message = result.stderr.strip()
            if expect_error and expect_error in error_message:
                return {}
            else:
                raise Exception(f"Command '{cmd}' failed with error: {error_message}")

    def fetch_nodes_uuid_ip(
            self,
            node_pool_name: str
    ) -> Dict[str, str]:
        """
        Fetches node uuid i.e, name and ip address
        :param node_pool_name: name of the
        :return:
        """
        if self._cache_addr2node is not None:
            return self._cache_addr2node

        return self._fetch_and_update_nodes(node_pool_name)

    @staticmethod
    def is_control_plane_node(
            node_spec: Dict
    ) -> bool:
        """
        Determine if the given node spec represents a control plane node.

        :param node_spec: The specification of the node as a dictionary.
        :return: True if the node is part of the control plane, False otherwise.
        """
        labels = node_spec.get("metadata", {}).get("labels", {})

        control_plane_labels = [
            # in older versions of Kubernetes and some distributions
            "node-role.kubernetes.io/master",
            "node-role.kubernetes.io/control-plane",
        ]

        for label in control_plane_labels:
            if label in labels:
                return True

        taints = node_spec.get("spec", {}).get("taints", [])
        for taint in taints:
            if taint.get("key") in ["node-role.kubernetes.io/master", "node-role.kubernetes.io/control-plane"]:
                return True

        return False

    def node_specs(
            self,
            node_name: str = None,
            is_worker_node_only: bool = True,
    ) -> Dict[str, Dict[Any, Any]]:
        """Method read kubernetes node specs and return
        a dictionary that holds a kubernetes node specs.

        A dictionary key is node name.  Note , by default, method filters out
        control plane nodes and return only worker node.

        If caller need a particular node name it should pass node_name arg.

        :param node_name: a particular node name that
        :param is_worker_node_only: if False will return all nodes specs.
        :raise ValueError: if node_name container invalid spaces
        :return: a dictionary that holds a kubernetes node specs
        """
        if node_name is not None and len(node_name.split()) > 1:
            raise ValueError("node name should not contain spaces")

        if node_name is not None and node_name in self._node_state:
            return {node_name: self._node_state[node_name]}

        if node_name:
            cmd = f"kubectl get node {node_name} -o json"
        else:
            cmd = "kubectl get nodes --no-headers -o json"

        node_output = self.run_command_json(cmd, expect_error="(NotFound)")
        if node_name:
            if ((self.is_control_plane_node(node_output) and is_worker_node_only)
                    or len(node_output) == 0):
                return {}
            self._node_state[node_name] = node_output
            return {node_name: node_output}

        for node in node_output.get('items', []):
            if is_worker_node_only and self.is_control_plane_node(node):
                continue
            node_name_key = node.get('metadata', {}).get('name')
            if node_name_key:
                self._node_state[node_name_key] = node

        return self._node_state

    def update_nodes_uuid_ip_view(
            self,
            node_substring: str = None
    ) -> Dict[str, str]:
        """
        Force fetching and updating the node's information.
        """
        # Clear the current nodes information to force a re-fetch.
        self._cache_addr2node.clear()
        return self._fetch_and_update_nodes(node_substring=node_substring)

    def _add_node_and_addr_entry(
            self,
            node_name: str,
            node_addr: str
    ):
        """
        :param node_name:
        :param node_addr:
        :return:
        """
        if self._cache_addr2node is None:
            self._cache_addr2node = {}

        if self._cache_node2addr is None:
            self._cache_node2addr = {}

        self._cache_addr2node[node_addr] = node_name
        self._cache_node2addr[node_name] = node_addr

    def _fetch_and_update_nodes(
            self,
            node_substring: str = None
    ) -> Dict[str, str]:
        """
        Fetch Kubernetes node names and their IP addresses.

        Helper method to avoid code duplication between fetch and update operations.
        Note node_substring is substring or exact string of node name that client need
        to filter out.

        :param node_substring:
        :return: a dictionary where key is ip address and it and value a name.
        """
        nodes_output = self.run_command("kubectl get nodes -o wide --no-headers")
        if nodes_output is None or len(nodes_output) == 0:
            return {}

        for line in nodes_output:
            if node_substring is None or node_substring in line:
                parts = line.split()
                if len(parts) > 5 and len(parts[0]) > 0:
                    node_name = parts[0].strip()
                    node_addr = parts[5].strip()
                    self._add_node_and_addr_entry(node_name, node_addr)
                    # for exact match we stop
                    if node_substring == node_name:
                        break

        return self._cache_addr2node

    def fetch_networks(
            self,
            refresh: Optional[bool] = False,
            ns_name: Optional[str] = "default"
    ) -> List[str]:
        """Fetch Kubernetes networks name and return list.

        :param ns_name:  by default only default namespace is returned.
        :param refresh: force to re fetch Kubernetes networks.
        :return: list of network names
        """
        if refresh is False and self._cache_networks is not None:
            return self._cache_networks

        raw_output = self.run_command(
            f"kubectl get net-attach-def -o custom-columns=NAME:.metadata.name --no-headers -n {ns_name}")

        if raw_output is None or (len(raw_output) == 1 and not raw_output[0].strip()):
            return []

        self._cache_networks = [net_name for net_name in raw_output]
        return self._cache_networks

    def read_all_node_specs(self):
        """Read all nodes spec and update internal
        :return:
        """
        return self.node_specs()

    def node_names(self) -> List[str]:
        """Return node names
        :return:
        """
        return list(self._cache_addr2node.values())

    def node_ips(
            self
    ) -> List[str]:
        """Return list of all node ip
        :return: list of node ips
        """
        if self._cache_addr2node is None:
            self._fetch_and_update_nodes(node_substring=None)

        return list(self._cache_addr2node.keys())

    @staticmethod
    def read_pod_spec(
            pod_name: str,
            ns: Optional[str] = "default"
    ):
        """
        :param pod_name:
        :param ns:
        :return:
        """
        return KubernetesState.run_command_json(f"kubectl get pod {pod_name} -n {ns} -o json")

    def pods_name(
            self,
            ns: Optional[str] = "default"
    ) -> List[str]:
        """Return a list of pod names as list of string
        :return:
        """
        if len(self._cache_pods_names) == 0:
            self.pod_node_ns_names(ns=ns)

        return list(self._cache_pods_names.keys())

    def pod_node_ns_names(
            self,
            ns: Optional[str] = "default"
    ) -> Dict[str, Dict[str, str]]:
        """Return pod node name and node name, and namespace.
        {'pod_name': {'node': 'node_name', 'ns': 'default'}}
        :return:
        """
        if ns == "all":
            raw_output = self.run_command(
                f"kubectl get pods -A "
                f"-o=custom-columns=NAME:.metadata.name,"
                f"NODE:.spec.nodeName,"
                f"NAMESPACE:.metadata.namespace "
                f"--no-headers")
        else:
            raw_output = self.run_command(
                f"kubectl get pods "
                f"-o=custom-columns=NAME:.metadata.name,"
                f"NODE:.spec.nodeName,"
                f"NAMESPACE:.metadata.namespace "
                f"--no-headers -n {ns}")

        for line in raw_output:
            if len(line) == 0:
                continue
            parts = line.split()
            if len(parts) > 2:
                self._cache_pods_names[parts[0]] = {
                    "node": parts[1],
                    "ns": parts[2]
                }

        return self._cache_pods_names

    def namespaces(
            self
    ) -> List[str]:
        """Return list of namespaces
        :return:
        """
        raw_output = self.run_command("kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'")
        if raw_output and len(raw_output) > 0:
            name_spaces = raw_output[0].split()
            self._namespaces = name_spaces
            return name_spaces
        else:
            return []

    def read_kube_config(self):
        """Read current kubernetes config
        :return:
        """
        if self.kube_config is not None:
            return self.kube_config

        self.kube_config = KubernetesState.run_command_json("kubectl config view -o json")
        return self.kube_config

    def read_cluster_name(self):
        """Reads cluster name from kubernetes config
        :return:
        """
        if self.kube_config is None:
            self.read_kube_config()

        return self.kube_config["clusters"][0]["name"] if self.kube_config["clusters"] else ""

    def read_cluster_username(self):
        """Reads from cluster config current cluster username
        :return:
        """
        if self.kube_config is None:
            self.read_kube_config()

        return self.kube_config["users"][0]["name"] if self.kube_config["users"] else ""

    def read_cluster_context(self):
        """Reads current cluster context
        :return:
        """
        if self.kube_config is None:
            self.read_kube_config()

        return self.kube_config["current-context"] if "current-context" in self.kube_config else ""

    @staticmethod
    def is_kubectl_installed() -> bool:
        """
        Check if kubectl is installed by attempting to run 'kubectl version'.
        :return: True if kubectl is installed, False otherwise.
        """
        try:
            subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True, check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def validate_kubeconfig() -> Dict:
        """
        Validates the kubeconfig by checking
        if 'clusters', 'users', or 'contexts' are present and not null.

        Uses 'kubectl config view -o json' command for validation.

        :return: Parsed JSON of kubeconfig if valid.
        :raises: Exception if kubeconfig is empty or improperly configured.
        """
        cmd = "kubectl config view -o json"
        kubeconfig = KubernetesState.run_command_json(cmd)
        if not kubeconfig.get('clusters') or not kubeconfig.get('users') or not kubeconfig.get('contexts'):
            raise Exception("Kubeconfig appears to be empty or "
                            "improperly configured. Please check your kubeconfig.")

        if "SKIP_KUBE_SERVER_CHECK" not in os.environ:
            raw_output = KubernetesState.run_command_json("kubectl version -o json")
            if 'serverVersion' not in raw_output:
                raise Exception("Failed fetch server version. Please check your kubeconfig")

        return kubeconfig

    def read_node_metadata(
            self,
            node_name: str
    ) -> Dict[str, Any]:
        """
        Reads node metadata from node spec
        :param node_name:
        :return:
        """
        node_spec = self.node_specs(node_name=node_name)
        if node_name in node_spec and 'metadata' in node_spec[node_name]:
            return node_spec[node_name]['metadata']
        return {}

    def read_node_labels(
            self,
            node_name: str
    ) -> Dict[str, Any]:
        """
        Reads labels from metadata.
        :param node_name: a kubernetes node name
        :return: a dictionary with labels as keys.
        """
        meta = self.read_node_metadata(node_name)
        if 'labels' in meta:
            return meta['labels']
        return {}

    def read_node_pool_name(
            self,
            node_name: str
    ) -> Optional[str | None]:
        """
        Reads node pool labels VMware specific name for a node pools, if it presents in  metadata
        :param node_name: a kubernetes node name
        :return: return node pool name
        """
        labels = self.read_node_labels(node_name)
        for k, v in labels.items():
            if 'nodepool' in k:
                return v
        return None


