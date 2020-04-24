from collections import namedtuple
from packets.icmp import ICMP
from consts import *
from exceptions import *
from abc import ABCMeta, abstractmethod


WaitingFor = namedtuple("WaitingFor", "condition value")
""""
The condition function must receive one argument (a packet object) and return a bool.
the value in initialization will be a new `ReturnedPacket` object.
that object will be filled with the packets that fit the condition and returned to
the process when it continues running.

The condition should be specific so you dont accidentally catch the wrong packet!
"""


def arp_reply_from(ip_address):
    """Returns a function that tests if the packet given to it is an ARP reply for the `ip_address`"""
    def tester(packet):
        return ("ARP" in packet) and (packet["ARP"].opcode == ARP_REPLY) and (packet["ARP"].src_ip == ip_address)
    return tester


def ping_reply_from(ip_address):
    """Returns a function that tests if the packet given to it is a ping reply for the `ip_address`"""
    return lambda p: (ICMP in p) and (p["ICMP"].opcode == ICMP_REPLY) and (p["IP"].src_ip == ip_address)


class Process(metaclass=ABCMeta):
    """
    This class is a process in the computer class.
    It holds a state of the process and can run and perform code, then stop, wait for a condition and
        when that condition is met it can continue running.
    It has a `code` method which is a generator function that yields `WaitingFor` namedtuple-s.

    The `WaitingFor` tuples have a condition and a value, they tell the computer
    that's running the process that the process should be stopped until the `condition`
    function is met by a packet that was received recently. Then the computer puts the
    packet in the `value` object and continues the process run.

    So the process runs the `code` method until it yields a `WaitingFor`, then it stops, once a packet fits the condition
    it continues running until the next yeild. That is the way that a process can run smoothly in one function while waiting
    for packets without blocking the main loop.

    The `process` property of the Process is a generator of the code, the value
    of the `self.code()` method call.
    """
    def __init__(self, computer):
        """
        The process currently has access to all of the computer's resources.
        :param computer: The computer that this process is run on.
        """
        self.computer = computer
        self.process = self.code()

    @abstractmethod
    def code(self):
        """
        The `code` generator is the main function of the process.
        It yields the parameters it needs to continue its run.
        usually it will be to wait for some packet.
        :return:
        """
        yield WaitingFor(lambda p: False, ReturnedPacket())

    def __repr__(self):
        """The string representation of the Process"""
        return "Unnamed Process"


class SendPing(Process):
    """
    This is a process for sending a ping request to another computer and receiving the reply.
    """
    def __init__(self, computer, ip_address, opcode=ICMP_REQUEST):
        super(SendPing, self).__init__(computer)
        self.dst_ip = ip_address
        self.ping_opcode = opcode
        self.is_sending_to_gateway = False

    def _send_the_ping(self, ip_for_the_mac):
        """
        Does all things necessary to send the ping.
        (decides the interfaces, maps ip to mac and actually sends the ping)
        :param ip_for_the_mac: The `IPAddress` we use to get the MAC address we send the ping to.
            (will be of the destination if in the same LAN, otherwise, will be of the gateway)
        :return: None
        """
        if not self.computer.has_ip():
            raise NoIPAddressError("The sending computer has no IP address!!!")

        dst_mac = self.computer.arp_cache[ip_for_the_mac].mac
        self.computer.send_ping_to(dst_mac, self.dst_ip, self.ping_opcode)

    def code(self):
        """
        This code sends a ping (request or reply).
        If the address is unknown, first it sends an ARP and waits for a reply.
        :return: a generator of `WaitingFor` namedtuple-s.
        """
        if not self.computer.is_reachable(self.dst_ip):
            self.is_sending_to_gateway = True
            if self.computer.gateway is None: # network is totally unreachable
                return

        ip_for_the_mac = self.computer.routing_table[self.dst_ip].ip_address
        # ^ the IP we use to get our destination MAC address

        while ip_for_the_mac not in self.computer.arp_cache:
            self.computer.send_arp_to(ip_for_the_mac)
            yield WaitingFor(arp_reply_from(ip_for_the_mac), NoNeedForPacket())

        self._send_the_ping(ip_for_the_mac)

        if self.ping_opcode == ICMP_REQUEST:
            ping_reply_returned_packet = ReturnedPacket()
            yield WaitingFor(ping_reply_from(self.dst_ip), ping_reply_returned_packet)
            # self.computer.print(f"ping reply! {ping_reply_returned_packet.packet.multiline_repr()}")

    def __repr__(self):
        """The string representation of the SendPing process"""
        return "SendPing process"


class ReturnedPacket:
    """
    The proper way to get received packets back from the running computer.
    `self.packets` is a dictionary with `Packet` keys and the values are the interfaces they were received from.
    """
    def __init__(self):
        self.packets = {}
        self.packet_iterator = None

    @property
    def packet(self):
        """
        Returns the a packet that was returned. The next call will give a different
        result. If there are no more packets left to return, raise `NoSuchPacketError`
        :return: a `Packet` object that was not yet used.
        """
        if self.packet_iterator is None:
            self.packet_iterator = iter(self.packets)

        try:
            return next(self.packet_iterator)
        except StopIteration:
            raise NoSuchPacketError("All of the packets were requested from this object already!!")

    @property
    def packet_and_interface(self):
        """
        just like `self.packet` but returns a tuple of (packet, interface) [actually (packet, self.packets[packet])
        :return:
        """
        packet = self.packet
        return packet, self.packets[packet]

class NoNeedForPacket(ReturnedPacket):
    """
    This is the class that you generate an instance of the signal that the process is not interested in the packet
    that will be returned for it.

    A process that is waiting for some packet must yield a `ReturnedPacket` in his `WaitingFor`, this is the way to
    ignore that packet without raising errors.
    """
