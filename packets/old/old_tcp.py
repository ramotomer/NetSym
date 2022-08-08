import copy

from packets.protocol import Protocol

from consts import *


class TCP(Protocol):
    """
    A TCP packet!!!
    It is in the fourth layer, has ports, is in charge of making sure all packets get to their destination, in-order and
    in-tact.
    It has the TCP flags (SYN, FIN, RST...) they are stored in a dictionary {FLAG: bool}
    It has a sequence number and an ACK number.
    It has some ip_layer and its length is specified in the `length` attribute.
    The window size is also specified.
    """
    def __init__(self, src_port, dst_port, sequence_number,
                 flags: set = None, ack_number=None, window_size=PROTOCOLS.TCP.MAX_WINDOW_SIZE,
                 data='', options=None, mss=PROTOCOLS.TCP.MAX_MSS, is_retransmission=False):
        """
        Creates a TCP packet! With all of its parameters!
        :param src_port:
        :param dst_port:  Src and Dst port, self explanatory.
        :param flags:  an iterable of all of the flags that this packet has on.
        :param sequence_number: an int which is the TCP sequence number of the packet
        :param ack_number: an int which is the sequence number that the packet ACKs and expects to receive next.
        :param window_size: The size of the sending window of the sender of this packet
        :param options: a dictionary of the TCP options. (for now it is empty)
        :param data: the actual ip_layer of the packet.
        """
        super(TCP, self).__init__(4, data)
        self.src_port, self.dst_port = src_port, dst_port
        self.flags = flags
        self.sequence_number = sequence_number
        self.ack_number = ack_number if OPCODES.TCP.ACK in self.flags else None
        self.window_size = window_size

        self.options = options
        if options is None:
            self.options = {
                PROTOCOLS.TCP.OPTIONS.MSS: mss,
                PROTOCOLS.TCP.OPTIONS.WINDOW_SCALE: None,
                PROTOCOLS.TCP.OPTIONS.SACK: None,
                PROTOCOLS.TCP.OPTIONS.TIMESTAMPS: None,
            }

        self.is_retransmission = is_retransmission

    @property
    def opcode(self):
        """
        This is used to determine which packet drawing will be displayed for this packet (prioritizing the flags)
        :return: one of the TCP flags.
        """
        for flag in OPCODES.TCP.FLAGS_DISPLAY_PRIORITY:
            if flag in self.flags:
                return flag if not self.is_retransmission else flag + OPCODES.TCP.RETRANSMISSION
        return OPCODES.NO_TCP_FLAGS

    @property
    def true_flags_string(self):
        """
        Returns a string which is a list of the flags that are true in this packet
        :return:
        """
        return ', '.join(self.flags)

    @property
    def length(self):
        """
        The length of the ip_layer of the packet
        :return: int
        """
        if {OPCODES.TCP.SYN, OPCODES.TCP.FIN} & self.flags:
            return 1
        return len(self.data)

    def copy(self):
        """
        Copy the TCP packet
        :return:
        """
        return self.__class__(
            self.src_port,
            self.dst_port,
            self.sequence_number,
            copy.deepcopy(self.flags),
            self.ack_number,
            self.window_size,
            self.data.copy() if hasattr(self.data, "copy") else self.data,
            copy.deepcopy(self.options),
            self.options[PROTOCOLS.TCP.OPTIONS.MSS],
            is_retransmission=self.is_retransmission,
        )

    def __repr__(self):
        """

        :return:
        """
        return ' '.join(self.multiline_repr().split('\n'))

    def multiline_repr(self):
        """
        The multiline representation of the TCP packet
        :return: a string that represents it
        """
        linesep = '\n'
        return f"""
TCP{' (retransmission)' if self.is_retransmission else ''}:
from port {self.src_port} to port {self.dst_port}
length: {len(self.data)}
flags: {self.true_flags_string}
seq={self.sequence_number}, ack={self.ack_number}, win={self.window_size}
options:
{linesep.join(f'{option}: {value}' for option, value in self.options.items())}

data:
{getattr(self.data, "multiline_repr", self.data.__str__)()}
"""
