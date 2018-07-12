from datetime import datetime

from pollen.attack_reporting import AttackReport
import json
from utils import calculate_subnet, safedivision


class Attackers:
    def __init__(self):
        self._addresses_by_subnetwork = {}

    def __str__(self):
        return json.dumps(self._addresses_by_subnetwork)

    def __iter__(self):
        return self._addresses_by_subnetwork.iteritems()

    def add_address(self, address):
        subnetwork = calculate_subnet(address, "255.255.255.0")
        if subnetwork not in self._addresses_by_subnetwork:
            self._addresses_by_subnetwork[subnetwork] = set()
        self._addresses_by_subnetwork[subnetwork].add(address)

    def remove_address(self, address):
        subnetwork = calculate_subnet(address, "255.255.255.0")
        if subnetwork in self._addresses_by_subnetwork:
            self._addresses_by_subnetwork[subnetwork].remove(address)

    def get_addresses(self, subnetwork):
        if subnetwork in self._addresses_by_subnetwork:
            return self._addresses_by_subnetwork[subnetwork]
        return None


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
        self.attackers = Attackers()
        self._config = config

        self.rx_traffic_per_source = {}
        self.tx_traffic_per_destination = {}

        self.last_rx_reset = datetime.now()
        self.last_tx_reset = datetime.now()

    def __eq__(self, other):
        return (self.ip_address == other.ip_address or
                self.mac_address == other.mac_address)

    def __ne__(self, other):
        return not self.__eq__(other)

    def set_rx_traffic(self, source, traffic):
        current_time = datetime.now()
        delta_time = (current_time - self.last_rx_reset).seconds

        if delta_time > self._config['THRESHOLD']['MAX_AVG_RX_WINDOW_SECONDS']:
            self.last_rx_reset = current_time
            self.rx_traffic_per_source = dict()
            self.rx_traffic_per_source[source] = [traffic]
        else:
            if source in self.rx_traffic_per_source:
                self.rx_traffic_per_source[source].append(traffic)
            else:
                self.rx_traffic_per_source[source] = [traffic]

        self._check_traffic_thresholds()

    def set_tx_traffic(self, destination, traffic):
        current_time = datetime.now()
        delta_time = (current_time - self.last_tx_reset).seconds

        if delta_time > self._config['THRESHOLD']['MAX_AVG_TX_WINDOW_SECONDS']:
            self.last_tx_reset = current_time
            self.tx_traffic_per_destination = dict()
            self.tx_traffic_per_destination[destination] = [traffic]
        else:
            if destination in self.tx_traffic_per_destination:
                self.tx_traffic_per_destination[destination].append(traffic)
            else:
                self.tx_traffic_per_destination[destination] = [traffic]

    def get_avg_tx_traffic(self):
        result = 0.0
        for destination, _ in self.tx_traffic_per_destination.iteritems():
            result += self._get_avg_tx_traffic_per_destination(destination)
        return result

    def get_avg_rx_traffic(self):
        result = 0.0
        for source, _ in self.rx_traffic_per_source.iteritems():
            result += self._get_avg_rx_traffic_per_source(source)
        return result

    def _get_avg_tx_traffic_per_destination(self, destination):
        return safedivision(
            sum(self.tx_traffic_per_destination[destination]),
            float(len(self.tx_traffic_per_destination[destination]))
        )

    def _get_avg_rx_traffic_per_source(self, source):
        return safedivision(
            sum(self.rx_traffic_per_source[source]),
            float(len(self.rx_traffic_per_source[source]))
        )

    def _check_traffic_thresholds(self):
        if (self.get_avg_rx_traffic()
                >= self._config['THRESHOLD']['WARNING_MBPS']):
            for source, traffic in self.rx_traffic_per_source.iteritems():
                if (self._get_avg_rx_traffic_per_source(source)
                        >= self._config['THRESHOLD']['SINGLE_CONNECTION_MBPS']):
                    self.attackers.add_address(source)
                elif source in self.attackers:
                    self.attackers.remove_address(source)
        else:
            self.attackers = Attackers()


class Hosts:
    def __init__(self, config):
        self._hosts = {}
        self._config = config

        # TODO: Move addresses to the contract (stored in IPFS)
        addresses = self._config['NETWORK']['ADDRESSES']

        for datapath_id, ip_to_mac_mappings in addresses.iteritems():
            self._hosts[datapath_id] = []
            for ip_address, mac_address in ip_to_mac_mappings.iteritems():
                id = 'h' + ip_address.split(".")[3]
                self._hosts[datapath_id].append(Host(id=id,
                                                     datapath_id=datapath_id,
                                                     mac_address=mac_address,
                                                     ip_address=ip_address,
                                                     config=self._config))

    def get_host(self, mac_address=None, ip_address=None):
        if mac_address:
            host = Host(self._config, mac_address=mac_address)
            for _, hosts in self._hosts.iteritems():
                if host in hosts:
                    return hosts[hosts.index(host)]
        elif ip_address:
            host = Host(self._config, ip_address=ip_address)
            for _, hosts in self._hosts.iteritems():
                if host in hosts:
                    return hosts[hosts.index(host)]
        else:
            return None

    def get_total_inbound_traffic(self):
        inbound_traffic = 0.0
        for _, hosts in self._hosts.iteritems():
            for host in hosts:
                inbound_traffic += host.get_avg_rx_traffic()
        return inbound_traffic

    def get_total_outbound_traffic(self):
        outbound_traffic = 0.0
        for _, hosts in self._hosts.iteritems():
            for host in hosts:
                outbound_traffic += host.get_avg_tx_traffic()
        return outbound_traffic

    def detect_ongoing_attacks(self, datapath_id):
        attack_reports = []
        for host in self._hosts[str(datapath_id)]:
            if (host.get_avg_rx_traffic() >= self._config['THRESHOLD']
                                                         ['BLOCKING_MBPS']):
                for subnetwork, addresses in host.attackers:
                    timestamp = datetime.now().strftime(
                        self._config['DEFAULT']['TIMESTAMP_FORMAT']
                    )

                    attack_report = AttackReport(target=host.ip_address,
                                                 action="blackhole",
                                                 timestamp=timestamp,
                                                 subnetwork=subnetwork,
                                                 addresses=addresses)
                    attack_reports.append(attack_report)
        return attack_reports
