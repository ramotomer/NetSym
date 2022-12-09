import pytest
from _pytest.monkeypatch import MonkeyPatch

from NetSym.address.ip_address import IPAddress
from NetSym.computing.internals.network_data_structures.dns_cache import DNSCache, DNSCacheItem
from tests.usefuls import mock_mainloop_time


@pytest.fixture
def example_dns_cache():
    return DNSCache({
        "www.google.com.":    DNSCacheItem(IPAddress("8.8.8.8"),     10, 1),
        "connect.Eshel.dom.": DNSCacheItem(IPAddress("60.102.1.16"), 20, 1),
        "tomer.fun.":         DNSCacheItem(IPAddress("192.168.1.2"), 30, 1),
    })


@pytest.mark.parametrize(
    "hostname, result_ip",
    [
        ("www.google.com.",    "8.8.8.8"),
        ("connect.Eshel.dom.", "60.102.1.16"),
    ]
)
def test___getitem__(example_dns_cache, hostname, result_ip):
    assert example_dns_cache[hostname].ip_address == result_ip


@pytest.mark.parametrize(
    "hostname, should_be_in",
    [
        ("www.google.com.",  True),
        ("tomer.fun.",       True),
        ("www.youtube.com.", False),
        ("www.google.com",   False),
        ("google.com.",      False),
    ]
)
def test___contains__(example_dns_cache, hostname, should_be_in):
    assert (hostname in example_dns_cache) is should_be_in


def test_add_item(example_dns_cache):
    with MonkeyPatch.context() as m:
        mocked_mainloop = mock_mainloop_time(m)
        mocked_mainloop.set_time(123)

        old_cache_len = len(example_dns_cache)
        example_dns_cache.add_item("hello.world.", IPAddress("1.2.3.4"), 100)

        assert old_cache_len + 1 == len(example_dns_cache)
        assert example_dns_cache["hello.world."].ip_address == "1.2.3.4"
        assert example_dns_cache["hello.world."].creation_time == 123


def test_forget_old_items(example_dns_cache):
    with MonkeyPatch.context() as m:
        mocked_mainloop = mock_mainloop_time(m)

        mocked_mainloop.set_time(11.1)
        example_dns_cache.forget_old_items()
        assert "www.google.com." not in example_dns_cache
        assert len(example_dns_cache) == 2

        mocked_mainloop.set_time(21.1)
        example_dns_cache.forget_old_items()
        assert "connect.Eshel.dom." not in example_dns_cache
        assert len(example_dns_cache) == 1

        mocked_mainloop.set_time(31.1)
        example_dns_cache.forget_old_items()
        assert len(example_dns_cache) == 0


def test_wipe(example_dns_cache):
    initial_length = len(example_dns_cache)
    example_dns_cache.wipe()

    assert initial_length != 0
    assert len(example_dns_cache) == 0
