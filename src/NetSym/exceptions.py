# DO NOT IMPORT ANYTHING TO THIS FILE!!!!


class NetworkSimulationError(Exception):
    """
    Every exception that I make will inherit from this one.
    This way I know if U raised an exception or I had another problem and can
    catch them all.
    """


class AttributeError_(NetworkSimulationError):
    """
    For some reason pyglet makes attribute errors silent.
    I catch them early and replace them with this custom AttributeError
    """


# ----------------------------------------------------------------------------------------------------------------------


class AddressError(NetworkSimulationError):
    """
    This error indicates of a problem with a MAC or IP address. usually that
    they are invalid.
    """


class InvalidAddressError(AddressError):
    """
    This error indicates that some address (IP or MAC) is invalid.
    """


class NoIPAddressError(AddressError):
    """
    Occurs when an IP is requested and one does not exist!
    """


class AddressTooLargeError(AddressError):
    """
    Occurs when one tries to increase an IPAddress that is at its subnet maximum size.
    """


class InvalidDomainHostnameError(InvalidAddressError):
    """
    The supplied domain hostname is invalid
        (see the `validate_domain_hostname` function for more documentation)
    """


# ----------------------------------------------------------------------------------------------------------------------


class SomethingWentTerriblyWrongError(NetworkSimulationError):
    """
    An error that tells you if your code got to a place where it should not
    ever reach (mainly default cases in a switch case situation)
    """


class ThisValueShouldNeverBeNone(SomethingWentTerriblyWrongError, ValueError):
    """
    Raised when a value that should never be none - is none.
    """


class WrongUsageError(SomethingWentTerriblyWrongError):
    """
    Occurs when a function is used not in the way it was intended
    """


class WrongIPRouteUsageError(WrongUsageError):
    """
    Wrong usage of the `ip route` command
    """


class ThisCodeShouldNotBeReached(SomethingWentTerriblyWrongError):
    """
    This should be raised in some code segment that should never be reached, but it is good practice to write it anyway.
    """


# ----------------------------------------------------------------------------------------------------------------------


class PacketError(NetworkSimulationError):
    """
    A super-class to all packet-related errors.
    """


class UnknownPacketTypeError(PacketError):
    """
    An error that happens when the computer does not know how to handle
    a certain packet.
    """


class NoSuchPacketError(PacketError):
    """
    Occurs when a packet that does not exist is required and used.
    """


class IPError(PacketError):
    """
    An error related to the IP protocol
    """


class FragmentationError(IPError):
    """
    An error related to an IP fragmentation of a packet
    """


class PacketTooLongToFragment(FragmentationError):
    """
    I am not writing doc for this screw you
    """


class PacketAlreadyFragmentedError(FragmentationError):
    """
    Need to fragment a packet - but it is already fragmented!
    """


class PacketTooLongButDoesNotAllowFragmentation(FragmentationError):
    """
    The packet is too long to send - but the DONT_FRAGMENT flag is set!
    """


class InvalidFragmentsError(FragmentationError):
    """
    Got an invalid list of fragments
    """


class STPError(PacketError):
    """
    Indicates an STP related error.
    """


class NoSuchLayerError(PacketError):
    """
    Occurs when a packet does not contain a required Layer.
    """


class NoARPLayerError(NoSuchLayerError):
    """
    An error that occurs when a packet is treated as an ARP when in fact
    it contains no ARP layer.
    """


class TCPError(PacketError):
    """
    A TCP related exception
    """


class TCPDoneReceiving(TCPError):
    """
    used to indicate that a TCP process has finished to receive information.
    """


class TCPDataLargerThanMaxSegmentSize(TCPError):
    """
    This is raised when some ip_layer is sent by TCP when it is larger than the MSS (max segment size) of that packet
    """


# ----------------------------------------------------------------------------------------------------------------------


class InterfaceError(NetworkSimulationError):
    """
    An error to indicate something wrong on the interface level
    """


class DeviceAlreadyConnectedError(InterfaceError):
    """
    Occurs when trying to connect an interface that is already connected
    """


class InterfaceNotConnectedError(InterfaceError):
    """
    This occurs when you try to send or receive from an interface that is not
    connected.
    """


class NoSuchInterfaceError(InterfaceError):
    """
    Occurs when you look for an interface that does not exist (usually by name)
    """


