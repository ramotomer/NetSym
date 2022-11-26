from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, TYPE_CHECKING, Iterable

from NetSym.consts import OPCODES
from NetSym.exceptions import FilesystemError
from NetSym.packets.usefuls.dns import T_Hostname, canonize_domain_hostname, is_domain_hostname_valid
from NetSym.usefuls.funcs import get_the_one_with_raise

if TYPE_CHECKING:
    from NetSym.computing.computer import Computer


VARIABLE_DEFINITION_PREFIX = "$"
COMMENT_PREFIX = ';'
LINE_HEADER_COUNT_WITHOUT_SPECIFIC_TTL = 4
LINE_HEADER_COUNT_WITH_SPECIFIC_TTL = 5

EXAMPLE = """
$ORIGIN example.com.     ; designates the start of this zone file in the namespace
$TTL 3600                ; default expiration time (in seconds) of all RRs without their own TTL value

example.com.  IN  SOA   ns.example.com. username.example.com. ( 2020091025 7200 3600 1209600 3600 )

example.com.       IN  A     192.0.2.1             ; IPv4 address for example.com  
@                  IN  AAAA  2001:db8:10::1        ; IPv6 address for example.com  (@ is replaced by the zone origin)
ns                 IN  A     192.0.2.2             ; IPv4 address for ns.example.com
                   IN  AAAA  2001:db8:10::2        ; IPv6 address for ns.example.com
www                IN  CNAME example.com.          ; www.example.com is an alias for example.com
wwwtest            IN  CNAME www                   ; wwwtest.example.com is another alias for www.example.com
mail               IN  A     192.0.2.3             ; IPv4 address for mail.example.com
mail2              IN  A     192.0.2.4             ; IPv4 address for mail2.example.com
mail3              IN  A     192.0.2.5             ; IPv4 address for mail3.example.com
cool.example.com.  IN  NS    192.0.2.254           ; cool.example.com is a nameserver where 'cool.example.com.zone' is located
"""


class InvalidZoneFileError(FilesystemError):
    """
    Zone file is not in a valid format!!
    """


@dataclass
class ZoneRecord:
    record_name:  T_Hostname
    record_class: str
    record_type:  str
    record_data:  str
    ttl:          Optional[int] = None


