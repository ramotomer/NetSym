from collections import namedtuple

from consts import INTERFACES
from packets.protocol import Protocol


DBDescription = namedtuple("DBDescription", [
    "oob_resync",  # ???
    "init",
    "more",
    "master_slave",
])


class OSPFLinkStateAdvertisement(Protocol):
    def __init__(self,
                 description,
                 interface_mtu=INTERFACES.MAX_MTU,
                 ):
        super(OSPFLinkStateAdvertisement, self).__init__(6, '')


    def copy(self):
        pass

    def multiline_repr(self):
        return '\n'.join(self.get_all_interesting_attributes())