class NotAnInterfaceError(InterfaceError):
    """
    Occurs when an interface is requested but another type of object is given.
    """


class DeviceNameAlreadyExists(InterfaceError):
    """
    Indicates a creation of an interface with a name that is taken.
    """


# ----------------------------------------------------------------------------------------------------------------------


class ComputerError(NetworkSimulationError):
    """
    Occurs in computer-related errors
    """


class NoSuchComputerError(ComputerError):
    """
    Occurs when a computer that does not exist is accessed
    """


class RoutingTableError(ComputerError):
    """
    Indicates an error in the routing table of a computer.
    """


class RoutingTableCouldNotRouteToIPAddress(KeyError, RoutingTableError):
    """
    The routing table did not have an item that matched the IP that one tried to route to :(
    """


class PortError(ComputerError):
    """
    Indicates a port-related error
    """


class UnknownPortError(PortError):
    """
    Occurs when one tries to open a port that is not familiar to the operating computer
    """


class PortAlreadyOpenError(PortError):
    """
    Occurs when a port that is open is opened
    """


# ----------------------------------------------------------------------------------------------------------------------


class GraphicsError(NetworkSimulationError):
    """
    An exception that is raised because of some graphics problem.
    """


class NotAskingForStringError(GraphicsError):
    """
    When you try to end a string request in the UserInterface when one is not currently running.
    """


class NoSuchGraphicsObjectError(GraphicsError):
    """
    Occurs when a graphics object that does not exist is required or used.
    """


class GraphicsObjectAlreadyRegistered(GraphicsError):
    """
    Trying to register a `GraphicsObject` which is already registered
    """


class GraphicsObjectNotYetInitialized(GraphicsError):
    """
    Trying to get the value of the graphics object before the `init_graphics` method was called
    """


class ParentGraphicsObjectNotSet(GraphicsObjectNotYetInitialized):
    """
    An object has an attribute that can only be initialized by a parent `GraphicsObject`.
    That attribute was accessed but no parent `GraphicsObject` was set :(
    """


class PopupWindowWithThisError(GraphicsError):
    """
    This is raised inside an action of a popup window and it is caught inside the popup and a popup error window
    is opened.
    """


class ObjectIsNotResizableError(GraphicsError):
    """
    When a resizing dot is assigned to a non-resizable object.
    """


class MainLoopError(NetworkSimulationError):
    """
    An error related to the main loop
    """


class MainLoopInstanceNotYetInitiated(MainLoopError):
    """
    Some code was trying to use the `MainLoop.instance` before it was initiated
    Probably somewhere in the `UserInterface` class because it is initiated before the main loop
    """


class MainWindowError(GraphicsError):
    """
    An error related to the MainWindow object
    """


class UnknownEventType(MainWindowError):
    """
    Trying to register a function to handle an event which is unknown
    """


class ImageError(GraphicsError):
    """
    An error related to an ImageGraphicsObject
    """


class ImageNotLoadedError(ImageError):
    """
    An image was used before being loaded from the file!
    """

# ----------------------------------------------------------------------------------------------------------------------


class ProcessError(NetworkSimulationError):
    """
    Indicates some problem with the processes of a computer.
    """


class NoSuchProcessError(ProcessError):
    """
    Occurs when a process that does not exist is required.
    """


class UnknownProcessTypeError(ProcessError):
    """
    only known types are USERMODE and KERNELMODE - the others are unknown :/
    """

# ----------------------------------------------------------------------------------------------------------------------


class ConnectionsError(NetworkSimulationError):
    """
    Indicates an error in a connection or in connection related functions.
    """


class NoSuchConnectionSideError(ConnectionsError):
    """
    Occurs when a certain connection-side is requested when it does not exist.
    """


class NoSuchConnectionError(ConnectionsError):
    """
    Occurs when a connection that does not exist is requested or used.
    """


class ConnectionComputerNotDefined(ConnectionsError):
    """
    One of the computers in `connection.computers` is None - that means the connection is not connected on one of its sides
    """

# ----------------------------------------------------------------------------------------------------------------------


class UserInterfaceError(NetworkSimulationError):
    """
    a problem with something that is related to an action that the user has performed.
    """


class KeyboardError(UserInterfaceError):
    """
    problem related to the keyboard.
    """


