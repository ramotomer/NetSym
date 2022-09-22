from scapy.layers.dns import DNSRR, DNSQR

from usefuls.attribute_renamer import define_attribute_aliases

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
        "query_class":        "rclass",
    }
)


def dns_resource_record_to_list(dns_resource_records):
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


def dns_query_record_to_list(dns_query_records):
    """
    Take in the raw scapy format and turn it to something that will be more fun to use

    Will put the values into a list, where each value is
    """
    return [
        DNSQueryRecord(
            query_name=       dns_query_records[i].qname,
            query_type=       dns_query_records[i].qtype,
            query_class=      dns_query_records[i].qclass,
        )
        for i in range(len(dns_query_records.layers()))
    ]
