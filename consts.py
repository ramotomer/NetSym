# this cannot import from anything!!!

from exceptions import TCPDoneReceiving


def debugp(string):
    """
    A print i use for debugging so i know where to delete it afterwards.
    :param string:
    :return:
    """
    print(f"DEBUG: {string}")


DEFAULT_CONNECTION_SPEED = 200  # pixels / second
DEFAULT_CONNECTION_LENGTH = 100  # pixels
LOOPBACK_CONNECTION_RADIUS = 15
LOOPBACK_CONNECTION_SPEED = 200

SENDING_GRAT_ARPS = False

BROADCAST_MAC = 'ff:ff:ff:ff:ff:ff'
STP_MULTICAST_MAC = "01:80:C2:00:00:00"
DEFAULT_COMPUTER_IP = "192.168.1.2/24"
ON_LINK = "On-link"

ROOT_PORT = "ROOT"
DESIGNATED_PORT = "DESIGNATED"
BLOCKED_PORT = "BLOCKED"
NO_STATE = "no state!"

OS_WINDOWS = 'Windows'
OS_LINUX = 'Linux'
OS_SOLARIS = 'Solaris'
TTLS = {
    OS_LINUX: 64,
    OS_WINDOWS: 128,
    OS_SOLARIS: 255,
}
MAX_TTL = 255

ARP_CACHE_FORGET_TIME = 300  # seconds
SWITCH_TABLE_ITEM_LIFETIME = 300  # seconds

STP_NORMAL_SENDING_INTERVAL = 1.7  # seconds
STP_STABLE_SENDING_INTERVAL = 6  # seconds
TREE_STABLIZING_MAX_TIME = 30  # seconds
BLOCKED_INTERFACE_UPDATE_INTERVAL = 10  # seconds
ROOT_MAX_DISAPPEARING_TIME = 40
MAX_CONNECTION_DISAPPEARED_TIME = 40
DEFAULT_SWITCH_PRIORITY = 32768

ARP_RESEND_TIME = 6  # seconds
ARP_RESEND_COUNT = 3  # seconds

ARP_REPLY = "ARP reply"
ARP_REQUEST = "ARP request"
ARP_GRAT = "gratuitous ARP"
ICMP_REQUEST = "ping request"
ICMP_REPLY = "ping reply"
ICMP_TIME_EXCEEDED = "ICMP Time Exceeded!"
ICMP_UNREACHABLE = "ICMP Unreachable"
ICMP_PORT_UNREACHABLE = "ICMP Port Unreachable"
DHCP_DISCOVER = "DHCP Discover"
DHCP_OFFER = "DHCP Offer"
DHCP_REQUEST = "DHCP Request"
DHCP_PACK = "DHCP Pack"

FTP_REQUEST_PACKET = "FTP Request"
FTP_DATA_PACKET = "FTP Data"

TCP_ACK = "ACK"
TCP_SYN = "SYN"
TCP_FIN = "FIN"
TCP_RST = "RST"
TCP_PSH = "PSH"
NO_TCP_FLAGS = None

TCP_FLAGS = {
    TCP_ACK,
    TCP_FIN,
    TCP_PSH,
    TCP_SYN,
    TCP_RST,
}

TCP_FLAGS_DISPLAY_PRIORITY = [TCP_SYN, TCP_FIN, TCP_RST, TCP_PSH, TCP_ACK]
TCP_RETRANSMISSION = " retransmission"

TCP_MAX_SEQUENCE_NUMBER = 2**32 - 1
TCP_RESEND_TIME = 15  # seconds
USERMODE_USABLE_PORT_RANGE = (2 ** 15 - 2 ** 14), 2 ** 16 - 1
TCP_MAX_WINDOW_SIZE = 20  # packets
TCP_SENDING_INTERVAL = 0.1  # seconds
TCP_DONE_RECEIVING = TCPDoneReceiving
TCP_MAX_UNUSED_CONNECTION_TIME = 15  # seconds
TCP_MAX_MSS = 100

TCP_MSS_OPTION = "MSS"  # maximum segment size
TCP_WINDOW_SCALE_OPTION = "Window Scale"
TCP_SACK_OPTION = "SACK"
TCP_TIMESTAMPS_OPTION = "Timestamps"

DAYTIME_PORT = 13
FTP_PORT = 21
SSH_PORT = 22
DHCP_SERVER_PORT = 67
DHCP_CLIENT_PORT = 68
HTTP_PORT = 80
HTTPS_PORT = 443

PACKET_GOING_RIGHT = 'R'
PACKET_GOING_LEFT = 'L'
CONNECTION_PL_PERCENT = 0.5  # the point in the connection where packets are dropped
MOUSE_IN_CONNECTION_LENGTH = 5  # pixels

