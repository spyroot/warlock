"""
This class represents a set of action that mutate a node state.

For example, we can use scenario a , b  c and mutate a system
and observer a result.

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import json
import subprocess
from typing import List, Dict

from ssh_operator import SSHOperator
import time


class NodeActions:
    def __init__(
            self, node_ips: List[str],
            ssh_executor: SSHOperator,
            test_environment_spec=None
    ):
        """
        Initializes the NodeActions instance with a list of node IPs, an SSH command executor,
        and the test environment specification.

        :param node_ips: A list of IP addresses for the  kubernetes nodes.
        :param ssh_executor: An object responsible for executing SSH commands.
        :param test_environment_spec: The test environment specification including configurations for the test.
        """
        self.node_ips = node_ips
        self.ssh_executor = ssh_executor

        # Set test environment specification directly from the provided argument
        if test_environment_spec is not None:
            self.tun_value = test_environment_spec
        else:
            # If no spec is provided, fallback to loading from the default file (optional)
            self.tun_value_file = "../mutate.json"
            with open(self.tun_value_file, 'r') as file:
                self.tun_value = json.load(file)

        self.debug = True

    def update_ring_buffer(self):
        """
        Updates the ring buffer settings for network adapters on
        nodes based on a JSON configuration file.
        """
        for adapter_config in self.tun_value.get('adapters_tune', []):
            adapter_name = adapter_config.get('adapter_name', '')
            rx_value = adapter_config.get('rx', 1024)
            tx_value = adapter_config.get('tx', 1024)
            command = f"sudo ethtool -G {adapter_name} rx {rx_value} tx {tx_value}"

            for ip in self.node_ips:
                raw_out, exit_code, execution_time = self.ssh_executor.run(ip, command)
                if exit_code == 0:
                    print(f"Adapter {adapter_name} updated successfully on {ip}.")
                elif exit_code == 80:
                    print(f"No changes made to adapter {adapter_name} on {ip}; values already set.")
                else:
                    print(f"Failed to update adapter {adapter_name} on {ip}; exit code: {exit_code}.")

                print(f"Output: {raw_out}")
                print(f"Execution Time: {execution_time} seconds, exit code: {exit_code}")

    def reboot_node(self):
        """
        Reboots each remote host, waits for it to come back online, and checks the uptime.
        """
        reboot_command = "sudo reboot"
        uptime_command = "uptime"

        for ip in self.node_ips:
            print(f"Rebooting {ip}...")

            current_uptime, _, _ = self.ssh_executor.run(ip, uptime_command)
            print(f"Current uptime for {ip}: {current_uptime}")

            # Initiate reboot
            self.ssh_executor.run(ip, reboot_command)
            self.ssh_executor._release_connection(ip)

            # Wait for the host to go down and come back up
            print(f"Waiting for {ip} to reboot...")
            time.sleep(5)

            reboot_confirmed = False
            attempts = 0
            while not reboot_confirmed and attempts < 30:
                time.sleep(10)
                try:
                    # Attempt to reconnect and check uptime
                    new_uptime, _, _ = self.ssh_executor.run(ip, uptime_command)
                    if new_uptime != current_uptime:
                        print(f"Reboot confirmed for {ip}. New uptime: {new_uptime}")
                        reboot_confirmed = True
                    else:
                        print(f"Waiting for {ip} to finish rebooting...")
                except Exception as e:
                    print(f"Reconnect attempt failed for {ip}: {e}")
                attempts += 1

            if not reboot_confirmed:
                print(f"Failed to confirm reboot for {ip} after multiple attempts.")

    def update_active_tuned(self):
        """
        Updates the active tuned profile on remote hosts based on a JSON configuration file.
        """
        # Extract the tuned profile configuration
        tuned_profile_config = self.tun_value.get('tuned_profile', {})
        profile_name = tuned_profile_config.get('profile', '')
        profile_path = tuned_profile_config.get('path', '')

        for ip in self.node_ips:
            # Fetch the currently active profile
            command_get_active_profile = "sudo tuned-adm active | awk '{print $NF}'"
            current_profile, exit_code, exec_time = self.ssh_executor.run(ip, command_get_active_profile)

            if exit_code == 0 and current_profile != profile_name:
                print(f"Active profile on {ip}: {current_profile}")
                print(f"Setting profile {profile_name} on {ip}...")
                # Set the new profile
                command_set_profile = f"sudo tuned-adm profile {profile_name}"
                _, set_profile_exit_code, _ = self.ssh_executor.run(ip, command_set_profile)
                if set_profile_exit_code == 0:
                    print(f"Profile {profile_name} set successfully on {ip}.")
                else:
                    print(f"Failed to set profile {profile_name} on {ip}; exit code: {set_profile_exit_code}.")

                # Optionally, reboot the host if needed
                # command_reboot = "sudo reboot"
                # self.ssh_executor.run(ip, command_reboot)
            elif exit_code == 0:
                print(f"Profile on {ip} is already set to {profile_name}. No changes made.")
            else:
                print(f"Failed to get current profile on {ip}; exit code: {exit_code}.")

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

    def start_environment(self):
        """
        Starts an iperf server on one pod and then starts an iperf client
        on another pod to perform a test, based on the configuration defined in a JSON file.
        Server pod's IP address is provided as an argument.
        """
        server_config = self.tun_value.get('environment', {}).get('server', {})
        client_config = self.tun_value.get('environment', {}).get('client', {})
        server_pod_ip = server_config.get('ip')

        server_pod_name = server_config.get('pod_name')
        server_cmd = server_config.get('cmd')
        server_port = server_config.get('port')
        server_options = server_config.get('options')

        client_pod_name = client_config.get('pod_name')
        client_cmd = client_config.get('cmd')
        client_port = client_config.get('port')
        duration = client_config.get('duration', 60)
        parallel_streams = client_config.get('parallel_streams', 4)
        client_options = client_config.get('options')

        try:
            server_command = (f"kubectl exec {server_pod_name} "
                              f"-- /bin/bash -c \"{server_cmd} "
                              f"--bind {server_pod_ip} {server_options} "
                              f"--port {server_port}\"")
            server_output = self.run_command(server_command)
            time.sleep(1)

            client_command = (f"kubectl exec -it {client_pod_name} "
                              f"-- /bin/bash -c \"{client_cmd} "
                              f"--client {server_pod_ip} {client_options} "
                              f"--time {duration} "
                              f"--parallel {parallel_streams} --port {client_port}\"")

            client_out = self.run_command_json(client_command)
            bps_sent = client_out["end"]["sum_sent"]["bits_per_second"]
            bps_received = client_out["end"]["sum_received"]["bits_per_second"]

            if self.debug:
                print(f"Bits per second sent: {bps_sent}")
                print(f"Bits per second received: {bps_received}")
                print(json.dumps(client_out, indent=4))

            return bps_sent, bps_received, client_cmd
        except json.JSONDecodeError:
            print("Failed to parse client output as JSON.")

        return 0, 0, {}


