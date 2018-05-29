import json
from threading import Thread

import requests
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (MAIN_DISPATCHER,
                                    DEAD_DISPATCHER,
                                    CONFIG_DISPATCHER)
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

import stalk.api as api
from configuration import Configuration
from flow_statistics_manager import FlowStatisticsManager
from logger import Logger
from pollen.database import PollenDatabase
from stalk.hosts import Hosts


class Controller(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)

        self._config = Configuration()
        self._logger = Logger("Stalk")
        self._database = PollenDatabase(self._config)
        self._datapaths = {}
        self._flow_statistics_manager = FlowStatisticsManager(self._config)
        self._hosts = Hosts(self._config)
        self._flow_statistics_thread = hub.spawn(self._request_flow_statistics)
        self._api_thread = Thread(target=self._start_api)
        self._api_thread.start()

    def _start_api(self):
        api.stalk_controller = self
        api.app.run(debug=False, host="localhost", port=6001)

    def _request_flow_statistics(self):
        while True:
            for datapath in self._datapaths.values():
                parser = datapath.ofproto_parser
                request = parser.OFPFlowStatsRequest(datapath)
                datapath.send_msg(request)

            if self._config['INTERVAL']['TRAFFIC_STATS_POLLING_SECONDS'] > 0:
                hub.sleep(self._config['INTERVAL']
                                      ['TRAFFIC_STATS_POLLING_SECONDS'])

    def get_datapath(self, datapath_id):
        if datapath_id in self._datapaths:
            return self._datapaths[datapath_id]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        if datapath.id not in self._datapaths:
            self._datapaths[datapath.id] = datapath

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER,
                                                DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self._datapaths:
                self._datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self._datapaths:
                del self._datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        datapath_id = ev.msg.datapath.id

        self._flow_statistics_manager.calculate_bandwidth_per_flow(datapath_id,
                                                                   ev.msg.body)
        flows = self._flow_statistics_manager.get_flows(datapath_id)
        for flow in flows:
            source_host = self._hosts.get_host(ip_address=flow.source)
            if source_host:
                source_host.set_tx_traffic(flow.destination, flow.mbps)
            destination_host = self._hosts.get_host(ip_address=flow.destination)
            if destination_host:
                destination_host.set_rx_traffic(flow.source, flow.mbps)

        total_inbound_traffic = self._hosts.get_total_inbound_traffic()
        total_outbound_traffic = self._hosts.get_total_outbound_traffic()

        if total_inbound_traffic >= 0.0 and total_outbound_traffic >= 0.0:
            self._database.update_inbound_traffic(datapath_id,
                                                  total_inbound_traffic)
            self._database.update_outbound_traffic(datapath_id,
                                                   total_outbound_traffic)

        self.find_and_report_attackers(datapath_id)

    def block_attackers(self, attack_report):
        blocked_addresses_by_datapath_id = {}
        for attacker_address in attack_report.addresses:
            attacker = self._hosts.get_host(ip_address=attacker_address)
            datapath = self.get_datapath(attacker.datapath_id)
            parser = datapath.ofproto_parser

            match = parser.OFPMatch(ipv4_dst=attack_report.target,
                                    ipv4_src=attacker.ip_address)
            ofproto = datapath.ofproto
            if attack_report.action == "blackhole":
                actions = [parser.OFPActionOutput(99)]
            instructions = [parser.OFPInstructionActions(ofproto
                                                         .OFPIT_APPLY_ACTIONS,
                                                         actions)]
            blocking_duration = (self._config['INTERVAL']
                                             ['MAX_BLOCKING_DURATION_SECONDS'])
            mod = parser.OFPFlowMod(datapath=datapath,
                                    command=ofproto.OFPFC_ADD,
                                    priority=999,
                                    idle_timeout=blocking_duration,
                                    hard_timeout=blocking_duration,
                                    match=match,
                                    instructions=instructions)
            datapath.send_msg(mod)
            self._logger.info("Blocked address {} targeting {}"
                              .format(attacker.ip_address,
                                      attack_report.target))
            if attacker.datapath_id not in blocked_addresses_by_datapath_id:
                blocked_addresses_by_datapath_id[attacker.datapath_id] = 0
            blocked_addresses_by_datapath_id[attacker.datapath_id] += 1
        for datapath_id, count in blocked_addresses_by_datapath_id.iteritems():
            self._database.update_blocked_addresses(datapath_id, count)

    def find_and_report_attackers(self, datapath_id):
        attack_reports = self._hosts.detect_ongoing_attacks(datapath_id)
        if len(attack_reports) > 0:
            dict_reports = {}
            count = 0
            for report in attack_reports:
                dict_reports[report.target] = json.loads(str(report))
                count += len(report.addresses)
            requests.post(
                self._config['ENDPOINT']['BLOSS'] + '/api/v1.0/report',
                json.dumps(dict_reports))
            self._database.update_reported_addresses(datapath_id, count)
            self._led_hotfix(count)

    # TODO: Make this obsolete by fixing the LED problem
    @staticmethod
    def _led_hotfix(count):
        # FIX to get the LEDs working properly.
        try:
            import socket
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            HOST = '192.168.30.18'
            PORT = 5050
            dst = (HOST, PORT)
            if len(count) >= 4:
                udp.sendto("1-inc", dst)
            elif len(count) < 4:
                udp.sendto("1-dec", dst)
        except:
            print "error"
            udp.close()
