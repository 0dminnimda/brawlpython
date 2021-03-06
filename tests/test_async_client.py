# -*- coding: utf-8 -*-

import asyncio
from brawlpython import AsyncClient
from brawlpython.api_toolkit import unique, same
from brawlpython.cache_utils import iscoro
from configobj import ConfigObj
import pytest


url_uuid = "http://httpbin.org/uuid"

config = ConfigObj("config.ini")
api_key = config["DEFAULT"].get("API_KEY")


@pytest.fixture
def factory(loop):
    client = None

    async def maker(*args, **kwargs):
        nonlocal client
        client = await AsyncClient(*args, **kwargs)
        return client

    yield maker

    if client is not None:
        loop.run_until_complete(client.close())


@pytest.fixture
def client(factory, loop):
    return loop.run_until_complete(factory(api_key))


async def test_async_init():
    client = AsyncClient(api_key)

    assert iscoro(client)

    assert isinstance(await client, AsyncClient)


async def test_closing(client):
    assert not client.closed

    for _ in 1, 2:
        await client.close()

        assert client.closed


async def no_test_cache(client):
    responses = [await client._get(url_uuid) for _ in range(2)]
    assert same(responses)

    await asyncio.sleep(2)

    assert await client._get(url_uuid) != responses[0]


async def no_test_no_cache(factory):
    client = await factory(api_key, use_cache=False)

    assert unique([await client._get(url_uuid) for _ in range(2)])

    assert unique(await client._gets([url_uuid] * 2))


# FIXME: complete test
async def test_data_handler(factory):
    client = await factory(api_key, data_handler=lambda *x: None)

    await client._get(url_uuid)


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
