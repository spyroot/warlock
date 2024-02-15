import json
import subprocess
from typing import Dict, List, Optional


class KubernetesNodes:

    def __init__(self):
        """
        """
        self.node_state: Dict[str, Dict] = {}
        self.nodes: Dict[str, str] = {}
        self.networks = None

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

        :param node_pool_name:
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
        """Return node ip"
        :return:
        """
        return list(self.nodes.keys())
