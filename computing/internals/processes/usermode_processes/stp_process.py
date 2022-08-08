from os import linesep

from computing.internals.processes.abstracts.process import Process, WaitingForPacketWithTimeout, ReturnedPacket, \
    Timeout
from consts import *
from exceptions import *
from gui.main_loop import MainLoop
from packets.packet import Packet


class BID:
    """
    A Bridge Identifier.
    This is a unique ID for each switch in a STP session.
    I consists of a priority and the switches MAC address (one of them).
    """

    def __init__(self, priority, mac, computer_name=None):
        """
        Initiates a BID object.
        :param priority: The priority of the switch
        :param mac: one of the `MACAddress`-s of the switch.
        """
        self.priority = priority
        self.mac = mac
        self.computer_name = computer_name
        self.done_loading = True

    @property
    def value(self):
        """
        The numerical value of the BID.
        :return: an integer value of the BID..
        """
        return int(str(self.priority) + str(self.mac.as_number()))

    @classmethod
    def root_from_stp(cls, packet):
        """
        Take in an STP packet and return the root BID
        """
        stp = packet
        if isinstance(packet, Packet):
            stp = packet["STP"]
        return cls(stp.root_id, stp.root_mac)

    @classmethod
    def bridge_from_stp(cls, packet):
        """
        Take in an STP packet and return the BID of the sending switch
        """
        stp = packet
        if isinstance(packet, Packet):
            stp = packet["STP"]
        return cls(stp.bridge_id, stp.bridge_mac)

    def __gt__(self, other):
        """
        Allows to use the `this_BID > other_BID` notation
        :param other: another `BID` object or a number.
        :return: whether or not this is greater then the other.
        """
        if isinstance(other, int) or isinstance(other, float):
            return self.value > other
        if isinstance(other, self.__class__):
            return self.value > other.value
        raise STPError(f"Cannot compare BID with this type: {type(other).__name__}!!!!")

    def __repr__(self):
        """The String representation of the BID"""
        return f"{self.priority}{self.mac}" \
            f"{f' ({self.computer_name})' if self.computer_name is not None else ''}"

    def __str__(self):
        """The short string representation of the BID"""
        return f"{self.priority}{self.mac}"

    def __hash__(self):
        """For using this as dictionary keys"""
        return hash(self.value)

    def __eq__(self, other):
        """Returns whether or not two BID objects are equal"""
        return self.value == other.value


class STPPort:
    """
    This represents a port of the switch that receives STP packets. (That means there is another STP switch behind it)
    It contains all kinds of information that the process has to remember per-port of the switch.
    """

    def __init__(self, interface, state, distance_to_root, last_time_got_packet):
        """
        Initiates the STP-port with the original interface, the state of the port, the distance that that port has to the
        root switch and the last time that an STP packet was received in this port.

        :param interface: an `Interface` object
        :param state: the state of the port (`ROOT_PORT`, `DESIGNATED_PORT`, `BLOCKED_PORT` or `NO_STATE`)
        :param distance_to_root: the distance that if you go out from this port you have to go to get to the root switch
        :param last_time_got_packet: a result of the `time.time()` method of the last time an STP packet was received on this port.
        """
        self.interface = interface
        self.state = state
        self.distance_to_root = distance_to_root
        self.last_time_got_packet = last_time_got_packet