class KeyActionAlreadyExistsError(KeyboardError):
    """
    Trying to assign an action to a key that an action is already assigned to it...
    """


class UnknownModeError(UserInterfaceError):
    """
    An unknown mode was specified or used without being defined first :(
    """


# ----------------------------------------------------------------------------------------------------------------------


class FilesystemError(ComputerError):
    """
    An error with the filesystem of a computer.
    """


class NoSuchItemError(FilesystemError):
    """
    When a filesystem item is requested but does not exist!
    """


class NoSuchFileError(NoSuchItemError):
    """
    When a file that is accessed does not exist.
    """


class NoSuchDirectoryError(NoSuchItemError):
    """
    when dir no exist this happen
    """


class PathError(FilesystemError):
    """
    A problem with a path.
    """


class DirectoryAlreadyExistsError(FilesystemError):
    """
    Directory to be created already exists in dest location.
    """


class FileNotOpenError(FilesystemError):
    """
    Reading from a closed file.
    """


# ----------------------------------------------------------------------------------------------------------------------


class ShellError(NetworkSimulationError):
    """
    An error in a shell
    """


class CommandError(ShellError):
    """
    Error with a command
    """


class ErrorForCommandOutput(CommandError):
    """
    This is an exception that is caught if it is raised inside of a shell command.
    The message of this exception will be printed to the screen of the shell! nice
    """


class NoSuchFileError__ErrorForCommandOutput(NoSuchFileError, ErrorForCommandOutput):
    """
    This error will be raised when a file is accessed but no such file exists.
    In addition this exception is caught and printed to the shell if it is raised inside of a shell command.
    """


class CommandParsingError(CommandError):
    """
    Error in parsing a command in the shell
    """


class SyntaxArgumentMessageError(CommandParsingError):
    """
    Raised when the syntax of a shell command is invalid
    """


class WrongArgumentsError(CommandParsingError):
    """
    Arguments that were given to the parsed command were not correct.
    """


class CannotBeUsedWithPiping(CommandError):
    """
    There are commands that cannot be used with piping (for example: `echo hi | rm` cannot be done!)
    """


class InvalidAliasCommand(CommandError):
    pass


# ----------------------------------------------------------------------------------------------------------------------


class SocketError(ComputerError):
    """
    An error in a computer socket in the simulations
    """


class WrongUsageSocketError(SocketError):
    """
    Occurs when the order of commands activated on a socket is not correct
    """


class SocketIsBrokenError(WrongUsageSocketError):
    """
    Trying to send or receive through a broken socket
    """


class SocketNotBoundError(WrongUsageSocketError):
    """
    Trying to use an un-bound socket
    """


class SocketNotConnectedError(WrongUsageSocketError):
    """
    Trying to receive or send using a disconnected socket
    """


class SocketAlreadyConnectedError(WrongUsageSocketError):
    """
    Raises when trying to connect a socket that is already connected :)
    """
    pass


class SocketNotRegisteredError(WrongUsageSocketError):
    """
    Occurs when one tries to bind a socket that is not known to the operation system.
    """


class PortAlreadyBoundError(WrongUsageSocketError):
    """
    Trying to bind a port on an already bound port.
    """


class SocketIsClosedError(WrongUsageSocketError):
    """
    Trying to use a closed socket.
    """


class RawSocketError(SocketError):
    """
    an exception related to raw sockets specifically
    """


class L4SocketError(SocketError):
    """
    An error related to L4 sockets (tcp/udp)
    """


class TCPSocketError(L4SocketError):
    """
    An error related to TCP sockets
    """


class UDPSocketError(L4SocketError):
    """
    An error related to UDP sockets
    """


class ActionNotSupportedInARawSocket(RawSocketError):
    """
    The action you were trying to perform should not be done on a socket of type raw
    """


class UnknownSocketTypeError(SocketError):
    """
    The supplied type is not a valid socket type
    """


class UnknownLayer4SocketTypeError(UnknownSocketTypeError, L4SocketError):
    """
    The supplied type is not a valid l4 socket type (udp/tcp)
    """


class TCPSocketConnectionRefused(TCPSocketError):
    """
    Tried connecting a TCP socket but the connection was not successful
    """


class DNSError(PacketError):
    """
    Exception related to the DNS protocol
    """


class DNSRouteNotFound(DNSError):
    """
    Failed to find a good value for a supplied domain name
    """