# key modifiers:
CAPS_MODIFIER = 8
ALT_MODIFIER = 4
CTRL_MODIFIER = 2
SHIFT_MODIFIER = 1
NO_MODIFIER = 0
# you can `|` them together to get the different combinations.

MAC_ADDRESS_SEPARATOR = ':'
IP_ADDRESS_SEPARATOR = '.'
IP_SUBNET_SEPARATOR = '/'
DEFAULT_SUBNET_MASK = '24'
IP_ADDRESS_BIT_LENGTH = 32

INVALID_MAC_ADDRESS = "The MAC address is not valid!"
INVALID_IP_ADDRESS = "The IP address is not valid!"
NETWORK_UNREACHABLE_MSG = "Cannot send packet, Network is unreachable!"

INSERT_PL_MSG = "insert your desired pl (0 <= pl <= 1)!!!"
INSERT_SPEED_MSG = "insert your desired connection speed:"
INSERT_IP_MSG = "Enter your desired IP for this interface:"
INSERT_GATEWAY_MSG = "Enter your desired IP for the gateway:"
INSERT_INTERFACE_INFO_MSG = "Insert the name of the interface:"
INSERT_IP_FOR_PROCESS = "Insert an IP to start your process to:"
INSERT_PORT_NUMBER = "Insert a port number to open/close:"
INSERT_COMPUTER_NAME_MSG = "Insert a new name for the computer:"

FILES = "../res/files/{}"
IMAGES = "../res/sprites/{}"

INTERFACE_NAMES = [line.strip() for line in open(FILES.format("interface_names.txt")).readlines()]
COMPUTER_NAMES = [line.strip() for line in open(FILES.format("computer_names.txt")).readlines()]
ANY_INTERFACE = None
TRANSFER_FILE = "transfer_me.txt"
WINDOW_INPUT_LIST_FILE = FILES.format("window_inputs.txt")

LOGO_ANIMATION_IMAGE = "misc/logo.png"

ETHERNET_IMAGE = "packets/ethernet_packet.png"
ARP_REQUEST_IMAGE = "packets/arp_request.png"
ARP_REPLY_IMAGE = "packets/arp_reply.png"
ARP_GRAT_IMAGE = "packets/arp_grat.png"
IP_IMAGE = "packets/ip_packet.png"
ICMP_REPLY_IMAGE = "packets/ping_reply.png"
ICMP_REQUEST_IMAGE = "packets/ping_request.png"
ICMP_TIME_EXCEEDED_IMAGE = "packets/icmp_time_exceeded.png"
ICMP_UNREACHABLE_IMAGE = "packets/icmp_unreachable.png"
ICMP_PORT_UNREACHABLE_IMAGE = "packets/icmp_port_unreachable.png"
DHCP_DISCOVER_IMAGE = "packets/dhcp_discover.png"
DHCP_OFFER_IMAGE = "packets/dhcp_offer.png"
DHCP_REQUEST_IMAGE = "packets/dhcp_request.png"
DHCP_PACK_IMAGE = "packets/dhcp_pack.png"
UDP_IMAGE = "packets/udp_packet.png"
STP_IMAGE = "packets/stp_packet.png"
TCP_SYN_IMAGE = "packets/tcp_syn.png"
TCP_FIN_IMAGE = "packets/tcp_fin.png"
TCP_RST_IMAGE = "packets/tcp_rst.png"
TCP_PSH_IMAGE = "packets/tcp_psh.png"
TCP_ACK_IMAGE = "packets/tcp_ack.png"
TCP_ACK_RETRANSMISSION_IMAGE = "packets/tcp_ack_retransmission.png"
TCP_PSH_RETRANSMISSION_IMAGE = "packets/tcp_psh_retransmission.png"
TCP_SYN_RETRANSMISSION_IMAGE = "packets/tcp_syn_retransmission.png"
TCP_FIN_RETRANSMISSION_IMAGE = "packets/tcp_fin_retransmission.png"
TCP_PACKET_IMAGE = "packets/tcp_packet.png"
FTP_REQUEST_PACKET_IMAGE = "packets/ftp_request.png"
FTP_DATA_PACKET_IMAGE = "packets/ftp_data.png"

COMPUTER_IMAGE = "computers/endpoint.png"
SWITCH_IMAGE = "computers/switch.png"
ROUTER_IMAGE = "computers/router2.png"
HUB_IMAGE = "computers/hub.png"
SERVER_IMAGE = "computers/server.png"
VPN_IMAGE = "computers/VPN.png"
PROXY_IMAGE = "computers/proxy.png"
NAT_IMAGE = "computers/NAT.png"
ANTENNA_IMAGE = "computers/antenna.png"

