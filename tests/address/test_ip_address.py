import pytest

from NetSym.address.ip_address import IPAddress
from NetSym.exceptions import AddressTooLargeError


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
        ("1.1.0.1/23",   "1.1.1.2/23",  True),
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


# TODO: test is_broadcast


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


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("1.1.1.1/24",     "1.1.1.1"),
        ("1.1.1.250/24",   "1.1.1.1"),
        ("1.1.1.0/16",     "1.1.1.1"),
        ("10.168.1.100/8", "10.168.1.1"),
    ]
)
def test_expected_gateway(ip, expected):
    assert IPAddress(ip).expected_gateway() == IPAddress(expected)


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("1.1.1.1/24",           "1.1.1.0/24"),
        ("1.1.1.0/24",           "1.1.1.0/24"),
        ("1.1.1.1/16",           "1.1.0.0/16"),
        ("3.4.5.7/8",            "3.0.0.0/8"),
        ("250.2.2.2/1",          "128.0.0.0/1"),
        ("255.255.255.255/24",   "255.255.255.0/24"),
    ]
)
def test_subnet(ip, expected):
    assert IPAddress(ip).subnet() == IPAddress(expected)


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("1.1.1.1/24",     "1.1.1.255"),
        ("1.1.1.1/16",     "1.1.255.255"),
        ("1.1.1.1/8",      "1.255.255.255"),
        ("192.168.1.1/20", "192.168.15.255"),
        ("1.168.2.14/1",   "127.255.255.255"),
    ]
)
def test_subnet_broadcast(ip, expected):
    assert IPAddress(ip).subnet_broadcast() == IPAddress(expected)


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("1.1.1.1",         b"\x01\x01\x01\x01"),
        ("255.255.255.255", b"\xff\xff\xff\xff"),
        ("192.168.1.2",     b"\xc0\xa8\x01\x02"),
        ("0.0.0.0",         b"\x00\x00\x00\x00"),
    ]
)
def test_as_bytes(ip, expected):
    assert IPAddress.as_bytes(ip) == expected


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("1.1.1.1",         True),
        ("192.168.1.2",     True),
        ("10.0.0.0",        True),
        ("0.0.0.0",         True),
        ("255.255.255.255", True),
        ("1.2.3.4.5.6",     False),
        ("1.2.3",           False),
        ("1.2.3.5f",        False),
        ("3-4-5-6",         False),
        ("hello world",     False),
    ]
)
def test_is_valid(ip, expected):
    assert IPAddress.is_valid(ip) is expected


@pytest.mark.parametrize(
    "mask, expected",
    [
        ("30", True),
        ("24", True),
        ("16", True),
        ("8",  True),
        ("2",  True),
        ("0",  True),
        (24,   False),
        (None, False),
        ("33", False),
        ("-3", False),
    ]
)
def test_is_valid_subnet_mask(mask, expected):
    assert IPAddress.is_valid_subnet_mask(mask) is expected


@pytest.mark.parametrize(
    "number, expected",
    [
        (31, "255.255.255.254"),
        (24, "255.255.255.0"),
        (21, "255.255.248.0"),
        (16, "255.255.0.0"),
        (8,  "255.0.0.0"),
        (1,  "128.0.0.0"),
        (0,  "0.0.0.0"),
    ]
)
def test_mask_from_number(number, expected):
    assert IPAddress.mask_from_number(number) == expected


@pytest.mark.parametrize(
    "ip, expected",
    [
        ('1.1.1.1',         '0b00000001000000010000000100000001'),
        ('255.255.255.255', '0b11111111111111111111111111111111'),
        ('192.168.1.2',     '0b11000000101010000000000100000010'),
        ('0.0.0.0',         '0b00000000000000000000000000000000'),
    ]
)
def test_is_bits(ip, expected):
    assert IPAddress.as_bits(ip) == expected


@pytest.mark.parametrize(
    "bits, ip",
    [
        ('0b00000001000000010000000100000001', '1.1.1.1'),
        ('0b11111111111111111111111111111111', '255.255.255.255'),
        ('0b11000000101010000000000100000010', '192.168.1.2'),
        ('0b00000000000000000000000000000000', '0.0.0.0'),
    ]
)
def test_from_bites(bits, ip):
    assert IPAddress.from_bits(bits) == IPAddress(ip)


@pytest.mark.parametrize(
    "ip",
    [
        "1.1.1.1",
        "255.255.255.255",
        "192.168.1.2",
        "0.0.0.0",
    ]
)
def test_copy(ip):
    ip_address = IPAddress(ip)
    copy = IPAddress.copy(ip_address)
    assert (copy == ip_address) and (copy is not ip_address)
