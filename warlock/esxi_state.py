from warlock.ssh_runner import SshRunner
class EsxiState:
    def __init__(
            self,
            ssh_executor: SshRunner,
            fqdn: str,
            username: str = "root",
            password: str = ""
    ):
        """
        :param path_to_kubeconfig:
        """
        self.fqdn = fqdn
        self.username = username
        self.password = password

    # def read_network_adapter(self):





