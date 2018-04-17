import configuration


def _retrieve_bc(self):
    global blocked_ip

    def blackhole_attacker_traffic(attacker, victim_ip_addr):
        datapath = self.get_datapath(attacker.dpid)
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(ipv4_dst=victim_ip_addr, ipv4_src=attacker.ip_addr)
        ofproto = datapath.ofproto
        actions = [parser.OFPActionOutput(99)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        timeout = configuration.get('INTERVALS', 'MAX_BLOCKING_DURATION_SECONDS')
        mod = parser.OFPFlowMod(datapath=datapath,
                                command=ofproto.OFPFC_ADD,
                                priority=999,
                                idle_timeout=timeout,
                                hard_timeout=timeout,
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