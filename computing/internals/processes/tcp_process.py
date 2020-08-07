import random
from abc import ABCMeta, abstractmethod
from collections import deque
from operator import attrgetter

from recordclass import recordclass

from computing.internals.processes.process import Process, WaitingForPacketWithTimeout, Timeout, ReturnedPacket, \
    NoNeedForPacket, WaitingFor
from consts import *
from exceptions import TCPDataLargerThanMaxSegmentSize
from gui.main_loop import MainLoop
from packets.packet import Packet
from packets.tcp import TCP
from usefuls.funcs import insort
from usefuls.funcs import split_by_size

NotAckedPacket = recordclass("NotAckedPacket", [  # this is like a `namedtuple` but it is mutable!
    "packet",
    "sending_time",
    "is_sent",
])

SackEdges = recordclass("SackEdges", [
    "left",
    "right",
])


def is_number_acking_packet(ack_number: int, packet):
    """
    Receives an ACK number and a packet and returns whether or not the packet is ACKed in that ACK
    :param ack_number:
    :param packet: a `Packet` object.
    :return:
    """
    return packet["TCP"].sequence_number + packet["TCP"].length <= ack_number


class TCPProcess(Process, metaclass=ABCMeta):
    """
    The TCP process abstract class which represents any TCP based process (HTTP, SSH whatever)
    It creates an abstraction for all of the methods for sending and receiving ip_layer without the child process class
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
    def __init__(self, pid, computer, dst_ip=None, dst_port=None, src_port=None, is_client=True, mss=PROTOCOLS.TCP.MAX_MSS):
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

    def _create_packet(self, flags=None, data='', is_retransmission=False):
        """
        Creates a full packet that contains TCP with all of the appropriate fields according to the state of
        this process
        """
        packet = self.computer.ip_wrap(self.dst_mac, self.dst_ip,
                                       TCP(
                                            self.src_port,
                                            self.dst_port,
                                            self.sequence_number,
                                            flags,
                                            self.receiving_window.ack_number,
                                            self.sending_window.window_size,
                                            data,
                                            mss=self.mss,
                                            is_retransmission=is_retransmission,
                                       )
                                       )
        self.sequence_number += packet["TCP"].length
        return packet

    def _send_ack_for(self, packet, additional_flags: set = None):
        """
        Creates and sends an ACK packet for the given `Packet` that was received from the other side.
        :param packet: a `Packet` object.
        :param additional_flags: a set of additional flags to put in the ACK packets
        :return: a TCP packet
        """
        is_retransmission = False
        additional_flags_set = set() if not additional_flags else additional_flags

        if packet["TCP"].sequence_number == self.receiving_window.ack_number:
            # ^ the received packet is in-order
            self.receiving_window.ack_number += packet["TCP"].length

        elif packet["TCP"].sequence_number < self.receiving_window.ack_number:
            # ^ the packet was already received (lost ACK)
            is_retransmission = True

        elif packet["TCP"].sequence_number > self.receiving_window.ack_number:
            # ^ a sequence number was jumped (lost packet)
            is_retransmission = True
            self.receiving_window.add_to_sack(packet)
            self.receiving_window.merge_sack_blocks()

        ack = self._create_packet(({OPCODES.TCP.ACK} | additional_flags_set), is_retransmission=is_retransmission)
        ack["TCP"].options[PROTOCOLS.TCP.OPTIONS.SACK] = self.receiving_window.sack_blocks[:]

        if additional_flags_set:
            self.sending_window.add_waiting(ack)
        else:
            self.sending_window.add_no_wait(ack)

    def _my_tcp_packets(self, packet):
        """
        This is a tester function that checks if a packet is for this TCP session.
        :param packet: a `Packet` object.
        :return: True of False
        """
        if "TCP" not in packet or \
                not packet.is_valid() or \
                not self.computer.has_this_ip(packet["IP"].dst_ip) or \
                packet["TCP"].dst_port != self.src_port:
            return False

        tcp_packet = packet["TCP"]

        if (self.dst_ip is None or self.dst_port is None or self.dst_port is None) and \
                OPCODES.TCP.SYN in tcp_packet.flags:
            return True

        return packet["IP"].src_ip == self.dst_ip and \
            tcp_packet.dst_port == self.src_port and \
            tcp_packet.src_port == self.dst_port

    def _tcp_with_flags(self, *flag_lists):
        """
        Takes in a bunch of flag lists, if any of them fit exactly returns a function that returns true on them
        For example if we receive ([TCP_SYN, TCP_ACK], [TCP_RST]) we will return a function that will return True
        if a packet is either a SYN-ACK or a RST.
        :param flags:
        :return:
        """
        def tester(packet):
            return self.computer.has_this_ip(packet["IP"].dst_ip) and \
                   any("TCP" in packet and
                       packet["TCP"].dst_port == self.src_port and
                       flags == packet["TCP"].flags
                       for flags in flag_lists)
        return tester

    def reset_connection(self):
        """
        When you need to abruptly end the connection.
        (Sends a TCP RST packet)
        :return: None
        """
        self.computer.send(self._create_packet({OPCODES.TCP.RST}))
        self._end_session()

    def _update_from_handshake_packet(self, packet):
        """
        Takes in a `ReturnedPacket` object which is the SYN or SYN ACK packet of the handshake and updates all of
        details of the process according to it.
        :return: None
        """
        self.dst_port = packet["TCP"].src_port
        self.dst_ip = packet["IP"].src_ip
        self.sending_window.window_size = min(packet["TCP"].window_size, self.sending_window.window_size)
        self.mss = min(packet["TCP"].options[PROTOCOLS.TCP.OPTIONS.MSS], self.mss)

    def _acknowledge_with_packet(self, packet):
        """
        Takes in an ACk number and releases all of the packets that are ACKed by it.
        :param packet: a packet that contains the ACK information to remove sent packets from my sending window.
        :return: None
        """
        ack_number = packet["TCP"].ack_number
        acked_count = 0
        for not_acked_packet in self.sending_window.window:
            if is_number_acking_packet(ack_number, not_acked_packet.packet):
                acked_count += 1
            else:
                break
        self.sending_window.slide_window(acked_count)

        sack_blocks = packet["TCP"].options[PROTOCOLS.TCP.OPTIONS.SACK]
        if not isinstance(sack_blocks, list) or not sack_blocks:
            return
        for not_acked_packet in list(self.sending_window.window):
            for left, right in sack_blocks:
                if left <= not_acked_packet.packet["TCP"].sequence_number and \
                        is_number_acking_packet(right, not_acked_packet.packet):
                    self.sending_window.window.remove(not_acked_packet)

    def hello_handshake(self):
        """
        Starts the TCP handshake by sending a SYN packet to the destination.
        :return: None
        """
        if self.is_client:
            yield from self._client_hello_handshake()
        else:  # if is server
            yield from self._server_hello_handshake()

    def _client_hello_handshake(self):
        """
        the initial handshake on the client side. sends syn, waits for syn ack, sends ack.
        :return:
        """
        ip_for_the_mac, done_searching = self.computer.request_address(self.dst_ip, self)
        yield WaitingFor(done_searching)
        self.dst_mac = self.computer.arp_cache[ip_for_the_mac].mac

        self.sending_window.add_waiting(self._create_packet({OPCODES.TCP.SYN}))

        tcp_syn_ack_list = []
        yield from self.handle_tcp_and_receive(tcp_syn_ack_list, is_blocking=True, receive_flags=True)
        if self.kill_me:
            self.computer.print("Server unavailable :(!")
            return

        syn_ack, = tcp_syn_ack_list
        self._update_from_handshake_packet(syn_ack)

    def _server_hello_handshake(self):
        """
        The initial handshake on the server side. waits for syn, sends syn ack waits for ack
        :return:
        """
        tcp_syn_list = []
        while not tcp_syn_list or \
                not isinstance(tcp_syn_list[0], Packet) or \
                "TCP" not in tcp_syn_list[0] or \
                OPCODES.TCP.SYN not in tcp_syn_list[0]["TCP"].flags:
            yield from self.handle_tcp_and_receive(tcp_syn_list, is_blocking=True, receive_flags=True)
        syn, = tcp_syn_list
        self._update_from_handshake_packet(syn)

        ip_for_the_mac, done_searching = self.computer.request_address(self.dst_ip, self)
        yield WaitingFor(done_searching)
        self.dst_mac = self.computer.arp_cache[ip_for_the_mac].mac

        self._send_ack_for(syn, {OPCODES.TCP.SYN})  # sends SYN ACK
        while not self.sending_window.nothing_to_send():  # while the syn ack was not ACKed
            yield from self.handle_tcp_and_receive([], receive_flags=True)

    def _send_and_wait_with_retries(self, sent, waiting_for, timeout, got_packet=None, max_tries=PROTOCOLS.ARP.RESEND_COUNT):
        """
        Receives a packet and a condition for a reply to that packet and receives a timeout for waiting.
        Sends the packet and waits for the reply for it. If did not get a reply in `timeout` seconds, try again,
        do this for `max_tries` times. If still did not get the packet, reset the connection.
        This is a generator that yields `WaitingFor` tuples.
        :param sent: The `Packet` to send
        :param waiting_for: a condition packet to wait for which is the answer for the packet you send
        :param got_packet: a `ReturnedPacket` object that will contain the packet that is returned.
        :param timeout: the amount of seconds to wait for a reply
        :param max_tries: the amount of tries before giving up
        :return: None
        """
        returned_packet = NoNeedForPacket() if got_packet is None else got_packet
        self.computer.send(sent)
        for _ in range(max_tries):
            yield WaitingForPacketWithTimeout(waiting_for, returned_packet, Timeout(timeout))
            if returned_packet.packets:
                return
            self.computer.send(sent)

        self.reset_connection()
        return

    def goodbye_handshake(self, initiate=True):
        """
        Ends the TCP connection with good terms and with both sides' agreement.
        This can be called with `initiate=True` to end the connection.
        This should be called with `initiate=False` if a TCP FIN packet was received from the destination computer.
        :return: None
        """
        if initiate:
            self.sending_window.clear()
            self.sending_window.add_waiting(self._create_packet({OPCODES.TCP.FIN}))
            fin_ack_list = []
            while not fin_ack_list or \
                    not isinstance(fin_ack_list[0], Packet) or \
                    "TCP" not in fin_ack_list[0] or \
                    {OPCODES.TCP.FIN, OPCODES.TCP.ACK} != fin_ack_list[0]["TCP"].flags:
                yield from self.handle_tcp_and_receive(fin_ack_list, receive_flags=True)
                if fin_ack_list:
                    pass

            self._send_ack_for(fin_ack_list[0])
            while not self.sending_window.nothing_to_send():
                yield from self.handle_tcp_and_receive([], receive_flags=True)

        else:  # if received a FIN, then sent a FIN ACK from the main function
            timeout = Timeout(PROTOCOLS.TCP.RESEND_TIME * 2)
            while not self.sending_window.nothing_to_send() and not timeout:  # waiting for an ACK for the fin ack...
                yield from self.handle_tcp_and_receive([], receive_flags=True)
        self._end_session()

    def _end_session(self):
        """
        Ends the current session. For the client that kills the process after it is done, this does nothing
        This is mostly for servers that server multiple clients in the same process. It resets everything and gets ready
        to serve another client.
        :return:
        """
        self.sending_window.clear()
        self.receiving_window.clear()
        self.sequence_number = 0
        self.receiving_window.ack_number = 0
        self.dst_port = None
        self.dst_mac = None

    def send(self, data, packet_constructor=lambda d: d):
        """
        Takes in some ip_layer and sends it over TCP as soon as possible.
        :param data: the piece of the ip_layer that the child process class wants to send over TCP
        :param packet_constructor: a function is applied to the ip_layer after it is divided to TCP segments and before
        it is sent.
        :return: None
        """
        if isinstance(data, str):
            for data_part in split_by_size(data, self.mss):
                self.send_no_split(packet_constructor(data_part))
        else:
            self.send_no_split(data)

    def send_no_split(self, data):
        """
        This function assumes that the length of the ip_layer is not larger than the MSS of the process.
        If it is larger, raises an exception.
        :param data:
        :return:
        """
        if len(data) > self.mss:
            raise TCPDataLargerThanMaxSegmentSize("To split string ip_layer, use the `TCPProcess.send` method")
        self.sending_window.add_waiting(self._create_packet({OPCODES.TCP.PSH}, data))

    def is_done_transmitting(self):
        """
        Returns whether or not the process has finished transmitting all of the desired ip_layer.
        :return: bool
        """
        return self.sending_window.nothing_to_send()

    def _session_timeout(self):
        """Returns whether or not the connection should be timed-out"""
        return MainLoop.instance.time_since(self.last_packet_sent_time) >= PROTOCOLS.TCP.MAX_UNUSED_CONNECTION_TIME

    def _physically_send_packets_with_time_gaps(self):
        """
        Sends the next packet in the `self.sending_window.sent` list.
        The packets are not all sent in one go because then the graphics will one over the other.
        This function sends a packet if was not just sent.
        :return:
        """
        if MainLoop.instance.time_since(self.last_packet_sent_time) > PROTOCOLS.TCP.SENDING_INTERVAL:
            if self.sending_window.sent:
                self.computer.send(self.sending_window.sent.popleft())
                self.last_packet_sent_time = MainLoop.instance.time()

    def handle_tcp_and_receive(self, received_data, is_blocking=False, receive_flags=False):
        """
        This function is a generator that yield `WaitingFor` and `WaitingForPacket` namedtuple-s.
        It receives TCP packets from the destination sends ACKs sends all of the other packets in the
        TCP_SENDING_INTERVAL gaps. "Blocks" the process until packets are received.
        :param received_data: a list that we append ip_layer we receive to it. Any packet's ip_layer is appended to it.
        :param is_blocking: whether or not the function loops until it receives a packet.
        If a FIN was received, appends the list a `DON_RECEIVING` constant (None) that tells
        it that the process terminates.
        :param receive_flags: whether or not to insert TCP SYN and FIN packets to the `received_data`
        :return: yields WaitingFor-s.

        when a SYN packet is received, the whole packet is appended to the received_data list.
        """
        received_packets = ReturnedPacket()

        while not received_packets.packets:
            yield WaitingForPacketWithTimeout(self._my_tcp_packets, received_packets, Timeout(0.01))

            for packet in received_packets.packets:
                yield from self._handle_packet_and_receive(packet, received_data, receive_flags)
                if self.kill_me:
                    return

            self.receiving_window.add_data_and_remove_from_window(received_data)

            self.sending_window.fill_window()  # if the amount of sent packets is not the window size, fill it up
            self.sending_window.send_window()  # send the packets that were not yet sent
            self.sending_window.retransmit_unacked()  # send the packets that were sent a long time ago and not ACKed.

            self._physically_send_packets_with_time_gaps()  # send all of the packets above in appropriate time gaps

            if not is_blocking:
                return

    def _handle_packet_and_receive(self, packet, received_data, receive_flags):
        """
        Receives a packet and handles it, sends ack, learns, and adds the ip_layer to a given `received_data` list
        :param packet: the packet to handle
        :param received_data: a list of ip_layer from the PSH tcp packets
        :return: None
        """
        tcp_layer = packet["TCP"]

        if OPCODES.TCP.PSH in tcp_layer.flags:
            if not is_number_acking_packet(self.receiving_window.ack_number, packet):
                self.receiving_window.add_packet(packet)  # if the packet was not received already
            self._send_ack_for(packet)

        if OPCODES.TCP.SYN in tcp_layer.flags or {OPCODES.TCP.FIN, OPCODES.TCP.ACK} == tcp_layer.flags:
            if receive_flags:
                received_data.append(packet)

            if {OPCODES.TCP.SYN, OPCODES.TCP.ACK} == tcp_layer.flags:
                self._send_ack_for(packet)

        if OPCODES.TCP.ACK in tcp_layer.flags:
            self._acknowledge_with_packet(packet)

        if {OPCODES.TCP.FIN} == tcp_layer.flags and not receive_flags:
            self._send_ack_for(packet, additional_flags={OPCODES.TCP.FIN})  # FIN ACK
            yield from self.goodbye_handshake(initiate=False)
            received_data.append(PROTOCOLS.TCP.DONE_RECEIVING)

        if OPCODES.TCP.RST in tcp_layer.flags:
            received_data.append(PROTOCOLS.TCP.DONE_RECEIVING)
            self.kill_me = True

    @abstractmethod
    def code(self):
        """
        The actual code of the process if for each child process to implement
        :return: generator of `WaitingFor`s bluh bluh you know the drill...
            (If not go to 'processes.process.py' and read some documentation :) )
        """
        pass

    def __repr__(self):
        """String representation of the process"""
        return "A TCP Process"


class SendingWindow:
    """
    A class that represents the sending window in a TCP process.
    It has three queues, the packets that are not yet sent, the packets that are sent and not yet acked and a list of
    `sent` packets that need to be physically sent one by one (in the `TCP_SENDING_INTERVAL` time gaps).
    """
    def __init__(self, window_size=PROTOCOLS.TCP.MAX_WINDOW_SIZE):
        """
        Initiates the three queues of the window.
        """
        self.window_size = window_size

        self.waiting_for_sending = deque()
        self.window = deque()
        self.sent = deque()

    def clear(self):
        """
        Clears all of the attributes of the window.
        :return:
        """
        self.waiting_for_sending.clear()
        self.window.clear()
        self.sent.clear()

    def fill_window(self):
        """
        Fills the window until it is in its full window size
        :return:
        """
        while len(self.window) < self.window_size and self.waiting_for_sending:
            self.window.append(NotAckedPacket(self.waiting_for_sending.popleft(), MainLoop.instance.time(), False))

    def slide_window(self, count):
        """
        Moves the window `count` packets to the right.
        Also fills up the window if it is not full.
        :return:
        """
        for _ in range(count):
            if not self.window:
                break
            self.window.popleft()
        self.fill_window()

    def send_window(self):
        """
        Sends all of the packets in the window (adds them to the `sent` queue)
        Only does that to NotAckedPackets where the `is_sent` attribute is False.
        :return:
        """
        for not_acked_packet in self.window:
            if not not_acked_packet.is_sent:
                self.sent.append(not_acked_packet.packet.copy())
                not_acked_packet.is_sent = True

    def add_waiting(self, packet):
        """
        Adds a new packet to the end of the `waiting_for_sending` queue
        :param packet: a `Packet` object.
        :return:
        """
        self.waiting_for_sending.append(packet)

    def add_no_wait(self, packet):
        """
        Adds a packet to the `sent` queue so it will be sent almost immediately
        :param packet:
        :return:
        """
        self.sent.append(packet.copy())

    def nothing_to_send(self):
        """
        Returns whether or there is nothing left to send.
        :return:
        """
        return not self.sent and not self.window and not self.waiting_for_sending

    def retransmit_unacked(self):
        """
        Retransmits all of the packets that were not ACKed for too long!
        :return: None
        """
        for not_acked_packet in list(self.window):
            if MainLoop.instance.time_since(not_acked_packet.sending_time) > PROTOCOLS.TCP.RESEND_TIME:
                not_acked_packet.packet["TCP"].is_retransmission = True
                self.add_no_wait(not_acked_packet.packet)
                not_acked_packet.sending_time = MainLoop.instance.time()

    def __repr__(self):
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
    def __init__(self):
        """
        Initiates the receiving window with an empty window.
        """
        self.window = []
        self.ack_number = 0
        self.sack_blocks = []

    def clear(self):
        """
        Clears the window and resets it like it was just created
        :return:
        """
        self.window.clear()
        self.sack_blocks.clear()
        self.ack_number = 0

    def add_packet(self, packet):
        """
        Adds a packet to the window.
        :return:
        """
        insort(self.window, packet, key=lambda p: p["TCP"].sequence_number)

    def add_data_and_remove_from_window(self, received_data):
        """
        Adds the ip_layer from all of the packets that arrived in-order to the given list.
        Also removes them from the receiving window.
        :param received_data: a list of ip_layer that is received from the destination computer.
        :return: None
        """
        for packet in self.window[:]:
            if is_number_acking_packet(self.ack_number, packet):
                received_data.append(packet["TCP"].data)
                self.window.remove(packet)
            else:
                break  # the window is sorted by the sequence number.

    def add_to_sack(self, packet):
        """
        Adds a packet to the SACK ip_layer of the process.
        :param packet: a `Packet` object that contains a TCP layer
        :return: None
        """
        packet_start = packet["TCP"].sequence_number
        packet_length = packet["TCP"].length
        packet_end = packet_start + packet_length

        for block in self.sack_blocks:
            if block.left == packet_end:
                block.left = packet_start
                return
            elif block.right == packet_start:
                block.right = packet_end
                return

        insort(self.sack_blocks, SackEdges(packet_start, packet_end), key=attrgetter('left'))

    def merge_sack_blocks(self):
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
