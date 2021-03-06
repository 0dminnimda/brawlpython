# -*- coding: utf-8 -*-

from brawlpython import SyncClient
from brawlpython.api_toolkit import unique, same
from configobj import ConfigObj
import pytest
import time


url_uuid = "http://httpbin.org/uuid"

config = ConfigObj("config.ini")
api_key = config["DEFAULT"].get("API_KEY")


@pytest.yield_fixture
def factory():
    client = None

    def maker(*args, **kwargs):
        nonlocal client
        client = SyncClient(*args, **kwargs)
        return client

    yield maker

    if client is not None:
        client.close()


@pytest.yield_fixture
def client(factory):
    return factory(api_key)


def test_sync_init():
    client = SyncClient(api_key)

    assert isinstance(client, SyncClient)


def test_closing(client):
    assert not client.closed

    for _ in 1, 2:
        client.close()

        assert client.closed


def no_test_cache(client):
    responses = [client._get(url_uuid) for _ in range(2)]
    assert same(responses)

    time.sleep(2)

    assert client._get(url_uuid) != responses[0]


def no_test_no_cache(factory):
    client = factory(api_key, use_cache=False)

    assert unique([client._get(url_uuid) for _ in range(2)])

    assert unique(client._gets([url_uuid] * 2))


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
