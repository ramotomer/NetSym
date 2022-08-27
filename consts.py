# this cannot import from anything!!! (almost)
import os
from math import sqrt

import pyglet
from scapy.layers.dhcp import DHCPTypes

from exceptions import TCPDoneReceiving


def debugp(*strings):
    """
    A print i use for debugging so i know where to delete it afterwards.
    :param string:
    :return:
    """
    print(f"DEBUG:", *strings)


SENDING_GRAT_ARPS = False


class ADDRESSES:
    class MAC:
        BROADCAST = 'ff:ff:ff:ff:ff:ff'
        STP_MULTICAST = "01:80:C2:00:00:00"

        SEPARATOR = ':'

    class IP:
        DEFAULT = "192.168.1.2/24"
        ON_LINK = "On-link"
        SEPARATOR = '.'
        SUBNET_SEPARATOR = '/'
        DEFAULT_SUBNET_MASK = '24'
        BIT_LENGTH = 32

    class LLC:
        STP_SAP = 0x42
        STP_CONTROL_FIELD = 0x3


class OS:
    WINDOWS = 'Windows'
    LINUX = 'Linux'
    SOLARIS = 'Solaris'


class TTL:
    BY_OS = {
        OS.LINUX: 64,
        OS.WINDOWS: 128,
        OS.SOLARIS: 255,
    }
    MAX = 255


