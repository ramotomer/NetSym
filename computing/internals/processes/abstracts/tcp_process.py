from __future__ import annotations

import random
from abc import ABCMeta, abstractmethod
from collections import deque
from dataclasses import dataclass
from functools import reduce
from operator import attrgetter, concat
from typing import Optional, List, TYPE_CHECKING, Iterable

from address.ip_address import IPAddress
from computing.internals.processes.abstracts.process import Process, WaitingForPacketWithTimeout, Timeout, \
    ReturnedPacket, \
    T_ProcessCode, ProcessInternalError
from consts import *
from exceptions import TCPDataLargerThanMaxSegmentSize
from gui.main_loop import MainLoop
from packets.all import TCP
from packets.packet import Packet
from usefuls.funcs import insort
from usefuls.funcs import split_by_size

if TYPE_CHECKING:
    from computing.computer import Computer


@dataclass
class NotAckedPacket:
    packet:       Packet
    sending_time: T_Time
    is_sent:      bool


@dataclass
class SackEdges:
    left:  int
    right: int

    def __iter__(self) -> Iterable[int]:
        return iter((
            self.left,
            self.right,
        ))


class ProcessInternalError_TCPConnectionWasReset(ProcessInternalError):
    """This is used to kill the process if the connection was reset :)"""


def get_tcp_packet_data_length(tcp_packet: Packet) -> int:
    """
    Returns the length of the data of the TCP packet
    """
    if (OPCODES.TCP.SYN & tcp_packet["TCP"].flags) or (OPCODES.TCP.FIN & tcp_packet["TCP"].flags):
        return 1  # handshake ghost byte
    return len(tcp_packet["TCP"].payload.build())


def is_number_acking_packet(ack_number: int, packet: Packet) -> bool:
    """
    Receives an ACK number and a packet and returns whether or not the packet is ACKed in that ACK
    :param ack_number:
    :param packet: a `Packet` object.
    :return:
    """
    return packet["TCP"].sequence_number + get_tcp_packet_data_length(packet) <= ack_number


