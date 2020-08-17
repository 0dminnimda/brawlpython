# -*- coding: utf-8 -*-

from aiohttp import ClientSession, TCPConnector, ClientTimeout
import asyncio
from cachetools import TTLCache
from requests import Session

from .api_toolkit import make_headers
from .async_init import AsyncInitObject
from .cache_utils import self_cache
from .exceptions import WITH_CODE, UnexpectedResponseCode

from typing import (
    Any,
    Coroutine,
    Dict,
    Generator,
    Generic,
    Iterable,
    List,
    Mapping,
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

def raise_for_status(self, url: str, code: int,
                     data: Mapping[str, Any]) -> None:
    if 200 <= code < 400:
        pass
    elif code in (400, 403, 404, 429, 500, 503):
        excp = next(filter(lambda x: x.code == code, WITH_CODE))

        raise excp(url, data.get("reason", ""), data.get("message", ""))
    else:
        raise UnexpectedResponseCode(
            url, code, data.get("reason", ""), data.get("message", ""))


class AsyncSession(AsyncInitObject):
    async def __init__(self, token: str, trust_env: bool = True,
                       cache_ttl: Union[int, float] = 60,
                       cache_limit: int = 1024,
                       use_cache: bool = True,
                       timeout: Union[int, float] = 30) -> None:
        headers = make_headers(token)
        loop = asyncio.get_event_loop()
        self.session = ClientSession(
            loop=loop,
            connector=TCPConnector(use_dns_cache=False, loop=loop),
            trust_env=trust_env,
            headers=headers,
            timeout=ClientTimeout(total=timeout),
        )

        self.cache = TTLCache(maxsize=cache_limit, ttl=cache_ttl)
        self.use_cache = use_cache

    async def close(self) -> None:
        """Close underlying connector.
        Release all acquired resources.
        """
        if not self.closed:
            # XXX: https://github.com/aio-libs/aiohttp/issues/1925
            await self.session.close()
            # Zero-sleep to allow underlying connections to close
            await asyncio.sleep(0)

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    raise_for_status = raise_for_status

    async def simple_get_json(self, url: str) -> Dict:
        async with self.session.get(url) as response:
            data = await response.json()

            self.raise_for_status(url, response.status, data)

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
                 cache_limit: int = 1024, use_cache: bool = True,
                 timeout: Union[int, float] = 30) -> None:
        self._closed = False

        headers = make_headers(token)
        self.session = Session()
        self.session.trust_env = trust_env
        self.session.headers.update(headers)

        self.cache = TTLCache(maxsize=cache_limit, ttl=cache_ttl)
        self.use_cache = use_cache

        self.timeout = timeout

    def close(self) -> None:
        """Closes all adapters and as such the session"""
        if not self.closed:
            self.session.close()
            self._closed = True

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self._closed

    raise_for_status = raise_for_status

    def simple_get_json(self, url: str) -> Dict:
        with self.session.get(url, timeout=self.timeout) as response:
            data = response.json()

            self.raise_for_status(url, response.status_code, data)

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
