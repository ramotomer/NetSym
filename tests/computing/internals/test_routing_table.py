import pytest

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.routing_table import RoutingTable, RoutingTableItem
from NetSym.consts import ADDRESSES
from NetSym.exceptions import *


@pytest.fixture
def example_table():
    return RoutingTable(
        {
            IPAddress("0.0.0.0/0"):       RoutingTableItem(IPAddress("2.2.2.1"), IPAddress("2.2.2.200")),
            IPAddress("1.0.0.0/8"):       RoutingTableItem(IPAddress("1.4.4.1"), IPAddress("1.4.4.200")),
            IPAddress("2.2.2.0/24"):      RoutingTableItem(IPAddress("2.2.2.1"), IPAddress("2.2.2.200")),
            IPAddress("1.2.3.0/24"):      RoutingTableItem(IPAddress("1.2.3.1"), IPAddress("1.2.3.200")),
            IPAddress("192.168.3.0/24"):  RoutingTableItem(ADDRESSES.IP.ON_LINK, IPAddress("192.168.3.200")),
            IPAddress("192.168.2.0/24"):  RoutingTableItem(ADDRESSES.IP.ON_LINK, IPAddress("192.168.2.200")),
            IPAddress("192.168.0.0/16"):  RoutingTableItem("192.168.10.254",     IPAddress("192.168.10.200")),
        }
    )


@pytest.fixture
def example_table_without_default_gateway():
    return RoutingTable(
        {
            IPAddress("1.0.0.0/8"):      RoutingTableItem(IPAddress("1.4.4.1"), IPAddress("1.4.4.200")),
            IPAddress("2.2.2.0/24"):     RoutingTableItem(IPAddress("2.2.2.1"), IPAddress("2.2.2.200")),
            IPAddress("1.2.3.0/24"):     RoutingTableItem(IPAddress("1.2.3.1"), IPAddress("1.2.3.200")),
            IPAddress("192.168.3.0/24"): RoutingTableItem(ADDRESSES.IP.ON_LINK, IPAddress("192.168.3.200")),
            IPAddress("192.168.2.0/24"): RoutingTableItem(ADDRESSES.IP.ON_LINK, IPAddress("192.168.2.200")),
            IPAddress("192.168.0.0/16"): RoutingTableItem("192.168.10.254",     IPAddress("192.168.10.200")),
        }
    )


def test_default_gateway(example_table):
    assert RoutingTable().default_gateway is None
    gateway = example_table.default_gateway
    assert isinstance(gateway, RoutingTableItem)
    assert gateway.ip_address   == "2.2.2.1"
    assert gateway.interface_ip == "2.2.2.200"


def test_set_default_gateway(example_table_without_default_gateway):
    default_gateway, interface_to_default_gateway = IPAddress("8.8.8.1"), IPAddress("8.8.8.200")
    example_table_without_default_gateway.set_default_gateway(default_gateway, interface_to_default_gateway)

    assert example_table_without_default_gateway.default_gateway.ip_address   == default_gateway
    assert example_table_without_default_gateway.default_gateway.interface_ip == interface_to_default_gateway


# def test_create_default(cls, computer: Computer, expect_normal_gateway: bool = True):
#     """
#     This is a constructor class method.
#     Creates a default routing table for a given `Computer`.
#     :param computer: a `Computer` object.
#     :param expect_normal_gateway: whether or not to set the gateway to be the expected one (192.168.1.1 for example)
#     :return: a `RoutingTable` object.
#     """
#     try:
#         main_interface = get_the_one_with_raise(computer.interfaces, lambda i: i.has_ip(), NoSuchInterfaceError)
#     except NoSuchInterfaceError:
#         return cls()    # if there is no interface with an IP address
#
#     returned = cls()
#
#     if expect_normal_gateway:
#         gateway = main_interface.get_ip().expected_gateway()  # the expected IP address of a gateway in that subnet.
#         returned.set_default_gateway(gateway, main_interface.get_ip())
#
#     for interface in computer.interfaces:
#         if interface.has_ip():
#             returned.route_add(interface.get_ip().subnet(), ADDRESSES.IP.ON_LINK, IPAddress.copy(interface.get_ip()))
#             returned.route_add(IPAddress(interface.get_ip().string_ip + "/32"),
#                                IPAddress.copy(computer.loopback.get_ip()),
#                                IPAddress.copy(computer.loopback.get_ip()))
#
#     return returned

@pytest.mark.parametrize(
    "dst_ip, gateway_ip, interface_ip",
    [
        ("0.0.0.0/0",                 "1.1.1.1",            "1.2.3.4"),
        ("1.0.0.0/8",                 "1.2.3.4",            "1.9.9.9"),
        (IPAddress("192.168.1.1/32"), ADDRESSES.IP.ON_LINK, "192.168.1.200"),
        (IPAddress("192.168.1.3/32"), ADDRESSES.IP.ON_LINK, IPAddress("192.168.1.200")),
        (IPAddress("192.168.1.3/32"), IPAddress("1.1.1.1"), IPAddress("1.1.1.2")),
    ]
)
def test_route_add(example_table, dst_ip, gateway_ip, interface_ip):
    example_table.route_add(dst_ip, gateway_ip, interface_ip)

    assert dst_ip in example_table
    assert isinstance(example_table[dst_ip], RoutingTableItem)
    assert example_table[dst_ip].interface_ip == IPAddress(interface_ip)


