# -*- coding: utf-8 -*-

from aiohttp import ClientSession, TCPConnector
import asyncio
from requests import Session

from .api_toolkit import make_headers
from .async_init import AsyncInitObject

from typing import (
    Any,
    Coroutine,
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


class AsyncSession(AsyncInitObject):
    async def __init__(self, token: str, trust_env: bool = True, ttl: int) -> None:
        headers = make_headers(token)
        loop = asyncio.get_event_loop()
        self.session = ClientSession(
            loop=loop,
            # XXX: it is probably better to use "cachetools.TTLCache"
            connector=TCPConnector(use_dns_cache=False, loop=loop),
            trust_env=trust_env,
            headers=headers,
        )

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


class SyncSession:
    def __init__(self, token: str, trust_env: bool = True) -> None:
        self._closed = False

        headers = make_headers(token)
        self.session = Session()
        self.session.trust_env = trust_env
        self.session.headers.update(headers)

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
