from exceptions import *


class ProcessInternalError(Exception):
    """
    If this exception is raised inside a code of a process, the process will be terminated but the rest of NetSym will continue
    """


class ProcessInternalError_Suicide(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process
    """


class ProcessInternalError_InvalidDomainHostname(ProcessInternalError_Suicide, InvalidDomainHostnameError):
    """
    This indicates a self-inflicted death of the process due to an invalid domain hostname
    """


class ProcessInternalError_NoResponseForARP(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process due to an ARP that was sent but was not responded
    """


class ProcessInternalError_DNSNameErrorFromServer(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process due to a DNS query that was sent but was not responded
    """


class ProcessInternalError_NoResponseForDNSQuery(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process due to a DNS query that was sent but was not responded
    """


class ProcessInternalError_NoIPAddressError(ProcessInternalError, NoIPAddressError):
    """
    This indicates a self-inflicted death of the process due to a lack of an IP address
    """


class ProcessInternalError_RoutedPacketTTLExceeded(ProcessInternalError):
    """
    This indicates a self-inflicted death of the process because the packet that was routed did not have enough TTL to actually be routed
    """


class ProcessInternalError_WrongUsageError(ProcessInternalError, WrongUsageError):
    """
    This indicates a self-inflicted death of the process due to the process not being used correctly
    """


class ProcessInternalError_InvalidParameters(ProcessInternalError_WrongUsageError):
    """
    This indicates a self-inflicted death of the process due to the supplied parameters being invalid or incorrect
    """


class ProcessInternalError_PacketTooLongToFragment(ProcessInternalError, PacketTooLongToFragment):
    """
    This indicates a self-inflicted death of the process due to a packet being too large for it to fragment it
    """


class ProcessInternalError_PacketTooLongButDoesNotAllowFragmentation(ProcessInternalError, PacketTooLongButDoesNotAllowFragmentation):
    """
    This indicates a self-inflicted death of the process due to a packet being too large and must be fragmented - but the DONT_FRAGMENT flag is set!
    """
