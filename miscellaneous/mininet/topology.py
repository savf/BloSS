#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController, CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
from time import sleep

from requests import put
from json import dumps
from subprocess import check_output
from os import listdir
import re
import socket


"sFlow Topology -> JSON"

collector = '127.0.0.1'
sampling = 10
polling = 10

def getIfInfo(ip):
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect((ip, 0))
      ip = s.getsockname()[0]
      ifconfig = check_output(['ifconfig'])
      ifs = re.findall(r'^(\S+).*?inet addr:(\S+).*?', ifconfig, re.S|re.M)
      for entry in ifs:
            if entry[1] == ip:
              return entry
      
def sendTopology(net,agent,collector):
      print "*** Sending topology"
      topo = {'nodes':{}, 'links':{}}
      for s in net.switches:
            topo['nodes'][s.name] = {'agent':agent, 'ports':{}}
      path = '/sys/devices/virtual/net/'
      for child in listdir(path):
            parts = re.match('(^s[0-9]+)-(.*)', child)
            if parts == None: continue
            ifindex = open(path+child+'/ifindex').read().split('\n',1)[0]
            topo['nodes'][parts.group(1)]['ports'][child] = {'ifindex': ifindex}
      i = 0
      for s1 in net.switches:
        j = 0
        for s2 in net.switches:
              if j > i:
                    intfs = s1.connectionsTo(s2)
                    for intf in intfs:
                          s1ifIdx = topo['nodes'][s1.name]['ports'][intf[0].name]['ifindex']
                          s2ifIdx = topo['nodes'][s2.name]['ports'][intf[1].name]['ifindex']
                          linkName = '%s-%s' % (s1.name, s2.name)
                          topo['links'][linkName] = {'node1': s1.name, 'port1': intf[0].name, 'node2': s2.name, 'port2': intf[1].name}
              j += 1
        i += 1

      put('http://'+collector+':8008/topology/json',data=dumps(topo))


