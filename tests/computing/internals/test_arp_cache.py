import pytest
from _pytest.monkeypatch import MonkeyPatch

from NetSym.address.ip_address import IPAddress
from NetSym.address.mac_address import MACAddress
from NetSym.computing.internals.arp_cache import ArpCache, ARPCacheItem
from NetSym.consts import COMPUTER
from tests.usefuls import mock_mainloop_time


@pytest.fixture
def example_cache():
    return ArpCache(
        {
            IPAddress("1.2.3.4"): ARPCacheItem(MACAddress("00:11:22:33:44:55"), 10, COMPUTER.ARP_CACHE.DYNAMIC),
            IPAddress("4.3.2.1"): ARPCacheItem(MACAddress("10:11:22:33:44:55"), 20, COMPUTER.ARP_CACHE.DYNAMIC),
            IPAddress("4.4.4.4"): ARPCacheItem(MACAddress("10:11:22:34:44:55"), 30, COMPUTER.ARP_CACHE.STATIC),
        }
    )


@pytest.mark.parametrize(
    "item_insertion_time, time_since, max_lifetime, should_be_removed",
    [
        (0,     0,   1,   False),
        (10000, 10,  100, False),
        (1,     10,  10,  False),
        (0,     10,  1,   True),
        (10,    10,  1,   True),
        (10000, 10,  1,   True),
    ]
)
def test_forget_old_items(item_insertion_time, time_since, max_lifetime, should_be_removed):
    with MonkeyPatch.context() as m:
        mocking_mainloop = mock_mainloop_time(m)

        cache = ArpCache({IPAddress("1.2.3.4"): ARPCacheItem(MACAddress("00:11:22:33:44:55"), item_insertion_time, COMPUTER.ARP_CACHE.DYNAMIC)})
        mocking_mainloop.set_time(item_insertion_time)
        mocking_mainloop.increase_time_by(time_since)
        cache.forget_old_items(max_lifetime)
        assert len(cache) == int(not should_be_removed)


@pytest.mark.parametrize(
    "method_name, expected_record_type",
    [
        ("add_dynamic", COMPUTER.ARP_CACHE.DYNAMIC),
        ("add_static",  COMPUTER.ARP_CACHE.STATIC),
    ]
)
def test_add(example_cache, method_name, expected_record_type):
    with MonkeyPatch.context() as m:
        mocking_mainloop = mock_mainloop_time(m)

        initial_cache_length = len(example_cache)
        initial_time = 1

        mocking_mainloop.set_time(initial_time)
        getattr(example_cache, method_name)("10.20.30.40",            "00:11:22:33:44:55")
        getattr(example_cache, method_name)(IPAddress("11.21.31.41"), MACAddress("01:11:21:31:41:51"))

        assert len(example_cache) == initial_cache_length + 2
        assert "10.20.30.40" in example_cache
        assert example_cache["10.20.30.40"].type == expected_record_type
        assert example_cache["10.20.30.40"].time == initial_time


@pytest.mark.parametrize(
    "only_remove_dynamic_entries, result_length",
    [
        (True,  1),
        (False, 0),
    ]
)
def test_wipe(example_cache, only_remove_dynamic_entries, result_length):
    initial_cache_length = len(example_cache)
    example_cache.wipe(only_remove_dynamic_entries)
    assert len(example_cache) != initial_cache_length
    assert len(example_cache) == result_length


@pytest.mark.parametrize(
    "ip, result",
    [
        ("1.2.3.4",            True),
        ("4.3.2.1",            True),
        (IPAddress("4.4.4.4"), True),
        (IPAddress("9.8.7.7"), False),
        ("12.23.34.45",        False),
        ("255.255.255.255",    False),
    ]
)
def test_contains(example_cache, ip, result):
    assert (ip in example_cache) is result


@pytest.mark.parametrize(
    "ip, mac, time, type_, raises",
    [
        ("1.2.3.4",            "00:11:22:33:44:55", 10,   COMPUTER.ARP_CACHE.DYNAMIC, None),
        (IPAddress("4.3.2.1"), "10:11:22:33:44:55", 20,   COMPUTER.ARP_CACHE.DYNAMIC, None),
        ("5.5.5.5",            None,                None, None,                       KeyError),
    ]
)
def test_getitem(example_cache, ip, mac, time, type_, raises):
    if raises is not None:
        with pytest.raises(raises):
            _ = example_cache[ip]
        return

    assert example_cache[ip].mac == mac
    assert example_cache[ip].time == time
    assert example_cache[ip].type == type_
