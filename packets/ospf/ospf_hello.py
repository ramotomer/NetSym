from collections import namedtuple

from consts import PROTOCOLS
from packets.protocol import Protocol

OSPFHelloOptions = namedtuple("OSPFHelloOptions", [
    "DN",  # ?
    "O",   # ?
    "supports_demand_circuits",
    "contains_lls_data_block",
    "supports_nssa",
    "multicast_capable",
    "has_external_routing",
])


class OSPFHello(Protocol):
    def __init__(self,
                 designated_router_id,
                 active_neighbor_id,
                 options,
                 backup_designated_router_id=None,
                 hello_interval=PROTOCOLS.OSPF.DEFAULT_HELLO_INTERVAL,
                 router_dead_interval=PROTOCOLS.OSPF.DEFAULT_ROUTER_DEAD_INTERVAL,
                 router_priority=PROTOCOLS.OSPF.DEFAULT_ROUTER_PRIORITY,
                 network_mask="255.255.255.0",
                 ):
        super(OSPFHello, self).__init__(5, '')

        self.designated_router = designated_router_id
        self.active_neighbor = active_neighbor_id
        self.backup_designated_router = backup_designated_router_id
        self.hello_interval = hello_interval
        self.router_dead_interval = router_dead_interval
        self.router_priority = router_priority
        self.network_mask = network_mask

        self.options = options

    def copy(self):
        pass

    def multiline_repr(self):
        return '\n'.join(self.get_all_interesting_attributes())