class TCPProcess(Process, metaclass=ABCMeta):
    """
    The TCP process abstract class which represents any TCP based process (HTTP, SSH whatever)
    It creates an abstraction for all of the methods for sending and receiving data without the child process class
    has to handle of the retransmissions and ACKs and all of that. that is handled here.

    A server-side `code` function example:

    while True:
        yield from self.hello_handshake()
        # ^ blocks the process until a client is connected.

        self.send(<DATA>)
        while not self.is_done_transmitting():   # until all is acked and fine
            yield from self.handle_tcp_and_receive([])

        yield from self.goodbye_handshake(initiate=True)

    """

    def __init__(self,
                 pid: int,
                 computer: Computer,
                 dst_ip: Optional[IPAddress] = None,
                 dst_port: Optional[int] = None,
                 src_port: Optional[int] = None,
                 is_client: bool = True,
                 mss: int = PROTOCOLS.TCP.MAX_MSS) -> None:
        """
        Initiates a TCP process.
        :param computer: the `Computer` running the process
        :param dst_ip: the `IPAddress` of the other computer in the session. (If unknown at initiation - None)
        :param dst_port: the destination port number of the other computer in the session.
        (If unknown at initiation - None)
        :param is_client: whether or not this computer sends the initial SYN packet.
        :param src_port: the source port of the process (If unknown - None - and it will be randomized)
        """
        super(TCPProcess, self).__init__(pid, computer)

        self.is_client = is_client  # decides who sends the original SYN packet (the client does)

        self.dst_ip = dst_ip
        self.src_port = random.randint(*PORTS.USERMODE_USABLE_RANGE) if self.is_client else src_port
        self.dst_port = dst_port
        self.dst_mac = None

        self.sequence_number = 0  # randint(0, TCP_MAX_SEQUENCE_NUMBER)
        # self.next_sequence_number = 1 + self.sequence_number

        self.receiving_window = ReceivingWindow()
        self.sending_window = SendingWindow()
        self.mss = mss

        self.last_packet_sent_time = MainLoop.instance.time()

        for signum in COMPUTER.PROCESSES.SIGNALS.KILLING_SIGNALS:
            self.signal_handlers[signum] = self.kill_signal_handler

    def _create_packet(self, flags: Union[TCPFlag, int] = None, data: str = '', is_retransmission: bool = False) -> Packet:
        """
        Creates a full packet that contains TCP with all of the appropriate fields according to the state of
        this process
        """
        packet = self.computer.ip_wrap(self.dst_mac, self.dst_ip,
                                       TCP(
                                           src_port=self.src_port,
                                           dst_port=self.dst_port,
                                           sequence_number=self.sequence_number,
                                           flags=flags,
                                           ack_number=self.receiving_window.ack_number,
                                           window_size=self.sending_window.window_size,
                                           options=[("MSS", self.mss)],
                                       ) / data
                                       )
        packet["TCP"].is_retransmission = is_retransmission
        self.sequence_number += get_tcp_packet_data_length(packet)
        return packet

    def _send_ack_for(self, packet: Packet, additional_flags: Optional[TCPFlag] = None) -> None:
        """
        Creates and sends an ACK packet for the given `Packet` that was received from the other side.
        """
        is_retransmission = False
        additional_flags = OPCODES.TCP.NO_FLAGS if additional_flags is None else additional_flags

        if packet["TCP"].sequence_number == self.receiving_window.ack_number:
            # ^ the received packet is in-order
            self.receiving_window.ack_number += get_tcp_packet_data_length(packet)

        elif packet["TCP"].sequence_number < self.receiving_window.ack_number:
            # ^ the packet was already received (lost ACK)
            is_retransmission = True

        elif packet["TCP"].sequence_number > self.receiving_window.ack_number:
            # ^ a sequence number was jumped (lost packet)
            is_retransmission = True
            self.receiving_window.add_to_sack(packet)
            self.receiving_window.merge_sack_blocks()

        ack = self._create_packet((OPCODES.TCP.ACK | additional_flags), is_retransmission=is_retransmission)
        ack["TCP"].parsed_options.SACK = self.receiving_window.get_sack_blocks_as_tuple()

        if additional_flags:
            self.sending_window.add_waiting(ack)
        else:
            self.sending_window.add_no_wait(ack)

    def _my_tcp_packets(self, packet: Packet) -> bool:
        """
        This is a tester function that checks if a packet is for this TCP session.
        """
        if "TCP" not in packet or \
                not packet.is_valid() or \
                not self.computer.has_this_ip(packet["IP"].dst_ip) or \
                packet["TCP"].dst_port != self.src_port:
            return False

        tcp_packet = packet["TCP"]

        if (self.dst_ip is None or self.dst_port is None or self.dst_port is None) and \
                (OPCODES.TCP.SYN & tcp_packet.flags):
            return True

        return packet["IP"].src_ip == self.dst_ip and \
               tcp_packet.dst_port == self.src_port and \
               tcp_packet.src_port == self.dst_port

    def reset_connection(self) -> None:
        """
        When you need to abruptly end the connection.
        (Sends a TCP RST packet)
        :return: None
        """
        self.computer.send(self._create_packet(OPCODES.TCP.RST))
        self._end_session()

    def _update_from_handshake_packet(self, packet: Packet) -> None:
        """
        Takes in a `Packet` object which is the SYN or SYN ACK packet of the handshake and updates all of
        details of the process according to it.
        """
        self.dst_port = packet["TCP"].src_port
        self.dst_ip = packet["IP"].src_ip
        self.sending_window.window_size = min(packet["TCP"].window_size, self.sending_window.window_size)
        self.mss = min(packet["TCP"].parsed_options.MSS, self.mss)

    def _acknowledge_with_packet(self, packet: Packet) -> None:
        """
        Takes in an ACk number and releases all of the packets that are ACKed by it.
        :param packet: a packet that contains the ACK information to remove sent packets from my sending window.
        """
        ack_number = packet["TCP"].ack_number
        acked_count = 0
        for not_acked_packet in self.sending_window.window:
            if is_number_acking_packet(ack_number, not_acked_packet.packet):
                acked_count += 1
            else:
                break
        self.sending_window.slide_window(acked_count)

        sack_blocks = ReceivingWindow.get_sack_blocks_from_tuple(getattr(packet["TCP"].parsed_options, 'SACK', ()))
        if not isinstance(sack_blocks, list) or not sack_blocks:
            return
        for not_acked_packet in list(self.sending_window.window):
            for left, right in sack_blocks:
                if left <= not_acked_packet.packet["TCP"].sequence_number and \
                        is_number_acking_packet(right, not_acked_packet.packet):
                    self.sending_window.window.remove(not_acked_packet)

    def on_connection_reset(self) -> None:
        """
        This function should be overridden
        Specify what should be done once received an RST packet
        """
        raise ProcessInternalError_TCPConnectionWasReset

    def hello_handshake(self) -> T_ProcessCode:
        """
        Starts the TCP handshake by sending a SYN packet to the destination.
        """
        if self.is_client:
            yield from self._client_hello_handshake()
        else:  # if is server
            yield from self._server_hello_handshake()

    def _client_hello_handshake(self) -> T_ProcessCode:
        """
        the initial handshake on the client side. sends syn, waits for syn ack, sends ack.
        :return:
        """
        ip_for_the_mac, self.dst_mac = yield from self.computer.resolve_ip_address(self.dst_ip, self)

        self.sending_window.add_waiting(self._create_packet(OPCODES.TCP.SYN))

        tcp_syn_ack_list = []
        yield from self.handle_tcp_and_receive(tcp_syn_ack_list, is_blocking=True, insert_flag_packets_to_received_data=True)

        syn_ack, = tcp_syn_ack_list
        self._update_from_handshake_packet(syn_ack)

    def _server_hello_handshake(self) -> T_ProcessCode:
        """
        The initial handshake on the server side. waits for syn, sends syn ack waits for ack
        :return:
        """
        tcp_syn_list = []
        while not tcp_syn_list or \
                not isinstance(tcp_syn_list[0], Packet) or \
                "TCP" not in tcp_syn_list[0] or \
                not (OPCODES.TCP.SYN & tcp_syn_list[0]["TCP"].flags):
            yield from self.handle_tcp_and_receive(tcp_syn_list, is_blocking=True, insert_flag_packets_to_received_data=True)
        syn, = tcp_syn_list
        self._update_from_handshake_packet(syn)

        ip_for_the_mac, self.dst_mac = yield from self.computer.resolve_ip_address(self.dst_ip, self)

        self._send_ack_for(syn, OPCODES.TCP.SYN)  # sends SYN ACK
        while not self.sending_window.nothing_to_send():  # while the syn ack was not ACKed
            yield from self.handle_tcp_and_receive([], insert_flag_packets_to_received_data=True)

    def goodbye_handshake(self, initiate: bool = True) -> T_ProcessCode:
        """
        Ends the TCP connection with good terms and with both sides' agreement.
        This can be called with `initiate=True` to end the connection.
        This should be called with `initiate=False` if a TCP FIN packet was received from the destination computer.
        :return: None
        """
        if initiate:
            self.sending_window.clear()
            self.sending_window.add_waiting(self._create_packet(OPCODES.TCP.FIN))
            fin_ack_list = []
            while not fin_ack_list or \
                    not isinstance(fin_ack_list[0], Packet) or \
                    "TCP" not in fin_ack_list[0] or \
                    ((OPCODES.TCP.FIN | OPCODES.TCP.ACK) != fin_ack_list[0]["TCP"].flags):
                yield from self.handle_tcp_and_receive(fin_ack_list, insert_flag_packets_to_received_data=True)
                if fin_ack_list:
                    pass

            self._send_ack_for(fin_ack_list[0])
            while not self.sending_window.nothing_to_send():
                yield from self.handle_tcp_and_receive([], insert_flag_packets_to_received_data=True)

        else:  # if received a FIN, then sent a FIN ACK from the main function
            timeout = Timeout(PROTOCOLS.TCP.RESEND_TIME * 2)
            while not self.sending_window.nothing_to_send() and not timeout:  # waiting for an ACK for the fin ack...
                yield from self.handle_tcp_and_receive([], insert_flag_packets_to_received_data=True)
        self._end_session()

    def _end_session(self) -> None:
        """
        Ends the current session. For the client that kills the process after it is done, this does nothing
        This is mostly for servers that serve multiple clients in the same process. It resets everything and gets ready
        to serve another client.
        """
        self.sending_window.clear()
        self.receiving_window.clear()
        self.sequence_number = 0
        self.receiving_window.ack_number = 0
        self.dst_port = None
        self.dst_mac = None

    def send(self, data, packet_constructor=lambda d: d) -> None:
        """
        Takes in some data and sends it over TCP as soon as possible.
        :param data: the piece of the data that the child process class wants to send over TCP
        :param packet_constructor: a function is applied to the data after it is divided to TCP segments and before
        it is sent.
        :return: None
        """
        if isinstance(data, str):
            for data_part in split_by_size(data, self.mss):
                self.send_no_split(packet_constructor(data_part))
        else:
            self.send_no_split(data)

    def send_no_split(self, data: str) -> None:
        """
        This function assumes that the length of the data is not larger than the MSS of the process.
        If it is larger, raises an exception.
        """
        if len(data) > self.mss:
            raise TCPDataLargerThanMaxSegmentSize("To split string data, use the `TCPProcess.send` method")
        self.sending_window.add_waiting(self._create_packet(OPCODES.TCP.PSH, data))

    def is_done_transmitting(self) -> bool:
        """
        Returns whether or not the process has finished transmitting all of the desired data.
        :return: bool
        """
        return self.sending_window.nothing_to_send()

    def _session_timeout(self) -> bool:
        """Returns whether or not the connection should be timed-out"""
        return MainLoop.instance.time_since(self.last_packet_sent_time) >= PROTOCOLS.TCP.MAX_UNUSED_CONNECTION_TIME

    def _physically_send_packets_with_time_gaps(self) -> None:
        """
        Sends the next packet in the `self.sending_window.sent` list.
        The packets are not all sent in one go because then the graphics will one over the other.
        This function sends a packet if was not just sent.
        """
        if MainLoop.instance.time_since(self.last_packet_sent_time) > PROTOCOLS.TCP.SENDING_INTERVAL:
            if self.sending_window.sent:
                packet = self.sending_window.sent.popleft()
                debugp(f"{self.computer.name:<20}: TCP({get_dominant_tcp_flag(packet['TCP'])}, {packet['TCP'].sequence_number}, {packet['TCP'].ack_number})")
                self.computer.send(packet)
                self.last_packet_sent_time = MainLoop.instance.time()

    def handle_tcp_and_receive(self,
                               received_data: List,
                               is_blocking: bool = False,
                               insert_flag_packets_to_received_data: bool = False) -> T_ProcessCode:
        """
        This function is a generator that yield `WaitingFor` and `WaitingForPacket` namedtuple-s.
        It receives TCP packets from the destination sends ACKs sends all of the other packets in the
        TCP_SENDING_INTERVAL gaps. "Blocks" the process until packets are received.
        :param received_data: a list that we append data we receive to it. Any packet's data is appended to it.
        :param is_blocking: whether or not the function loops until it receives a packet.
        If a FIN was received, appends the list a `DON_RECEIVING` constant (None) that tells
        it that the process terminates.
        :param insert_flag_packets_to_received_data: whether or not to insert TCP SYN and FIN packets to the `received_data`

        when a SYN packet is received, the whole packet is appended to the received_data list.
        """
        received_packets = ReturnedPacket()

        while not received_packets.packets:
            received_packets = yield WaitingForPacketWithTimeout(self._my_tcp_packets, Timeout(0.01))

            for packet in received_packets.packets:
                yield from self._handle_packet(packet, received_data, insert_flag_packets_to_received_data)

            self.receiving_window.add_data_and_remove_from_window(received_data)

            self.sending_window.fill_window()  # if the amount of sent packets is not the window size, fill it up
            self.sending_window.send_window()  # send the packets that were not yet sent
            self.sending_window.retransmit_unacked()  # send the packets that were sent a long time ago and not ACKed.

            self._physically_send_packets_with_time_gaps()  # send all of the packets above in appropriate time gaps

            if not is_blocking:
                return

    def _handle_packet(self,
                       packet: Packet,
                       received_data: List,
                       insert_flag_packets_to_received_data: bool) -> T_ProcessCode:
        """
        Receives a packet and handles it, sends ack, learns, and adds the data to a given `received_data` list.
        If it is a FIN or RST, reacts accordingly.
        :param packet: the packet to handle
        :param received_data: a list of data from the PSH tcp packets
        :param insert_flag_packets_to_received_data: whether or not to insert SYN or FIN packets to received data
        """
        tcp_layer = packet["TCP"]

        if OPCODES.TCP.PSH & tcp_layer.flags:
            if not is_number_acking_packet(self.receiving_window.ack_number, packet):
                self.receiving_window.add_packet(packet)  # if the packet was not received already
            self._send_ack_for(packet)

        if (OPCODES.TCP.SYN & tcp_layer.flags) or (OPCODES.TCP.FIN | OPCODES.TCP.ACK) == tcp_layer.flags:
            if insert_flag_packets_to_received_data:
                received_data.append(packet)

            if (OPCODES.TCP.SYN | OPCODES.TCP.ACK) == tcp_layer.flags:
                self._send_ack_for(packet)

        if OPCODES.TCP.ACK & tcp_layer.flags:
            self._acknowledge_with_packet(packet)

        if OPCODES.TCP.FIN == tcp_layer.flags and not insert_flag_packets_to_received_data:
            self._send_ack_for(packet, additional_flags=OPCODES.TCP.FIN)  # FIN ACK
            yield from self.goodbye_handshake(initiate=False)

        if OPCODES.TCP.RST & tcp_layer.flags:
            self.on_connection_reset()
            return

    def kill_signal_handler(self, signum: int) -> None:
        """
        This is the handler to each signal that is supposed to kill this process.
        """
        self.reset_connection()
        self.die()

    @abstractmethod
    def code(self) -> T_ProcessCode:
        """
        The actual code of the process if for each child process to implement
        :return: generator of `WaitingFor`s bluh bluh you know the drill...
            (If not go to 'processes.process.py' and read some documentation :) )
        """
        pass


