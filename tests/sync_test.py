# -*- coding: utf-8 -*-

import pytest
from brawlpython import SyncClient


@pytest.yield_fixture
def create_client():
    client = None

    def maker(*args, **kwargs):
        nonlocal client
        client = SyncClient(*args, **kwargs)
        return client

    yield maker

    if client is not None:
        client.close()


@pytest.yield_fixture
def client(create_client):
    return create_client("")


def test_closing(client):
    assert not client.closed

    client.close()

    assert client.closed


def test_any(client):
    with client.session.get("https://www.python.org/") as resp:
        assert resp.status_code == 200


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
