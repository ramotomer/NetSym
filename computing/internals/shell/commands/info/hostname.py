from computing.internals.shell.commands.command import Command, CommandOutput
from exceptions import PopupWindowWithThisError


class Hostname(Command):
    """
    Prints the computers name
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Hostname, self).__init__('hostname', 'print computer name', computer, shell)

        self.parser.add_argument('-i', '--ip', dest='show_addresses', action='store_true',
                                 help='print IP addresses of this computer')
        self.parser.add_argument('-s', '--set', metavar='NAME', dest='new_name', help='set computer name')

    def to_print(self, parsed_args):
        """
        The message to print.
        :return:
        """
        if parsed_args.show_addresses:
            return '\n'.join([str(interface.ip) for interface in self.computer.interfaces if interface.has_ip()])
        return self.computer.name

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        if parsed_args.new_name is not None:
            try:
                self.computer.set_name(parsed_args.new_name)
            except PopupWindowWithThisError as err:
                return CommandOutput('', f"{str(err)} :(")
            return CommandOutput(f"Set computer name to '{parsed_args.new_name}' successfully!", '')

        return CommandOutput(self.to_print(parsed_args), '')
