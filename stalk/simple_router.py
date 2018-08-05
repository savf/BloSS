from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet.arp import ARP_HW_TYPE_ETHERNET
from ryu.lib.packet.arp import arp
from ryu.lib.packet.ethernet import ethernet
from ryu.lib.packet.ipv4 import ipv4
from ryu.lib.packet.packet import Packet
from ryu.ofproto import ether
from ryu.ofproto import ofproto_v1_3

from configuration import Configuration
from logger import Logger
from utils import calculate_subnet


# Modified from: https://github.com/ttsubo/simpleRouter/blob/master/ryu-app/blog/article_02/simpleForward.py


class SimpleRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleRouter, self).__init__(*args, **kwargs)
        self._config = Configuration()
        self._logger = Logger("SimpleRouter")
        addresses = self._config['NETWORK']['ADDRESSES']
        self._ip_to_mac_mappings = {}
        for _, address_mappings in addresses.iteritems():
            self._ip_to_mac_mappings.update(address_mappings)
        self._ip_to_mac_mappings[self._config['NETWORK']['ROUTER_IP']] =\
            self._config['NETWORK']['ROUTER_MAC']
        self._out_ports = self._config['NETWORK']['OUT_PORTS']

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        datapath.id = msg.datapath_id
        ofproto_parser = datapath.ofproto_parser

        set_config = ofproto_parser.OFPSetConfig(
            datapath,
            datapath.ofproto.OFPC_FRAG_NORMAL,
            datapath.ofproto.OFPCML_MAX
        )
        datapath.send_msg(set_config)
        self.install_table_miss(datapath, datapath.id)

    @staticmethod
    def install_table_miss(datapath, datapath_id):
        datapath.id = datapath_id

        match = datapath.ofproto_parser.OFPMatch()

        actions = [datapath.ofproto_parser.OFPActionOutput(
                   datapath.ofproto.OFPP_CONTROLLER,
                   datapath.ofproto.OFPCML_NO_BUFFER)]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(datapath=datapath,
                                                 priority=0,
                                                 buffer_id=0xffffffff,
                                                 match=match,
                                                 instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']

        packet = Packet(msg.data)
        ether_frame = packet.get_protocol(ethernet)
        if ether_frame.ethertype == ether.ETH_TYPE_ARP:
            self.receive_arp(datapath, packet, ether_frame)
            return 0
        elif ether_frame.ethertype == ether.ETH_TYPE_IP:
            self.receive_ip(datapath, packet, in_port)
            return 1
        else:
            return 2

    def receive_ip(self, datapath, packet, in_port):
        ip_packet = packet.get_protocol(ipv4)
        self._logger.debug("receive IP packet {} => {} (in port: {})"
                           .format(ip_packet.src, ip_packet.dst, in_port))

        source_ip = ip_packet.src
        source_subnet = calculate_subnet(source_ip,
                                         '255.255.255.0')
        destination_ip = ip_packet.dst
        destination_subnet = calculate_subnet(destination_ip,
                                              '255.255.255.0')
        if (destination_subnet in self._out_ports
                and source_subnet in self._out_ports):
            self.add_flow(datapath=datapath,
                          ethertype=ether.ETH_TYPE_IP,
                          source_ip=source_ip,
                          target_ip=destination_ip,
                          out_port=self._out_ports[destination_subnet])

    def receive_arp(self, datapath, packet, ether_frame):
        arp_packet = packet.get_protocol(arp)

        if arp_packet.opcode == 1:
            self.request_arp(datapath, ether_frame, arp_packet)
        elif arp_packet.opcode == 2:
            self.reply_arp(datapath, ether_frame, arp_packet)
            pass

    def request_arp(self, datapath, ether_frame, arp_packet):
        source_ip = arp_packet.src_ip
        source_mac = ether_frame.src
        source_subnet = calculate_subnet(source_ip,
                                         '255.255.255.0')
        destination_ip = arp_packet.dst_ip
        destination_subnet = calculate_subnet(destination_ip,
                                              '255.255.255.0')
        self._logger.debug("ARP request packet {} => {} (source mac: {})"
                           .format(source_ip, destination_ip, source_mac))

        try:
            subnetworks = self._config['NETWORK']['SUBNETWORKS']
            if destination_subnet in subnetworks:
                destination_mac = self._ip_to_mac_mappings[destination_ip]
                self.send_arp(datapath=datapath,
                              opcode=2,
                              source_mac=destination_mac,
                              source_ip=destination_ip,
                              destination_mac=source_mac,
                              destination_ip=source_ip,
                              out_port=self._out_ports[source_subnet])
            else:
                # ARP request can't be answered in our subnet,
                # relay to correct subnet
                self.send_arp(datapath=datapath,
                              opcode=1,
                              source_mac=source_mac,
                              source_ip=source_ip,
                              destination_mac=ether_frame.dst,
                              destination_ip=destination_ip,
                              out_port=self._out_ports[destination_subnet])
        except Exception as e:
            self._logger.debug("Failed to handle ARP request {} => {}"
                               .format(source_ip, destination_ip))
            return

    def reply_arp(self, datapath, ether_frame, arp_packet):
        source_ip = arp_packet.src_ip
        source_mac = ether_frame.src
        destination_ip = arp_packet.dst_ip
        destination_mac = ether_frame.dst
        destination_subnet = calculate_subnet(destination_ip,
                                              '255.255.255.0')

        self._logger.debug("ARP reply packet {} => {} (source mac: {})"
                           .format(source_ip, destination_ip, source_mac))

        try:
            self.send_arp(datapath=datapath,
                          opcode=2,
                          source_mac=source_mac,
                          source_ip=source_ip,
                          destination_mac=destination_mac,
                          destination_ip=destination_ip,
                          out_port=self._out_ports[destination_subnet])
        except Exception as e:
            return

    @staticmethod
    def send_arp(datapath, opcode, source_mac, source_ip,
                 destination_mac, destination_ip, out_port):

        in_port = datapath.ofproto.OFPP_CONTROLLER

        e = ethernet(destination_mac, source_mac, ether.ETH_TYPE_ARP)
        a = arp(ARP_HW_TYPE_ETHERNET, ether.ETH_TYPE_IP,
                6,  # ethernet mac address length
                4,  # ipv4 address length
                opcode,
                source_mac, source_ip,
                destination_mac, destination_ip)
        p = Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port, 0)]
        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath,
                                                   buffer_id=0xffffffff,
                                                   in_port=in_port,
                                                   actions=actions,
                                                   data=p.data)
        datapath.send_msg(out)

    @staticmethod
    def add_flow(datapath, ethertype, source_ip, target_ip, out_port):
        match = datapath.ofproto_parser.OFPMatch(
                eth_type=ethertype,
                ipv4_src=source_ip,
                ipv4_dst=target_ip )
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port, 0)]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                cookie=0,
                cookie_mask=0,
                flags=datapath.ofproto.OFPFF_CHECK_OVERLAP,
                table_id=0,
                command=datapath.ofproto.OFPFC_ADD,
                datapath=datapath,
                idle_timeout=0,
                hard_timeout=0,
                priority=0xff,
                buffer_id=0xffffffff,
                out_port=datapath.ofproto.OFPP_ANY,
                out_group=datapath.ofproto.OFPG_ANY,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)
