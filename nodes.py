import subprocess
from typing import List, Tuple


def run_command(command):
    """
    :param command:
    :return:
    """
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        return result.stdout.strip().split('\n')
    else:
        raise Exception(f"Command '{command}' failed with error: {result.stderr.strip()}")


def get_node_names_and_ips(node_pool_name) -> tuple[list[str], list[str]]:
    """
    :param node_pool_name:
    :return:
    """
    node_names = []
    node_ips = []

    nodes_output = run_command("kubectl get nodes -o wide --no-headers")

    for line in nodes_output:
        if node_pool_name in line:
            parts = line.split()
            node_names.append(parts[0])
            node_ips.append(parts[5])
    return node_names, node_ips
