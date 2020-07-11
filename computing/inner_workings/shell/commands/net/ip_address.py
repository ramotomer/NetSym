from address.mac_address import MACAddress
from computing.inner_workings.shell.commands.command import Command, CommandOutput
from gui.tech.loopback_connection_graphics import LoopbackConnectionGraphics


class IpAddressCommand(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(IpAddressCommand, self).__init__('ip_address', 'manage ip addresses of the device', computer, shell)

    @staticmethod
    def _get_interface_data(interface, index=0):
        """
        Receives interface, returns string data
        :param interface:
        :return:
        """
        type_ = 'LOOPBACK' if isinstance(interface.graphics, LoopbackConnectionGraphics) else 'BROADCAST'

        # TODO: this ^ does not work AT ALL!!!

        is_up = 'UP' if interface.is_powered_on else 'DOWN'
        type_2 = 'loopback' if type_ == 'LOOPBACK' else 'ether'
        broadcast_ip = 'brd ' + (str(interface.ip.subnet_broadcast()) if interface.ip is not None else '')

        return f"""{index}: {interface.name} <{type_},{is_up}>
    link/{type_2} {interface.mac} brd {MACAddress.broadcast()}
    inet {repr(interface.ip)} {broadcast_ip} scope global
"""

    def _list_interfaces(self):
        """
        return a string that lists the interfaces of the computer
        :return:
        """
        stdout = [self._get_interface_data(interface, i) for i, interface in enumerate(self.computer.all_interfaces)]
        return CommandOutput('\n'.join(stdout), '')

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        return self._list_interfaces()
