# this cannot import from anything!!!
import os


def debugp(string):
    """
    A print i use for debugging so i know where to delete it afterwards.
    :param string:
    :return:
    """
    print(f"DEBUG: {string}")


WINDOW_NAME = "NetSym"
WINDOW_WIDTH = 1275
WINDOW_HEIGHT = 600
INITIAL_WINDOW_LOCATION = 4, 50

SPRITE_SCALE_FACTOR = 3
PACKET_SCALE_FACTOR = 1.5
VIEWING_OBJECT_SCALE_FACTOR = 5

DEFAULT_TEXT_Y_PADDING = -30
BUTTON_TEXT_PADDING = 8
SELECTED_OBJECT_PADDING = 5
DEFAULT_FONT = "Arial"
DEFAULT_FONT_SIZE = 10

FRAME_RATE = 1 / 60.0

DEFAULT_CONNECTION_SPEED = 300  # pixels / second
DEFAULT_CONNECTION_LENGTH = 100  # pixels
LOOPBACK_CONNECTION_RADIUS = 15
LOOPBACK_CONNECTION_SPEED = 200

SENDING_GRAT_ARPS = False

MAC_ADDRESS_SEPARATOR = ':'
IP_ADDRESS_SEPARATOR = '.'
IP_SUBNET_SEPARATOR = '/'
DEFAULT_SUBNET_MASK = '24'
IP_ADDRESS_BIT_LENGTH = 32

INVALID_MAC_ADDRESS = "The MAC address is not valid!"
INVALID_IP_ADDRESS = "The IP address is not valid!"
NETWORK_UNREACHABLE_MSG = "Cannot send packet, Network is unreachable!"

# key modifiers:
CAPS_MODIFIER = 8
ALT_MODIFIER = 4
CTRL_MODIFIER = 2
SHIFT_MODIFIER = 1
NO_MODIFIER = 0
# you can `|` them together to get the different combinations.


FILES = "res/files/{}"
IMAGES = "res/sprites/{}"
if os.name == 'nt':
    FILES = "..\\res\\files\\{}"
    IMAGES = "..\\res\\sprites\\{}"
    if os.environ['COMPUTERNAME'].lower() == "bottomtext":          # so it will work in my ipython
        FILES = "C:/users/user/pycharmprojects/netsym/res/files/{}"
        IMAGES = "C:/users/user/pycharmprojects/netsym/res/sprites/{}"

ETHERNET_IMAGE = "ethernet_packet.png"
ARP_REQUEST_IMAGE = "arp_request.png"
ARP_REPLY_IMAGE = "arp_reply.png"
ARP_GRAT_IMAGE = "arp_grat.png"
IP_IMAGE = "ip_packet.png"
ICMP_REPLY_IMAGE = "ping_reply.png"
ICMP_REQUEST_IMAGE = "ping_request.png"
ICMP_TIME_EXCEEDED_IMAGE = "time_exceeded.png"
ICMP_UNREACHABLE_IMAGE = "icmp_unreachable.png"
DHCP_DISCOVER_IMAGE = "dhcp_discover.png"
DHCP_OFFER_IMAGE = "dhcp_offer.png"
DHCP_REQUEST_IMAGE = "dhcp_request.png"
DHCP_PACK_IMAGE = "dhcp_pack.png"
UDP_IMAGE = "udp_packet.png"
STP_IMAGE = "stp_packet.png"

COMPUTER_IMAGE = "endpoint.png"
SWITCH_IMAGE = "switch.png"
ROUTER_IMAGE = "router.png"
HUB_IMAGE = "hub.png"

ARP_REPLY = "ARP reply"
ARP_REQUEST = "ARP request"
ARP_GRAT = "gratuitous ARP"
ICMP_REQUEST = "ping request"
ICMP_REPLY = "ping reply"
ICMP_TIME_EXCEEDED = "ICMP Time Exceeded!"
ICMP_UNREACHABLE = "ICMP Unreachable"
DHCP_DISCOVER = "DHCP Discover"
DHCP_OFFER = "DHCP Offer"
DHCP_REQUEST = "DHCP Request"
DHCP_PACK = "DHCP Pack"

