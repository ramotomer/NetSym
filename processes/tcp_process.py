import random
from abc import ABCMeta, abstractmethod
from collections import deque

from recordclass import recordclass

from consts import *
from gui.main_loop import MainLoop
from packets.tcp import TCP
from processes.process import Process, WaitingForPacketWithTimeout, Timeout, WaitingForPacket, ReturnedPacket, \
    NoNeedForPacket, WaitingFor

NotAckedPacket = recordclass("NotAckedPacket", "packet sending_time is_sent")  # this is like a `namedtuple` but it is mutable!


class TCPProcess(Process, metaclass=ABCMeta):
    """
    The TCP process abstract class which represents any TCP based process (HTTP, SSH whatever)
    It creates an abstraction for all of the methods for sending and receiving data without the child process class has to
    handle of the retransmissions and ACKs and all of that. that is handled here.

    A server-side `code` function example:

    while True:
        yield from self.hello_handshake()
        # ^ blocks the process until a client is connected.

        self.send(<DATA>)
        while not self.is_done_transmitting():   # until all is acked and fine
            yield from self.handle_tcp_and_receive([])

        yield from self.goodbye_handshake(initiate=True)

    """
    def __init__(self, computer, dst_ip=None, dst_port=None , src_port=None, is_client=True):
        """
        Initiates a TCP process.
        :param computer: the `Computer` running the process
        :param dst_ip: the `IPAddress` of the other computer in the session. (If unknown at initiation - None)
        :param dst_port: the destination port number of the other computer in the session. (If unknown at initiation - None)
        :param is_client: whether or not this computer sends the initial SYN packet.
        :param src_port: the source port of the process (If unknown - None - and it will be randomized)
        """
        super(TCPProcess, self).__init__(computer)

        self.is_client = is_client  # decides who sends the original SYN packet (the client does)

        self.dst_ip = dst_ip
        self.src_port = random.randint(*TCP_USABLE_PORT_RANGE) if self.is_client else src_port
        self.dst_port = dst_port
        self.dst_mac = None

        self.sequence_number = 0  # randint(0, TCP_MAX_SEQUENCE_NUMBER)
        self.next_sequence_number = 1 + self.sequence_number
        self.ack_next_sequence_number = 0

        self.sending_window = SendingWindow()

        self.last_packet_sent_time = MainLoop.instance.time()

    def _create_packet(self, flags=None, data=''):
        """Creates a full packet that contains TCP with all of the appropriate fields according to the state of this process"""
        packet = self.computer.ip_wrap(self.dst_mac, self.dst_ip,
                                     TCP(self.src_port,
                                         self.dst_port,
                                         self.sequence_number,
                                         flags,
                                         self.ack_next_sequence_number,
                                         self.sending_window.window_size,
                                         data)
                                     )
        self.sequence_number += 1 if TCP_SYN in flags else len(data)
        return packet

    def _send_ack_for(self, packet):
        """
        Creates and sends an ACK packet for the given `Packet` that was received from the other side.
        :param packet: a `Packet` object.
        :return: a TCP packet
        """
        self.ack_next_sequence_number += packet["TCP"].length if not packet["TCP"].flags[TCP_SYN] else 1
        self.sending_window.add_no_wait(self._create_packet([TCP_ACK]))

    def _my_tcp_packets(self, packet):
        """
        This is a tester function that checks if a packet is for this TCP session.
        :param packet: a `Packet` object.
        :return: True of False
        """
        return "TCP" in packet and packet.is_valid() and \
               self.computer.has_this_ip(packet["IP"].dst_ip) and packet["IP"].src_ip == self.dst_ip and \
               packet["TCP"].dst_port == self.src_port and packet["TCP"].src_port == self.dst_port

    def _tcp_with_flags(self, flags):
        """
        Returns a function
        :param flags:
        :return:
        """
        def tester(packet):
            return "TCP" in packet and \
            all(packet["TCP"].flags[flag] for flag in flags)  and \
            not any(packet["TCP"].flags[flag] for flag in (set(TCP_FLAGS) - set(flags))) and \
            self.computer.has_this_ip(packet["IP"].dst_ip)
        return tester

    def reset_connection(self):
        """
        When you need to abruptly end the connection.
        (Sends a TCP RST packet)
        :return: None
        """
        self.computer.send(self._create_packet([TCP_RST]))

    def _update_from_handshake_packet(self, packet):
        """
        Takes in a `ReeturnedPacket` object which is the SYN or SYN ACK packet of the handshake and updates all of
        details of the process according to it.
        :param returned_packet: a `Packet` object
        :return: None
        """
        self.dst_port = packet["TCP"].src_port
        self.dst_ip = packet["IP"].src_ip
        self.sending_window.window_size = min(packet["TCP"].window_size, self.sending_window.window_size)
        # add MSS here!

    def _acknowledge_packets(self, ack_number):
        """
        Takes in an ACk number and releases all of the packets that are ACKed by it.
        :param ack_number: a number of an ACK in a TCP ACK packet.
        :return: None
        """
        acked_count = 0
        for packet, _, _ in self.sending_window.window:
            if packet["TCP"].sequence_number + packet["TCP"].length <= ack_number:
                acked_count += 1
            else:
                break
        self.sending_window.slide_window(acked_count)

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
        ip_for_the_mac, done_searching = self.computer.request_address(self.dst_ip)
        yield WaitingFor(done_searching)
        if ip_for_the_mac not in self.computer.arp_cache:
            self.kill_me = True
            return
        self.dst_mac = self.computer.arp_cache[ip_for_the_mac].mac

        self.computer.send(self._create_packet([TCP_SYN]))

        tcp_syn_ack = ReturnedPacket()
        yield WaitingForPacket(self._tcp_with_flags([TCP_SYN, TCP_ACK]), tcp_syn_ack)
        packet = tcp_syn_ack.packet
        self._update_from_handshake_packet(packet)

        self.ack_next_sequence_number = 1
        self.computer.send(self._create_packet([TCP_ACK]))

    def _server_hello_handshake(self):
        """
        The initial handshake on the server side. waits for syn, sends syn ack waits for ack
        :return:
        """
        tcp_syn = ReturnedPacket()
        yield WaitingForPacket(self._tcp_with_flags([TCP_SYN]), tcp_syn)
        self._update_from_handshake_packet(tcp_syn.packet)

        ip_for_the_mac, done_searching = self.computer.request_address(self.dst_ip)
        yield WaitingFor(done_searching)
        if ip_for_the_mac not in self.computer.arp_cache:
            self.kill_me = True
            return
        self.dst_mac = self.computer.arp_cache[ip_for_the_mac].mac

        self.ack_next_sequence_number = 1
        self.computer.send(self._create_packet([TCP_SYN, TCP_ACK]))

        yield WaitingForPacket(self._tcp_with_flags([TCP_ACK]), NoNeedForPacket())

    def goodbye_handshake(self, initiate=True):
        """
        Ends the TCP connection with good terms and with both sides' agreement.
        This can be called with `initiate=True` to end the connection.
        This should be called with `initiate=False` if a TCP FIN packet was received from the destination computer.
        :return: None
        """
        if initiate:
            self.computer.send(self._create_packet([TCP_FIN]))
            tcp_fin_ack = ReturnedPacket()
            yield WaitingForPacket(self._tcp_with_flags([TCP_FIN, TCP_ACK]), tcp_fin_ack)
            self.computer.send(self._create_packet([TCP_ACK]))

        else:  # if received a FIN
            self.computer.send(self._create_packet([TCP_FIN, TCP_ACK]))
            yield WaitingForPacket(self._tcp_with_flags([TCP_ACK]), NoNeedForPacket())

    def send(self, data):
        """
        Takes in some data and sends it over TCP as soon as possible.
        :param data: the piece of the data that the child process class wants to send over TCP
        :return: None
        """
        self.sending_window.add_waiting(self._create_packet([TCP_PSH], data))

    def is_done_transmitting(self):
        """
        Returns whether or not the process has finished transmitting all of the desired data.
        :return: bool
        """
        return self.sending_window.nothing_to_send()

    def _session_timeout(self):
        """Returns whether or not the connection should be timed-out"""
        return MainLoop.instance.time_since(self.last_packet_sent_time) >= TCP_MAX_UNUSED_CONNECTION_TIME

    def handle_tcp_and_receive(self, received_data):
        """
        This function is a generator that yield `WaitingFor` and `WaitingForPacket` namedtuple-s.
        It receives TCP packets from the destination sends ACKs sends all of the other packets in the TCP_SENDING_INTERVAL gaps.
        "Blocks" the process until packets are received.
        :param received_data: a list that we append data we receive to it. Any packet's data is appended to it.
        If a FIN was received, appends the list a `DON_RECEIVING` constant (None) that tells it that the process terminates.
        :yields WaitingFor-s.
        """
        packets = ReturnedPacket()
        yield WaitingForPacketWithTimeout(self._my_tcp_packets, packets, Timeout(0.01))

        self.sending_window.fill_window()  # if the amount of sent packets is not the window size
        self.sending_window.send_window()  # send the packets that were not yet sent
        self.sending_window.retransmit_unacked()  # send the packets that were sent a long time ago and not ACKed.

        if MainLoop.instance.time_since(self.last_packet_sent_time) > TCP_SENDING_INTERVAL:
            if self.sending_window.sent:
                self.computer.send(self.sending_window.sent.popleft())
                self.last_packet_sent_time = MainLoop.instance.time()       # physically send all of the packets in the appropriate time gaps

        for packet in packets.packets:
            if packet["TCP"].flags[TCP_PSH] or packet["TCP"].flags[TCP_SYN]:
                self._send_ack_for(packet)
                received_data.append(packet["TCP"].data)
            if packet["TCP"].flags[TCP_ACK]:
                self._acknowledge_packets(packet["TCP"].ack_number)
            if packet["TCP"].flags[TCP_FIN]:
                yield from self.goodbye_handshake(initiate=False)
                received_data.append(TCP_DONE_RECEIVING)

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
        return "Some TCP Process"