class SendingWindow:
    """
    A class that represents the sending window in a TCP process.
    It has three queues, the packets that are not yet sent, the packets that are sent and not yet acked and a list of
    `sent` packets that need to be physically sent one by one (in the `TCP_SENDING_INTERVAL` time gaps).
    """

    def __init__(self, window_size: int = PROTOCOLS.TCP.MAX_WINDOW_SIZE) -> None:
        """
        Initiates the three queues of the window.
        """
        self.window_size = window_size

        self.waiting_for_sending = deque()
        self.window = deque()
        self.sent = deque()

    def clear(self) -> None:
        """
        Clears all of the attributes of the window.
        :return:
        """
        self.waiting_for_sending.clear()
        self.window.clear()
        self.sent.clear()

    def fill_window(self) -> None:
        """
        Fills the window until it is in its full window size
        """
        while len(self.window) < self.window_size and self.waiting_for_sending:
            self.window.append(NotAckedPacket(self.waiting_for_sending.popleft(), MainLoop.instance.time(), False))

    def slide_window(self, count: int) -> None:
        """
        Moves the window `count` packets to the right.
        Also fills up the window if it is not full.
        """
        for _ in range(count):
            if not self.window:
                break
            self.window.popleft()
        self.fill_window()

    def send_window(self) -> None:
        """
        Sends all of the packets in the window (adds them to the `sent` queue)
        Only does that to NotAckedPackets where the `is_sent` attribute is False.
        """
        for non_acked_packet in self.window:
            if not non_acked_packet.is_sent:
                self.sent.append(non_acked_packet.packet.copy())
                non_acked_packet.is_sent = True

    def add_waiting(self, packet: Packet) -> None:
        """
        Adds a new packet to the end of the `waiting_for_sending` queue
        :param packet: a `Packet` object.
        """
        self.waiting_for_sending.append(packet)

    def add_no_wait(self, packet: Packet) -> None:
        """
        Adds a packet to the `sent` queue so it will be sent almost immediately
        :param packet:
        :return:
        """
        self.sent.append(packet.copy())

    def nothing_to_send(self) -> bool:
        """
        Returns whether or there is nothing left to send.
        """
        return not self.sent and not self.window and not self.waiting_for_sending

    def retransmit_unacked(self) -> None:
        """
        Retransmits all of the packets that were not ACKed for too long!
        """
        for non_acked_packet in list(self.window):
            if MainLoop.instance.time_since(non_acked_packet.sending_time) > PROTOCOLS.TCP.RESEND_TIME:
                non_acked_packet.packet["TCP"].is_retransmission = True
                self.add_no_wait(non_acked_packet.packet)
                non_acked_packet.sending_time = MainLoop.instance.time()

    def __repr__(self) -> str:
        """
        The string representation of the sending window.
        """
        window = [(not_acked.packet["TCP"].true_flags_string, not_acked.packet["TCP"].sequence_number)
                  for not_acked in self.window]
        return f"""
waiting to be sent: {[packet["TCP"].sequence_number for packet in self.waiting_for_sending]}
window: {window}
window size: {self.window_size}
sent: {[packet["TCP"].sequence_number for packet in self.sent]}
"""


