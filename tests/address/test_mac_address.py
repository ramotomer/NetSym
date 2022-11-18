import pytest

from NetSym.address.mac_address import MACAddress


@pytest.mark.parametrize(
    "mac, vendor",
    [
        ("00:11:22:33:44:55", "00:11:22"),
        ("ff:ff:ff:33:44:55", "ff:ff:ff"),
        ("00:00:00:00:00:00", "00:00:00"),
    ]
)
def test_vendor(mac, vendor):
    assert MACAddress(mac).vendor == vendor


@pytest.mark.parametrize(
    "mac, expected",
    [
        ("ff:ff:ff:ff:ff:ff", True),
        ("FF:FF:FF:FF:FF:FF", True),
        ("ff:Ff:FF:Ff:FF:fF", True),
        ("00:22:33:55:ff:ee", False),
        ("00:00:00:00:00:00", False),
    ]
)
def test_is_broadcast(mac, expected):
    assert MACAddress(mac).is_broadcast() is expected


@pytest.mark.parametrize(
    "expected",
    [
        "ff:ff:ff:ff:ff:ff",
        "FF:FF:FF:FF:FF:FF",
    ]
)
def test_broadcast(expected):
    assert MACAddress.broadcast() == MACAddress(expected)


def test_no_mac_and_is_no_mac():
    assert MACAddress.no_mac().is_no_mac()


@pytest.mark.parametrize(
    "mac",
    [
        "11:22:33:44:55:ff",
        "00:00:00:00:00:00",
        "AA:BB:CC:DD:EE:23",
    ]
)
def test_copy(mac):
    mac1 = MACAddress(mac)
    mac2 = MACAddress.copy(mac1)
    assert (mac1 == mac2) and (mac1 is not mac2)


@pytest.mark.parametrize(
    "mac, expected",
    [
        ("00:11:22:33:44:55", True),
        ("00:00:00:00:00:00", True),
        ("ff:ff:ff:ff:ff:ff", True),
        ("11:AA:bb:f3:ab:c7", True),
        ("aa:gg:hh:ii:kk:kk", False),
        ("11123423132434234", False),
        ("11-22-33-44-55-66", False),
        ("11:34",             False),
        ("",                  False),
        ("hello world",       False),
    ]
)
def test_is_valid(mac, expected):
    assert MACAddress.is_valid(mac) is expected


@pytest.mark.parametrize(
    "mac, expected",
    [
        ("00:11:22:33:44:55", b"\x00\x11\x22\x33\x44\x55"),
        ("ff:ff:ff:ff:ff:ff", b"\xff\xff\xff\xff\xff\xff"),
        ("00:00:00:00:00:00", b"\x00\x00\x00\x00\x00\x00"),
        ("a1:B3:f1:55:10:00", b"\xa1\xb3\xf1\x55\x10\x00"),
    ]
)
def test_as_bytes(mac, expected):
    assert MACAddress(mac).as_bytes() == expected


@pytest.mark.parametrize(
    "mac, expected",
    [
        ("00:11:22:33:44:55", 0x001122334455),
        ("ff:ff:ff:ff:ff:ff", 0xffffffffffff),
        ("00:00:00:00:00:00", 0x000000000000),
        ("a1:B3:f1:55:10:00", 0xa1b3f1551000),
    ]
)
def test_as_number(mac, expected):
    assert MACAddress(mac).as_number() == expected


@pytest.mark.parametrize(
    "mac, other, expected",
    [
        ("00:11:22:33:44:55", "00:11:22:33:44:55", True),
        ("ff:ff:ff:ff:ff:ff", "FF:fF:Ff:FF:ff:Ff", True),
        ("00:11:22:33:44:55", "a3:32:fd:de:a5:4a", False),
    ]
)
def test___eq__(mac, other, expected):
    assert (MACAddress(mac) == MACAddress(other)) is expected
