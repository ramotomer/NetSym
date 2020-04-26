from processes.process import Process, WaitingForWithTimeout, ReturnedPacket, Timeout, NoNeedForPacket
from packets.stp import BID
from collections import namedtuple
from exceptions import *
from consts import *
import time
from os import linesep


STPInterface = namedtuple("STPInterface", "interface state distance_to_root")


class STPProcess(Process):
    """
    The process of sending and receiving STP packets.
    It is run by some switches to avoid switch loops and 'Chernobyl packets'
    """
    def __init__(self, computer):
        """
        Initiates the process.
        :param computer: The `Computer` that runs this process.
        """
        super(STPProcess, self).__init__(computer)
        self.my_bid = BID(self.computer.priority, self.computer.get_mac(), self.computer.name)
        self.root_bid = self.my_bid
        self.stp_interfaces = {}
        self.last_root_changing_time = time.time()
        self.last_sending_time = time.time()

    @property
    def root_port(self):
        """
        Returns the current port of the switch that points to the shortest way to the root switch.
        If no STP packets were received raises `NoSuchInterfaceError`
        :return: an `Interface` object.
        """
        if not self.stp_interfaces:
            raise NoSuchInterfaceError("No STP packets were received yet!!!!")
        return min(self.stp_interfaces, key=lambda i: self.stp_interfaces[i].distance_to_root)

    @property
    def distance_to_root(self):
        """
        Returns this switch's shortest way to the current root switch.
        If no STP packets were recieved yet, returns 0.
        :return: `int`
        """
        try:
            return self.stp_interfaces[self.root_port].distance_to_root
        except NoSuchInterfaceError:
            return 0

    def _i_am_root(self):
        """
        Returns whether or not I am the current root of the tree.
        :return: `bool`
        """
        return self.my_bid == self.root_bid

    def _send_packet(self):
        """
        Sends the STP packet with the information of the current state of the switch.
        :return: None
        """
        self.computer.send_stp(self.my_bid, self.root_bid, self.distance_to_root)
        self.last_sending_time = time.time()

    def _update_root(self, new_root_bid, distance_to_new_root, receiving_interface):
        """
        Updates the root switch according to the inforamtion from other received STP packets.
        :param new_root_bid: The `BID` of the new root.
        :param distance_to_new_root: the distance that the switch that sent this STP packet reports it has to the root switch.
        :param receiving_interface: The `Interface` that received the STP packet.
        :return: None
        """
        self.root_bid = new_root_bid
        self.last_root_changing_time = time.time()
        if receiving_interface not in self.stp_interfaces:
            self._add_interface(receiving_interface)
        self._update_distance(distance_to_new_root, receiving_interface)

    def _update_distance(self, distance_to_root, receiving_interface):
        """
        Updates the distance to the root that a certain interface keeps.
        The information comes from a received STP packet with the same root_bid
        :param distance_to_root: The distance to the root that is reported in the received packet.
        :param receiving_interface: The `Interface` that received that packet (it is the one that will be updated)
        :return: None
        """
        state = self.stp_interfaces[receiving_interface].state
        self.stp_interfaces[receiving_interface] = STPInterface(
                receiving_interface,
                state,
                (distance_to_root  + receiving_interface.connection_length) if not self._i_am_root() else 0
            )

    def _add_interface(self, interface):
        """
        Adds a new `Interface` to the `self.stp_interfaces` dictionary.
        An interface turns to an 'stp interface' when it receives an STP packet.
        :param interface: an `Interface` object of the switch.
        :return: None
        """
        self.stp_interfaces[interface] = STPInterface( interface, NO_STATE, 0)

    def _set_state(self, interface, state):
        """
        Sets the state of an stp interface. They can be ROOT_PORT, DESIGNATED_PORT or BLOCKED_PORT.
        :param interface: the `Interface` object
        :param state: the new state that is should have. (ROOT_PORT, DESIGNATED_PORT or BLOCKED_PORT.)
        :return: None
        """
        if interface not in self.stp_interfaces:
            raise NoSuchInterfaceError("The interface is not an STP interface!!!!")

        _, interface_state, distance_to_root = self.stp_interfaces[interface]
        if interface_state == BLOCKED_PORT and state != BLOCKED_PORT:
            interface.unblock()
        self.stp_interfaces[interface] = STPInterface(interface, state, distance_to_root)

    def _set_root_port(self, interface):
        """
        This sets an STP port to be a root port.
        :param interface: an `Interface` object.
        :return: None
        """
        for port in self.stp_interfaces:
            if self.stp_interfaces[port].state == ROOT_PORT:
                self._set_state(port, NO_STATE)                    # there can only be one ROOT_PORT at a time!

        self._set_state(interface, ROOT_PORT)

    def _set_designated_port(self, interface):
        """
        Sets a port to be a designated port.
        :param interface: an STP `Interface` object.
        :return: None
        """
        self._set_state(interface, DESIGNATED_PORT)

    def _set_blocked_port(self, interface):
        """
        Sets an STP port's state to be blocked and also physically blocks it.
        :param interface: the STP `Interface` object.
        :return: None
        """
        interface.block(accept="STP")
        self._set_state(interface, BLOCKED_PORT)

    def _is_root_port(self, port):
        """Receives an STP interface of the switch and decides if it is a root port"""
        if self._i_am_root():
            return False
        return self.root_port is port

    def _is_designated(self, interface):
        """
        Finds out if an stp interface should be designated.
        Rvery STP interface has another STP switch behind it. Every interface now checks if that switch has a higher
        distance to the root or does its own switch. The switch with the lower distance to the root is the one with the
        designated port (The other switch's port will be either root port or a blocked port).
        :param interface: an `Interface` object.
        :return: whether or not this interface should be designated. (`bool`)
        """
        if self._i_am_root():
            return True
        other_interface_distance_to_root = self.stp_interfaces[interface].distance_to_root - interface.connection_length
        return other_interface_distance_to_root > self.distance_to_root

    def get_info(self):
        """For debugging, returns some information about the state of the STP process on the switch."""
        return f"""
STP info:
----------------------------------------
my BID: {self.my_bid}                   {"(ROOT!)" if self._i_am_root() else ""}
root BID: {self.root_bid!r}
distance to root: {self.distance_to_root}
interface states:

{linesep.join(f"{interface.name}: {self.stp_interfaces[interface].state}" for interface in self.stp_interfaces)}
----------------------------------------
"""

    def code(self):
        """
        The actual code of the STP process.
        It sends out its-own information and waits and learns from the other STP packets' information.
        Updates its-own information accordingly.
        :return: yields `WaitingFor` namedtuple-s.
        """
        while True:
            if (time.time() - self.last_sending_time) > STP_SENDING_INTERVAL:
                self._send_packet()

            stp_packets = ReturnedPacket()
            yield WaitingForWithTimeout(lambda p: ("STP" in p), stp_packets, Timeout(0))

            for packet, interface in stp_packets.packets.items():
                if interface not in self.stp_interfaces:
                    self._add_interface(interface)

                if packet["STP"].root_bid < self.root_bid:
                    self._update_root(packet["STP"].root_bid, packet["STP"].distance_to_root, interface)

                elif packet["STP"].root_bid == self.root_bid:
                    self._update_distance(packet["STP"].distance_to_root, interface)

            for interface in self.stp_interfaces:
                if self._is_root_port(interface):
                    self._set_root_port(interface)
                elif self._is_designated(interface):
                    self._set_designated_port(interface)
                else:  # the port will be blocked, since it has no state!
                    self._set_blocked_port(interface)

    def __repr__(self):
        """The string representation of the STP process"""
        return "STP process"
