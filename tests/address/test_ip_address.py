import pytest

from NetSym.address.ip_address import IPAddress
from exceptions import AddressTooLargeError


@pytest.mark.parametrize(
    "method_name, expected_string_ip, expected_subnet_mask",
    [
        ('broadcast',  "255.255.255.255", 32),
        ('no_address', "0.0.0.0",         0),
        ('loopback',   "127.0.0.1",       8),
    ]
)
def test_address_constructor(method_name, expected_string_ip, expected_subnet_mask):
    ip = getattr(IPAddress, method_name)()

    assert ip.string_ip == expected_string_ip
    assert ip.subnet_mask == expected_subnet_mask


@pytest.mark.parametrize(
    "ip1, ip2, expected",
    [
        ("1.1.1.1/24",   "1.1.1.2/24",  True),
        ("1.1.1.1/16",   "1.1.1.2/24",  True),
        ("1.1.2.1/23",   "1.1.1.2/23",  True),
        ("1.1.1.1/0",    "12.3.76.1/0", True),
        ("1.1.1.1/32",   "1.1.1.1/32",  True),
        ("1.1.2.1/24",   "1.1.1.2/24",  False),
        ("1.2.1.1/24",   "1.1.1.2/24",  False),
        ("7.1.1.1/24",   "1.1.1.2/24",  False),
        ("1.1.1.100/31", "1.1.1.1/31",  False),
    ]
)
def test_is_same_subnet(ip1, ip2, expected):
    assert (IPAddress(ip1).is_same_subnet(IPAddress(ip2))) is expected


# TODO: test is broadcast


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("192.168.1.2",     True),
        ("192.168.100.100", True),
        ("10.1.2.3",        True),
        ("10.0.0.1",        True),
        ("172.17.0.1",      True),
        ("193.167.1.1",     False),
        ("192.167.1.1",     False),
        ("1.1.1.1",         False),
        ("0.0.0.0",         False),
        ("255.255.255.255", False),
    ]
)
def test_is_private_address(ip, expected):
    assert IPAddress(ip).is_private_address() is expected


@pytest.mark.parametrize(
    "ip, expected, raises",
    [
        ("1.1.1.1/24",        "1.1.1.2",   False),
        ("4.4.6.2/24",        "4.4.6.3",   False),
        ("1.2.3.4/24",        "1.2.3.5",   False),
        ("1.1.10.255/16",     "1.1.11.0",  False),
        ("1.50.255.255/8",    "1.51.0.0",  False),

        ("1.1.1.255/24",      None,        True),
        ("1.1.1.3/30",        None,        True),
    ]
)
def test_increased(ip, expected, raises):
    if raises:
        with pytest.raises(AddressTooLargeError):
            IPAddress.increased(IPAddress(ip))

    else:
        assert IPAddress.increased(IPAddress(ip)) == IPAddress(expected)
