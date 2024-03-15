from typing import List, Dict


class SpellGenerator:
    def __init__(
            self,
            hosts: List[str] = None,
    ):
        self.hosts = hosts

    def generate_ring_spec(
            self,
            nic_configs: List[Dict[str, int]]
    ) -> List[Dict[str, List[Dict[str, int]]]]:
        """
           Generates a list of NIC RX/TX specifications for each host based on provided configurations.

           hosts = ["esxi-host1.example.com", "esxi-host2.example.com"]
           spec_generator = SpecGenerator(hosts=hosts)

          nic_configs = [
                    {"nics": ["vmnic0", "vmnic1"], "RX": 1024, "TX": 1024},
                    {"nics": ["vmnic0", "vmnic1"], "RX": 4096, "TX": 4096},
         ]

         specs = spec_generator.generate_ring_spec(nic_configs)


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

        :return:
        """
        spec_list = []

        for spec_config in nic_configs:
            host_config = {}
            for host in self.hosts:
                nic_settings = [{"nic": nic_name,
                                 "RX": spec_config["RX"],
                                 "TX": spec_config["TX"]}
                                for nic_name in spec_config["nics"]]
                host_config[host] = nic_settings
            spec_list.append(host_config)
        return spec_list
