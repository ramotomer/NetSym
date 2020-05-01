class NetworkSimulationError(Exception):
    """
    Every exception that I make will inherit from this one.
    This way I know if U raised an exception or I had another problem and can
    catch them all.
    """


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


class SomethingWentTerriblyWrongError(NetworkSimulationError):
    """
    An error that tells you if your code got to a place where it should not
    ever reach (mainly default cases in a switch case situation)
    """


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


class ProcessError(NetworkSimulationError):
    """
    Indicates some problem with the processes of a computer.
    """

class NoSuchProcessError(ProcessError):
    """
    Occurs when a process that does not exist is required.
    """


class ConnectionError(NetworkSimulationError):
    """
    Indicates an error in a connection or in connection related functions.
    """

class NoSuchConnectionSideError(ConnectionError):
    """
    Occurs when a certain connection-side is requested when it does not exist.
    """

class NoSuchConnectionError(ConnectionError):
    """
    Occurs when a connection that does not exist is requested or used.
    """
