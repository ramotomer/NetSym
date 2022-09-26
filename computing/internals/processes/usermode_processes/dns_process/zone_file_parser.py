from typing import Dict, List

from exceptions import *

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


def parse_zone_file_format(zone_file_content: str) -> List:
    """
    Take in the content of a DNS 'zone' file
    Return an accessible dict of the data of the file
    :param zone_file_content:
    """
    variables = {}
    records = []
    previous_record_name = None

    for line in map(str, filter(bool, zone_file_content.splitlines())):
        line = line.split(COMMENT_PREFIX)[0]             # ; remove comments

        if line.startswith(VARIABLE_DEFINITION_PREFIX):  # $TTL 3600   ; for example
            key, value = line.lstrip(VARIABLE_DEFINITION_PREFIX).split()
            variables[key.upper()] = value
            continue

        splitted_line = line.split()
        if line[0].isspace():                        # this is when the line key is the previous key
            splitted_line = [previous_record_name] + splitted_line

        ttl = None
        record_name, record_class, record_type = splitted_line[:3]
        if len(splitted_line) == LINE_HEADER_COUNT_WITHOUT_SPECIFIC_TTL:  # ttl should be taken from the default
            address, = splitted_line[3:]
        elif len(splitted_line) == LINE_HEADER_COUNT_WITH_SPECIFIC_TT:    # ttl is specified explicitly
            ttl, address = splitted_line[3:]
        else:
            raise InvalidZoneFileError(f"Line too long!! \n{line}")
        previous_record_name = record_name

        records.append((record_name, record_class, record_type, ttl, address))
        return records


def write_zone_file(parsed_zone_file: Dict) -> str:
    """

    :param parsed_zone_file:
    :return:
    """
