# -*- coding: utf-8 -*-

from brawlpython.sessions import SyncSession
from brawlpython.api_toolkit import unique, same
from configobj import ConfigObj
import pytest
import time


url_uuid = "http://httpbin.org/uuid"

config = ConfigObj("config.ini")
token = config["DEFAULT"]["API_KEY"]


@pytest.yield_fixture
def factory():
    client = None

    def maker(*args, **kwargs):
        nonlocal client
        client = SyncSession(*args, **kwargs)
        return client

    yield maker

    if client is not None:
        client.close()


@pytest.yield_fixture
def client(factory):
    return factory(token, cache_ttl=1)


def test_sync_init():
    client = SyncSession(token)

    assert isinstance(client, SyncSession)


def test_closing(client):
    assert not client.closed

    for _ in 1, 2:
        client.close()

        assert client.closed


def test_cache(client):
    responses = [client.get(url_uuid) for _ in range(2)]
    assert same(responses)

    time.sleep(2)

    assert client.get(url_uuid) != responses[0]


def test_no_cache(factory):
    client = factory(token, use_cache=False)

    assert unique([client.get(url_uuid) for _ in range(2)])

    assert unique(client.gets([url_uuid] * 2))


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
