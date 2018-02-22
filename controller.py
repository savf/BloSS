from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from collections import defaultdict

import dbinflux as db
import ddosbc as bc
import hosts as host_mgmt
import input



class Controller(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):

        super(Controller, self).__init__(*args, **kwargs)

        self.datapaths = {}

        '''
        Structures to store/verify suspicious hosts
        '''

        self.suspicious_hosts = {}
        self.eval_domain_traffic = []

        '''
        Structures to keep port and flow statistics
        '''

        self.prev_stats_ports = defaultdict(lambda: defaultdict(lambda: None))
        self.prev_stats_flows = defaultdict(lambda: defaultdict(lambda: None))

        '''
        Create our hosts
        '''

        self.hosts = host_mgmt.init_hosts()

        '''
        Blockchain connection
        '''
        bc.connect()

        '''
        Methods on the polling interval
        '''

        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        if datapath.id not in self.datapaths:
            self.datapaths[datapath.id] = datapath

    def get_datapath(self, dpid):
        for id, value in self.datapaths.iteritems():
            if dpid == id:
                return self.datapaths[id]

    '''
    Handle OpenFlow state changes updating the list
    of node identifiers (datapath id's -> dpid)
    '''

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]

        self.ddosbc_thread = hub.spawn(self._retrieve_bc)

    def _retrieve_bc(self):

        def block_host(attacker, victim_ip_addr):
            datapath = self.get_datapath(attacker.dpid)
            parser = datapath.ofproto_parser
            match = parser.OFPMatch(ipv4_dst=victim_ip_addr, ipv4_src=attacker.ip_addr)
            ofproto = datapath.ofproto
            actions = [parser.OFPActionOutput(99)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 actions)]
            idle_timeout = hard_timeout = input.DEF_IDLE_TIMEOUT
            mod = parser.OFPFlowMod(datapath=datapath,
                                    command=ofproto.OFPFC_ADD,
                                    buffer_id=ofproto.OFP_NO_BUFFER,
                                    priority=999,
                                    idle_timeout=idle_timeout,
                                    hard_timeout=hard_timeout,
                                    match=match,
                                    instructions=inst)
            datapath.send_msg(mod)
            return True

        while True:
            try:
                hash, attackers = bc.retrieve_ipv4()
            except:
                hub.sleep(input.STATS_DDOSBC_RETRIEVE_INTERVAL)
                continue
            if attackers:
                blocked_addresses = []
                for issuer, addresses in attackers.iteritems():
                    for ip_addr in addresses:
                        attacker = host_mgmt.get_host(self.hosts, ip=ip_addr)
                        if attacker:
                            block_host(attacker, issuer)
                            blocked_addresses.append(attacker.ip_addr)

                if len(blocked_addresses) > 0:
                    bc.confirm_addresses_block(hash, blocked_addresses)

            hub.sleep(input.STATS_DDOSBC_RETRIEVE_INTERVAL)

    '''
    Request Flow/Port statistics
    '''

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                parser = dp.ofproto_parser
                req = parser.OFPFlowStatsRequest(dp)
                dp.send_msg(req)

            # Polling interval cannot be zero or negative
            if input.STATS_POLLING_INTERVAL > 0:
                hub.sleep(input.STATS_POLLING_INTERVAL)

    '''
    Convert bytes to Mbps
    '''

    def bytes_to_mbps(self, bytes):
        mbps = ((bytes / 1024.0 / 1024.0) * 8) / input.STATS_POLLING_INTERVAL
        return mbps

    '''
    Handle flow-statistics
    '''

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):

        dpid = ev.msg.datapath.id

        src_flag = False
        dst_flag = False

        for stat in ev.msg.body:
            try:
                match = (stat.match['ipv4_src'], stat.match['ipv4_dst'])
            except:
                continue

            if not self.prev_stats_flows[dpid][match]:
                self.prev_stats_flows[dpid][match] = 0

            prev_byte_count = self.prev_stats_flows[dpid][match]
            delta_bytes_count = stat.byte_count - prev_byte_count
            self.prev_stats_flows[dpid][match] = stat.byte_count

            traffic_mbps = self.bytes_to_mbps(delta_bytes_count)

            src = stat.match['ipv4_src']
            dst = stat.match['ipv4_dst']

            for host in self.hosts:
                # todo: fix this crap
                # soft cap because we have fast ethernet switches
                # and gigabit hosts
                if traffic_mbps > 50.0: traffic_mbps = 50.0
                if traffic_mbps < 0.0: traffic_mbps = 0.0
                #

                if src == host.ip_addr:
                    src_flag = True
                    host.set_tx_traffic(dst, traffic_mbps)
                    db.update_outbound_intratraffic(host.id, host.ip_addr, host.get_sum_tx_traffic())

                elif dst == host.ip_addr:
                    dst_flag = True
                    host.set_rx_traffic(src, traffic_mbps)
                    db.update_inbound_intratraffic(host.id, host.ip_addr, host.get_sum_rx_traffic())

        if not src_flag and not dst_flag:
            for host in self.hosts:
                db.update_outbound_intratraffic(host.id, host.ip_addr, 0.0)
                db.update_inbound_intratraffic(host.id, host.ip_addr, 0.0)

        inbound_mbps = 0.0
        outbound_mbps = 0.0

        for host in self.hosts:
            inbound_mbps += host.get_sum_rx_traffic()
            outbound_mbps += host.get_sum_tx_traffic()


        if inbound_mbps >= 0.0 and outbound_mbps >= 0.0:
            db.update_inbound_traffic(dpid, inbound_mbps)
            db.update_outbound_traffic(dpid, outbound_mbps)


        self.check_hosts_threshold(dpid)

    def check_hosts_warning_rx_threshold(self):
        for issuer in self.hosts:
            if issuer.get_avg_rx_traffic >= input.THRESHOLD_HOST_WARNING:
                for suspect, traffic in issuer.avg_rx_per_src.iteritems():
                    if traffic >= input.THRESHOLD_HOST_SINGLE_CONNECTION:
                        if issuer.ip_addr not in self.suspicious_hosts:
                            self.suspicious_hosts[issuer.ip_addr] = []
                        else:
                            if suspect not in self.suspicious_hosts[issuer.ip_addr]:
                                self.suspicious_hosts[issuer.ip_addr].append(suspect)

                    elif traffic < input.THRESHOLD_HOST_SINGLE_CONNECTION \
                            and issuer.ip_addr in self.suspicious_hosts \
                            and suspect in self.suspicious_hosts[issuer.ip_addr]:
                        self.suspicious_hosts[issuer.ip_addr].remove(suspect)

    def check_hosts_threshold(self, dpid):
        for issuer in self.hosts:
            if issuer.get_avg_rx_traffic >= input.THRESHOLD_HOST_BLOCKING:
                self.check_hosts_warning_rx_threshold()
                bc.report_ipv4(self.suspicious_hosts)
            else:
                self.check_hosts_warning_rx_threshold()