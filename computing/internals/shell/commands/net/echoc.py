from address.ip_address import IPAddress
from computing.internals.processes.usermode_processes.echo_server_process import EchoClientProcess
from computing.internals.shell.commands.command import Command, CommandOutput
from consts import PORTS, PROTOCOLS


class Echoc(Command):
    """
    The command that runs the echocd process - sending data to an echo server

        echo client
    """

    def __init__(self, computer, shell):
        """
        initiates the command.
        :param computer:
        """
        super(Echoc, self).__init__('echoc', 'send a string to an echo server', computer, shell)

        self.parser.add_argument('ip', type=str, help='the echo server ip address')
        self.parser.add_argument('data', type=str, nargs='*', help='the data to send to the server')

        self.parser.add_argument('-p', type=int, dest='port', default=PORTS.ECHO_SERVER, help='the server UDP port')
        self.parser.add_argument('-c', type=int, dest='count', default=PROTOCOLS.ECHO_SERVER.DEFAULT_REQUEST_COUNT,
                                 help='the amount of requests to send')

    def action(self, parsed_args):
        """
        start the `echocd` process
        """
        self.computer.process_scheduler.start_usermode_process(
            EchoClientProcess,
            (IPAddress(parsed_args.ip), parsed_args.port),
            ' '.join(parsed_args.data),
            parsed_args.count,
        )
        return CommandOutput('', '')
