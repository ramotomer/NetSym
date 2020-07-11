# this cannot import from anything!!! (almost)
import os

from exceptions import TCPDoneReceiving


def debugp(*strings):
    """
    A print i use for debugging so i know where to delete it afterwards.
    :param string:
    :return:
    """
    print(f"DEBUG:", *strings)


SENDING_GRAT_ARPS = False


class SWITCH_TABLE:
    ITEM_LIFETIME = 300  # seconds


class ARP_CACHE:
    ITEM_LIFETIME = 300  # seconds


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


class OPCODES:
    class ARP:
        REPLY = "ARP reply"
        REQUEST = "ARP request"
        GRAT = "gratuitous ARP"

    class ICMP:
        REQUEST = "ping request"
        REPLY = "ping reply"
        TIME_EXCEEDED = "ICMP Time Exceeded!"
        UNREACHABLE = "ICMP Unreachable"
        PORT_UNREACHABLE = "ICMP Port Unreachable"

    class DHCP:
        DISCOVER = "DHCP Discover"
        OFFER = "DHCP Offer"
        REQUEST = "DHCP Request"
        PACK = "DHCP Pack"

    class FTP:
        REQUEST_PACKET = "FTP Request"
        DATA_PACKET = "FTP Data"

    class TCP:
        ACK = "ACK"
        SYN = "SYN"
        FIN = "FIN"
        RST = "RST"
        PSH = "PSH"
        RETRANSMISSION = " retransmission"
        NO_FLAGS = None
        FLAGS = {ACK, FIN, PSH, SYN, RST}
        FLAGS_DISPLAY_PRIORITY = [SYN, FIN, RST, PSH, ACK]


class PROTOCOLS:
    class ARP:
        RESEND_TIME = 6  # seconds
        RESEND_COUNT = 3  # seconds

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


class PORTS:
    DAYTIME = 13
    FTP = 21
    SSH = 22
    DHCP_SERVER = 67
    DHCP_CLIENT = 68
    HTTP = 80
    HTTPS = 443

    USERMODE_USABLE_RANGE = (2 ** 15 - 2 ** 14), 2 ** 16 - 1

    TO_IMAGES = {
        DAYTIME: "processes/daytime_process.png",
        FTP: "processes/ftp_process.png",
        SSH: "processes/ssh_process.png",
        HTTP: "processes/http_process.png",
        HTTPS: "processes/https_process.png",
    }


class KEYBOARD:
    PRINTABLE_RANGE = range(0x20, 0x80)

    class MODIFIERS:
        """
        key modifiers, you can `|` them together to get the different combinations.
        """
        NONE = 0
        SHIFT = 1
        CTRL = 2
        ALT = 4
        CAPS = 8


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


class DIRECTORIES:
    IMAGES = "../res/sprites"
    FILES = "../res/files"
    SAVES = "../res/files/saves"


INTERFACE_NAMES = [line.strip() for line in open(os.path.join(DIRECTORIES.FILES, "interface_names.txt")).readlines()]
COMPUTER_NAMES = [line.strip() for line in open(os.path.join(DIRECTORIES.FILES, "computer_names.txt")).readlines()]
TRANSFER_FILE = "transfer_me.txt"
WINDOW_INPUT_LIST_FILE = os.path.join(DIRECTORIES.FILES, "window_inputs.txt")


class COLORS:
    DARK_GRAY = (20, 20, 20)
    GRAY = (10, 10, 10)
    LIGHT_GRAY = (150, 150, 150)
    VERY_LIGHT_GRAY = (200, 200, 200)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)
    LIGHT_BLUE = (100, 100, 255)
    VERY_LIGHT_BLUE = (180, 180, 255)
    PURPLE = (171, 71, 188)
    BROWN = (62, 39, 35)
    RED = (150, 0, 0)
    YELLOW = (200, 200, 0)
    GREEN = (0, 255, 0)
    DARK_GREEN = (0, 100, 0)
    PINK = (255, 170, 170)
    ORANGE = (255, 215, 0)
    TURQUOISE = (10, 255, 255)
    DARK_RED = (100, 0, 0)

    COLOR_DIFF = 20
    LARGE_COLOR_DIFF = 70


