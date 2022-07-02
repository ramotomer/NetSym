class NetworkSimulationError(Exception):
    """
    Every exception that I make will inherit from this one.
    This way I know if U raised an exception or I had another problem and can
    catch them all.
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


# ----------------------------------------------------------------------------------------------------------------------


class SomethingWentTerriblyWrongError(NetworkSimulationError):
    """
    An error that tells you if your code got to a place where it should not
    ever reach (mainly default cases in a switch case situation)
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


class PopupWindowWithThisError(GraphicsError):
    """
    This is raised inside an action of a popup window and it is caught inside the popup and a popup error window
    is opened.
    """


class ObjectIsNotResizableError(GraphicsError):
    """
    When a resizing dot is assigned to a non-resizable object.
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


class CommandParsingError(CommandError):
    """
    Error in parsing a command in the shell
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


class SocketIsBrokenError(SocketError):
    """
    Trying to send or receive through a broken socket
    """


class SocketNotBoundError(SocketError):
    """
    Trying to use an un-bound socket
    """


class SocketNotConnectedError(SocketError):
    """
    Trying to receive or send using a disconnected socket
    """


class SocketNotRegisteredError(SocketError):
    """
    Occurs when one tries to bind a socket that is not known to the operation system.
    """


class PortAlreadyBoundError(SocketError):
    """
    Trying to bind a port on an already bound port.
    """


class SocketIsClosedError(SocketError):
    """
    Trying to use a closed socket.
    """


class RawSocketError(SocketError):
    """
    an exception related to raw sockets specifically
    """


class ActionNotSupportedInARawSocket(RawSocketError):
    """
    The action you were trying to perform should not be done on a socket of type raw
    """
