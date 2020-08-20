# -*- coding: utf-8 -*-

from aiohttp import ClientSession, TCPConnector, ClientTimeout
import asyncio
from cachetools import TTLCache
from functools import update_wrapper
from requests import Session

from .api_toolkit import make_headers, multiparams, multiparams_classcache
from .base_classes import AsyncInitObject, AsyncWith, SyncWith
from .cache_utils import classcache, somecachedmethod, iscorofunc
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

import orjson
import time

__all__ = (
    "AsyncSession",
    "SyncSession",
)


# XXX: in both functions I need to find a suitable cache_limit
# 1024 is a relatively random choice and
# has nothing to do with the desired behavior

def _raise_for_status(self, url: str, code: int,
                      data: Mapping[str, Any]) -> None:

    excp = next(filter(lambda x: x.code == code, WITH_CODE), None)
    if excp is not None:
        raise excp(url, data.get("reason", ""), data.get("message", ""))
    else:
        raise UnexpectedResponseCode(
            url, code, data.get("reason", ""), data.get("message", ""))


def decor_get(func):
    if iscorofunc:
        async def wrapper(self, url: Any, *args: Any, **kwargs: Any) -> Any:
            for i in self._attempts:
                code, data = await func(self, url, *args, **kwargs)

                if code == 200:
                    get_items = data.get("items")
                    if get_items is not None and isinstance(get_items, list):
                        return get_items
                    return data
                elif i == 0:
                    self.raise_for_status(url, code, data)
            raise RuntimeError(
                "self._attempts argument was changed"
                " causing it to work incorrectly")
    else:
        def wrapper(self, url: Any, *args: Any, **kwargs: Any) -> Any:
            for i in self._attempts:
                code, data = func(self, url, *args, **kwargs)

                if code == 200:
                    get_items = data.get("items")
                    if get_items is not None and isinstance(get_items, list):
                        return get_items
                    return data
                elif i == 0:
                    self.raise_for_status(url, code, data)
            raise RuntimeError(
                "self._attempts argument was changed"
                " causing it to work incorrectly")
    return update_wrapper(wrapper, func)


class AsyncSession(AsyncInitObject, AsyncWith):
    async def __init__(self, token: str, trust_env: bool = True,
                       cache_ttl: Union[int, float] = 60,
                       cache_limit: int = 1024,
                       use_cache: bool = True,
                       timeout: Union[int, float] = 30,
                       repeat_failed: int = 3) -> None:
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

        if repeat_failed > 1:
            self._attempts = range(repeat_failed - 1, -1, -1)
        else:
            self._attempts = (0)

    async def close(self) -> None:
        """Close underlying connector.
        Release all acquired resources.
        """
        if not self.closed:
            # XXX: https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await self.session.close()
            # Zero-sleep to allow underlying connections to close
            await asyncio.sleep(0.300)

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    raise_for_status = _raise_for_status

    async def _simple_get(self, url: str) -> Tuple[int, str]:
        # time_start = time.time()
        async with self.session.get(url) as response:
            # time_end = time.time()
            code = response.status
            data = orjson.loads(await response.text())

        return code, data  # , time_start, time_end

    _cached_get = classcache(_simple_get)
    _multi_get = multiparams_classcache(_simple_get)

    _get = decor_get(_cached_get)
    _gets = decor_get(_multi_get)

    async def get(self, url: str) -> R:
        return await self._get(url)

    async def gets(self, urls: URLS) -> L:
        return await self._gets(url)


class SyncSession(SyncWith):
    def __init__(self, token: str, trust_env: bool = True,
                 cache_ttl: Union[int, float] = 60,
                 cache_limit: int = 1024, use_cache: bool = True,
                 timeout: Union[int, float] = 30,
                 repeat_failed: int = 3) -> None:
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

        if repeat_failed > 1:
            self._attempts = range(repeat_failed - 1, -1, -1)
        else:
            self._attempts = (0)

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

    raise_for_status = _raise_for_status

    def _simple_get(self, url: str) -> Tuple[int, str]:
        # time_start = time.time()
        with self.session.get(url, timeout=self.timeout) as response:
            # time_end = time.time()
            code = response.status_code
            data = orjson.loads(response.text)

        return code, data  # , time_start, time_end

    _cached_get = classcache(_simple_get)
    _multi_get = multiparams_classcache(_simple_get)

    _get = decor_get(_cached_get)
    _gets = decor_get(_multi_get)

    def get(self, url: str) -> R:
        return self._get(url)

    def gets(self, urls: URLS) -> L:
        return self._gets(url)
