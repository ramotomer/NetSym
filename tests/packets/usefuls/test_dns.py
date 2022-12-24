import pytest

from NetSym.consts import OPCODES
from NetSym.exceptions import InvalidDomainHostnameError
from NetSym.packets.usefuls.dns import get_dns_opcode, validate_domain_hostname, is_domain_hostname_valid, is_canonized, canonize_domain_hostname, \
    decanonize_domain_hostname, domain_hostname_split
from tests.usefuls import example_dns

hostname_validity_tests = [
    ('hello.com',              True),
    ('www.google.com.',        True),
    ('eshel.d7149.d8200.dom.', True),
    ('hi',                     True),
    ('',                       False),
    ('.hello.com.',            False),
    ('google..com',            False),
    ('.',                      False),
    ('eshel.d7149..',          False),
    ('192.168.1.2',            False),
]


def test_get_dns_opcode():
    dns_query = example_dns()
    dns_error = example_dns()
    dns_error.return_code = OPCODES.DNS.RETURN_CODES.NAME_ERROR
    dns_reply = example_dns(is_query=False)

    query_opcode = get_dns_opcode(dns_query)
    error_opcode = get_dns_opcode(dns_error)
    reply_opcode = get_dns_opcode(dns_reply)

    assert query_opcode == OPCODES.DNS.QUERY
    assert error_opcode == OPCODES.DNS.SOME_ERROR
    assert reply_opcode == OPCODES.DNS.ANSWER


@pytest.mark.parametrize(
    "hostname, is_valid",
    hostname_validity_tests,
)
def test_validate_domain_hostname(hostname, is_valid):
    if not is_valid:
        with pytest.raises(InvalidDomainHostnameError):
            validate_domain_hostname(hostname)
        return

    validate_domain_hostname(hostname)


@pytest.mark.parametrize(
    "hostname, result",
    hostname_validity_tests,
)
def test_is_domain_hostname_valid(hostname, result):
    assert is_domain_hostname_valid(hostname) is result


@pytest.mark.parametrize(
    "hostname, result",
    [
        ("com.",        True),
        ("com",         False),
        ("google.com.", True),
        ("google.com",  False),
    ]
)
def test_is_canonized(hostname, result):
    assert is_canonized(hostname) is result


@pytest.mark.parametrize(
    "hostname, zone_origin, result",
    [
        ('example.dom',  None,           'example.dom.'),
        ('example.dom.', None,           'example.dom.'),
        ('@',            'example.dom.', 'example.dom.'),
    ]
)
def test_canonize_domain_hostname(hostname, zone_origin, result):
    assert canonize_domain_hostname(hostname, zone_origin) == result


@pytest.mark.parametrize(
    "hostname, zone_origin, error",
    [
        ('@', None, InvalidDomainHostnameError),
    ]
)
def test_canonize_domain_hostname__fail(hostname, zone_origin, error):
    with pytest.raises(error):
        canonize_domain_hostname(hostname, zone_origin)


@pytest.mark.parametrize(
    "hostname, result",
    [
        ('example.dom',  'example.dom'),
        ('example.dom.', 'example.dom'),
    ]
)
def test_canonize_domain_hostname__success(hostname, result):
    assert decanonize_domain_hostname(hostname) == result


@pytest.mark.parametrize(
    "hostname, result",
    [
        ('this.is.test.', ['this', 'is', 'test']),
        ('this.test.',    ['this', 'test']),
        ('hi',            []),
    ]
)
def test_domain_hostname_split(hostname, result):
    assert domain_hostname_split(hostname) == result


# def test_does_domain_hostname_end_with(hostname, domain_name, zone_origin = None):
#     """
#     Returns whether or not this hostname ends with a specified domain name
# 
#         ('tomer.noyman.com.', 'noyman.com.') -> True
#         ('tomer.noyman.com.', 'man.com.')    -> False
#     """
#     domain_name = canonize_domain_hostname(domain_name, zone_origin)
#     if len(domain_hostname_split(domain_name)) > len(domain_hostname_split(hostname)):  # ^ `domain_name` cannot be longer!
#         return False
# 
#     return all(my_domain == other_domain for my_domain, other_domain in
#                zip(reversed(domain_hostname_split(hostname)), reversed(domain_hostname_split(domain_name))))
# 
# 
# def test_default_tmp_query_output_file_path(name):
#     return os.path.join(COMPUTER.FILES.CONFIGURATIONS.DNS_TMP_QUERY_RESULTS_DIR_PATH, name + '.json')
# 
# 
# DNSResourceRecord = define_attribute_aliases(
#     DNSRR,
#     {
#         "record_name":        "rrname",
#         "record_type":        "type",
#         "record_class":       "rclass",
#         "time_to_live":       "ttl",
#         "record_data_length": "rdlen",
#         "record_data":        "rdata",
#     }
# )
# 
# DNSQueryRecord = define_attribute_aliases(
#     DNSQR,
#     {
#         "query_name":         "qname",
#         "query_type":         "qtype",
#         "query_class":        "qclass",
#     }
# )
# 
# 
# def test_dns_resource_record_to_list(dns_resource_records):
#     """
#     Take in the raw scapy format and turn it to something that will be more fun to use
# 
#     Will put the values into a list, where each value is
#     """
#     return [
#         DNSResourceRecord(
#             record_name=       dns_resource_records[i].rrname,
#             record_type=       dns_resource_records[i].type,
#             record_class=      dns_resource_records[i].rclass,
#             time_to_live=      dns_resource_records[i].ttl,
#             record_data_length=dns_resource_records[i].rdlen,
#             record_data=       dns_resource_records[i].rdata,
#         )
#         for i in range(len(dns_resource_records.layers()))
#     ]
#
# def test_list_to_dns_resource_record(list_):
#     """
# 
#     :param list_:
#     :return:
#     """
#     returned = None
#     for dns_resource_records in list_:
#         layer = DNSRR(
#             rrname= dns_resource_records.record_name,
#             type=   dns_resource_records.record_type,
#             rclass= dns_resource_records.record_class,
#             ttl=    dns_resource_records.time_to_live,
#             rdlen=  dns_resource_records.record_data_length,
#             rdata = dns_resource_records.record_data,
#         )
#         returned = layer if returned is None else (returned / layer)
#     return returned
# 
# 
# def test_dns_query_record_to_list(dns_query_records):
#     """
#     Take in the raw scapy format and turn it to something that will be more fun to use
# 
#     Will put the values into a list, where each value is
#     """
#     return [
#         DNSQueryRecord(
#             query_name=  dns_query_records[i].qname,
#             query_type=  dns_query_records[i].qtype,
#             query_class= dns_query_records[i].qclass,
#         )
#         for i in range(len(dns_query_records.layers()))
#     ]
# 
# 
# def test_list_to_dns_query(list_):
#     """
# 
#     :param list_:
#     :return:
#     """
#     returned = None
#     for dns_resource_records in list_:
#         layer = DNSQR(
#             qname=  dns_resource_records.query_name,
#             qtype=  dns_resource_records.query_type,
#             qclass= dns_resource_records.query_class,
#         )
#         returned = layer if returned is None else (returned / layer)
#     return returned
