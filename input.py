from confidential import BC_ACCOUNT_PASSWORD

#################################################
#Controller Polling Interval (STATS) - in seconds
#################################################

STATS_POLLING_INTERVAL = 1
STATS_DDOSBC_RETRIEVE_INTERVAL = 1

#################################################
#Thresholds (THRESHOLD) - in mbps
#################################################

THRESHOLD_WARNING = 30
THRESHOLD_BLOCKING = 50

THRESHOLD_HOST_BLOCKING = 10
THRESHOLD_HOST_WARNING = 5
THRESHOLD_HOST_SINGLE_CONNECTION = 2

MAX_TIME_WINDOW_AVG_TX_TRAFFIC = 10 #seconds
MAX_TIME_WINDOW_AVG_RX_TRAFFIC = 10 #seconds

#################################################
#Hosts in the Network(s) (NET)
#################################################


NET1_AS_NETWORK = ["192.168.10.0/24"]
NET1_IP_ADDR = ["192.168.10.1", "192.168.10.2", "192.168.10.3","192.168.10.4","192.168.10.5","192.168.10.6"]
NET1_MAC_ADDR = ["64:D1:54:09:C1:31", "2C:4D:54:42:C4:76","2C:4D:54:42:C8:F1","2C:4D:54:42:C3:73","2C:4D:54:42:C1:76","2C:4D:54:42:C8:75"]
#
NET1_MAC_ADDR_ = {"192.168.10.1":"64:D1:54:09:C1:31","192.168.10.2":"2C:4D:54:42:C4:76","192.168.10.3":"2C:4D:54:42:C8:F1","192.168.10.5":"2C:4D:54:42:C3:73","192.168.10.4":"2C:4D:54:42:C1:76","192.168.10.6":"2C:4D:54:42:C8:75"}

NET1_ROUTER_IPADDR = "192.168.10.1"
NET1_ROUTER_MACADDR = "64:D1:54:09:C1:31"
NET1_ROUTER_PORT = 3

###

NET2_AS_NETWORK = ["192.168.20.0/24"]
NET2_IP_ADDR = ["192.168.20.8", "192.168.20.9","192.168.20.10","192.168.20.11","192.168.20.12"]
NET2_MAC_ADDR = ["2C:4D:54:42:BD:66", "2C:4D:54:42:C5:E2","2C:4D:54:42:C3:E9","2C:4D:54:42:C6:52","2C:4D:54:42:C8:4F"]
NET2_MAC_ADDR_ = {"192.168.20.8":"2C:4D:54:42:BD:66","192.168.20.9":"2C:4D:54:42:C5:E2","192.168.20.10":"2C:4D:54:42:C3:E9","192.168.20.11":"2C:4D:54:42:C6:52","192.168.20.12":"2C:4D:54:42:C8:4F"}

NET2_ROUTER_IPADDR = "192.168.20.1"
NET2_ROUTER_MACADDR = "6C:3B:6B:51:1D:2D"

###

NET3_AS_NETWORK = ["192.168.30.0/24"]
NET3_IP_ADDR = ["192.168.30.14", "192.168.30.15","192.168.30.16","192.168.30.17","192.168.30.18"]
NET3_MAC_ADDR = ["2C:4D:54:42:C8:7B","2C:4D:54:42:C9:C8","2C:4D:54:42:C9:F9","2C:4D:54:42:C5:AA","2C:4D:54:42:C9:13"]
NET3_MAC_ADDR_ = {"192.168.30.14":"2C:4D:54:42:C8:7B","192.168.30.15":"2C:4D:54:42:C9:C8","192.168.30.16":"2C:4D:54:42:C9:F9","192.168.30.17":"2C:4D:54:42:C5:AA","192.168.30.18":"2C:4D:54:42:C9:13"}

NET3_ROUTER_IPADDR = "192.168.30.1"
NET3_ROUTER_MACADDR = "E4:8D:8C:B1:FB:37"


#################################################
#Data to connect to the blockchain (bc = blockchain)
#################################################

BC_HOST_ADDRESS = "localhost"
BC_PORT = "8545"
###
BC_CONTRACT_ABI = [{"constant":"false","inputs":[{"name":"x","type":"string"}],"name":"set_network","outputs":[],"payable":"false","type":"function"},
                   {"constant":"false","inputs":[{"name":"x","type":"string"}],"name":"report_ipv4","outputs":[],"payable":"false","type":"function"},
                   {"constant":"true","inputs":[],"name":"retrieve_ipv4","outputs":[{"name":"","type":"string"}],"payable":"false","type":"function"},
                   {"constant":"true","inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":"false","type":"function"},
                   {"constant":"true","inputs":[],"name":"get_network","outputs":[{"name":"","type":"string"}],"payable":"false","type":"function"}]

###
BC_CONTRACT_ADDRESS = '0x7cc7a2f1113165a92bb5fb657cac997261211f40'
#BC_CONTRACT_ADDRESS = "0xb70b1450b7afeb50f68617297fbff6772a9aea11"
###

BC_ACCOUNT_TIME = 9999999
###


def transact_with_gas(account_address):
    return {'from':account_address, 'gas': '4700000'}

BC_AS_NETWORKS = {
    'ASN1': NET1_AS_NETWORK,
    'ASN2': NET2_AS_NETWORK,
    'ASN3': NET3_AS_NETWORK
}
###
BC_MAX_REPORT_INTERVAL = 30 #seconds
BC_MIN_REPORT_INTERVAL = 10 #seconds
BC_MAX_RETRIEVE_INTERVAL = 60 * 2 #seconds - if the message is 5 mins old then ignore it.

###
BC_TIMESTAMP_FORMAT = '%Y-%m-%d-%H:%M:%S'


#################################################
#InfluxDB (idb)
#################################################

DB_HOST = '172.10.15.31'
DB_PORT = 8086
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'mydb'

#################################################
#Protection Configuration (def)
#################################################

DEF_IDLE_TIMEOUT = 30 #seconds

