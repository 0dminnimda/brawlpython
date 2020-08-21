# -*- coding: utf-8 -*-

import pytest
import asyncio
from brawlpython.sessions import AsyncSession
from brawlpython.api_toolkit import unique, same
from brawlpython.cache_utils import iscoro
from configobj import ConfigObj


url_uuid = "http://httpbin.org/uuid"


# @pytest.yield_fixture
# def token():
config = ConfigObj("config.ini")
token = config["DEFAULT"]["API_KEY"]


@pytest.fixture
def factory(loop):
    client = None

    async def maker(*args, **kwargs):
        nonlocal client
        client = await AsyncSession(*args, **kwargs)
        return client

    yield maker

    if client is not None:
        loop.run_until_complete(client.close())


@pytest.fixture
def client(factory, loop):
    return loop.run_until_complete(factory(token, cache_ttl=1))


async def test_async_init():
    client = AsyncSession(token)

    assert iscoro(client)

    assert isinstance(await client, AsyncSession)


async def test_closing(client):
    assert not client.closed

    for _ in 1, 2:
        await client.close()

        assert client.closed


async def test_cache(client):
    responses = [await client.get(url_uuid) for _ in range(2)]
    assert same(responses)

    await asyncio.sleep(2)

    assert await client.get(url_uuid) != responses[0]


async def test_no_cache(factory):
    client = await factory(token, use_cache=False)

    assert unique([await client.get(url_uuid) for _ in range(2)])


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
