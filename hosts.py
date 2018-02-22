import input
from datetime import datetime

class Host( object ):
    def __init__(self, host, dpid, port, mac_addr, ip_addr):
        self.id = host
        self.dpid = dpid
        self.port = port
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr

        self.rx_traffic = []
        self.tx_traffic = []

        self.tx_per_dst = {}
        self.rx_per_dst = {}

        self.avg_rx_per_src = {}
        self.avg_tx_per_dst = {}

        self.time = datetime.now()

    def set_rx_traffic(self, src, traffic):

        curr_time = datetime.now()
        delta_time = (curr_time - self.time).seconds

        if delta_time > input.MAX_TIME_WINDOW_AVG_RX_TRAFFIC:
            self.time = curr_time
            self.rx_traffic = [traffic]
            self.rx_per_dst[src] = [traffic]
            self.avg_rx_per_src[src] = self.get_avg_rx_traffic()

        else:
            self.rx_traffic.append(traffic)
            self.rx_per_dst[src] = self.rx_traffic
            self.avg_rx_per_src[src] = self.get_avg_rx_traffic()
        return True

    def set_tx_traffic(self, dst, traffic):

        curr_time = datetime.now()
        delta_time = (curr_time - self.time).seconds

        if delta_time > input.MAX_TIME_WINDOW_AVG_TX_TRAFFIC:
            self.time = curr_time
            self.tx_traffic = [traffic]
            self.tx_per_dst[dst] = [traffic]
            self.avg_tx_per_dst[dst] = self.get_avg_tx_traffic()
        else:
            self.tx_traffic.append(traffic)
            self.tx_per_dst[dst] = self.tx_traffic
            self.avg_tx_per_dst[dst] = self.get_avg_tx_traffic()
        return True

    def get_avg_tx_traffic(self):
        return sum(self.tx_traffic)/float(len(self.tx_traffic))

    def get_avg_rx_traffic(self):
        return sum(self.rx_traffic)/float(len(self.rx_traffic))

    def get_sum_tx_traffic(self):
        overall_traffic = 0.0
        for dst, traffic in self.avg_tx_per_dst.iteritems():
            overall_traffic += traffic
        return overall_traffic

    def get_sum_rx_traffic(self):
        overall_traffic = 0.0
        for src, traffic in self.avg_rx_per_src.iteritems():
            overall_traffic += traffic
        return overall_traffic

def init_hosts():
    '''
    Harcoded configuration of hosts, check "input.py" and the file network.py (mininet/custom/)
    :return: list of 'Host' objects containing all the attributes defined in the class.
    '''
    hl = []

    def create(dpid, ip_addr_list, mac_addr_list):
        for i in range(len(mac_addr_list)): #using the MAC addresses list to count the total of hosts
            id = "h"+ip_addr_list[i].split(".")[3] #h1, h2, ..., h13, h14, h15
            port = i+1
            macaddr = mac_addr_list[i]
            ipaddr = ip_addr_list[i]
            hl.append( Host( host=id, dpid=dpid, port=port, mac_addr=macaddr, ip_addr=ipaddr ) )

    create( dpid=123917682137032, ip_addr_list= input.NET1_IP_ADDR, mac_addr_list= input.NET1_MAC_ADDR )

    return hl

def get_host(hosts_list, mac=None, ip=None, dpid=None, port=None):
    '''
    Return a host by dpid/port or mac or ip
    :param list of Host objects: hosts list is maintained at the controller
    :return: host object
    '''
    if dpid and port:
        for h in hosts_list:
            if h.dpid == dpid and h.port == port:
                assert isinstance( h, object )
                return h
    if mac:
        for h in hosts_list:
            if h.mac_addr == mac:
                assert isinstance( h, object )
                return h
    elif ip:
        for h in hosts_list:
            if h.ip_addr == ip:
                assert isinstance( h, object )
                return h
    else:
        return None



