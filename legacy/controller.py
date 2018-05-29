from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from collections import defaultdict
from datetime import datetime
from ryu.log import

import dbinflux as db
import ddosbc as bc
from stalk import hosts as host_mgmt
import input


blocked_ip = []


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
        if dpid in self.datapaths:
            return self.datapaths[dpid]

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
        global blocked_ip

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
                                    #buffer_id=ofproto.OFP_NO_BUFFER,
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
                            blocked_ip.append(attacker.ip_addr)
                            attacker.time_blocked = datetime.now()
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

        global blocked_ip
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
                #todo: fix this crap
                # soft cap because we have fast ethernet switches
                # and gigabit hosts
                if traffic_mbps > 50.0: traffic_mbps = 50.0
                if traffic_mbps < 0.0: traffic_mbps = 0.0
                #
                try:
                    if host.ip_addr in blocked_ip:
                        traffic_mbps = 0.0
                except:
                    pass

                if src == host.ip_addr:
                    src_flag = True
                    host.set_tx_traffic(dst, traffic_mbps)

                elif dst == host.ip_addr:
                    dst_flag = True
                    host.set_rx_traffic(src, traffic_mbps)

        #if not src_flag and not dst_flag:
        #    for host in self.hosts:
        #        db.update_outbound_intratraffic(host.id, host.ip_addr, 0.0)
        #        db.update_inbound_intratraffic(host.id, host.ip_addr, 0.0)


        inbound_mbps = 0.0
        outbound_mbps = 0.0

        for host in self.hosts:
            #db.update_outbound_intratraffic(host.id, host.ip_addr, host.get_sum_tx_traffic())
            #db.update_inbound_intratraffic(host.id, host.ip_addr, host.get_sum_rx_traffic())
            inbound_mbps += host.get_sum_rx_traffic()
            outbound_mbps += host.get_sum_tx_traffic()

        if inbound_mbps >= 0.0 and outbound_mbps >= 0.0:
            db.update_inbound_traffic(dpid, inbound_mbps)
            db.update_outbound_traffic(dpid, outbound_mbps)

        self.check_hosts_threshold(dpid)

        # Update num reported addresses
        count = 0
        for issuer, attacker_list in self.suspicious_hosts.iteritems():
            count += len(attacker_list)
            for ip in attacker_list:
                if ip not in blocked_ip:
                    blocked_ip.append(ip)
        db.update_reported_addr(dpid, count)

        # Check idle time-out to unblock hosts
        current_timestamp = datetime.now()
        for host in self.hosts:
            delta_timestamp_seconds = (current_timestamp - host.time_blocked).seconds
            if host.ip_addr in blocked_ip and delta_timestamp_seconds > input.DEF_IDLE_TIMEOUT:
                blocked_ip.remove(host.ip_addr)

        # Update num blocked addresses
        try:
            num = 0 #todo: quick fix because I only have 4 hosts. Check why it is appearing more than 4.
            if len(blocked_ip) > 4:
                num = 4
            else:
                num = len(blocked_ip)
            db.update_blocked_addr(dpid, num)
        except:
            db.update_blocked_addr(dpid, 0)

        # FIX to get the LEDs working properly.
        try:
            import socket
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            HOST = '192.168.30.18'  # Endereco IP do Servidor
            PORT = 5050  # Porta que o Servidor esta
            dst = (HOST, PORT)
            if len(blocked_ip) >= 4:
                udp.sendto("1-inc", dst)
            elif len(blocked_ip) < 4:
                udp.sendto("1-dec", dst)
        except:
            print "error"
            udp.close()


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
            # TODO: Could be a bug, since function is not called..
            if issuer.get_avg_rx_traffic >= input.THRESHOLD_HOST_BLOCKING:
                self.check_hosts_warning_rx_threshold()
                bc.report_ipv4(self.suspicious_hosts)
            else:
                self.check_hosts_warning_rx_threshold()