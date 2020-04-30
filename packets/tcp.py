from packets.protocol import Protocol


class TCP(Protocol):
    """
    A TCP packet!!!
    It is in the fourth layer, has ports, is in charge of making sure all packets get to their destination, in-order and
    in-tact.
    It has the TCP flags (SYN, FIN, RST...) they are stored in a dictionary {FLAG: bool}
    It has a sequence number and an ACK number.
    It has some data and its length is specified in the `length` attribute.
    The window size is also specified.
    """
