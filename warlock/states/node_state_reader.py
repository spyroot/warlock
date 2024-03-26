"""
NodeStateReader, designed to encapsulate reading kubernetes node (worker)
state information.

Author: Mus
 spyroot@gmail.com
 mbayramo@stanford.edu
"""
import logging
import os
from abc import ABC
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List, Callable, Any

from warlock.operators.ssh_operator import SSHOperator
from warlock.states.spell_caster_state import SpellCasterState


class InvalidNodeHostException(Exception):
    """Exception raised when the target host is not identified as a Linux node."""
    def __init__(self, host, message="The target host does not appear to be a Linux node."):
        self.host = host
        self.message = f"{message} Host: {host}"
        super().__init__(self.message)


class NodeStateReader(SpellCasterState, ABC):
    """

    """
    INTERRUPT_INTERVAL_RANGE = 4095
    MAX_VMDQ = 16

    def __init__(
            self,
            ssh_operator: SSHOperator,
            credential_dict: Optional[Dict] = None,
            node_address: Optional[str] = None,
            username: Optional[str] = "capv",
            password: Optional[str] = "",
            logger: Optional[logging.Logger] = None
    ):
        """
        Class reads different state from a worker node.

        A state value are current network adapter low level values such ring size,
        vmdq etc.

        In order collect and read a state we need an operator. Since most of the values
        has to be collected directly we read this value via SSH transport.

        :param ssh_operator:  ssh operator is ssh operator that we use to connect and execute
        :param node_address: worker node fqdn or ip address
        :param username: node username
        :param password: node password
        """
        super().__init__()
        self._ssh_operator = ssh_operator
        self._credential_dict = credential_dict
        self.logger = logger if logger else logging.getLogger(__name__)

        if ssh_operator is None or not isinstance(ssh_operator, SSHOperator):
            raise ValueError(f"ssh_operator must be an instance "
                             f"of SSHOperator, got {type(ssh_operator)}")

        if not isinstance(node_address, str):
            raise TypeError(f"node address must be a string, got {type(node_address)}")

        if not isinstance(username, str):
            raise TypeError(f"node username must be a string, got {type(username)}")

        if not isinstance(password, str):
            raise TypeError(f"node password must be a string, got {type(password)}")

        default_node_address = self._credential_dict.get('caas', {}).get(
            'node_address', '') if self._credential_dict else ''
        default_username = self._credential_dict.get('caas', {}).get(
            'username', '') if self._credential_dict else ''
        default_password = self._credential_dict.get('caas', {}).get(
            'password', '') if self._credential_dict else ''

        self.node_address = node_address if node_address is not None else default_node_address
        self.username = username if username is not None else default_username
        self.password = password if password is not None else default_password

    def __enter__(self):
        """
        Return the instance itself when entering the context.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ensure all connections are closed when exiting the context.
        """
        if self._ssh_operator is not None:
            self._ssh_operator.close_all()
            del self._ssh_operator

    def release(self):
        """Explicitly release resources,  closing all SSH connections.
        """
        if self._ssh_operator is not None:
            self._ssh_operator.close_all()
            del self._ssh_operator

    def _create_ssh_operators(
            self,
            node_address: str,
            num_operators: int
    ) -> List[SSHOperator]:
        """
        Create a list of SSHOperator instances.

        :param node_address: The address of the node to connect to.
        :param num_operators: The number of SSHOperator instances to create.
        :return: A list of SSHOperator instances.
        """
        return [
            SSHOperator(
                remote_hosts=[node_address],
                username=self.username,
                password=self.password,
                is_password_auth_only=True
            ) for _ in range(num_operators)
        ]

    @classmethod
    def from_optional_credentials(
            cls,
            node_address: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """
        Constructor that creates an instance using optional credentials.

        :param node_address: Optional esxi fqdn or ip address.
        :param username: Optional esxi username.
        :param password: Optional esxi password.
        :return: An instance of EsxiState.
        """
        if not isinstance(node_address, str):
            raise TypeError(f"node address must be a string, got {type(node_address)}")

        if not isinstance(username, str):
            raise TypeError(f"node username must be a string, got {type(username)}")

        if not isinstance(password, str):
            raise TypeError(f"node password must be a string, got {type(password)}")

        node_address = node_address or os.getenv('NODE_IP')
        username = username or os.getenv('NODE_USERNAME')
        password = password or os.getenv('NODE_PASSWORD')

        ssh_operator = SSHOperator(
            remote_hosts=[node_address],
            username=username,
            password=password,
            is_password_auth_only=True
        )

        output, exit_code, _ = ssh_operator.run(node_address, "uname -a")
        if cls.__is_linux(output):
            output, exit_code, _ = ssh_operator.run(node_address, "uname -r")
            _node_version = cls.__read_version(output)
            if _node_version is None:
                ssh_operator.close_all()
                raise InvalidNodeHostException(node_address)
        else:
            ssh_operator.close_all()
            raise InvalidNodeHostException(node_address)

        return cls(ssh_operator, None, node_address.strip(), username.strip(), password.strip())

    @classmethod
    def from_optional_operator(
            cls,
            ssh_operator: SSHOperator,
            node_address: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
    ):
        """
        Constructor that creates an instance using existing ssh operator.

        :param ssh_operator: Instance of ssh operator.
        :param node_address: Optional esxi fqdn or ip address.
        :param username: Optional esxi username.
        :param password: Optional esxi password.
        :return: An instance of EsxiState.
        """
        node_address = node_address or os.getenv('NODE_IP')
        username = username or os.getenv('NODE_USERNAME')
        password = password or os.getenv('NODE_PASSWORD')

        if not isinstance(node_address, str):
            raise TypeError(f"esxi must be a string, got {type(node_address)}")

        if not isinstance(username, str):
            raise TypeError(f"esxi username must be a string, got {type(username)}")

        if not isinstance(password, str):
            raise TypeError(f"esxi password must be a string, got {type(password)}")

        if node_address:
            if not ssh_operator.has_active_connection(node_address):
                raise ValueError(f"No active connection for host {node_address}")

            output, exit_code, _ = ssh_operator.run(node_address, "uname -a")
            if cls.__is_linux(output):
                output, exit_code, _ = ssh_operator.run(node_address, "uname -r")
                _node_version = cls.__read_version(output)
                if _node_version is None:
                    ssh_operator.close_all()
                    raise InvalidNodeHostException(node_address)
            else:
                ssh_operator.close_all()
                raise InvalidNodeHostException(node_address)

        return cls(ssh_operator, None, node_address.strip(), username.strip(), password.strip())

    def is_active(self) -> bool:
        """
        Checks if there's an active SSH connection to the ESXi host.
        :return: True if there's an active connection, False otherwise.
        """
        return self._ssh_operator.get_active_ssh_connection(self.node_address) is not None

    @staticmethod
    def __is_linux(command_output: str) -> bool:
        return 'Linux' in command_output

    @staticmethod
    def __read_version(
            command_output: str
    ) -> Optional[str]:
        """
        Extracts the version from the command output.
        :param command_output: The output string from running `uname -r`.
        :return: The extracted version string or None if not found.
        """
        parts = command_output.split()
        return parts[0] if parts else None

    def read_pci_dev_name(
            self,
            ssh_operator: SSHOperator,
            pci_address: str
    ) -> str:
        """
        Return device name like Ethernet0 / pciPassthru24
        if failed will return empty string

        :param ssh_operator: The SSHOperator instance for running commands.
        :param pci_address: PCI address of the device.
        :return: The device name.
        """

        if pci_address is None or len(pci_address) == 0:
            return ""

        try:
            command = f"lspci -Dknn | grep -A 3 '{pci_address}'"
            output, exit_code, _ = ssh_operator.run(self.node_address, command)
            if exit_code != 0 or not output:
                return ""

            for line in output.split('\n'):
                if 'DeviceName' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        return parts[1].strip()
        except Exception as e:
            self.logger.error(f"An error occurred while reading PCI device name: {str(e)}")

        return ""

    def read_dev_aliases(
            self
    ) -> Dict:
        """Resolve logical - to device name
        :return:
        """

        aliases = {}
        try:

            command = (
                "for label_path in /sys/class/net/*/device/label; do "
                "interface=$(basename $(dirname $(dirname $label_path))); "
                "label=$(cat $label_path); "
                "echo \"$interface - $label\"; "
                "done"
            )
            output, exit_code, _ = self._ssh_operator.run(self.node_address, command)

            if exit_code != 0:
                return {}

            aliases = {}
            lines = output.strip().split('\n')
            for line in lines:
                parts = line.split(' - ')
                if len(parts) == 2:
                    interface, label = parts
                    aliases[interface] = label

        except Exception as e:
            self.logger.error(f"An error occurred fetching logical name: {str(e)}")

        return aliases

    def read_pci_dev_phy_slot(
            self,
            ssh_operator: SSHOperator,
            pci_address) -> str:
        """
        Return the physical slot number for the device.

        :param ssh_operator:
        :param pci_address: PCI address of the device.
        :return: The physical slot number.
        """
        if pci_address is None or len(pci_address) == 0:
            return ""

        output, exit_code, _ = ssh_operator.run(
            self.node_address,
            f"lspci -vmmks {pci_address}"
        )

        if exit_code != 0 or not output:
            return ""

        slots = [line.split(':', 1)[1].strip()
                 for line in output.split('\n') if line.startswith('PhySlot:')]
        return slots[0] if slots else ""

    def read_dev_and_mac(
            self,
            ssh_operator: SSHOperator,
            dev_name,
            dev_aliases
    ):
        """
        Retrieves the network interface name and MAC address
        for the given device name. (Ethernet0/pciPassthruX)

        :param ssh_operator:
        :param dev_name: The device name to search for in the aliases.
        :param dev_aliases: A dictionary mapping network interfaces to device names.
        :return: A tuple containing the logical name and MAC address.
        """
        logical_name = None
        mac_address = None

        for interface, label in dev_aliases.items():
            if label == dev_name:
                logical_name = interface
                mac_output, mac_exit_code, _ = ssh_operator.run(
                    self.node_address,
                    f"cat /sys/class/net/{interface}/address"
                )
                if mac_exit_code == 0:
                    mac_address = mac_output.strip()
                break

        return logical_name, mac_address

    def _process_pci_device(
            self,
            ssh_operator,
            capture_buffer: str,
            dev_aliases
    ) -> Dict[str, Any]:
        """A callback function to process a pci device.
        A capture buffer is string that must hold capture line for lspci device output.

        :return:
        """
        parts = capture_buffer.split('"', 1)
        if len(parts) < 2:
            return {}

        pci_address = parts[0].strip()
        dev_name = self.read_pci_dev_name(ssh_operator, pci_address)
        dev_slot = self.read_pci_dev_phy_slot(ssh_operator, pci_address)
        logical_name, mac_address = self.read_dev_and_mac(ssh_operator, dev_name, dev_aliases)

        return {
            'pci_address': pci_address,
            'device': dev_name,
            'slot': dev_slot,
            'logical_name': logical_name,
            'mac_address': mac_address
        }

    def _thread_run(
            self, callback: Callable,
            *args,
            **kwargs
    ):
        """
        THis call create ssh operator and take callback and all args and pass all args to a callback.
        execute and externalize back.

        It main purpose to execute set of command via ssh transport
        via parallel channels to remote host.

        :param callback: a callback thread need execute
        :param args: arguments passed to callback
        :param kwargs: keyword arguments passed to callback
        :return:
        """
        with SSHOperator(
                remote_hosts=[self.node_address],
                username=self.username,
                password=self.password,
                is_password_auth_only=True
        ) as ssh_operator:
            return callback(ssh_operator, *args, **kwargs)

    def execute_in_parallel(
            self,
            tasks: List[Any]
    ) -> List[Any]:
        """
        Executes tasks in parallel using a thread pool executor.
        It receives a list of tasks where a task is some callback and its arguments.
        It delegates to a thread for parallel execution.

        Note it designed so each task run in parallel without
        mutating shared states.

        :param tasks: A list of tuples, where each tuple contains the callback function
                      and its arguments for the task.
        :return: A list of results from each executed task.
        """
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._thread_run, *task) for task in tasks]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing task: {e}")

        return results

    def read_pci_devices(
            self
    ) -> List[Dict]:
        """
        Reads the PCI devices using lspci and returns a list of dictionaries with details
        about each device, including the logical network
        interface name and MAC address if available.

        - It includes logical and device name for kernel claimed device.
        - For VF it includes device name and PCI address and slot number.
         {
            "pci_address": "0000:02:00.0",
            "device": "Ethernet0",
            "slot": "160",
            "logical_name": "eth0",
            "mac_address": "00:50:56:b6:b7:c3"
        },

        {
            "pci_address": "0000:22:01.0",
            "device": "Ethernet1",
            "slot": "33",
            "logical_name": "eth1",
            "mac_address": "00:50:56:b6:97:23"
         },

        {
            "pci_address": "0000:23:00.0",
            "device": "pciPassthru24",
            "slot": "64",
            "logical_name": null,
            "mac_address": null
        },

        for unclassified pci device such as VF that hanging mac address is None.

        :return: A list of dictionaries, each representing a PCI device.
        """

        pci_devices = []
        cli_output, exit_code, _ = self._ssh_operator.run(self.node_address, "lspci -Dmm")
        if exit_code != 0:
            return pci_devices

        dev_aliases = self.read_dev_aliases()

        tasks = []
        for line in cli_output.strip().split('\n'):
            if 'Ethernet controller' in line or 'Network controller' in line or 'Ethernet' in line:
                tasks.append((self._process_pci_device, line, dev_aliases))

        return self.execute_in_parallel(tasks)