class STPProcess(Process):
    """
    The process of sending and receiving STP packets.
    It is run by some switches to avoid switch loops and 'Chernobyl packets'
    """

    def __init__(self, pid, computer):
        """
        Initiates the process.
        :param computer: The `Computer` that runs this process.
        """
        super(STPProcess, self).__init__(pid, computer)
        self.my_bid = BID(self.computer.priority, self.computer.get_mac(), self.computer.name)
        self.root_bid = self.my_bid
        self.stp_ports = {}  # format: {`Interface`: `STPPort`}

        self.root_declaration_time = MainLoop.instance.time()
        self.last_root_changing_time = MainLoop.instance.time()
        self.last_sending_time = MainLoop.instance.time()
        self.last_port_blocking_time = MainLoop.instance.time()

        self.sending_interval = PROTOCOLS.STP.NORMAL_SENDING_INTERVAL
        self.tree_stable = False
        self.root_timeout = PROTOCOLS.STP.ROOT_MAX_DISAPPEARING_TIME

    @property
    def root_port(self):
        """
        Returns the current port of the switch that points to the shortest way to the root switch.
        If no STP packets were received raises `NoSuchInterfaceError`
        :return: an `Interface` object.
        """
        if not self.stp_ports:
            raise NoSuchInterfaceError("No STP packets were received yet!!!!")
        return min(self.stp_ports, key=lambda port: self.stp_ports[port].distance_to_root)

    @property
    def distance_to_root(self):
        """
        Returns this switch's shortest way to the current root switch.
        If no STP packets were received yet, returns 0.
        :return: `int`
        """
        try:
            return self.stp_ports[self.root_port].distance_to_root
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
        self.computer.send()
        # TODO: are STP sockets a thing? should they be?
        self.computer.send_stp(
            self.my_bid,
            self.root_bid,
            self.distance_to_root,
            MainLoop.instance.time() if self._i_am_root() else self.root_declaration_time,
            sending_interval=self.sending_interval,
            root_timeout=PROTOCOLS.STP.ROOT_MAX_DISAPPEARING_TIME,
        )
        self.last_sending_time = MainLoop.instance.time()

    def _update_root(self, new_root_bid, distance_to_new_root, root_declaration_time, receiving_port):
        """
        Updates the root switch according to the information from other received STP packets.
        :param new_root_bid: The `BID` of the new root.
        :param distance_to_new_root: the distance that the switch that sent this STP packet reports it has to the root switch.
        :param receiving_port: The `Interface` that received the STP packet.
        :return: None
        """
        if MainLoop.instance.time_since(root_declaration_time) > PROTOCOLS.STP.ROOT_MAX_DISAPPEARING_TIME:
            return

        self.root_bid = new_root_bid
        self.last_root_changing_time = MainLoop.instance.time()
        if root_declaration_time > self.root_declaration_time:
            self.root_declaration_time = root_declaration_time

        if self.tree_stable:
            self._tree_unstable_again()  # if the root is updated, the tree is not really stable!

        if receiving_port not in self.stp_ports:
            self._add_port(receiving_port)
        self._update_distance(distance_to_new_root, root_declaration_time, receiving_port)

    def _update_distance(self, distance_to_root, root_declaration_time, receiving_port):
        """
        Updates the distance to the root that a certain interface keeps.
        The information comes from a received STP packet with the same root_bid
        :param distance_to_root: The distance to the root that is reported in the received packet.
        :param receiving_port: The `Interface` that received that packet (it is the one that will be updated)
        :return: None
        """
        if root_declaration_time > self.root_declaration_time:
            self.root_declaration_time = root_declaration_time

        if self._i_am_root():
            self.stp_ports[receiving_port].distance_to_root = 0
        else:
            self.stp_ports[receiving_port].distance_to_root = distance_to_root + receiving_port.connection_length

    def _add_port(self, interface):
        """
        Adds a new `Interface` to the `self.stp_ports` dictionary.
        An interface turns to an 'stp interface' when it receives an STP packet.
        :param interface: an `Interface` object of the switch.
        :return: None
        """
        self.stp_ports[interface] = STPPort(interface, PROTOCOLS.STP.NO_STATE, 0, MainLoop.instance.time())

    def _set_state(self, port, state):
        """
        Sets the state of an stp interface. They can be ROOT_PORT, DESIGNATED_PORT or BLOCKED_PORT.
        :param port: the `Interface` object
        :param state: the new state that is should have. (ROOT_PORT, DESIGNATED_PORT or BLOCKED_PORT.)
        :return: None
        """
        if port not in self.stp_ports:
            raise NoSuchInterfaceError("The other_port is not an STP other_port!!!!")

        if state == PROTOCOLS.STP.ROOT_PORT:
            for other_port in self.stp_ports:
                if self.stp_ports[other_port].state == PROTOCOLS.STP.ROOT_PORT:
                    self.stp_ports[other_port].state = PROTOCOLS.STP.NO_STATE  # there can only be one ROOT_PORT at a time!

        self.stp_ports[port].state = state

    def _is_root_port(self, port):
        """Receives an STP interface of the switch and decides if it is a root port"""
        if self._i_am_root():
            return False
        return port is self.root_port

    def _is_designated(self, port):
        """
        Finds out if an stp interface should be designated.
        Every STP interface has another STP switch behind it. Every interface now checks if that switch has a higher
        distance to the root or does its own switch. The switch with the lower distance to the root is the one with the
        designated port (The other switch's port will be either root port or a blocked port).
        :param port: an `Interface` object.
        :return: whether or not this interface should be designated. (`bool`)
        """
        if self._i_am_root():
            return True
        other_interface_distance_to_root = self.stp_ports[port].distance_to_root - port.connection_length
        return other_interface_distance_to_root > self.distance_to_root

    def _set_interface_states(self):
        """Sets the states of the ports of the switch (ROOT, DESIGNATED or BLOCKED)"""
        for port in self.stp_ports:
            if self._is_root_port(port):
                self._set_state(port, PROTOCOLS.STP.ROOT_PORT)

            elif self._is_designated(port):
                self._set_state(port, PROTOCOLS.STP.DESIGNATED_PORT)

            else:  # the port will be blocked, since it has no state!
                self._set_state(port, PROTOCOLS.STP.BLOCKED_PORT)

    def get_info(self):
        """For debugging, returns some information about the state of the STP process on the switch."""
        return f"""
    STP info:
----------------------------------------------
    my BID: {self.my_bid}                   {"(ROOT!)" if self._i_am_root() else ""}
    root BID: {self.root_bid!r}
    distance to root: {self.distance_to_root}
    root declaration time: {str(MainLoop.instance.time_since(self.root_declaration_time))[:5]} seconds ago
    port states:

{linesep.join(f"{port.name}: {self.stp_ports[port].state} (last got packet {str(MainLoop.instance.time_since(self.stp_ports[port].last_time_got_packet))[:5]} seconds ago)" for port in self.stp_ports)}
-----------------------------------------------
    """

    def _root_not_updated_for(self, seconds):
        """Returns whether or not the root was updated in the last `seconds` seconds."""
        return MainLoop.instance.time_since(self.last_root_changing_time) > seconds

    def _root_disappeared(self):
        """Returns whether or not the root has disappeared and did not report for a long time"""
        return MainLoop.instance.time_since(self.root_declaration_time) > self.root_timeout

    def _port_disappeared(self, port):
        """
        Returns whether or not the given interface received any STP packets lately.
        If it has not, it should be removed from the STP interfaces list.
        :param port: a key in the `self.stp_ports` dictionary.
        """
        return MainLoop.instance.time_since(self.stp_ports[port].last_time_got_packet) > PROTOCOLS.STP.MAX_CONNECTION_DISAPPEARED_TIME

    def _block_blocked_ports(self):
        """Blocks the `BLOCKED_PORT`-s and unblocks the other ones."""
        if MainLoop.instance.time_since(self.last_port_blocking_time) < PROTOCOLS.STP.BLOCKED_INTERFACE_UPDATE_INTERVAL:
            return

        self.last_port_blocking_time = MainLoop.instance.time()
        for port in self.stp_ports:
            if self.stp_ports[port].state == PROTOCOLS.STP.BLOCKED_PORT and not port.is_blocked:
                port.block(accept="STP")
            if self.stp_ports[port].state != PROTOCOLS.STP.BLOCKED_PORT and port.is_blocked:
                port.unblock()

    def _tree_is_probably_stable(self):
        """
        This is called when the switch tree is probably stable.
        It decreases the sending rate, and moves to hello packets
        """
        if not self.tree_stable:
            self.sending_interval = PROTOCOLS.STP.STABLE_SENDING_INTERVAL
            self.tree_stable = True
            self.computer.print("STP Tree stable!")

    def _tree_unstable_again(self):
        """
        This is called if the tree was thought to be stable but then the root was updated, Takes the STP process
        back to the unstable state
        :return: None
        """
        self.computer.print("STP Tree unstable!")
        self.tree_stable = False
        self.sending_interval = PROTOCOLS.STP.NORMAL_SENDING_INTERVAL

    def _recalculate_root(self):
        """Restarts the root calculation process with itself as the new root"""
        for port in self.stp_ports:
            self._update_root(self.my_bid, 0, MainLoop.instance.time(), port)

    def _learn_from_packet(self, packet, receiving_port):
        """
        Learns from a new packet (adds a new interface to the `stp_ports`, updates the root and updates the
        distances of existing interfaces to the root)
        :param packet: a `Packet` that contains STP
        :param receiving_port: an `Interface` object that the packet was captured on.
        :return: None
        """
        packet_root_bid = BID.root_from_stp(packet["STP"])
        packet_root_declaration_time = MainLoop.instance.time() - packet["STP"].age

        self.root_timeout = packet["STP"].max_age
        self.stp_ports[receiving_port].last_time_got_packet = MainLoop.instance.time()

        if receiving_port not in self.stp_ports:  # if a new interface received an STP packet, add it to the known ones.
            self._add_port(receiving_port)

        if packet_root_bid < self.root_bid:  # if there is a new root that is better than yours, update yours
            self._update_root(packet_root_bid, packet["STP"].path_cost, packet_root_declaration_time, receiving_port)

        elif packet_root_bid == self.root_bid:  # if a packet was received with a root that you already know, update your distance.
            self._update_distance(packet["STP"].path_cost, packet_root_declaration_time, receiving_port)

    def _update_disconnected_ports(self):
        """
        Removes the disconnected interfaces from the `stp_ports` dictionary.
        If a port is suddenly disconnected like this, the tree is not stable anymore, and we update the sending speed.
        We also remove ports that did not receive a packet for a long time, They do not count as STP ports anymore.
        :return: None
        """
        for port in list(self.stp_ports.keys()):
            if not port.is_connected() or self._port_disappeared(port):
                self.computer.print("Lost a port! recalculating...")

                if port.is_blocked:
                    port.unblock()

                del self.stp_ports[port]

    def code(self):
        """
        The actual code of the STP process.
        It sends out its-own information and waits and learns from the other STP packets' information.
        Updates its-own information accordingly.
        :return: yields `WaitingForPacket` namedtuple-s.
        """
        self.computer.print("Start STP...")

        while True:

            if MainLoop.instance.time_since(self.last_sending_time) > self.sending_interval:
                self._send_packet()

            stp_packets = ReturnedPacket()
            yield WaitingForPacketWithTimeout(lambda p: ("STP" in p), stp_packets, Timeout(0))
            self._update_disconnected_ports()

            for packet, packet_metadata in stp_packets.packets.items():
                self._learn_from_packet(packet, receiving_port=packet_metadata.interface)

            self._set_interface_states()

            if self._root_not_updated_for(seconds=PROTOCOLS.STP.TREE_STABLIZING_MAX_TIME):
                self._block_blocked_ports()
                self._tree_is_probably_stable()

            self._update_disconnected_ports()

            if self._root_disappeared():
                self.computer.print("Lost root! recalculating....")
                self._recalculate_root()

    def __repr__(self):
        """The string representation of the STP process"""
        return "stpd"