class SendingWindow:
    """
    A class that represents the sending window in a TCP process.
    It has three queues, the packets that are not yet sent, the packets that are sent and not yet acked and a list of
    `sent` packets that need to be physically sent one by one (in the `TCP_SENDING_INTERVAL` time gaps).
    """
    def __init__(self, window_size=TCP_MAX_WINDOW_SIZE):
        """
        Initiates the three queues of the window.
        """
        self.window_size = window_size

        self.waiting_for_sending = deque()
        self.window = deque()
        self.sent = deque()

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
                self.sent.append(not_acked_packet.packet)
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
        Adds a packet to the `sent` queue so it will be sent almost immidiately
        :param packet:
        :return:
        """
        self.sent.append(packet)

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
            if MainLoop.instance.time_since(not_acked_packet.sending_time) > TCP_RESEND_TIME:
                self.add_waiting(not_acked_packet.packet)
                not_acked_packet.sending_time = MainLoop.instance.time()

    def __repr__(self):
        """The string representation of the sending window"""
        window = [(not_acked.packet["TCP"].true_flags_string, not_acked.packet["TCP"].sequence_number) for not_acked in self.window]
        return f"""
waiting to be sent: {[packet["TCP"].sequence_number for packet in self.waiting_for_sending]}
window: {window}
window size: {self.window_size}
sent: {[tcp.sequence_number for tcp in self.sent]}
"""
