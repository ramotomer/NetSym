from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, TYPE_CHECKING

from consts import OPCODES
from exceptions import FilesystemError, DNSRouteNotFound
from packets.usefuls.dns import T_Hostname
from packets.usefuls.dns import canonize_domain_hostname
from usefuls.funcs import get_the_one

if TYPE_CHECKING:
    from computing.computer import Computer


VARIABLE_DEFINITION_PREFIX = "$"
COMMENT_PREFIX = ';'
LINE_HEADER_COUNT_WITHOUT_SPECIFIC_TTL = 4
LINE_HEADER_COUNT_WITH_SPECIFIC_TT = 5

EXAMPLE = """
$ORIGIN example.com.     ; designates the start of this zone file in the namespace
$TTL 3600                ; default expiration time (in seconds) of all RRs without their own TTL value

example.com.  IN  SOA   ns.example.com. username.example.com. ( 2020091025 7200 3600 1209600 3600 )

example.com.  IN  NS    ns                    ; ns.example.com is a nameserver for example.com
example.com.  IN  NS    ns.somewhere.example. ; ns.somewhere.example is a backup nameserver for example.com
example.com.  IN  MX    10 mail.example.com.  ; mail.example.com is the mailserver for example.com
@             IN  MX    20 mail2.example.com. ; equivalent to above line, "@" represents zone origin
@             IN  MX    50 mail3              ; equivalent to above line, but using a relative host name
example.com.  IN  A     192.0.2.1             ; IPv4 address for example.com
              IN  AAAA  2001:db8:10::1        ; IPv6 address for example.com
ns            IN  A     192.0.2.2             ; IPv4 address for ns.example.com
              IN  AAAA  2001:db8:10::2        ; IPv6 address for ns.example.com
www           IN  CNAME example.com.          ; www.example.com is an alias for example.com
wwwtest       IN  CNAME www                   ; wwwtest.example.com is another alias for www.example.com
mail          IN  A     192.0.2.3             ; IPv4 address for mail.example.com
mail2         IN  A     192.0.2.4             ; IPv4 address for mail2.example.com
mail3         IN  A     192.0.2.5             ; IPv4 address for mail3.example.com
"""


class InvalidZoneFileError(FilesystemError):
    """
    Zone file is not in a valid format!!
    """


@dataclass
class ZoneFileRecord:
    record_name:  T_Hostname
    record_class: str
    record_type:  str
    record_data:  str
    ttl:          Optional[int] = None

    def matches(self, name: T_Hostname) -> bool:
        """
        Returns whether or not a supplied hostname can be resolved using this DNS record
        """
        return canonize_domain_hostname(name).endswith(canonize_domain_hostname(self.record_name)) and \
               name[:-len(self.record_name)][-1] == '.'


@dataclass
class ParsedZoneFile:
    records:                          List[ZoneFileRecord]

    serial_number:                    Optional[int] = None
    slave_refresh_period:             Optional[int] = None
    slave_retry_time:                 Optional[int] = None
    slave_expiration_time:            Optional[int] = None
    max_record_cache_time:            Optional[int] = None

    origin:                           Optional[str] = None
    default_ttl:                      Optional[int] = None

    authoritative_master_name_server: Optional[T_Hostname] = None
    admin_mail_address:               Optional[T_Hostname] = None

    @classmethod
    def with_default_values(cls, domain_name: T_Hostname, computer: Computer) -> ParsedZoneFile:
        domain_name = canonize_domain_hostname(domain_name)
        ip_address = computer.get_ip().string_ip

        return cls(
            records=[
                ZoneFileRecord(domain_name, OPCODES.DNS.QUERY_CLASSES.INTERNET, OPCODES.DNS.QUERY_TYPES.HOST_ADDRESS,                ip_address),
                ZoneFileRecord('ns',        OPCODES.DNS.QUERY_CLASSES.INTERNET, OPCODES.DNS.QUERY_TYPES.HOST_ADDRESS,                ip_address),
                ZoneFileRecord(domain_name, OPCODES.DNS.QUERY_CLASSES.INTERNET, OPCODES.DNS.QUERY_TYPES.AUTHORITATIVE_NAME_SERVER,   'ns'),
                ZoneFileRecord('www',       OPCODES.DNS.QUERY_CLASSES.INTERNET, OPCODES.DNS.QUERY_TYPES.CANONICAL_NAME_FOR_AN_ALIAS, domain_name),
            ],
            serial_number                   = 2020091025,
            slave_refresh_period            = 7200,
            slave_retry_time                = 3600,
            slave_expiration_time           = 1209600,
            max_record_cache_time           = 3600,
            origin                          = domain_name,
            default_ttl                     = 3600,
            authoritative_master_name_server= f'ns.{domain_name}',
            admin_mail_address              = f'admin.{domain_name}',
        )

    @classmethod
    def from_zone_file_content(cls, zone_file_content: str) -> ParsedZoneFile:
        return parse_zone_file_format(zone_file_content)

    def to_zone_file_format(self) -> str:
        return write_zone_file(self)

    def __getitem__(self, item: T_Hostname) -> ZoneFileRecord:
        return get_the_one(
            self.records,
            lambda record: record.record_name == item,
            raises=KeyError
        )

    def resolve_name(self, name: T_Hostname) -> ZoneFileRecord:
        """
        Receive a name and return the best way you can resolve it using the current zone file
        whether it is the actual IP address, or another DNS server that will have a more specific answer
        """
        most_specific_result = None
        for zone_file_record in self.records:
            if zone_file_record.matches(name) and \
                    zone_file_record.record_type != OPCODES.DNS.QUERY_TYPES.CANONICAL_NAME_FOR_AN_ALIAS and \
                    (most_specific_result is None or (len(most_specific_result.record_name) < len(zone_file_record.record_name))):
                    # TODO: add CNAME support
                most_specific_result = zone_file_record
        if most_specific_result is None:
            raise DNSRouteNotFound(f"No good matches found in zone file.\nFile: {repr(self)}")
        return most_specific_result

    def is_resolvable(self, name: T_Hostname) -> bool:
        """returns whether or not the supplied name can be resolved by this zone file"""
        try:
            self.resolve_name(name)
        except DNSRouteNotFound:
            return False
        return True


