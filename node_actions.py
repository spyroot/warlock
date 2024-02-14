
class NodeActions:
    def __init__(self, node_ips, command_executer):
        """

        :param node_ips:
        """
        self.node_ips = node_ips
        self.tuned_profile_name = ""
        self.tuned_profile_path = ""
        self.ssh_cmd_runner = command_executer

    def update_ring_buffer(self, adapter_name, username, password=None):
        """
        :param adapter_name:
        :param username:
        :param password:
        :return:
        """
        for ip in self.node_ips:
            self.ssh_cmd_runner.ssh_command(ip, f"sudo ethtool -G {adapter_name} rx 1024 tx 1024", username, password)

    def update_active_tuned(self, username, password=None):
        """Function to update the active tuned profile on remote hosts.
        :param node_ips:
        :param tuned_profile_name:
        :param tuned_profile_path:
        :param username:
        :param password:
        :return:
        """
        for ip in self.node_ips:
            profile_name = self.ssh_cmd_runner.ssh_command(ip, "sudo tuned-adm active | awk '{print $NF}'", username,
                                                           password)
            print(f"Active profile on {ip}: {profile_name}")
            if profile_name != self.tuned_profile_name:
                print(f"Setting profile {self.tuned_profile_name} on {ip}...")
                self.ssh_cmd_runnerr.ssh_command(ip, f"sudo tuned-adm profile {tuned_profile_name}", username, password)
                self.ssh_cmd_runner.ssh_command(ip, "sudo reboot", username, password)
            else:
                print(f"Profile on {ip} is already set to {tuned_profile_name}. No changes made.")