class ReceivingWindow:
    """
    The receiving window of the process
    Handles the SACk option of TCP
    """

    def __init__(self) -> None:
        """
        Initiates the receiving window with an empty window.
        """
        self.window = []
        self.ack_number = 0
        self.sack_blocks = []

    def clear(self) -> None:
        """
        Clears the window and resets it like it was just created
        :return:
        """
        self.window.clear()
        self.sack_blocks.clear()
        self.ack_number = 0

    def add_packet(self, packet: Packet) -> None:
        """
        Adds a packet to the window.
        """
        insort(self.window, packet, key=lambda p: p["TCP"].sequence_number)

    def add_data_and_remove_from_window(self, received_data: List) -> None:
        """
        Adds the data from all of the packets that arrived in-order to the given list.
        Also removes them from the receiving window.
        :param received_data: a list of data that is received from the destination computer.
        """
        for packet in self.window[:]:
            if is_number_acking_packet(self.ack_number, packet):
                received_data.append(packet["TCP"].payload.build())
                self.window.remove(packet)
            else:
                break  # the window is sorted by the sequence number.

    def add_to_sack(self, packet: Packet) -> None:
        """
        Adds a packet to the SACK data of the process.
        """
        packet_start = packet["TCP"].sequence_number
        packet_length = get_tcp_packet_data_length(packet)
        packet_end = packet_start + packet_length

        for block in self.sack_blocks:
            if block.left == packet_end:
                block.left = packet_start
                return
            elif block.right == packet_start:
                block.right = packet_end
                return

        insort(self.sack_blocks, SackEdges(packet_start, packet_end), key=attrgetter('left'))

    def merge_sack_blocks(self) -> None:
        """
        Merges the SACK blocks to the ack number.
        :return: None
        """
        for block in self.sack_blocks[:]:
            if self.ack_number == block.left:
                self.ack_number = block.right
                self.sack_blocks.remove(block)

        for i, block in enumerate(self.sack_blocks[:-1]):
            next_block = self.sack_blocks[i + 1]

            if block.right == next_block.left:
                self.sack_blocks.remove(block)
            next_block.left = block.left

    def get_sack_blocks_as_tuple(self) -> Union[Tuple[int], Tuple]:
        """
        :receives: self.sack_blocks = [SackEdges(a, b), SackEdges(c, d), ...]
        :return:                      (a, b, c, d, ...)
        """
        return reduce(concat, map(tuple, self.sack_blocks), ())

    @staticmethod
    def get_sack_blocks_from_tuple(tuple_: Tuple[int]) -> List[SackEdges]:
        """
        :receives: (a, b, c, d, ...)
        :returns:  [SackEdges(a, b), SackEdges(c, d), ...]
        """
        try:
            return [SackEdges(tuple_[i], tuple_[i + 1]) for i in range(0, len(tuple_), 2)]
        except IndexError:
            raise IndexError(f"Tuple {tuple_} must have an even length in order to be parsed as a list of `SackEdges`")