@pytest.mark.parametrize(
    "dst_ip, gateway_ip, interface_ip",
    [
        ("9.0.0.0/8",                 "9.2.3.4",            "9.9.9.9"),
        (IPAddress("192.168.1.1/32"), ADDRESSES.IP.ON_LINK, "192.168.1.200"),
        (IPAddress("192.168.1.3/32"), ADDRESSES.IP.ON_LINK, IPAddress("192.168.1.200")),
        (IPAddress("192.168.1.3/16"), IPAddress("1.1.2.1"), IPAddress("1.1.1.2")),
    ]
)
def test_route_delete(example_table, dst_ip, gateway_ip, interface_ip):
    with pytest.raises(RoutingTableError):
        example_table.route_delete(dst_ip)

    example_table.route_add(dst_ip, gateway_ip, interface_ip)
    example_table.route_delete(dst_ip)
    assert dst_ip not in example_table.dictionary


def test_add_interface(example_table):
    interface_ip = IPAddress("1.2.30.4/24")

    example_table.add_interface(interface_ip)
    assert "1.2.30.4/32" in map(repr, example_table.dictionary.keys())
    assert "1.2.30.0/24" in map(repr, example_table.dictionary.keys())
    assert example_table["1.2.30.0/24"].interface_ip == interface_ip


def test_delete_interface(example_table):
    interface_ip = IPAddress("1.2.30.4/24")
    dictionary_before_actions = {**example_table.dictionary}

    example_table.add_interface(interface_ip)
    example_table.delete_interface(interface_ip)
    assert "1.2.30.4/32" not in map(repr, example_table.dictionary.keys())
    assert "1.2.30.0/24" not in map(repr, example_table.dictionary.keys())

    assert example_table.dictionary == dictionary_before_actions


@pytest.mark.parametrize(
    "item, result_gateway, result_interface, raises",
    [
        ("192.168.3.1",   ADDRESSES.IP.ON_LINK, "192.168.3.200",  False),
        ("192.168.2.1",   ADDRESSES.IP.ON_LINK, "192.168.2.200",  False),
        ("1.200.200.70",  "1.4.4.1",            "1.4.4.200",      False),
        ("1.1.1.1",       "1.4.4.1",            "1.4.4.200",      False),
        ("192.168.30.1",  "192.168.10.254",     "192.168.10.200", False),
        ("5.5.5.5",       None,                 None,             True),
        ("2.2.200.2",     None,                 None,             True),
        ("192.167.1.1",   None,                 None,             True),
    ]
)
def test_getitem(example_table_without_default_gateway, item, result_gateway, result_interface, raises):
    if raises:
        with pytest.raises(RoutingTableCouldNotRouteToIPAddress):
            _ = example_table_without_default_gateway[item]
        return

    result = example_table_without_default_gateway[item]
    assert (result.ip_address  == result_gateway) if result_gateway is not ADDRESSES.IP.ON_LINK else (result.ip_address == item)
    assert result.interface_ip == result_interface


@pytest.mark.parametrize(
    "item, result",
    [
        ("1.1.1.1",       True),
        ("192.168.3.1",   True),
        ("192.168.2.1",   True),
        ("192.168.30.1",  True),
        ("1.200.200.70",  True),
        ("5.5.5.5",       False),
        ("2.2.200.2",     False),
        ("192.167.1.1",   False),
    ]
)
def test_contains(example_table_without_default_gateway, item, result):
    assert (item in example_table_without_default_gateway) is result


def test_dict_save(example_table):
    result = {
        'class': 'RoutingTable',
        'dict': {
            '0.0.0.0/0':      ['2.2.2.1',            '2.2.2.200'],
            '2.2.2.0/24':     ['2.2.2.1',            '2.2.2.200'],
            '1.2.3.0/24':     ['1.2.3.1',            '1.2.3.200'],
            '192.168.3.0/24': [ADDRESSES.IP.ON_LINK, '192.168.3.200'],
            '192.168.2.0/24': [ADDRESSES.IP.ON_LINK, '192.168.2.200'],
            '1.0.0.0/8':      ['1.4.4.1',            '1.4.4.200'],
            '192.168.0.0/16': ['192.168.10.254',     '192.168.10.200']
        }
    }

    assert example_table.dict_save() == result


def test_from_dict_load(example_table):
    dict_ = {
        'class': 'RoutingTable',
        'dict': {
            '0.0.0.0/0':      ['2.2.2.1',            '2.2.2.200'],
            '2.2.2.0/24':     ['2.2.2.1',            '2.2.2.200'],
            '1.2.3.0/24':     ['1.2.3.1',            '1.2.3.200'],
            '192.168.3.0/24': [ADDRESSES.IP.ON_LINK, '192.168.3.200'],
            '192.168.2.0/24': [ADDRESSES.IP.ON_LINK, '192.168.2.200'],
            '1.0.0.0/8':      ['1.4.4.1',            '1.4.4.200'],
            '192.168.0.0/16': ['192.168.10.254',     '192.168.10.200']
        }
    }

    assert RoutingTable.from_dict_load(dict_).dictionary == example_table.dictionary
