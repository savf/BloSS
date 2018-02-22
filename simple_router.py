import logging

from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet.packet import Packet
from ryu.lib.packet.ethernet import ethernet
from ryu.lib.packet.arp import arp
from ryu.lib.packet.ipv4 import ipv4
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.ofproto import inet

LOG = logging.getLogger('SimpleForward')
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

#Modified from: https://github.com/ttsubo/simpleRouter/blob/master/ryu-app/blog/article_02/simpleForward.py

import input

class SimpleForward(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleForward, self).__init__(*args, **kwargs)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        datapath.id = msg.datapath_id
        ofproto_parser = datapath.ofproto_parser

        set_config = ofproto_parser.OFPSetConfig(
            datapath,
            datapath.ofproto.OFPC_FRAG_NORMAL,
            datapath.ofproto.OFPCML_MAX
        )
        datapath.send_msg(set_config)
        self.install_table_miss(datapath, datapath.id)


    def install_table_miss(self, datapath, dpid):
        datapath.id = dpid

        match = datapath.ofproto_parser.OFPMatch()

        actions = [datapath.ofproto_parser.OFPActionOutput(
                datapath.ofproto.OFPP_CONTROLLER,
                datapath.ofproto.OFPCML_NO_BUFFER)]
        inst = [datapath.ofproto_parser.OFPInstructionActions(
                datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
                datapath=datapath,
                priority=0,
                buffer_id=0xffffffff,
                match=match,
                instructions=inst)
        datapath.send_msg(mod)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        inPort = msg.match['in_port']

        packet = Packet(msg.data)
        etherFrame = packet.get_protocol(ethernet)
        if etherFrame.ethertype == ether.ETH_TYPE_ARP:
            self.receive_arp(datapath, packet, etherFrame, inPort)
            return 0
        elif etherFrame.ethertype == ether.ETH_TYPE_IP:
            self.receive_ip(datapath, packet, etherFrame, inPort)
            return 1
        else:
            #LOG.debug("receive Unknown packet %s => %s (port%d)"
            #           %(etherFrame.src, etherFrame.dst, inPort))
            #self.print_etherFrame(etherFrame)
            #LOG.debug("Drop packet")
            return 2


    def receive_ip(self, datapath, packet, etherFrame, inPort):
        ipPacket = packet.get_protocol(ipv4)
        #LOG.debug("receive IP packet %s => %s (in port:%d)"
        #               %(ipPacket.src, ipPacket.dst, inPort))

        #self.print_etherFrame(etherFrame)
        #self.print_ipPacket(ipPacket)

        src_ip = ipPacket.src
        dst_ip = ipPacket.dst

        if "192.168.20." in dst_ip or "192.168.30." in dst_ip:
            self.add_flow(datapath=datapath, inPort=input.NET1_ROUTER_PORT, ethertype=ether.ETH_TYPE_IP,
                          sourceIp=src_ip, targetIp=dst_ip, outPort=1)

        elif "192.168.10." in dst_ip:
            if dst_ip in input.NET1_IP_ADDR:
                self.add_flow(datapath=datapath, inPort=1, ethertype=ether.ETH_TYPE_IP,
                          sourceIp=src_ip, targetIp=dst_ip, outPort=input.NET1_ROUTER_PORT)

    def receive_arp(self, datapath, packet, etherFrame, inPort):
        arpPacket = packet.get_protocol(arp)

        if arpPacket.opcode == 1:
            "ARP Request"
            self.reply_arp(datapath, etherFrame, arpPacket)
        elif arpPacket.opcode == 2:
            "ARP Reply"
            #TODO
            # self.send_flow(datapath)
            pass

    def reply_arp(self, datapath, etherFrame, arpPacket):

        dstIp = arpPacket.src_ip
        srcIp = arpPacket.dst_ip
        dstMac = etherFrame.src

        #self.print_etherFrame(etherFrame)
        #self.print_arpPacket(arpPacket)

        try:
            if "192.168.10." in dstIp:
                if "192.168.20." in srcIp:
                    for ipaddr in input.NET2_IP_ADDR:
                        if ipaddr == srcIp:
                            srcMac = input.NET2_MAC_ADDR_[ipaddr]
                if "192.168.30." in srcIp:
                    for ipaddr in input.NET3_IP_ADDR:
                        if ipaddr == srcIp:
                            srcMac = input.NET3_MAC_ADDR_[ipaddr]
                self.send_arp(datapath, 2, srcMac, srcIp, dstMac, input.NET1_ROUTER_IPADDR,
                              3)
        except Exception as e:
            #print repr(e)
            return

    def send_arp(self, datapath, opcode, srcMac, srcIp, dstMac, dstIp, outPort):

        targetMac = dstMac
        targetIp = dstIp

        e = ethernet(dstMac, srcMac, ether.ETH_TYPE_ARP)
        a = arp(1, 0x0800, 6, 4, opcode, srcMac, srcIp, targetMac, targetIp)
        p = Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()

        actions = [datapath.ofproto_parser.OFPActionOutput(outPort, 0)]
        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=0xffffffff,
            in_port=datapath.ofproto.OFPP_CONTROLLER,
            actions=actions,
            data=p.data)
        datapath.send_msg(out)


    def add_flow(self, datapath, inPort, ethertype, sourceIp, targetIp, outPort):

        match = datapath.ofproto_parser.OFPMatch(
                #in_port=inPort,
                eth_type=ethertype,
                ipv4_src=sourceIp,
                ipv4_dst=targetIp )
        actions =[datapath.ofproto_parser.OFPActionOutput(outPort, 0)]
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


    def print_etherFrame(self, etherFrame):
        LOG.debug("---------------------------------------")
        LOG.debug("eth_dst_address: %s", etherFrame.dst)
        LOG.debug("eth_src_address: %s", etherFrame.src)
        LOG.debug("eth_ethertype: 0x%04x", etherFrame.ethertype)
        LOG.debug("---------------------------------------")


    def print_arpPacket(self, arpPacket):
        LOG.debug("arp_hwtype: %d", arpPacket.hwtype)
        LOG.debug("arp_proto: 0x%04x", arpPacket.proto)
        LOG.debug("arp_hlen: %d", arpPacket.hlen)
        LOG.debug("arp_plen: %d", arpPacket.plen)
        LOG.debug("arp_opcode: %d", arpPacket.opcode)
        LOG.debug("arp_src_mac: %s", arpPacket.src_mac)
        LOG.debug("arp_src_ip: %s", arpPacket.src_ip)
        LOG.debug("arp_dst_mac: %s", arpPacket.dst_mac)
        LOG.debug("arp_dst_ip: %s", arpPacket.dst_ip)
        LOG.debug("---------------------------------------")


    def print_ipPacket(self, ipPacket):
        LOG.debug("ip_version: %d", ipPacket.version)
        LOG.debug("ip_header_length: %d", ipPacket.header_length)
        LOG.debug("ip_tos: %d", ipPacket.tos)
        LOG.debug("ip_total_length: %d", ipPacket.total_length)
        LOG.debug("ip_identification: %d", ipPacket.identification)
        LOG.debug("ip_flags: %d", ipPacket.flags)
        LOG.debug("ip_offset: %d", ipPacket.offset)
        LOG.debug("ip_ttl: %d", ipPacket.ttl)
        LOG.debug("ip_proto: %d", ipPacket.proto)
        LOG.debug("ip_csum: %d", ipPacket.csum)
        LOG.debug("ip_src: %s", ipPacket.src)
        LOG.debug("ip_dst: %s", ipPacket.dst)
        LOG.debug("---------------------------------------")