CONNECTION_VIEW_IMAGE = "viewing_items/connection_view.png"
WIRELESS_CONNECTION_VIEW_IMAGE = "viewing_items/wireless_connection_view.png"
INTERFACE_VIEW_IMAGE = "viewing_items/interface_view.png"
EXPLOSION_ANIMATION = "misc/explosion.png"
ANIMATION_FRAME_RATE = 0.1
ANIMATION_X_COUNT, ANIMATION_Y_COUNT = 5, 3

PORT_NUMBER_TO_IMAGE = {
    DAYTIME_PORT: "processes/daytime_process.png",
    FTP_PORT: "processes/ftp_process.png",
    SSH_PORT: "processes/ssh_process.png",
    HTTP_PORT: "processes/http_process.png",
    HTTPS_PORT: "processes/https_process.png",
}
PROCESS_IMAGE_PADDING = 20, -15
PROCESS_IMAGE_GAP = 20

PACKET_TYPE_TO_IMAGE = {
            "Ethernet": ETHERNET_IMAGE,
            "IP": IP_IMAGE,
            "UDP": UDP_IMAGE,
            "STP": STP_IMAGE,
            "ARP": {
                ARP_REQUEST: ARP_REQUEST_IMAGE,
                ARP_REPLY: ARP_REPLY_IMAGE,
                ARP_GRAT: ARP_GRAT_IMAGE,
            },
            "DHCP": {
                DHCP_DISCOVER: DHCP_DISCOVER_IMAGE,
                DHCP_OFFER: DHCP_OFFER_IMAGE,
                DHCP_REQUEST: DHCP_REQUEST_IMAGE,
                DHCP_PACK: DHCP_PACK_IMAGE,
            },
            "ICMP": {
                ICMP_REQUEST: ICMP_REQUEST_IMAGE,
                ICMP_REPLY: ICMP_REPLY_IMAGE,
                ICMP_TIME_EXCEEDED: ICMP_TIME_EXCEEDED_IMAGE,
                ICMP_UNREACHABLE: ICMP_UNREACHABLE_IMAGE,
                ICMP_PORT_UNREACHABLE: ICMP_PORT_UNREACHABLE_IMAGE,
            },
            "TCP": {
                TCP_SYN: TCP_SYN_IMAGE,
                TCP_FIN: TCP_FIN_IMAGE,
                TCP_RST: TCP_RST_IMAGE,
                TCP_PSH: TCP_PSH_IMAGE,
                TCP_ACK: TCP_ACK_IMAGE,
                TCP_ACK + TCP_RETRANSMISSION: TCP_ACK_RETRANSMISSION_IMAGE,
                TCP_PSH + TCP_RETRANSMISSION: TCP_PSH_RETRANSMISSION_IMAGE,
                TCP_SYN + TCP_RETRANSMISSION: TCP_SYN_RETRANSMISSION_IMAGE,
                TCP_FIN + TCP_RETRANSMISSION: TCP_FIN_RETRANSMISSION_IMAGE,
                NO_TCP_FLAGS: TCP_PACKET_IMAGE,
            },
            "FTP": {
                FTP_REQUEST_PACKET: FTP_REQUEST_PACKET_IMAGE,
                FTP_DATA_PACKET: FTP_DATA_PACKET_IMAGE,
            }
        }

OPAQUE = 35
A_LITTLE_OPAQUE = 100
NOT_OPAQUE = 255

WINDOW_NAME = "NetSym"
WINDOW_WIDTH = 1275
WINDOW_HEIGHT = 400
INITIAL_WINDOW_LOCATION = 4, 50

IMAGES_SIZE = 16
SPRITE_SCALE_FACTOR = 3
PACKET_SCALE_FACTOR = 1.2
VIEWING_OBJECT_SCALE_FACTOR = 5
PROCESS_IMAGE_SCALE_FACTOR = 1.3
INTERFACE_DISTANCE_FROM_COMPUTER = IMAGES_SIZE * SPRITE_SCALE_FACTOR - 20

DEFAULT_TEXT_Y_PADDING = -30
BUTTON_TEXT_PADDING = 8
SELECTED_OBJECT_PADDING = 5
DEFAULT_FONT = "Arial"
DEFAULT_FONT_SIZE = 10

FRAME_RATE = 1 / 60.0

DARK_GRAY = (20, 20, 20)
GRAY = (10, 10, 10)
LIGHT_COLOR_DIFF = 10
LIGHT_GRAY = (150, 150, 150)
VERY_LIGHT_GRAY = (180, 180, 180)
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

SIDE_WINDOW_WIDTH = 230

DEFAULT_BUTTON_TEXT = "BuTTon"
DEFAULT_BUTTON_WIDTH = SIDE_WINDOW_WIDTH - 40
DEFAULT_BUTTON_HEIGHT = 35


