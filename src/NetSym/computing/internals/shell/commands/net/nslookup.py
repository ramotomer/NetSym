from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from NetSym.computing.internals.processes.usermode_processes.dns_process.dns_client_process import DNSClientProcess
from NetSym.computing.internals.shell.commands.command import Command, CommandOutput
from NetSym.consts import PROTOCOLS
from NetSym.packets.usefuls.dns import is_domain_hostname_valid

if TYPE_CHECKING:
    from NetSym.computing.internals.shell.shell import Shell
    from NetSym.computing.computer import Computer


class Nslookup(Command):
    """
    Command that looks up the ip address of a supplied domain name
    """
    def __init__(self, computer: Computer, shell: Shell) -> None:
        """
        initiates the command.
        :param computer:
        """
        super(Nslookup, self).__init__('nslookup', 'Resolve a domain name', computer, shell)

        self.parser.add_argument('hostname', type=str, help='The domain name to resolve')
        self.parser.add_argument('-n', type=int, dest='retry_count',
                                 default=PROTOCOLS.DNS.DEFAULT_RETRY_COUNT,
                                 help='Retry count on no response')
        self.parser.add_argument('-t', type=float, dest='query_timeout',
                                 default=PROTOCOLS.DNS.CLIENT_QUERY_TIMEOUT,
                                 help='How long to wait until we send again')

    def action(self, parsed_args: argparse.Namespace) -> CommandOutput:
        """
        performs the action of the command
        """
        hostname = parsed_args.hostname

        if not is_domain_hostname_valid(hostname):
            return CommandOutput('', "\nERROR: Hostname is not valid!")

        if self.computer.dns_server is None:
            return CommandOutput('', '\nERROR: No DNS server configured!')

        self.computer.process_scheduler.start_usermode_process(
            DNSClientProcess,
            self.computer.dns_server,
            hostname,
            default_query_timeout=parsed_args.query_timeout,
            default_retry_count=  parsed_args.retry_count,
        )
        return CommandOutput('Searching...', '')
