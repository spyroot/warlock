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

import json
import subprocess
from typing import Dict, List, Optional


class KubernetesState:

    def __init__(self):
        """
        """
        # store a node state information
        self.node_state: Dict[str, Dict] = {}
        # store a node ip address as key and node name
        self.nodes: Dict[str, str] = {}
        # pods name, node name, ns
        self.pods: Dict[str, Dict[str, str]] = {}
        # networks
        self.networks = None
        # current cluster config
        self.kube_config = None

    @staticmethod
    def run_command(cmd):
        """
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
    def run_command_json(cmd: str) -> Dict:
        """
        Execute a shell command that returns JSON and parse the output to a Python dict.
        """
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise Exception(f"Command '{cmd}' failed with error: {result.stderr.strip()}")

    def fetch_nodes_uuid_ip(self, node_pool_name: str) -> Dict[str, str]:
        """
        Fetches node uuid i.e, name and ip address
        :param node_pool_name: name of the
        :return:
        """
        if self.nodes:
            return self.nodes

        return self._fetch_and_update_nodes(node_pool_name)

    def node_spec(self, node_name: str) -> Dict:
        """
        Fetch the specification for a given node in JSON format.
        """
        if node_name in self.node_state:
            return self.node_state[node_name]

        node_output = self.run_command_json(f"kubectl get node {node_name} -o json")
        self.node_state[node_name] = node_output
        return self.node_state

    def update_nodes_uuid_ip(self, node_pool_name: str) -> Dict[str, str]:
        """
        Force fetching and updating the nodes information.
        """
        # Clear the current nodes information to force a re-fetch.
        self.nodes.clear()
        return self._fetch_and_update_nodes(node_pool_name)

    def _fetch_and_update_nodes(self, node_pool_name: str) -> Dict[str, str]:
        """
        Fetch Kubernetes node names and their IP addresses.
        Helper method to avoid code duplication between fetch and update operations.
        """
        nodes_output = self.run_command("kubectl get nodes -o wide --no-headers")
        for line in nodes_output:
            if node_pool_name in line:
                parts = line.split()
                if len(parts) > 5 and len(parts[0]) > 0:
                    self.nodes[parts[5]] = parts[0]

        return self.nodes

    def fetch_networks(self, refresh: Optional[bool] = False) -> List[str]:
        """
        """

        if refresh is False and self.networks is not None:
            return self.networks

        raw_output = self.run_command(
            "kubectl get net-attach-def -o custom-columns=NAME:.metadata.name --no-headers")
        self.networks = [net_name for net_name in raw_output]
        return self.networks

    def read_all_node_specs(self):
        """Read all nodes spec and update internal
        :return:
        """
        for n in self.node_names():
            self.node_spec(n)
        return self.node_state

    def node_names(self) -> List[str]:
        """Return node names
        :return:
        """
        return list(self.nodes.values())

    def node_ips(self) -> List[str]:
        """Return node ip
        :return:
        """
        return list(self.nodes.keys())

    def read_pod_spec(self, pod_name: str, ns: Optional[str] = "default"):
        return self.run_command_json(f"kubectl get pod {pod_name} -n {ns} -o json")

    def pods_name(self,
                  ns: Optional[str] = "default") -> List[str]:
        """Return list of pod names as list of string
        :return:
        """
        if len(self.pods) == 0:
            self.pod_node_ns_names(ns=ns)

        return list(self.pods.keys())

    def pod_node_ns_names(
            self,
            ns: Optional[str] = "default") -> Dict[str, Dict[str, str]]:
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
            if len(line) > 0:
                parts = line.split()
                if len(parts) > 2:
                    self.pods[parts[0]] = {
                        "node": parts[1],
                        "ns": parts[2]
                    }
        return self.pods

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