@dataclass
class Zone:
    records:                          List[ZoneRecord]

    serial_number:                    Optional[int] = None
    slave_refresh_period:             Optional[int] = None
    slave_retry_time:                 Optional[int] = None
    slave_expiration_time:            Optional[int] = None
    max_record_cache_time:            Optional[int] = None

    origin:                           Optional[str] = None
    default_ttl:                      Optional[int] = None

    authoritative_master_name_server: Optional[T_Hostname] = None
    admin_mail_address:               Optional[T_Hostname] = None

    @property
    def host_or_alias_records(self) -> List[ZoneRecord]:
        return [r for r in self.records if r.record_type in [OPCODES.DNS.TYPES.HOST_ADDRESS,
                                                             OPCODES.DNS.TYPES.CANONICAL_NAME_FOR_AN_ALIAS]]

    @property
    def name_server_records(self) -> List[ZoneRecord]:
        return [r for r in self.records if r.record_type == OPCODES.DNS.TYPES.AUTHORITATIVE_NAME_SERVER]

    def __iter__(self) -> Iterable[ZoneRecord]:
        return iter(self.records)

    @classmethod
    def with_default_values(cls, domain_name: T_Hostname, computer: Computer) -> Zone:
        domain_name = canonize_domain_hostname(domain_name)
        ip_address = computer.get_ip().string_ip

        return cls(
            records=[
                ZoneRecord(domain_name, OPCODES.DNS.CLASSES.INTERNET, OPCODES.DNS.TYPES.HOST_ADDRESS, ip_address),
                ZoneRecord('ns', OPCODES.DNS.CLASSES.INTERNET, OPCODES.DNS.TYPES.HOST_ADDRESS, ip_address),
                ZoneRecord(domain_name, OPCODES.DNS.CLASSES.INTERNET, OPCODES.DNS.TYPES.AUTHORITATIVE_NAME_SERVER, 'ns'),
                ZoneRecord(f'www', OPCODES.DNS.CLASSES.INTERNET, OPCODES.DNS.TYPES.CANONICAL_NAME_FOR_AN_ALIAS, domain_name),
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
    def from_file_format(cls, zone_file_content: str) -> Zone:
        """
        Take in the content of a DNS 'zone' file
        Return an accessible dict of the data of the file
        :param zone_file_content:
        """
        parsed = cls([])
        previous_record_name = ''
        full_string_lines = [line.split(COMMENT_PREFIX, 1)[0].rstrip() for line in zone_file_content.splitlines() if line]
        # ^ remove comments and empty lines

        cls._extract_variables(full_string_lines, parsed)

        for line in full_string_lines:
            splitted_line = line.split()
            if line[0].isspace():  # this is when the line key is the previous key
                if not previous_record_name:
                    raise InvalidZoneFileError(f"No previous record name! Cannot start file without a key.\nline: '{line}'")
                splitted_line = [previous_record_name] + splitted_line

            record_name, record_class, record_type = splitted_line[:3]
            address, ttl = cls._parse_record_line(parsed, record_type, splitted_line)
            if address is None:  # this means it is the SOA record line! no need to put it in the `records` list
                continue

            previous_record_name = record_name
            parsed.records.append(ZoneRecord(record_name, record_class, record_type, address, ttl))
        return parsed

    def to_file_format(self) -> str:
        """
        Take in a parsed zone file and return it in a string format to later be saved into a file :)
        """
        linesep = '\n'
        integer_parameters = f"""{
            self.serial_number} {
            self.slave_refresh_period} {
            self.slave_retry_time} {
            self.slave_expiration_time} {
            self.max_record_cache_time
        }"""

        return f"""$ORIGIN {self.origin}
$TTL {self.default_ttl}\n
{self.origin} IN SOA {self.authoritative_master_name_server} {self.admin_mail_address} ( {integer_parameters} )\n
{linesep.join(f"{record.record_name: <30} {record.record_class: <3} {record.record_type: <5} {record.record_data}" for record in self.records)}
"""

    def __getitem__(self, item: T_Hostname) -> ZoneRecord:
        return get_the_one_with_raise(
            self.records,
            lambda record: record.record_name == item,
            raises=KeyError
        )

    @classmethod
    def _parse_record_line(cls, parsed: Zone, record_type: str, splitted_line: List[str]) -> Tuple[Optional[str], Optional[int]]:
        """
        Take in a line:
            >>> 'example.com.  IN  NS    ns.somewhere.example. ; ns.somewhere.example is a backup nameserver for example.com'
        If it is the SOA line - set attributes of the Zone accordingly, and return (None, None)
        Otherwise, return the ip address that is specified in the line and the TTL of that record (if it is the default - return None)
            Note that some lines specify TTL and some dont - that affects the parsing

        :param parsed:  The already somewhat parsed `Zone` object
        :param record_type: one of `OPCODES.DNS.TYPES`
        :param splitted_line: the line to parse, splitted by spaces and without inline comments

        :return (ip_address, ttl_or_none_if_default)
        """
        if record_type == OPCODES.DNS.TYPES.START_OF_AUTHORITY:
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

        if len(splitted_line) == LINE_HEADER_COUNT_WITH_SPECIFIC_TTL:  # ttl is specified explicitly
            return splitted_line[4], int(splitted_line[3])

        raise InvalidZoneFileError(f"Line too long!! line:\n'{' '.join(splitted_line)}'")

    @classmethod
    def _extract_variables(cls, full_string_lines: List[str], parsed: Zone) -> None:
        """
        Find the variable definition in the zone file ($ORIGIN, $TTL)
        Set the necessary attributes of the supplied `Zone` object
        """
        for line in full_string_lines[:]:
            if line.startswith('$ORIGIN'):
                parsed.origin = line.split(maxsplit=1)[1]
            elif line.startswith('$TTL'):
                parsed.default_ttl = int(line.split(maxsplit=1)[1])
            else:
                return
            full_string_lines.remove(line)

    def resolve_aliasing(self, alias_record: Optional[ZoneRecord]) -> Optional[str]:
        """
        Take in an alias record and return the record_data of the record that the alias refers to
        """
        if alias_record is None:
            return None

        if not is_domain_hostname_valid(alias_record.record_data):  # record is not an alias
            return alias_record.record_data

        resolved_record = get_the_one_with_raise(self.records, lambda r: r.record_name == alias_record.record_data, InvalidZoneFileError)
        if is_domain_hostname_valid(resolved_record.record_data):  # That means `resolved_record` is still an 'alias' record! (alias of an alias)
            return self.resolve_aliasing(resolved_record)
        return resolved_record.record_data
