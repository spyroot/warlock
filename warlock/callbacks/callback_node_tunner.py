from typing import List, Dict, Any, Tuple, Optional
from warlock.callbacks.callback import Callback, listify
from warlock.states.esxi_state_reader import EsxiStateReader
from concurrent.futures import ThreadPoolExecutor, as_completed


class CallbackNodeTunner(Callback):
    """
    This class is designed to adjust the RX and TX ring sizes for network adapters
    across a list of ESXi hosts. It receives a list of dictionaries detailing NICs,
    RX, and TX values for each host, and a list of EsxiStateReader objects to interact
    with the ESXi hosts.
    """

    def __init__(
            self,
            nic_rx_tx_map: List[Dict[Any, Any]],
            state_readers: List[EsxiStateReader],
            dry_run: Optional[bool] = True,
    ):
        """

        Example this a map that describe value for each nic worker node.
        On each call on_caas_mutate_begin we update ring size.

        On first call

        esxi-host1.example.com nic vmnic0, vmnic we TX/RX ring 1024
        esxi-host2.example.com  nic vmnic0, vmnic we TX/RX ring 1024

        On second run

        esxi-host1.example.com nic vmnic0, vmnic we TX/RX ring 4096
        esxi-host2.example.com  nic vmnic0, vmnic we TX/RX ring 4096

        nic_rx_tx_map = [

            {
                "esxi-host1.example.com": [
                    {"nic": "vmnic0", "RX": 1024, "TX": 1024},
                    {"nic": "vmnic1", "RX": 1024, "TX": 1024},
                ],
                "esxi-host2.example.com": [
                    {"nic": "vmnic0", "RX": 1024, "TX": 1024},
                    {"nic": "vmnic1", "RX": 1024, "TX": 1024},
                ],
            },

            {
                "esxi-host1.example.com": [
                    {"nic": "vmnic0", "RX": 4096, "TX": 4096},
                    {"nic": "vmnic1", "RX": 4096, "TX": 4096},
                ],
                "esxi-host2.example.com": [
                    {"nic": "vmnic0", "RX": 4096, "TX": 4096},
                    {"nic": "vmnic1", "RX": 4096, "TX": 4096},
                ],
            },
        ]

        StateReder[0].fqdn esxi-host1.example.com
        StateReder[1].fqdn esxi-host2.example.com

        :param nic_rx_tx_map:  List of dictionaries that describe list nic , rx and tx value for each host
        :param state_readers:  List of EsxiStateReader objects
        :param dry_run: on dry run we only read but never write or mutate.
        """
        super().__init__()

        if not all(isinstance(item, dict) for item in nic_rx_tx_map):
            raise ValueError("nic_rx_tx_map must be a list of dictionaries.")

        for config in nic_rx_tx_map:
            for host, nics in config.items():
                if not all(isinstance(nic, dict) for nic in nics):
                    raise ValueError("Each NIC configuration must be a dictionary.")
                for nic in nics:
                    if "nic" not in nic or "RX" not in nic or "TX" not in nic:
                        raise ValueError("Each NIC configuration must contain 'nic', 'RX', and 'TX' keys.")
                    if not (isinstance(nic["RX"], int) and isinstance(nic["TX"], int)):
                        raise ValueError("'RX' and 'TX' values must be integers.")

        if not all(isinstance(reader, EsxiStateReader) for reader in state_readers):
            raise ValueError("state_readers must be a list of EsxiStateReader objects.")

        # callback expect that both list have same keys , i.e fqdn/ip
        valid_fqdns = {reader.fqdn for reader in state_readers}
        for config in nic_rx_tx_map:
            for host_key in config.keys():
                if host_key not in valid_fqdns:
                    raise ValueError(f"Invalid host key '{host_key}' in nic_rx_tx_map. "
                                     f"It does not match any provided esxi_states_reader FQDN.")

        self.nic_rx_tx_map = listify(nic_rx_tx_map)
        self.esxi_states_readers = state_readers

        self._sample_index = 0
        self._initial_ring_size = {}

        self.is_dry_run = dry_run
        self.dry_run_plan = []

    def on_sample_tcp_buffer_size(self):
        """On sample, method return values that we mutate on follow-up call next etc.
        :return:
        """

    def on_sample_udp_buffer_size(self):
        """On sample, method return values that we mutate on follow-up call next etc.
        :return:
        """
        pass

    def on_sample_tuned_profile(self):
        """On sample, method return values that we mutate on follow-up call next etc.
        :return:
        """
        pass

    def on_sample_adapter_settings(self):
        """On sample, method return values that we mutate on follow-up call next etc.
        Values are set of setting for network adapter. For example
        UDP hash
        :return:
        """
        pass

    def on_sample_ring_value(
            self
    ) -> Dict[str, List[Tuple[str, int, int]]]:
        """On sample, method return values that we mutate on follow-up call next etc.
        Note this method is cycle back i.e. restart on follow-up calls.

        Assume we have two host x and y

        First scenario need mutate vmnic0/1 on x and 2/3 on y.

        {
            'x.x.x.x': [('eht0', 1024, 1024), ('eht0', 1024, 1024)],
            'y.y.y.y': [('eht1', 1024, 1024), ('eht1', 1024, 1024)]
        }

        Second scenario need mutate vmnic0/1 on x and 0/1 on y.

        {
            'x.x.x.x': [('eht0', 4096, 4096), ('eht0', 4096, 4096)],
            'y.y.y.y': [('eht1', 4096, 4096), ('eht1', 4096, 4096)]
        }

        then we wrap around.
        :return: A
        """
        if not self.nic_rx_tx_map:
            return {}

        values_for_run = self.nic_rx_tx_map[self._sample_index]
        self._sample_index = (self._sample_index + 1) % len(self.nic_rx_tx_map)

        transformed_values = {}
        for host, nics in values_for_run.items():
            transformed_values[host] = [(nic['nic'], nic['RX'], nic['TX']) for nic in nics]

        return transformed_values

    def __update_ring_size(
            self,
            nics_tx_rx,
            state_reader: EsxiStateReader
    ) -> None:
        """Update the ring size for a particular host.
        It uses state reader to update the ring size.

        :param nics_tx_rx: is List of tuples
        :param state_reader: a EsxiStateReader instance
        :return:
        """
        if state_reader.fqdn in nics_tx_rx:
            for nic, tx_size, rx_size in nics_tx_rx[state_reader.fqdn]:
                if not self.is_dry_run:
                    state_reader.write_ring_size(nic, tx_size, rx_size)
                else:
                    self._log_dry_run_operation(
                        "mutate ring size", state_reader, nic, rx_size, tx_size)

    def _prepare_host(
            self,
            state_reader: EsxiStateReader,
            unique_nics: set
    ):
        """Method to prepare a single host each thread call.
        :param state_reader:
        :param unique_nics:
        :return:
        """
        host_data = []
        for adapter_name in unique_nics:
            ring_size_data = state_reader.read_ring_size(adapter_name=adapter_name)[0]
            rx, tx = ring_size_data['RX'], ring_size_data['TX']
            host_data.append((adapter_name, rx, tx))
        return state_reader.fqdn, host_data

    def on_iaas_prepare(
            self
    ):
        """On prepare we concurrently read all nics
        that we will mutate and construct tuple of old values.

        {'x.x.x.x': [('vmnic1', 1024, 1024), ('vmnic0', 1024, 1024)]}

        {'x': [
               ('vmnic1', 1024, 1024),
               ('vmnic0', 1024, 1024)
           ],
         'y': [
                   ('vmnic2', 1024, 1024),
                   ('vmnic0', 1024, 1024),
                   ('vmnic3', 1024, 1024),
                   ('vmnic1', 1024, 1024)
               ]
         }
        :return: None
        """
        self._initial_ring_size = {}
        with ThreadPoolExecutor(max_workers=len(self.esxi_states_readers)) as executor:
            futures = [
                executor.submit(self._prepare_host, state_reader,
                                {nic_config['nic'] for nic_map in self.nic_rx_tx_map for nic_config
                                 in nic_map.get(state_reader.fqdn, [])})
                for state_reader in self.esxi_states_readers
            ]
            for future in as_completed(futures):
                fqdn, host_data = future.result()
                self._initial_ring_size[fqdn] = host_data

    def __restore_ring_size(
            self, state_reader: EsxiStateReader
    ):
        """
        :return:
        """
        for nic, rx_size, tx_size in self._initial_ring_size[state_reader.fqdn]:
            if not self.is_dry_run:
                state_reader.write_ring_size(nic, rx_size, tx_size)
            else:
                self._log_dry_run_operation(
                    "restore", state_reader, nic, rx_size, tx_size)

    def on_iaas_release(self):
        """On iaas release we restore.
        :return:
        """
        with ThreadPoolExecutor(max_workers=len(self.esxi_states_readers)) as executor:
            futures = [
                executor.submit(
                    self.__restore_ring_size, state_reader
                )
                for state_reader in self.esxi_states_readers
            ]

            for future in as_completed(futures):
                pass

    def on_iaas_spell_begin(self):
        """On iaas this all back mutate network adapter ring size.
        :return:
        """
        nics_tx_rx = self.sample_ring_value()
        with ThreadPoolExecutor(max_workers=len(self.esxi_states_readers)) as executor:
            futures = [
                executor.submit(
                    self.__update_ring_size, nics_tx_rx, state_reader
                )
                for state_reader in self.esxi_states_readers
            ]

            for future in as_completed(futures):
                pass

    def on_iaas_spell_end(self):
        """On iaas mutate end we do nothing
        :return:
        """
        pass

    def _log_dry_run_operation(
            self,
            ops: str,
            state_reader: EsxiStateReader,
            nic: str,
            rx_size: int,
            tx_size: int
    ):
        """
        Log an operation that would be executed during a dry run.

        :param state_reader: The state reader associated with the operation.
        :param nic: The NIC name.
        :param rx_size: The intended RX ring size.
        :param tx_size: The intended TX ring size.
        """
        operation = {
            "index": self._sample_index,
            "operation": ops,
            "host": state_reader.fqdn,
            "nic": nic,
            "rx_size": rx_size,
            "tx_size": tx_size,
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
        print("CallbackRingTunner on_scenario_begin")

    def on_scenario_end(self):
        print("CallbackRingTunner on_scenario_end")
