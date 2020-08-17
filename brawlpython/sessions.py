# -*- coding: utf-8 -*-

from aiohttp import ClientSession, TCPConnector
import asyncio
from cachetools import TTLCache
from requests import Session

from .api_toolkit import make_headers
from .async_init import AsyncInitObject
from .cache_utils import self_cache

from typing import (
    Any,
    Coroutine,
    Dict,
    Generator,
    Generic,
    Iterable,
    List,
    Mapping,
    NoReturn,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

__all__ = (
    "AsyncSession",
    "SyncSession",
)


# XXX: in both functions I need to find a suitable cache_limit
# 1024 is a relatively random choice and
# has nothing to do with the desired behavior

class AsyncSession(AsyncInitObject):
    async def __init__(self, token: str, trust_env: bool = True,
                       cache_ttl: Union[int, float] = 60,
                       cache_limit: int = 1024,
                       use_cache: bool = True) -> None:
        headers = make_headers(token)
        loop = asyncio.get_event_loop()
        self.session = ClientSession(
            loop=loop,
            connector=TCPConnector(use_dns_cache=False, loop=loop),
            trust_env=trust_env,
            headers=headers,
        )

        self.cache = TTLCache(maxsize=cache_limit, ttl=cache_ttl)
        self.use_cache = use_cache

    async def close(self) -> None:
        """
        Close underlying connector.
        Release all acquired resources.
        """
        if not self.closed:
            # XXX: https://github.com/aio-libs/aiohttp/issues/1925
            await self.session.close()
            # Zero-sleep to allow underlying connections to close
            await asyncio.sleep(0)

    @property
    def closed(self) -> bool:
        """
        Is client session closed.
        A readonly property.
        """
        return self.session.closed

    async def simple_get_json(self, url: str) -> Dict:
        data = {}
        async with self.session.get(url) as response:
            data = await response.json()
        return data

    @self_cache(sync=False)
    async def cached_get_json(self, url: str) -> Dict:
        return await self.simple_get_json(url)

    async def get_json(self, url: str,
                       use_cache: Optional[bool] = None) -> Dict:
        if use_cache is None:
            use_cache = self.use_cache

        if use_cache:
            return await self.cached_get_json(url)
        else:
            return await self.simple_get_json(url)


class SyncSession:
    def __init__(self, token: str, trust_env: bool = True,
                 cache_ttl: Union[int, float] = 60,
                 cache_limit: int = 1024, use_cache: bool = True) -> None:
        self._closed = False

        headers = make_headers(token)
        self.session = Session()
        self.session.trust_env = trust_env
        self.session.headers.update(headers)

        self.cache = TTLCache(maxsize=cache_limit, ttl=cache_ttl)
        self.use_cache = use_cache

    def close(self) -> None:
        """
        Closes all adapters and as such the session
        """
        if not self.closed:
            self.session.close()
            self._closed = True

    @property
    def closed(self) -> bool:
        """
        Is client session closed.
        A readonly property.
        """
        return self._closed

    def simple_get_json(self, url: str) -> Dict:
        with self.session.get(url) as response:
            data = response.json()

        return data

    @self_cache(sync=True)
    def cached_get_json(self, url: str) -> Dict:
        return self.simple_get_json(url)

    def get_json(self, url: str, use_cache: Optional[bool] = None) -> Dict:
        if use_cache is None:
            use_cache = self.use_cache

        if use_cache:
            return self.cached_get_json(url)
        else:
            return self.simple_get_json(url)
