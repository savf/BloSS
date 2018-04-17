from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from collections import defaultdict
from stalk import hosts as host_mgmt
from pollen import watcher


class TrafficMonitor(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(TrafficMonitor, self).__init__(*args, **kwargs)

        self.datapaths = {}

        self.last_byte_counts = defaultdict(lambda: defaultdict(lambda: None))

        self.hosts = host_mgmt.init_hosts()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        if datapath.id not in self.datapaths:
            self.datapaths[datapath.id] = datapath

    def get_datapath(self, dpid):
        if dpid in self.datapaths:
            return self.datapaths[dpid]

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]

        # TODO: At this point, BloSS needs to be called to start retrieving info from the blockchain
        self.ddosbc_thread = hub.spawn(self._retrieve_bc)