OPAQUE = 35
NOT_OPAQUE = 255

BROADCAST_MAC = 'ff:ff:ff:ff:ff:ff'
STP_MULTICAST_MAC = "01:80:C2:00:00:00"
DEFAULT_COMPUTER_IP = "192.168.1.2/24"
DHCP_CLIENT_PORT = 68
DHCP_SERVER_PORT = 67
ON_LINK = "On-link"

INTERFACE_NAMES = [line.strip() for line in open(FILES.format("interface_names.txt")).readlines()]
COMPUTER_NAMES = [line.strip() for line in open(FILES.format("computer_names.txt")).readlines()]
ANY_INTERFACE = None

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

ARP_CACHE_FORGET_TIME = 300  # seconds
SWITCH_TABLE_ITEM_LIFETIME = 300  # seconds
PACKETS_ARE_NOT_MOVING_MAX_TIME = 0.5  # second
# ^ this is the time that if the packets did not move for that much time (in a pause for example) we take them back a bit in the connection and adjust their `sending_time`
STP_NORMAL_SENDING_INTERVAL = 2 # seconds
STP_STABLE_SENDING_INTERVAL = 7 # seconds
TREE_STABLIZING_MAX_TIME = 10 # seconds
DEFAULT_SWITCH_PRIORITY = 32768

PACKET_GOING_RIGHT = 'R'
PACKET_GOING_LEFT = 'L'

DARK_GRAY = (20, 20, 20)
GRAY = (10, 10, 10)
LIGHT_GRAY = (150, 150, 150)
VERY_LIGHT_GRAY = (180, 180, 180)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
LIGHT_BLUE = (100, 100, 255)
PURPLE = (171, 71, 188)
BROWN = (62, 39, 35)
RED = (150, 0, 0)

SIDE_WINDOW_WIDTH = 230

DEFAULT_BUTTON_TEXT = "BuTTon"
DEFAULT_BUTTON_WIDTH = SIDE_WINDOW_WIDTH - 40
DEFAULT_BUTTON_HEIGHT = 30


def DEFAULT_BUTTON_LOCATION(button_index):
    return (WINDOW_WIDTH - SIDE_WINDOW_WIDTH + 20), (510 - (button_index * 40))


MAIN_MENU_BUTTONS = 0
VIEW_MODE_BUTTONS = 1

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
BLOCKED_CONNECTION_COLOR = RED

IMAGES_SIZE = 16
VIEWING_IMAGE_COORDINATES = ((WINDOW_WIDTH - (SIDE_WINDOW_WIDTH / 2)) - (
            IMAGES_SIZE * VIEWING_OBJECT_SCALE_FACTOR / 2)), WINDOW_HEIGHT - (
                                        (IMAGES_SIZE * VIEWING_OBJECT_SCALE_FACTOR) + 15)
VIEWING_TEXT_COORDINATES = (WINDOW_WIDTH - (SIDE_WINDOW_WIDTH / 2)), VIEWING_IMAGE_COORDINATES[1] - 10

CONSOLE_X, CONSOLE_Y = VIEWING_TEXT_COORDINATES[0] - 105, 10
CONSOLE_WIDTH = SIDE_WINDOW_WIDTH - 20
CONSOLE_HEIGHT = 3 * (CONSOLE_WIDTH / 4)
CONSOLE_FONT_SIZE = 8
CONSOLE_LINE_HEIGHT = 14

PAUSE_RECT_WIDTH = 10
PAUSE_RECT_HEIGHT = 60
PAUSE_RECT_COORDINATES = 20, ((WINDOW_HEIGHT - PAUSE_RECT_HEIGHT) - 10)

CIRCLE_SEGMENT_COUNT = 50

TEXTBOX_COORDINATES = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2  # the popup window
TEXTBOX_WIDTH = 400
TEXTBOX_HEIGHT = 170
TEXTBOX_COLOR = DARK_GRAY
SUBMIT_BUTTON_WIDTH = 100
