# -*- coding: utf-8 -*-

import pytest
import asyncio
from brawlpython import AsyncClient
from brawlpython.base_classes import AsyncWith, SyncWith, AsyncInitObject
from brawlpython.cache_utils import iscoro


async def test_async_with():
    async with AsyncWith() as async_with:
        assert isinstance(async_with, AsyncWith)

    assert async_with.test_close

    async_with = AsyncWith()
    await async_with.close()
    assert async_with.test_close

    with pytest.raises(TypeError):
        async with SyncWith():
            pass


def test_sync_with():
    with SyncWith() as sync_with:
        assert isinstance(sync_with, SyncWith)

    assert sync_with.test_close

    sync_with = SyncWith()
    sync_with.close()
    assert sync_with.test_close

    with pytest.raises(TypeError):
        with AsyncWith():
            pass


async def test_async_init():
    client = AsyncInitObject()

    assert iscoro(client)

    assert isinstance(await client, AsyncInitObject)


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
