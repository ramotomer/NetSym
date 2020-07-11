from computing.internals.shell.commands.command import Command, CommandOutput


class IpLinkCommand(Command):
    """
    The command that prints the arguments that it receives.
    """
    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(IpLinkCommand, self).__init__('ip_link', 'manage ip links of the device', computer, shell)

    def action(self, parsed_args):
        """
        prints out the arguments.
        """
        return CommandOutput("linkssss!!!!!!!!", '')
        # TODO: implement!
