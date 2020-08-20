# -*- coding: utf-8 -*-

from aiohttp import ClientSession, TCPConnector, ClientTimeout
import asyncio
from cachetools import TTLCache
from requests import Session

from .api_toolkit import make_headers, multiparams, multiparams_classcache
from .base_classes import AsyncInitObject, AsyncWith, SyncWith
from .cache_utils import classcache, somecachedmethod
from .exceptions import WITH_CODE, UnexpectedResponseCode
from .typedefs import URLS, L, R

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

import time 

__all__ = (
    "AsyncSession",
    "SyncSession",
)


# XXX: in both functions I need to find a suitable cache_limit
# 1024 is a relatively random choice and
# has nothing to do with the desired behavior

def raise_for_status(self, url: str, code: int,
                     data: Mapping[str, Any]) -> None:

    if code == 200:
        pass
    else:
        excp = next(filter(lambda x: x.code == code, WITH_CODE), None)
        if excp is not None:
            raise excp(url, data.get("reason", ""), data.get("message", ""))
        else:
            raise UnexpectedResponseCode(
                url, code, data.get("reason", ""), data.get("message", ""))


class AsyncSession(AsyncInitObject, AsyncWith):
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

        if use_cache:
            self.cache = TTLCache(maxsize=cache_limit, ttl=cache_ttl)
        else:
            self.cache = None
        self.use_cache = use_cache

    async def close(self) -> None:
        """Close underlying connector.
        Release all acquired resources.
        """
        if not self.closed:
            # XXX: https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await self.session.close()
            # Zero-sleep to allow underlying connections to close
            await asyncio.sleep(0.250)

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    raise_for_status = raise_for_status

    @somecachedmethod
    async def _get(self, url: str) -> R:
        time_start = time.time()
        async with self.session.get(url) as response:
            time_end = time.time()
            code = response.status
            text = await response.text()

        get_items = data.get("items")
        if get_items is not None and isinstance(get_items, list):
            return get_items
        return data

    @multiparams_classcache
    async def _get_jsons(self, urls: URLS) -> L:
        # in reality only one url and use_cache
        return await self.get_json(urls)

    async def get_jsons(self, urls: URLS) -> L:
        self._get_jsons(urls)


class SyncSession(SyncWith):
    def __init__(self, token: str, trust_env: bool = True,
                 cache_ttl: Union[int, float] = 60,
                 cache_limit: int = 1024, use_cache: bool = True,
                 timeout: Union[int, float] = 30) -> None:
        self._closed = False

        headers = make_headers(token)
        self.session = Session()
        self.session.trust_env = trust_env
        self.session.headers.update(headers)

        if use_cache:
            self.cache = TTLCache(maxsize=cache_limit, ttl=cache_ttl)
        else:
            self.cache = None
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

    def simple_get_json(self, url: str) -> R:
        with self.session.get(url, timeout=self.timeout) as response:
            data = response.json()

            self.raise_for_status(url, response.status_code, data)

        get_items = data.get("items")
        if get_items is not None and isinstance(get_items, list):
            return get_items
        return data

    @multiparams
    def simple_get_jsons(self, urls: URLS) -> L:
        return simple_get_json(urls)  # in reality only one url

    @classcache
    def cached_get_json(self, url: str) -> R:
        return self.simple_get_json(url)

    @multiparams
    def cached_get_jsons(self, urls: URLS) -> L:
        return self.cached_get_json(urls)  # in reality only one url

    def get_json(self, url: str, use_cache: Optional[bool] = None) -> R:
        if use_cache is None:
            use_cache = self.use_cache

        if use_cache:
            return self.cached_get_json(url)
        else:
            return self.simple_get_json(url)

    @multiparams
    def get_jsons(self, urls: URLS,
                  use_caches: Optional[Union[List[bool], bool]] = None) -> L:

        # in reality only one url and use_cache
        return self.get_json(urls, use_caches)