def parse_zone_file_format(zone_file_content: str) -> ParsedZoneFile:
    """
    Take in the content of a DNS 'zone' file
    Return an accessible dict of the data of the file
    :param zone_file_content:
    """
    parsed = ParsedZoneFile([])
    previous_record_name = ''
    full_string_lines = [line.split(COMMENT_PREFIX, 1)[0].rstrip() for line in zone_file_content.splitlines() if line]
    # ^ remove comments and empty lines

    _extract_variables(full_string_lines, parsed)

    for line in full_string_lines:
        splitted_line = line.split()
        if line[0].isspace():                                              # this is when the line key is the previous key
            if not previous_record_name:
                raise InvalidZoneFileError(f"No previous record name! Cannot start file without a key.\nline: '{line}'")
            splitted_line = [previous_record_name] + splitted_line

        record_name, record_class, record_type = splitted_line[:3]
        address, ttl = _parse_record_line(parsed, record_type, splitted_line)
        if address is None:                                        # this means it is the SOA record line! no need to put it in the `records` list
            continue

        previous_record_name = record_name
        parsed.records.append(ZoneFileRecord(record_name, record_class, record_type, address, ttl))
    return parsed


def _parse_record_line(parsed: ParsedZoneFile, record_type: str, splitted_line: List[str]) -> Tuple[Optional[str], Optional[int]]:
    """
    Take in a line:
        >>> 'example.com.  IN  NS    ns.somewhere.example. ; ns.somewhere.example is a backup nameserver for example.com'
    If it is the SOA line - set attributes of the ParsedZoneFile accordingly, and return (None, None)
    Otherwise, return the ip address that is specified in the line and the TTL of that record (if it is the default - return None)

    :param parsed:  The already somewhat parsed `ParsedZoneFile` object
    :param record_type: one of `OPCODES.DNS.QUERY_TYPES`
    :param splitted_line: the line to parse, splitted by spaces and without inline comments

    :return (ip_address, ttl_or_none_if_default)
    """
    if record_type == OPCODES.DNS.QUERY_TYPES.START_OF_AUTHORITY:
        (parsed.authoritative_master_name_server,
         parsed.admin_mail_address) = splitted_line[3:5]
        (parsed.serial_number,
         parsed.slave_refresh_period,
         parsed.slave_retry_time,
         parsed.slave_expiration_time,
         parsed.max_record_cache_time) = [int(c.strip("()")) for c in splitted_line[5:] if c not in "()"]

        return None, None

    if len(splitted_line) == LINE_HEADER_COUNT_WITHOUT_SPECIFIC_TTL:  # ttl should be taken from the default
        return splitted_line[3], None

    if len(splitted_line) == LINE_HEADER_COUNT_WITH_SPECIFIC_TT:  # ttl is specified explicitly
        return splitted_line[4], int(splitted_line[3])

    raise InvalidZoneFileError(f"Line too long!! line:\n'{' '.join(splitted_line)}'")


def _extract_variables(full_string_lines: List[str], parsed: ParsedZoneFile) -> None:
    """
    Find the variable definition in the zone file ($ORIGIN, $TTL)
    Set the necessary attributes of the supplied `ParsedZoneFile` object
    """
    for line in full_string_lines[:]:
        if line.startswith('$ORIGIN'):
            parsed.origin = line.split(maxsplit=1)[1]
            full_string_lines.remove(line)
        elif line.startswith('$TTL'):
            parsed.default_ttl = int(line.split(maxsplit=1)[1])
            full_string_lines.remove(line)


def write_zone_file(parsed: ParsedZoneFile) -> str:
    """
    Take in a parsed zone file and return it in a string format to later be saved into a file :)
    """
    linesep = '\n'
    integer_parameters = f"""{
        parsed.serial_number} {
        parsed.slave_refresh_period} {
        parsed.slave_retry_time} {
        parsed.slave_expiration_time} {
        parsed.max_record_cache_time
    }"""

    return f"""$ORIGIN {parsed.origin}
$TTL {parsed.default_ttl}\n
{parsed.origin} IN SOA {parsed.authoritative_master_name_server} {parsed.admin_mail_address} ( {integer_parameters} )\n
{linesep.join(f"{record.record_name: <13} {record.record_class: <3} {record.record_type: <5} {record.record_data}" for record in parsed.records)}
"""