def DEFAULT_BUTTON_LOCATION(button_index):
    return (WINDOW_WIDTH - SIDE_WINDOW_WIDTH + 20), (WINDOW_HEIGHT - 90 - (button_index * DEFAULT_BUTTON_HEIGHT))


WINDOW_BUTTONS_ID = -1
MAIN_BUTTONS_ID = 0

SIMULATION_MODE = 0  # the normal mode of the simulation
CONNECTING_MODE = 1  # The mode when we are connecting two computers (white on the edges)
VIEW_MODE = 2  # the mode when an object is pressed and we see it in the side window view
SNIFFING_MODE = 3  # the mode when we choose what computer will be sniffing
PINGING_MODE = 4  # the mode where we choose where a ping will be sent
DELETING_MODE = 5  # the mode where we choose what computer will be deleted

MODES_TO_COLORS = {
    SIMULATION_MODE: GRAY,
    CONNECTING_MODE: WHITE,
    VIEW_MODE: GRAY,
    SNIFFING_MODE: BLUE,
    PINGING_MODE: PURPLE,
    DELETING_MODE: BROWN,
}

CONNECTION_COLOR = WHITE
WIRELESS_CONNECTION_COLOR = LIGHT_GRAY
BLOCKED_CONNECTION_COLOR = RED
PL_CONNECTION_COLOR = DARK_GREEN
SELECTED_CONNECTION_COLOR = LIGHT_BLUE

REGULAR_INTERFACE_COLOR = WHITE
BLOCKED_INTERFACE_COLOR = RED

INTERFACE_WIDTH, INTERFACE_HEIGHT = 10, 10

VIEWING_IMAGE_COORDINATES = ((WINDOW_WIDTH - (SIDE_WINDOW_WIDTH / 2)) - (
            IMAGES_SIZE * VIEWING_OBJECT_SCALE_FACTOR / 2)), WINDOW_HEIGHT - (
                                        (IMAGES_SIZE * VIEWING_OBJECT_SCALE_FACTOR) + 15)
VIEWING_TEXT_COORDINATES = (WINDOW_WIDTH - (SIDE_WINDOW_WIDTH / 2)), VIEWING_IMAGE_COORDINATES[1] + 40

PIXELS_PER_SCROLL = 20

CONSOLE_X, CONSOLE_Y = VIEWING_TEXT_COORDINATES[0] - 105, 10
CONSOLE_WIDTH = SIDE_WINDOW_WIDTH - 20
CONSOLE_HEIGHT = 3 * (CONSOLE_WIDTH / 4)
CONSOLE_FONT_SIZE = 8
CONSOLE_LINE_HEIGHT = 14
CONSOLE_CHAR_WIDTH = 8

PAUSE_RECT_WIDTH = 10
PAUSE_RECT_HEIGHT = 60
PAUSE_RECT_COORDINATES = 20, ((WINDOW_HEIGHT - PAUSE_RECT_HEIGHT) - 10)

CIRCLE_SEGMENT_COUNT = 50
SINE_WAVE_MINIMAL_POINT_DISTANCE = 5
INITIAL_SINE_WAVE_ANGLE = 0
DEFAULT_SINE_WAVE_AMPLITUDE = 10
DEFAULT_SINE_WAVE_FREQUENCY = 10

DEFAULT_OUTLINE_WIDTH = 5

TEXTBOX_WIDTH = 400
TEXTBOX_HEIGHT = 170
TEXTBOX_COORDINATES = (WINDOW_WIDTH / 2) - (TEXTBOX_WIDTH / 2), (WINDOW_HEIGHT / 2) - (TEXTBOX_HEIGHT / 2)
TEXTBOX_UPPER_PART_HEIGHT = 30
TEXTBOX_COLOR = GRAY
TEXTBOX_OUTLINE_COLOR = LIGHT_BLUE
TEXTBOX_OUTLINE_WIDTH = DEFAULT_OUTLINE_WIDTH
POPUP_WINDOW_INFO_TEXT_PADDING = (TEXTBOX_WIDTH / 2), 6 * (TEXTBOX_HEIGHT / 7)
POPUP_WINDOW_TITLE_TEXT_PADDING = 35, TEXTBOX_HEIGHT + 22

SUBMIT_BUTTON_WIDTH = 100
SUBMIT_BUTTON_PADDING = (TEXTBOX_WIDTH / 2) - (SUBMIT_BUTTON_WIDTH / 2), 8
SUBMIT_BUTTON_COORDINATES = tuple(map(sum, zip(TEXTBOX_COORDINATES, SUBMIT_BUTTON_PADDING)))

NEW_WINDOW_LOCATION_PADDING = 10, -10

DEVICE_CREATION_BUTTON_SIZE = 80
DEVICE_CREATION_BUTTON_GAP = 5
