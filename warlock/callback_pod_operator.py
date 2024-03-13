import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from warlock.callback import Callback
from warlock.kube_state import KubernetesState
from warlock.shell_operator import ShellOperator


class CallbackPodsOperator(Callback):
    """
    This class is designed to adjust the RX and TX ring sizes for network adapters
    across a list of ESXi hosts. It receives a list of dictionaries detailing NICs,
    RX, and TX values for each host, and a list of EsxiStateReader objects to interact
    with the ESXi hosts.
    """

    def __init__(
            self,
            spell_file="spell.json",
            dry_run: Optional[bool] = True,
    ):
        """
        :param spell_file: on dry run we only read but never write or mutate.
        :param dry_run:
        """
        super().__init__()
        self.spell_file = spell_file

        working_dir =
        self.is_dry_run = dry_run
        self.dry_run_plan = []

    def _log_dry_run_operation(
            self,
            ops: str,
    ):
        """
        Log an operation that would be executed during a dry run.
        """
        operation = {
            "operation": ops,
        }
        self.dry_run_plan.append(operation)

    def get_dry_run_plan(self):
        """
        Retrieve the plan of operations
        that would be executed during a dry run.
        :return: A list of planned operations.
        """
        return self.dry_run_plan


    def on_scenario_begin(self):
        """
        :return:
        """
        print("CallbackRingTunner on_scenario_begin")
        with open(self.spell_file, 'r') as file:
            spell_spec_file = json.load(file)
            server_config = spell_spec_file.get('environment', {}).get('server', {})
            client_config = spell_spec_file.get('environment', {}).get('client', {})

            server_pod_spec = Path(server_config.get('pod_spec')).resolve().absolute()
            client_pod_spec = Path(client_config.get('pod_spec')).resolve().absolute()

            server_pod_name = server_config.get('pod_name')
            client_pod_name = client_config.get('pod_name')

            output = ShellOperator.run_command(f"kubectl apply -f {server_pod_spec}")
            print(output)
            server_pod_spec = KubernetesState.read_pod_spec(server_pod_name)
            server_pod_ip = server_pod_spec.get('status', {}).get('podIPs', [])[0].get('ip')

            _ = ShellOperator.run_command(f"kubectl apply -f {client_pod_spec}")
            server_pod_spec = KubernetesState.read_pod_spec(server_pod_name)
            client_pod_ip = server_pod_spec.get('status', {}).get('podIPs', [])[0].get('ip')

            server_config['ip'] = server_pod_ip
            client_config['ip'] = client_pod_ip

    def on_scenario_end(self):
        print("CallbackRingTunner on_scenario_end")
