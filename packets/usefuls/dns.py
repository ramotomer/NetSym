from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

from scapy.layers.dns import DNSRR, DNSQR

from consts import COMPUTER
from exceptions import InvalidDomainHostnameError
from usefuls.attribute_renamer import define_attribute_aliases

T_Hostname = str


def validate_domain_hostname(hostname: T_Hostname) -> None:
    """
    Make sure the supplied hostname is valid
        valid:
            'hi', 'hello.com', 'www.google.com.', 'eshel.d7149.d8200.dom.'

        invalid:
            '', '.hello.com.', 'google..com', '.', 'eshel.d7149..', '192.168.1.2'
    """
    message = f"Invalid domain hostname!! '{hostname}'"
    split_hostname = hostname.split('.')

    if not hostname:
        raise InvalidDomainHostnameError(f"{message} is an empty string")

    if (('' in split_hostname) and (split_hostname[-1] != '')) or split_hostname.count('') > 1:
        raise InvalidDomainHostnameError(f"{message} contains multiple consecutive dots ('..')")

    if not all(part.isalnum() for part in split_hostname if part):
        raise InvalidDomainHostnameError(f"{message} - Invalid character in hostname! Only numbers and letters allowed!")

    if any((part and part[0].isnumeric()) for part in split_hostname):
        raise InvalidDomainHostnameError(f"{message} - Domain names must not start with a number!!")


def is_domain_hostname_valid(hostname: T_Hostname) -> bool:
    """same - but does not raises, returns the answer"""
    try:
        validate_domain_hostname(hostname)
    except InvalidDomainHostnameError:
        return False
    return True


def is_canonized(hostname: T_Hostname) -> bool:
    validate_domain_hostname(hostname)
    return hostname.endswith('.')


def canonize_domain_hostname(hostname: T_Hostname, seed: Optional[T_Hostname] = None) -> T_Hostname:
    """
    'example.dom'  -> 'example.dom.'
    'axempla.dom.' -> 'axempla.dom.'
    """
    validate_domain_hostname(hostname)
    if seed:
        validate_domain_hostname(seed)
    return f"{hostname.rstrip('.')}.{canonize_domain_hostname(seed) if seed else ''}"


def decanonize_domain_hostname(hostname: T_Hostname) -> T_Hostname:
    """
    'axempla.dom.' -> 'axempla.dom'
    'example.dom'  -> 'example.dom'
    """
    validate_domain_hostname(hostname)
    return hostname.rstrip('.')


@dataclass
class DomainHostname:
    """
    A class containing much of the logic necessary for domain hostnames
    """
    hostname: T_Hostname

    def __init__(self, hostname: T_Hostname) -> None:
        validate_domain_hostname(hostname)
        self.hostname = decanonize_domain_hostname(hostname)

    @property
    def canonized(self):
        return canonize_domain_hostname(self.hostname)

    @property
    def domains(self):
        """
        'tomer.noyman.fun.' -> ['noyman', 'fun']
        'hi'                -> []
        """
        return self.hostname.split('.', 1)[1].split('.') if self.hostname.count('.') >= 1 else []

    def endswith(self, domain_name: T_Hostname) -> bool:
        """
        Returns whether or not this hostname ends with a specified domain name

            ('tomer.noyman.com.', 'noyman.com.') -> True
            ('tomer.noyman.com.', 'man.com.')    -> False
        """
        domain_name = decanonize_domain_hostname(domain_name)
        if domain_name == self.hostname:
            return True
        return all(my_domain == other_domain for my_domain, other_domain in zip(reversed(self.domains), reversed(domain_name.split('.')))) and \
               self.domains


def default_tmp_query_output_file_path(name):
    return os.path.join(COMPUTER.FILES.CONFIGURATIONS.DNS_TMP_QUERY_RESULTS_DIR_PATH, name + '.json')


DNSResourceRecord = define_attribute_aliases(
    DNSRR,
    {
        "record_name":        "rrname",
        "record_type":        "type",
        "record_class":       "rclass",
        "time_to_live":       "ttl",
        "record_data_length": "rdlen",
        "record_data":        "rdata",
    }
)

DNSQueryRecord = define_attribute_aliases(
    DNSQR,
    {
        "query_name":         "qname",
        "query_type":         "qtype",
        "query_class":        "qclass",
    }
)


def dns_resource_record_to_list(dns_resource_records: DNSRR) -> List[DNSResourceRecord]:
    """
    Take in the raw scapy format and turn it to something that will be more fun to use

    Will put the values into a list, where each value is
    """
    return [
        DNSResourceRecord(
            record_name=       dns_resource_records[i].rrname,
            record_type=       dns_resource_records[i].type,
            record_class=      dns_resource_records[i].rclass,
            time_to_live=      dns_resource_records[i].ttl,
            record_data_length=dns_resource_records[i].rdlen,
            record_data=       dns_resource_records[i].rdata,
        )
        for i in range(len(dns_resource_records.layers()))
    ]
    # TODO: this method could be a little better - Make the `transform_to_indicative_attribute_names` of packets more generic, and it could cast
    #  the objects automatically


def list_to_dns_resource_record(list_: List[DNSResourceRecord]) -> DNSRR:
    """

    :param list_:
    :return:
    """
    returned = None
    for dns_resource_records in list_:
        layer = DNSRR(
            rrname= dns_resource_records.record_name,
            type=   dns_resource_records.record_type,
            rclass= dns_resource_records.record_class,
            ttl=    dns_resource_records.time_to_live,
            rdlen=  dns_resource_records.record_data_length,
            rdata = dns_resource_records.record_data,
        )
        returned = layer if returned is None else (returned / layer)
    return returned


def dns_query_record_to_list(dns_query_records: DNSQR) -> List[DNSQueryRecord]:
    """
    Take in the raw scapy format and turn it to something that will be more fun to use

    Will put the values into a list, where each value is
    """
    return [
        DNSQueryRecord(
            query_name=  dns_query_records[i].qname,
            query_type=  dns_query_records[i].qtype,
            query_class= dns_query_records[i].qclass,
        )
        for i in range(len(dns_query_records.layers()))
    ]


def list_to_dns_query(list_: List[DNSQueryRecord]) -> DNSQR:
    """

    :param list_:
    :return:
    """
    returned = None
    for dns_resource_records in list_:
        layer = DNSQR(
            qname=  dns_resource_records.query_name,
            qtype=  dns_resource_records.query_type,
            qclass= dns_resource_records.query_class,
        )
        returned = layer if returned is None else (returned / layer)
    return returned
