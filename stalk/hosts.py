from datetime import datetime

from pollen.attack_reporting import AttackReport


class Host:
    def __init__(self, config,
                 id=None,
                 datapath_id=None,
                 mac_address=None,
                 ip_address=None):
        self.id = id
        self.datapath_id = datapath_id
        self.mac_address = mac_address
        self.ip_address = ip_address
        self.attackers = []
        self._config = config

        self.rx_traffic = []
        self.tx_traffic = []

        self.rx_traffic_per_source = {}
        self.tx_traffic_per_destination = {}

        self.time = datetime.now()
        self.time_blocked = datetime.now()

    def __eq__(self, other):
        return (self.ip_address == other.ip_address or
                self.mac_address == other.mac_address)

    def __ne__(self, other):
        return not self.__eq__(other)

    def set_rx_traffic(self, source, traffic):
        current_time = datetime.now()
        delta_time = (current_time - self.time).seconds

        if delta_time > self._config['THRESHOLD']['MAX_AVG_RX_WINDOW_SECONDS']:
            self.time = current_time
            self.rx_traffic = [traffic]
            self.rx_traffic_per_source[source] = [traffic]
        else:
            self.rx_traffic.append(traffic)
            self.rx_traffic_per_source[source].append(traffic)

        self._check_traffic_thresholds()

    def set_tx_traffic(self, destination, traffic):
        current_time = datetime.now()
        delta_time = (current_time - self.time).seconds

        if delta_time > self._config['THRESHOLD']['MAX_AVG_TX_WINDOW_SECONDS']:
            self.time = current_time
            self.tx_traffic = [traffic]
            self.tx_traffic_per_destination[destination] = [traffic]
        else:
            self.tx_traffic.append(traffic)
            self.tx_traffic_per_destination[destination].append(traffic)

    def get_avg_tx_traffic(self):
        return sum(self.tx_traffic)/float(len(self.tx_traffic))

    def get_avg_rx_traffic(self):
        return sum(self.rx_traffic)/float(len(self.rx_traffic))

    def get_avg_tx_traffic_per_destination(self, destination):
        return (sum(self.tx_traffic_per_destination[destination])
                / float(len(self.tx_traffic_per_destination[destination])))

    def get_avg_rx_traffic_per_source(self, source):
        return (sum(self.rx_traffic_per_source[source])
                / float(len(self.rx_traffic_per_source[source])))

    def _check_traffic_thresholds(self):
        if (self.get_avg_rx_traffic()
                >= self._config['THRESHOLD']['WARNING_MBPS']):
            for source, traffic in self.rx_traffic_per_source.iteritems():
                if (self.get_avg_rx_traffic_per_source(source)
                        >= self._config['THRESHOLD']['SINGLE_CONNECTION_MBPS']):
                    self.attackers.append(source)
                elif source in self.attackers:
                    self.attackers.remove(source)
        else:
            self.attackers = []


class Hosts:
    def __init__(self, config):
        self._hosts = []
        self._config = config
        self._datapath_id = self._config['NETWORK']['DATAPATH_ID']

        # TODO: Move addresses to the contract (stored in IPFS)
        ip_to_mac_mappings = self._config['NETWORK']['IP_TO_MAC_MAPPINGS']

        for ip_address, mac_address in ip_to_mac_mappings.iteritems():
            id = 'h' + ip_address.split(".")[3]
            self._hosts.append(Host(id=id,
                                    datapath_id=self._datapath_id,
                                    mac_address=mac_address,
                                    ip_address=ip_address,
                                    config=self._config))

    def get_host(self, mac_address=None, ip_address=None):
        if mac_address:
            host = Host(self._config, mac_address=mac_address)
            if host in self._hosts:
                return self._hosts[self._hosts.index(host)]
        elif ip_address:
            host = Host(self._config, ip_address=ip_address)
            if host in self._hosts:
                return self._hosts[self._hosts.index(host)]
        else:
            return None

    def get_total_inbound_traffic(self):
        inbound_traffic = 0.0
        for host in self._hosts:
            inbound_traffic += sum(host.rx_traffic)
        return inbound_traffic

    def get_total_outbound_traffic(self):
        outbound_traffic = 0.0
        for host in self._hosts:
            outbound_traffic += sum(host.tx_traffic)
        return outbound_traffic

    def detect_ongoing_attacks(self, datapath_id):
        attack_reports = []
        for host in self._hosts:
            if (host.datapath_id == datapath_id and
                host.get_avg_rx_traffic() >= self._config['THRESHOLD']
                                                         ['BLOCKING_MBPS']):
                timestamp = datetime.now().strftime(
                    self._config['DEFAULT']['TIMESTAMP_FORMAT']
                )
                attack_report = AttackReport(target=host.ip_address,
                                             action="blackhole",
                                             timestamp=timestamp,
                                             addresses=host.attackers)
                attack_reports.append(attack_report)
        return attack_reports