def multiController():

    net = Mininet(controller=RemoteController, switch=OVSSwitch, host=CPULimitedHost, link=TCLink, autoSetMacs=True)

    print "*** Creating (reference) Controller"
    net.addController('c1', port=6633, controller=RemoteController)
    #net.addController('c2', port=6634, controller=RemoteController)
    #net.addController('c3', port=6635, controller=RemoteController)

    print "*** Creating Switch(es)"
    s1 = net.addSwitch('s1', listenPort=6633)
    s2 = net.addSwitch('s2', listenPort=6633)
    s3 = net.addSwitch('s3', listenPort=6633)

    print "*** Creating Host(s)"

    "List of hosts of each network domain (A, B, C)"
    hosts_a = []
    hosts_b = []
    hosts_c = []

    for h in range(1,6):
        hosts_a.append(net.addHost('h%d' % h, cpu=0.1))

    for h in range(6,11):
        hosts_b.append(net.addHost('h%d' % h, cpu=0.1))

    for h in range(11,16):
        hosts_c.append(net.addHost('h%d' % h, cpu=0.1))

    print "*** Creating links"
    for h in hosts_a:
        net.addLink(s1, h)

    for h in hosts_b:
        net.addLink(s2, h)

    for h in hosts_c:
        net.addLink(s3, h)

    net.addLink(s1, s2)
    net.addLink(s2, s3)

    print "*** Starting Network"
    net.start()

    h15 = net.getNodeByName("h15")
    h15.setMAC( "00:00:00:00:00:15" )

    h14 = net.getNodeByName("h14")
    h14.setMAC( "00:00:00:00:00:14" )

    h13 = net.getNodeByName("h13")
    h13.setMAC( "00:00:00:00:00:13" )

    h12 = net.getNodeByName("h12")
    h12.setMAC( "00:00:00:00:00:12" )

    h11 = net.getNodeByName("h11")
    h11.setMAC( "00:00:00:00:00:11" )

    h10 = net.getNodeByName( "h10" )
    h10.setMAC( "00:00:00:00:00:10" )

    h9 = net.getNodeByName( "h9" )
    h9.setMAC( "00:00:00:00:00:09" )

    h8 = net.getNodeByName( "h8" )
    h8.setMAC( "00:00:00:00:00:08" )

    h7 = net.getNodeByName( "h7" )
    h7.setMAC( "00:00:00:00:00:07" )

    h6 = net.getNodeByName( "h6" )
    h6.setMAC( "00:00:00:00:00:06" )

    h5 = net.getNodeByName( "h5" )
    h5.setMAC( "00:00:00:00:00:05" )

    h4 = net.getNodeByName( "h4" )
    h4.setMAC( "00:00:00:00:00:04" )

    h3 = net.getNodeByName( "h3" )
    h3.setMAC( "00:00:00:00:00:03" )

    h2 = net.getNodeByName( "h2" )
    h2.setMAC( "00:00:00:00:00:02" )

    h1 = net.getNodeByName( "h1" )
    h1.setMAC( "00:00:00:00:00:01" )


    print "*** Testing Network"

    h15.cmd("iperf -s -u -p 5010 &")
    h15.cmd("iperf -s -p 5011 &")
    #h15.cmd( "iperf -s -u -p 5011 &" )


    h14.cmd("iperf -c 10.0.0.15 -p 5010 -b 10m -t 240 &")
    h13.cmd("iperf -c 10.0.0.15 -p 5010 -b 10m -t 240 &")

    h12.cmd("iperf -c 10.0.0.15 -p 5010 -b 10m -t 240 &")
    h11.cmd("iperf -c 10.0.0.15 -p 5010 -b 10m -t 240 &")

    for h in hosts_b:
        #h.cmd("hping3", "--flood", "-o", "28", "10.0.0.15 &")
        h.cmd( "iperf -c 10.0.0.15 -p 5010 -b 4m -t 240 &" )

    #sleep(10)

    for h in hosts_a:
        h.cmd( "iperf -c 10.0.0.15 -p 5011 -t 240 &" )
        #h.cmd( "hping3", "--flood", "-o", "28", "10.0.0.15 &" )

    #sleep(10)

    '''

    traffic_1 = "hping3 -S -p 80 -i u200000 -o 28 10.0.0.15 &" #tcp
    traffic_2 = "hping3 -S -p 80 -i u5000 -o 28 10.0.0.15 &" #tcp - new connection every 5ms
    traffic_3 = "hping3 -S --flood -o 28 10.0.0.15 &"
    flag = 1
    for h in hosts_a:
        if flag == 1:
            #h.cmd("hping3","--flood","-o","28","10.0.0.15 &")
            h.cmd(traffic_1)
            flag = 2
        elif flag == 2:
            h.cmd(traffic_2)
            flag = 3
        elif flag == 3:
            h.cmd(traffic_3)
            flag = 1

    '''
    #"sFlow agents"
    #os.system("sudo ovs-vsctl -- --id=@sflow create sflow agent=lo  target=127.0.0.1 sampling=10 polling=10 -- -- set bridge s1 sflow=@sflow -- set bridge s2 sflow=@sflow -- set bridge s3 sflow=@sflow")
    # (ifname, agent) = getIfInfo(collector)
    # sendTopology(net,agent,collector)

    # "QoS-queues"
    #for switch in range(1,3):
    #	for port in range (5,9):
    #		os.system('ovs-vsctl -- set port s'+str(switch)+'-eth'+str(port)+' qos=@newqos -- --id=@newqos create qos type=linux-htb \
    #		queues=0=@q0,1=@q1 -- --id=@q0 create queue other-config:min-rate=10000 \
    #		other-config:max-rate=40000 -- --id=@q1 create queue other-config:min-rate=1000 \
    #		other-config:max-rate=10000')


    #for h in hosts_b:
    #    h.cmd("hping3", "--flood", "-o", "28", "10.0.0.15 &")

    print "*** Running CLI"
    CLI( net )

    print "*** Stopping network"
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )  # for CLI output
    multiController()