class TCPFlag(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    @classmethod
    def absolute_value(cls, other):
        if isinstance(other, cls):
            return other.value
        return int(other)
        # raise TypeError(f"Type '{type(other)}' has no absolute value! only `TCPFlag` and `int` have!!")

    def __or__(self, other):
        return self.value | self.absolute_value(other)

    def __repr__(self):
        return self.name

    def __add__(self, other):
        return self.name + str(other)

    def __int__(self):
        return int(self.value)

    def __eq__(self, other):
        return self.value == self.absolute_value(other)

    def __hash__(self):
        return hash((self.name, self.value))


class OPCODES:
    class ARP:
        REQUEST = 1
        REPLY = 2
        GRAT = "gratuitous ARP"

    class ICMP:
        class TYPES:
            REQUEST = 8
            REPLY = 0
            TIME_EXCEEDED = 11
            UNREACHABLE = 3

        class CODES:
            NETWORK_UNREACHABLE = 0
            PORT_UNREACHABLE = 3

    class DHCP:
        DISCOVER = "discover"
        OFFER = "offer"
        REQUEST = "request"
        PACK = "ack"

    class FTP:
        REQUEST_PACKET = "FTP Request"
        DATA_PACKET = "FTP Data"

    class TCP:
        FIN =      TCPFlag("FIN",      0b00001)
        SYN =      TCPFlag("SYN",      0b00010)
        RST =      TCPFlag("RST",      0b00100)
        PSH =      TCPFlag("PSH",      0b01000)
        ACK =      TCPFlag("ACK",      0b10000)
        NO_FLAGS = TCPFlag("No Flags", 0b00000)
        RETRANSMISSION = " retransmission"
        FLAGS_DISPLAY_PRIORITY = [SYN, FIN, RST, PSH, ACK]

    class DNS:
        REQUEST = 'request'
        REPLY = 'reply'

    class BOOTP:
        REQUEST = "BOOTREQUEST"
        REPLY = "BOOTREPLY"


class PROTOCOLS:
    class ARP:
        RESEND_TIME = 6  # seconds
        RESEND_COUNT = 3  # seconds

    class ICMP:
        INFINITY = float("inf")  # the builtin infinity

    class DHCP:
        DEFAULT_TTL = 0

    class TCP:
        MAX_SEQUENCE_NUMBER = 2**32 - 1
        RESEND_TIME = 15  # seconds
        MAX_WINDOW_SIZE = 20  # packets
        SENDING_INTERVAL = 0.1  # seconds
        DONE_RECEIVING = TCPDoneReceiving
        MAX_UNUSED_CONNECTION_TIME = 15  # seconds
        MAX_MSS = 100

        class OPTIONS:
            MSS = "MSS"  # maximum segment size
            WINDOW_SCALE = "Window Scale"
            SACK = "SACK"
            TIMESTAMPS = "Timestamps"

    class STP:
        DEFAULT_SWITCH_PRIORITY = 32768
        NORMAL_SENDING_INTERVAL = 1.7  # seconds
        STABLE_SENDING_INTERVAL = 6  # seconds
        BLOCKED_INTERFACE_UPDATE_INTERVAL = 10  # seconds
        TREE_STABLIZING_MAX_TIME = 30  # seconds
        ROOT_MAX_DISAPPEARING_TIME = 40
        MAX_CONNECTION_DISAPPEARED_TIME = 40

        ROOT_PORT = "ROOT"
        DESIGNATED_PORT = "DESIGNATED"
        BLOCKED_PORT = "BLOCKED"
        NO_STATE = "no state!"

    class ECHO_SERVER:
        DEFAULT_REQUEST_COUNT = 1


class PORTS:
    DAYTIME = 13
    FTP = 21
    SSH = 22
    DNS = 53
    DHCP_SERVER = 67
    DHCP_CLIENT = 68
    HTTP = 80
    HTTPS = 443
    ECHO_SERVER = 1000
    ECHO_CLIENT = 1001

    SERVER_PORTS = [DAYTIME, FTP, SSH, DNS, DHCP_SERVER, HTTP, HTTPS, ECHO_SERVER]

    USERMODE_USABLE_RANGE = (2 ** 15 - 2 ** 14), 2 ** 16 - 1

    TO_IMAGES = {
        DAYTIME: "processes/daytime_process.png",
        FTP: "processes/ftp_process.png",
        SSH: "processes/ssh_process.png",
        HTTP: "processes/http_process.png",
        HTTPS: "processes/https_process.png",
        ECHO_SERVER: "processes/echo_server_process.png",
    }


class KEYBOARD:
    PRINTABLE_RANGE = range(0x20, 0x80)

    class MODIFIERS:
        """
        key modifiers, you can `|` them together to get the different combinations.
        """
        NONE =    0b00000000
        SHIFT =   0b00000001
        CTRL =    0b00000010
        ALT =     0b00000100
        CAPS =    0b00001000
        NUMLOCK = 0b00010000
        WINKEY =  0b00100000

        KEY_TO_MODIFIER = {
            pyglet.window.key.LSHIFT: SHIFT,
            pyglet.window.key.RSHIFT: SHIFT,
            pyglet.window.key.LCTRL: CTRL,
            pyglet.window.key.RCTRL: CTRL,
            pyglet.window.key.LALT: ALT,
            pyglet.window.key.RALT: ALT,
            pyglet.window.key.LWINDOWS: WINKEY,
            pyglet.window.key.RWINDOWS: WINKEY,
        }


class MESSAGES:
    INVALID_MAC_ADDRESS = "The MAC address is not valid!"
    INVALID_IP_ADDRESS = "The IP address is not valid!"

    class INSERT:
        PL = "insert your desired pl (0 <= pl <= 1)!!!"
        SPEED = "insert your desired connection speed:"
        IP = "Enter your desired IP for this interface:"
        GATEWAY = "Enter your desired IP for the gateway:"
        INTERFACE_INFO = "Insert the name of the interface:"
        IP_FOR_PROCESS = "Insert an IP to start your process to:"
        PORT_NUMBER = "Insert a port number to open/close:"
        COMPUTER_NAME = "Insert a new name for the computer:"
        COLOR = "choose a color:"


class DIRECTORIES:
    IMAGES = "../res/sprites"
    ANIMATIONS = "../res/animations"
    FILES = "../res/files"
    SAVES = "../res/files/saves"


INTERFACE_NAMES = [line.strip() for line in open(os.path.join(DIRECTORIES.FILES, "interface_names.txt")).readlines()]
COMPUTER_NAMES = [line.strip() for line in open(os.path.join(DIRECTORIES.FILES, "computer_names.txt")).readlines()]
TRANSFER_FILE = "transfer_me.txt"
WINDOW_INPUT_LIST_FILE = os.path.join(DIRECTORIES.FILES, "window_inputs.txt")


class COLORS:
    BLUE = (0, 0, 255)
    RED = (150, 0, 0)
    GREEN = (0, 255, 0)
    YELLOW = (200, 200, 0)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (10, 10, 10)
    BROWN = (62, 39, 35)
    PURPLE = (171, 71, 188)
    PINK = (255, 170, 170)
    TURQUOISE = (10, 255, 255)
    ORANGE = (255, 215, 0)

    VERY_LIGHT_GRAY = (200, 200, 200)
    SOMEWHAT_LIGHT_GRAY = (170, 170, 170)
    LIGHT_GRAY = (150, 150, 150)
    DARK_GRAY = (20, 20, 20)
    LIGHT_BLUE = (100, 100, 255)
    VERY_LIGHT_BLUE = (180, 180, 255)
    LIGHT_GREEN = (50, 255, 50)
    DARK_GREEN = (0, 100, 0)
    DARK_RED = (100, 0, 0)
    LIGHT_RED = (255, 50, 50)

    COLOR_DIFF = 20
    LARGE_COLOR_DIFF = 70


class WINDOWS:
    class MAIN:
        NAME = "NetSym"
        WIDTH = 1275
        HEIGHT = 600  # if not __debug__ else 350
        INITIAL_LOCATION = 4, 50
        FRAME_RATE = 1 / 60.0
        BACKGROUND = COLORS.VERY_LIGHT_GRAY  # if not __debug__ else COLORS.WHITE

    class SIDE:
        WIDTH = 230
        COLOR = COLORS.LIGHT_GRAY

        class VIEWING_OBJECT:
            class TEXT:
                PADDING = (7, -10)

    class POPUP:
        STACKING_PADDING = 10, -10
        DEACTIVATED_COLOR = COLORS.LIGHT_GRAY

        class DIRECTIONS:
            RIGHT = 'right'
            LEFT =  'left'
            UP =    'up'
            DOWN =  'down'

            OPPOSITE = {
                RIGHT: LEFT,
                LEFT: RIGHT,
                UP: DOWN,
                DOWN: UP,
            }

        class TEXTBOX:
            WIDTH = 400
            HEIGHT = 170
            COORDINATES = (437.5, 215.0)
            UPPER_PART_HEIGHT = 30
            COLOR = COLORS.SOMEWHAT_LIGHT_GRAY
            OUTLINE_COLOR = COLORS.LIGHT_BLUE

        class SUBMIT_BUTTON:
            WIDTH = 100
            PADDING = 200 - (WIDTH / 2), 8
            COORDINATES = tuple(map(sum, zip((437.5, 215.0), PADDING)))

        YES_BUTTON_COORDINATES = tuple(map(sum, zip(SUBMIT_BUTTON.COORDINATES, (-SUBMIT_BUTTON.WIDTH, 0))))
        NO_BUTTON_COORDINATES = tuple(map(sum, zip(SUBMIT_BUTTON.COORDINATES, (SUBMIT_BUTTON.WIDTH, 0))))

        class DEVICE_CREATION:
            BUTTON_SIZE = 80
            BUTTON_GAP = 5

        class HELP:
            WIDTH = 900
            HEIGHT = 500
            COORDINATES = 90, 40
            PADDING = 200 + (WIDTH / 2), 8
            OK_BUTTON_COORDINATES = tuple(map(sum, zip((90, 40), PADDING)))


class IMAGES:
    SIZE = 100

    IMAGE_NOT_FOUND = "misc/image_not_found.png"

    class SCALE_FACTORS:
        SPRITES = 0.5
        INTERNET = 8
        PACKETS = 1.35
        VIEWING_OBJECTS = 5 * SPRITES / 3
        PROCESSES = 1.3

    class PACKETS:
        ETHERNET = "packets/ethernet_packet.png"
        IP = "packets/ip_packet.png"
        UDP = "packets/udp_packet.png"
        STP = "packets/stp_packet.png"
        DNS = "packets/dns_packet.png"

        class ARP:
            REQUEST = "packets/arp_request.png"
            REPLY = "packets/arp_reply.png"
            GRAT = "packets/arp_grat.png"

        class ICMP:
            REPLY = "packets/ping_reply.png"
            REQUEST = "packets/ping_request.png"
            TIME_EXCEEDED = "packets/icmp_time_exceeded.png"
            UNREACHABLE = "packets/icmp_unreachable.png"
            PORT_UNREACHABLE = "packets/icmp_port_unreachable.png"

        class DHCP:
            DISCOVER = "packets/dhcp_discover.png"
            OFFER = "packets/dhcp_offer.png"
            REQUEST = "packets/dhcp_request.png"
            PACK = "packets/dhcp_pack.png"

        class TCP:
            SYN = "packets/tcp_syn.png"
            FIN = "packets/tcp_fin.png"
            RST = "packets/tcp_rst.png"
            PSH = "packets/tcp_psh.png"
            ACK = "packets/tcp_ack.png"
            ACK_RETRANSMISSION = "packets/tcp_ack_retransmission.png"
            PSH_RETRANSMISSION = "packets/tcp_psh_retransmission.png"
            SYN_RETRANSMISSION = "packets/tcp_syn_retransmission.png"
            FIN_RETRANSMISSION = "packets/tcp_fin_retransmission.png"
            PACKET = "packets/tcp_packet.png"

        class FTP:
            REQUEST_PACKET = "packets/ftp_request.png"
            DATA_PACKET = "packets/ftp_data.png"


    class COMPUTERS:
        COMPUTER = "computers/endpoint.png"
        SWITCH = "computers/switch.png"
        ROUTER = "computers/router2.png"
        HUB = "computers/hub.png"
        SERVER = "computers/server.png"
        VPN = "computers/VPN.png"
        PROXY = "computers/proxy.png"
        NAT = "computers/NAT.png"
        ANTENNA = "computers/antenna.png"
        INTERNET = "computers/cloud.png"

    class VIEW:
        CONNECTION = "viewing_items/connection_view.png"
        WIRELESS_CONNECTION = "viewing_items/wireless_connection_view.png"
        INTERFACE = "viewing_items/interface_view.png"

    class PROCESSES:
        PADDING = 20, -15
        GAP = 20

    class TRANSPARENCY:
        HIGH = 35
        MEDIUM = 100
        LOW = 255


class VIEW:
    IMAGE_SIZE = 83

    IMAGE_COORDINATES = ((WINDOWS.MAIN.WIDTH - (WINDOWS.SIDE.WIDTH / 2)) - (IMAGE_SIZE / 2)), \
                        WINDOWS.MAIN.HEIGHT - (IMAGE_SIZE + 5)

    TEXT_PADDING = 40
    PIXELS_PER_SCROLL = 20


class ANIMATIONS:
    EXPLOSION = "explosion.png"

    FRAME_RATE = 0.1
    X_COUNT, Y_COUNT = 5, 3


def get_dominant_tcp_flag(tcp):
    for flag in OPCODES.TCP.FLAGS_DISPLAY_PRIORITY:
        if int(tcp.flags) & int(flag):
            return flag
    return OPCODES.TCP.NO_FLAGS


class PACKET:
    class DIRECTION:
        RIGHT = 'R'
        LEFT = 'L'  # do not change value! Some things depend on it TODO: understand if this is desired
        WIRELESS = 'W'

        INCOMING = 'INCOMING'
        OUTGOING = 'OUTGOING'

    TYPE_TO_OPCODE_FUNCTION = {
        "ARP": lambda arp: arp.opcode,
        "ICMP": (lambda icmp: (icmp.type, icmp.code) if icmp.type == OPCODES.ICMP.TYPES.UNREACHABLE else icmp.type),
        "DHCP": lambda dhcp: DHCPTypes.get(dhcp.parsed_options.message_type, dhcp.parsed_options.message_type),
        "TCP": get_dominant_tcp_flag,
    }

    TYPE_TO_IMAGE = {
        "Ether": IMAGES.PACKETS.ETHERNET,
        "IP": IMAGES.PACKETS.IP,
        "UDP": IMAGES.PACKETS.UDP,
        "STP": IMAGES.PACKETS.STP,
        "ARP": {
            OPCODES.ARP.REQUEST: IMAGES.PACKETS.ARP.REQUEST,
            OPCODES.ARP.REPLY: IMAGES.PACKETS.ARP.REPLY,
            OPCODES.ARP.GRAT: IMAGES.PACKETS.ARP.GRAT,
        },
        "DHCP": {
            OPCODES.DHCP.DISCOVER: IMAGES.PACKETS.DHCP.DISCOVER,
            OPCODES.DHCP.OFFER: IMAGES.PACKETS.DHCP.OFFER,
            OPCODES.DHCP.REQUEST: IMAGES.PACKETS.DHCP.REQUEST,
            OPCODES.DHCP.PACK: IMAGES.PACKETS.DHCP.PACK,
        },
        "ICMP": {
            OPCODES.ICMP.TYPES.REQUEST: IMAGES.PACKETS.ICMP.REQUEST,
            OPCODES.ICMP.TYPES.REPLY: IMAGES.PACKETS.ICMP.REPLY,
            OPCODES.ICMP.TYPES.TIME_EXCEEDED: IMAGES.PACKETS.ICMP.TIME_EXCEEDED,
            (OPCODES.ICMP.TYPES.UNREACHABLE, OPCODES.ICMP.CODES.NETWORK_UNREACHABLE): IMAGES.PACKETS.ICMP.UNREACHABLE,
            (OPCODES.ICMP.TYPES.UNREACHABLE, OPCODES.ICMP.CODES.PORT_UNREACHABLE): IMAGES.PACKETS.ICMP.PORT_UNREACHABLE,
        },
        "TCP": {
            OPCODES.TCP.SYN: IMAGES.PACKETS.TCP.SYN,
            OPCODES.TCP.FIN: IMAGES.PACKETS.TCP.FIN,
            OPCODES.TCP.RST: IMAGES.PACKETS.TCP.RST,
            OPCODES.TCP.PSH: IMAGES.PACKETS.TCP.PSH,
            OPCODES.TCP.ACK: IMAGES.PACKETS.TCP.ACK,
            OPCODES.TCP.ACK.name + OPCODES.TCP.RETRANSMISSION: IMAGES.PACKETS.TCP.ACK_RETRANSMISSION,
            OPCODES.TCP.PSH.name + OPCODES.TCP.RETRANSMISSION: IMAGES.PACKETS.TCP.PSH_RETRANSMISSION,
            OPCODES.TCP.SYN.name + OPCODES.TCP.RETRANSMISSION: IMAGES.PACKETS.TCP.SYN_RETRANSMISSION,
            OPCODES.TCP.FIN.name + OPCODES.TCP.RETRANSMISSION: IMAGES.PACKETS.TCP.FIN_RETRANSMISSION,
            OPCODES.TCP.NO_FLAGS: IMAGES.PACKETS.TCP.PACKET,
        },
        "FTP": {
            OPCODES.FTP.REQUEST_PACKET: IMAGES.PACKETS.FTP.REQUEST_PACKET,
            OPCODES.FTP.DATA_PACKET: IMAGES.PACKETS.FTP.DATA_PACKET,
        },
        "DNS": {
            OPCODES.DNS.REQUEST,
            OPCODES.DNS.REPLY,
        },
    }


class BUTTONS:
    DEFAULT_TEXT = "buTTon"
    DEFAULT_WIDTH = WINDOWS.SIDE.WIDTH - 40
    DEFAULT_HEIGHT = 35
    TEXT_COLOR = COLORS.DARK_RED
    TEXT_PADDING = 8
    COLOR = WINDOWS.SIDE.COLOR
    SHADOW_WIDTH = 3
    OUTLINE_COLOR = COLORS.BLACK
    OUTLINE_WIDTH = 1
    Y_GAP = 5

    class ON_POPUP_WINDOWS:
        ID = -1

    class MAIN_MENU:
        ID = 0


class INTERFACES:
    COMPUTER_DISTANCE = 20
    COMPUTER_DISTANCE_RATIO = 1 / sqrt(2)
    COLOR = COLORS.GRAY
    BLOCKED_COLOR = COLORS.RED
    WIDTH, HEIGHT = 10, 10
    ANY_INTERFACE = None
    NO_INTERFACE = ''

    class TYPE:
        ETHERNET = "Ether"
        WIFI = "Wifi"


class TEXT:
    DEFAULT_Y_PADDING = -10
    COLOR = COLORS.BLACK

    class ALIGN:
        CENTER = 'center'
        LEFT = 'left'
        RIGHT = 'right'

    class FONT:
        DEFAULT = "Arial"
        DEFAULT_SIZE = 10


class CONNECTIONS:
    DEFAULT_SPEED = 150  # pixels / second
    DEFAULT_LENGTH = 100  # pixels
    DEFAULT_PL = 0.5  # the point in the connection where packets are dropped
    MOUSE_TOUCH_SENSITIVITY = 5  # pixels

    COLOR = COLORS.BLACK
    SELECTED_COLOR = COLORS.LIGHT_BLUE
    BLOCKED_COLOR = COLORS.LIGHT_RED
    PL_COLOR = COLORS.GREEN

    class WIRELESS:
        COLOR = COLORS.BLACK
        DEFAULT_SPEED = 400
        DEFAULT_FREQUENCY = 13.37

    class LOOPBACK:
        RADIUS = 15
        SPEED = 200


class MODES:
    NORMAL = 0  # the normal mode of the simulation
    CONNECTING = 1  # The mode when we are connecting two computers (white on the edges)
    VIEW = 2  # the mode when an object is pressed and we see it in the side window view
    PINGING = 3  # the mode where we choose where a ping will be sent

    TO_COLORS = {
        NORMAL: WINDOWS.SIDE.COLOR,
        CONNECTING: COLORS.WHITE,
        VIEW: WINDOWS.SIDE.COLOR,
        PINGING: COLORS.PURPLE,
    }


class CONSOLE:
    WIDTH = WINDOWS.SIDE.WIDTH - 20
    Y = 10
    HEIGHT = 3 * (WIDTH / 4)

    FONT_SIZE = 8
    LINE_HEIGHT = 14
    CHAR_WIDTH = 8

    COLOR = COLORS.BLACK
    TEXT_COLOR = COLORS.WHITE
    FONT = 'Courier New'

    class SHELL:
        WIDTH = 700
        HEIGHT = 500
        START_LOCATION = 170, 40

        PREFIX = '> '
        FONT_SIZE = TEXT.FONT.DEFAULT_SIZE
        FONT = 'Courier New'
        REDIRECTION = '>'
        CARET = '|'
        PIPING_CHAR = '|'
        COMMENT_SIGN = '#'
        ALIAS_SET_SIGN = '='
        END_COMMAND = ';'


class SHAPES:
    class CIRCLE:
        SEGMENT_COUNT = 50

        class FULL:
            DENSITY = 1 / 0.5  # circles per pixel

        class RESIZE_DOT:
            RADIUS = 5
            MINIMAL_RESIZE_SIZE = 15
            COLOR_WHEN_SELECTED = COLORS.LIGHT_GREEN

    class SINE_WAVE:
        MINIMAL_POINT_DISTANCE = 5
        INITIAL_ANGLE = 0
        DEFAULT_AMPLITUDE = 10
        DEFAULT_FREQUENCY = 10

    class RECT:
        DEFAULT_OUTLINE_WIDTH = 5

    class PAUSE_RECT:
        WIDTH, HEIGHT = 10, 60
        COORDINATES = 35, ((WINDOWS.MAIN.HEIGHT - HEIGHT) - 5)


class SELECTION_SQUARE:
    COLOR = COLORS.LIGHT_BLUE


class SELECTED_OBJECT:
    PADDING = 8
    COLOR = COLORS.BLUE
    STEP_SIZE = 30
    SMALL_STEP_SIZE = 5
    BIG_STEP_SIZE = 80


class FILESYSTEM:
    CWD = '.'
    PARENT_DIRECTORY = '..'
    SEPARATOR = '/'
    ROOT = '/'
    HOME_DIR = '/home'
    PIPING_FILE = ".%%%~P~i~p~i~n~g~/~F~i~l~e~%%%."

    class TYPE:
        NTFS = 'ntfs'
        EXT3 = 'ext3'
        EXT4 = 'ext4'
        FAT = 'fat'
        TMPFS = 'tmp'


class COMPUTER:
    class OUTPUT_METHOD:
        CONSOLE = 'console'
        SHELL = 'shell'
        STDOUT = 'stdout'
        NONE = None

    class PROCESSES:
        INIT_PID = 1

        class SIGNALS:
            SIGHUP = 1  # Hangup(POSIX)
            SIGINT = 2  # Terminal interrupt(ANSI)
            SIGQUIT = 3  # Terminal quit(POSIX)
            SIGILL = 4  # Illegal instruction(ANSI)
            SIGTRAP = 5  # Trace trap(POSIX)
            SIGIOT = 6  # IOT Trap(4.2 BSD)
            SIGBUS = 7  # BUS error(4.2 BSD)
            SIGFPE = 8  # Floating point exception(ANSI)
            SIGKILL = 9  # Kill(can 't be caught or ignored) (POSIX)
            SIGUSR1 = 10  # User defined signal 1(POSIX)
            SIGSEGV = 11  # Invalid memory segment access(ANSI)
            SIGUSR2 = 12  # User defined signal 2(POSIX)
            SIGPIPE = 13  # Write on a pipe with no reader, Broken pipe (POSIX)
            SIGALRM = 14  # Alarm clock (POSIX)
            SIGTERM = 15  # Termination (ANSI)
            SIGSTKFLT = 16  # Stack fault
            SIGCHLD = 17  # Child process has stopped or exited, changed (POSIX)
            SIGCONTv = 18  # Continue executing, if stopped (POSIX)
            SIGSTOP = 19  # Stop executing(can't be caught or ignored) (POSIX)
            SIGTSTP = 20  # Terminal stop signal (POSIX)
            SIGTTIN = 21  # Background process trying to read, from TTY (POSIX)
            SIGTTOU = 22  # Background process trying to write, to TTY (POSIX)
            SIGURG = 23  # Urgent condition on socket (4.2 BSD)
            SIGXCPU = 24  # CPU limit exceeded (4.2 BSD)
            SIGXFSZ = 25  # File size limit exceeded (4.2 BSD)
            SIGVTALRM = 26  # Virtual alarm clock (4.2 BSD)
            SIGPROF = 27  # Profiling alarm clock (4.2 BSD)
            SIGWINCH = 28  # Window size change (4.3 BSD, Sun)
            SIGIO = 29  # I / O now possible (4.2 BSD)
            SIGPWR = 30  # Power failure restart (System V)

            ALL = range(1, 32)

            KILLING_SIGNALS = {
                SIGTERM,
                SIGINT,
                SIGKILL,
                SIGQUIT,
                SIGSTOP,
                SIGTSTP,
            }

            UNIGNORABLE_KILLING_SIGNALS = {
                SIGKILL,
                SIGSTOP,
            }

        class MODES:
            USERMODE = 'usermode'
            KERNELMODE = 'kernelmode'

            ALL_MODES = [USERMODE, KERNELMODE]

    class ARP_CACHE:
        DYNAMIC = "dynamic"
        STATIC = "static"
        ITEM_LIFETIME = 300  # seconds

    class SWITCH_TABLE:
        ITEM_LIFETIME = 300  # seconds

    class SOCKETS:
        class TYPES:
            SOCK_STREAM = 1
            SOCK_DGRAM = 2
            SOCK_RAW = 3

        L4_PROTOCOLS = {
            TYPES.SOCK_STREAM: "TCP",
            TYPES.SOCK_DGRAM: "UDP",
        }

        class ADDRESS_FAMILIES:
            AF_INET = 2
            AF_INET6 = 23

        class STATES:
            UNBOUND = "UNBOUND"
            BOUND = "BOUND"
            LISTENING = "LISTENING"
            ESTABLISHED = "ESTABLISHED"
            CLOSED = "CLOSED"

        class REPR:
            LOCAL_ADDRESS_SPACE_COUNT = 22
            REMOTE_ADDRESS_SPACE_COUNT = 22
            STATE_SPACE_COUNT = 15
            PROTO_SPACE_COUNT = 6