class WINDOWS:
    class MAIN:
        NAME = "NetSym"
        WIDTH = 1275
        HEIGHT = 600
        INITIAL_LOCATION = 4, 50
        FRAME_RATE = 1 / 60.0
        BACKGROUND = COLORS.VERY_LIGHT_GRAY

    class SIDE:
        WIDTH = 230
        COLOR = COLORS.LIGHT_GRAY

    class POPUP:
        STACKING_PADDING = 10, -10

        class TEXTBOX:
            WIDTH = 400
            HEIGHT = 170
            COORDINATES = (437.5, 215.0)
            UPPER_PART_HEIGHT = 30
            COLOR = COLORS.LIGHT_GRAY
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

    class SCALE_FACTORS:
        SPRITES = 0.5
        INTERNET = 8
        PACKETS = 1.2
        VIEWING_OBJECTS = 5 * SPRITES / 3
        PROCESSES = 1.3

    class PACKETS:
        ETHERNET = "packets/ethernet_packet.png"
        IP = "packets/ip_packet.png"
        UDP = "packets/udp_packet.png"
        STP = "packets/stp_packet.png"

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
    IMAGE_COORDINATES = \
        ((WINDOWS.MAIN.WIDTH - (WINDOWS.SIDE.WIDTH / 2)) - (IMAGES.SIZE * IMAGES.SCALE_FACTORS.VIEWING_OBJECTS / 2)), \
        WINDOWS.MAIN.HEIGHT - ((IMAGES.SIZE * IMAGES.SCALE_FACTORS.VIEWING_OBJECTS) + 15)

    TEXT_PADDING = 40
    PIXELS_PER_SCROLL = 20


class ANIMATIONS:
    EXPLOSION = "misc/explosion.png"

    FRAME_RATE = 0.1
    X_COUNT, Y_COUNT = 5, 3


class PACKET:
    class DIRECTION:
        RIGHT = 'R'
        LEFT = 'L'

    TYPE_TO_IMAGE = {
        "Ethernet": IMAGES.PACKETS.ETHERNET,
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
            OPCODES.ICMP.REQUEST: IMAGES.PACKETS.ICMP.REQUEST,
            OPCODES.ICMP.REPLY: IMAGES.PACKETS.ICMP.REPLY,
            OPCODES.ICMP.TIME_EXCEEDED: IMAGES.PACKETS.ICMP.TIME_EXCEEDED,
            OPCODES.ICMP.UNREACHABLE: IMAGES.PACKETS.ICMP.UNREACHABLE,
            OPCODES.ICMP.PORT_UNREACHABLE: IMAGES.PACKETS.ICMP.PORT_UNREACHABLE,
        },
        "TCP": {
            OPCODES.TCP.SYN: IMAGES.PACKETS.TCP.SYN,
            OPCODES.TCP.FIN: IMAGES.PACKETS.TCP.FIN,
            OPCODES.TCP.RST: IMAGES.PACKETS.TCP.RST,
            OPCODES.TCP.PSH: IMAGES.PACKETS.TCP.PSH,
            OPCODES.TCP.ACK: IMAGES.PACKETS.TCP.ACK,
            OPCODES.TCP.ACK + OPCODES.TCP.RETRANSMISSION: IMAGES.PACKETS.TCP.ACK_RETRANSMISSION,
            OPCODES.TCP.PSH + OPCODES.TCP.RETRANSMISSION: IMAGES.PACKETS.TCP.PSH_RETRANSMISSION,
            OPCODES.TCP.SYN + OPCODES.TCP.RETRANSMISSION: IMAGES.PACKETS.TCP.SYN_RETRANSMISSION,
            OPCODES.TCP.FIN + OPCODES.TCP.RETRANSMISSION: IMAGES.PACKETS.TCP.FIN_RETRANSMISSION,
            OPCODES.TCP.NO_FLAGS: IMAGES.PACKETS.TCP.PACKET,
        },
        "FTP": {
            OPCODES.FTP.REQUEST_PACKET: IMAGES.PACKETS.FTP.REQUEST_PACKET,
            OPCODES.FTP.DATA_PACKET: IMAGES.PACKETS.FTP.DATA_PACKET,
        }
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
    COLOR = COLORS.GRAY
    BLOCKED_COLOR = COLORS.RED
    WIDTH, HEIGHT = 10, 10
    ANY_INTERFACE = None


class TEXT:
    DEFAULT_Y_PADDING = -30
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
    BLOCKED_COLOR = COLORS.RED
    PL_COLOR = COLORS.GREEN

    class WIRELESS:
        COLOR = COLORS.BLACK

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

    class SHELL:
        WIDTH = 400
        HEIGHT = 400
        PREFIX = '> '
        START_LOCATION = 270, 140
        FONT_SIZE = TEXT.FONT.DEFAULT_SIZE


class SHAPES:
    class CIRCLE:
        SEGMENT_COUNT = 50

    class SINE_WAVE:
        MINIMAL_POINT_DISTANCE = 5
        INITIAL_ANGLE = 0
        DEFAULT_AMPLITUDE = 10
        DEFAULT_FREQUENCY = 10

    class RECT:
        DEFAULT_OUTLINE_WIDTH = 5

    class PAUSE_RECT:
        WIDTH, HEIGHT = 10, 60
        COORDINATES = 20, ((WINDOWS.MAIN.HEIGHT - HEIGHT) - 10)


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
