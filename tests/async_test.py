# -*- coding: utf-8 -*-

import pytest
import brawlpython as bp


@pytest.fixture
def create_client(loop):
    client = None

    async def maker(*args, **kwargs):
        nonlocal client
        client = bp.AsyncClient(*args, **kwargs)
        return client

    yield maker

    if client is not None:
        loop.run_until_complete(client.close())


@pytest.fixture
def client(create_client, loop):
    return loop.run_until_complete(create_client())


async def test_any(client):
    assert not client.closed

    async with client.session.get("https://www.python.org/") as resp:
        assert resp.status == 200


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
