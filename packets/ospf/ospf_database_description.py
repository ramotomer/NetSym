from collections import namedtuple

from consts import INTERFACES
from packets.protocol import Protocol


DBDescription = namedtuple("DBDescription", [
    "oob_resync",  # ???
    "init",
    "more",
    "master_slave",
])


class OSPFDatabaseDescription(Protocol):
    def __init__(self,
                 description,
                 interface_mtu=INTERFACES.MAX_MTU,
                 ):
        super(OSPFDatabaseDescription, self).__init__(5, '')

        self.interface_mtu = interface_mtu
        self.description = description


    def copy(self):
        pass

    def multiline_repr(self):
        return '\n'.join(self.get_all_interesting_attributes())
