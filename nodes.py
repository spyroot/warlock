import subprocess
from typing import List, Tuple


class KubernetesNodes:

    def __init__(self):
        """
        """
        self._is_pubkey_authenticated = False

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

    def get_node_names_and_ips(self, node_pool_name) -> tuple[list[str], list[str]]:
        """
        :param node_pool_name:
        :return:
        """
        node_names = []
        node_ips = []

        nodes_output = self.run_command(
            "kubectl get nodes -o wide --no-headers")

        for line in nodes_output:
            if node_pool_name in line:
                parts = line.split()
                node_names.append(parts[0])
                node_ips.append(parts[5])

        return node_names, node_ips
