import logging
import time
from typing import Optional

from warlock.spell_specs import SpellSpecs
from warlock.callbacks.callback import Callback
from warlock.states.kube_state_reader import KubernetesState
from warlock.operators.shell_operator import ShellOperator


class CallbackPodsOperator(Callback['WarlockState']):
    """
    Manages the lifecycle of a set of Kubernetes pods as part of a scenario.
    This callback handles the creation, update, and deletion of pods according to
    the specifications provided in the spell master specs. It is designed to prepare
    the environment for running experiments by ensuring the necessary pods are
    deployed and in a ready state.

    Attributes:
        spell_master_specs (SpellSpecs): Specifications and configurations for the spell master.
        dry_run (bool, optional): If True, simulates operations without making any changes.
        logger (logging.Logger, optional): Logger instance for outputting information.
        reuse_existing (bool, optional): If True, existing pods are reused and not deleted.
    """
    def __init__(
            self,
            spell_master_specs: SpellSpecs,
            dry_run: Optional[bool] = True,
            logger: Optional[logging.Logger] = None,
            reuse_existing:  Optional[bool] = False,
    ):
        """
        Initializes the callback with the necessary configuration to manage Kubernetes pods.

        :param spell_master_specs: The specifications that include pod configuration.
        :param dry_run: If set to True, operations will be logged but not executed.
        :param logger: A logger instance for logging output. A default logger is used if none is provided.
        :param reuse_existing: If set to True, existing pods will not be deleted and will be reused.
        """
        super().__init__()
        self.logger = logger if logger else logging.getLogger(__name__)
        self._master_spell_spec = spell_master_specs

        self.is_dry_run = dry_run
        self.dry_run_plan = []
        self._abs_dir = self._master_spell_spec.absolute_dir

        # re-use exiting won't delete pod and re-use existing pods
        self._reuse_existing = reuse_existing
        # default wait time
        self._timeout = 30
        self._default_timeout = self._timeout

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
        Retrieves the list of operations that would be executed during a dry run.

        :return: A list of operations that are planned to be executed.
        """
        return self.dry_run_plan

    def on_scenario_begin(self):
        """
        On scenario begin this callback creates multiple pods and waits for all to be ready.
        It updates spell caster
        :return:
        """
        self.logger.info("CallbackPodsOperator scenario begin")

        pods_spec = self._master_spell_spec.pods_spells()
        pod_creation_cmd = []

        for k, v in pods_spec.items():
            if isinstance(v, dict) and v['type'] == 'pod':
                pod_spec = v
                pod_name = pod_spec['pod_name']
                pod_ns = pod_spec.get('namespace', "default")
                pod_spec_path = (self._abs_dir / pod_spec['pod_spec_file']).resolve()

                # schedule pod creation as best effort
                ShellOperator.run_command_json(f"kubectl apply -f {pod_spec_path} -n {pod_ns} -o json")
                pod_creation_cmd.append((k, pod_name, pod_ns))

        # blocking call
        all_pods_ready = False
        while self._timeout > 0 and not all_pods_ready:
            all_pods_ready = True
            for k, pod_name, pod_ns in pod_creation_cmd:
                pod_state = KubernetesState.read_pod_spec(pod_name, pod_ns)
                if (pod_state.get('status', {}).get('phase') != 'Running' or
                        not pod_state.get('status', {}).get('podIPs')):
                    all_pods_ready = False
                    break
            if not all_pods_ready:
                time.sleep(5)
                self._timeout -= 1

        if not all_pods_ready:
            self.logger.error("Not all pods were ready within the timeout period.")
            return

        for k, pod_name, pod_ns in pod_creation_cmd:
            pod_state = KubernetesState.read_pod_spec(pod_name, pod_ns)
            pod_addr = pod_state.get('status', {}).get('podIPs', [])[0].get('ip')
            phase = pod_state.get('status', {}).get('phase')
            node_addr = pod_state.get('status', {}).get('hostIP')
            self.logger.info(f"Scheduled pod read ip {pod_addr} status {phase} node {node_addr}")
            self.caster_state.k8s_pods_states[k] = {
                'ip': pod_addr,
                'phase': phase,
                'node_ip': node_addr,
                'pod_state': pod_state
            }

        self._timeout = self._default_timeout

    def on_scenario_end(self):
        """Executes at the end of a scenario, handling the cleanup of the created pods.
        If 'reuse_existing' is True, pods will not be deleted.
        :return:
        """
        self.logger.info("CallbackPodsOperator scenario end")

        if self._reuse_existing:
            self.logger.info("CallbackPodsOperator skip pod delete")
            return

        if not hasattr(self.caster_state, 'k8s_pods_states') or not self.caster_state.k8s_pods_states:
            self.logger.info("No pods recorded in the caster state for deletion.")
            return

        pods_spec = self._master_spell_spec.pods_spells()
        for k, v in pods_spec.items():
            if isinstance(v, dict) and v['type'] == 'pod':
                pod_spec = v
                pod_name = pod_spec['pod_name']
                pod_ns = pod_spec.get('namespace', "default")
                last_state = ShellOperator.run_command(f"kubectl delete pod {pod_name} -n {pod_ns}")
                self.logger.info(f"Deleted pod {pod_name} in namespace {pod_ns}: {last_state}")
