from computing.inner_workings.shell.commands.command import Command, CommandOutput
from computing.inner_workings.shell.commands.net.ip_address import IpAddressCommand
from computing.inner_workings.shell.commands.net.ip_link import IpLinkCommand
from computing.inner_workings.shell.commands.net.ip_route import IpRouteCommand


class Ip(Command):
    """
    Controls the network communication of the device.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer: 
        """
        super(Ip, self).__init__('ip', 'manage ip settings', computer, shell)
        self.parser.add_argument('object', metavar='object', type=str, nargs='?', help='type of ip command to run')
        self.parser.add_argument('args', metavar='args', nargs='*', type=str, help='rest of the arguments')

        self.object_to_command = {
            'address': IpAddressCommand,
            'link': IpLinkCommand,
            'route': IpRouteCommand,

            'a': IpAddressCommand,
            'l': IpLinkCommand,
            'r': IpRouteCommand,
        }

    @staticmethod
    def _ip_help():
        """
        Returns a string help document
        :return:
        """
        return """Usage: ip [OPTIONS] OBJECT { COMMAND }
where OBJECT := { link | address | route } 
"""

    def action(self, parsed_args):
        """
        redirects the action to the action of the specified `ip` command (ip a, ip l, etc...)
        """
        if parsed_args.object is None:
            return CommandOutput(self._ip_help(), '')
        command_class = self.object_to_command[parsed_args.object](self.computer, self.shell)
        _, parsed_additional_args = command_class.parse(' '.join([f'ip_{parsed_args.object}'] + parsed_args.args))
        return command_class.action(parsed_additional_args)
