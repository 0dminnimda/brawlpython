# -*- coding: utf-8 -*-

import pytest
import asyncio
from brawlpython import AsyncClient


@pytest.fixture
def create_client(loop):
    client = None

    async def maker(*args, **kwargs):
        nonlocal client
        client = await AsyncClient(*args, **kwargs)
        return client

    yield maker

    if client is not None:
        loop.run_until_complete(client.close())


@pytest.fixture
def client(create_client, loop):
    return loop.run_until_complete(create_client("", ttl=4))


def unique(x):
    seen = list()
    return not any(i in seen or seen.append(i) for i in x)


async def test_closing(client):
    assert not client.closed

    await client.close()

    assert client.closed


async def test_async_init():
    client = AsyncClient("")

    assert asyncio.iscoroutine(client)

    await client


async def test_any(client):
    url = "http://httpbin.org/uuid"

    async with client.session.session.get(url) as resp:
        assert resp.status == 200

    a = [
        await (await client.session.session.get(url)).json()
        for i in range(10)
    ]

    assert unique(a)

    resp1 = await client.session.cached_request(url)
    resp2 = await client.session.cached_request(url)

    await asyncio.sleep(5)

    assert resp1 == resp2


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
