from abc import ABCMeta
from typing import Tuple

from address.ip_address import IPAddress
from computing.internals.sockets.socket import Socket


class L4Socket(Socket, metaclass=ABCMeta):
    """
    UDP/TCP sockets have many functions in common :)
    """
    def receive(self, count=1024):
        """
        receive the information from the other side of the socket
        :param count: how many bytes to receive
        :return:
        """
        data = ''.join(self.received) if self.received else None
        self.received.clear()
        return data

    def bind(self, address: Tuple[IPAddress, int]):
        """
        Binds the socket to a certain address and port on the computer
        :param address:
        """
        self.computer.bind_socket(self, address)

    def __str__(self):
        return f"socket of {self.computer.name}"

    def __repr__(self):
        return f"{self.protocol}    " \
            f"{':'.join(map(str, self.bound_address)): <23}" \
            f"{':'.join(map(str, self.remote_address)): <23}" \
            f"{self.state: <16}" \
            f"{self.acquiring_process_pid}"
