# -*- coding: utf-8 -*-

from aiohttp import ClientSession, TCPConnector
import asyncio
from requests import Session

from .async_init import AsyncInitObject
from . import __version__

import sys

from types import TracebackType
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


TRUST_ENV = True

HEADERS = {
    "dnt": 1,
    "authorization": "Bearer {token}",
    "user-agent": f"brawlpython/{__version__} (Python {sys.version[:5]})",
    "accept-encoding": "br, gzip",
}


def is_sync(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.sync:
            raise Exception(f"use `await aclose` insted")

        return func(self, *args, **kwargs)

    return wrapper


def is_async(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.sync:
            raise Exception(f"use `{func.__name__[1:]}` insted")

        return func(self, *args, **kwargs)

    return wrapper


class MultiClient(AsyncInitObject):
    async def __init__(self, token: str, sync: bool) -> None:
        self.headers = {
            **HEADERS,
            "authorization": HEADERS["authorization"].format()
        }

        if sync:
            self._closed = False
        else:
            self.loop = asyncio.get_event_loop()

        if sync:
            self.session = Session()
            self.session.trust_env = TRUST_ENV
        else:
            self.session = ClientSession(
                loop=self._loop,
                # connector=TCPConnector(ttl_dns_cache=60),
                trust_env=TRUST_ENV,
            )

    def close(self) -> Optional[NoReturn]:
        if not self.sync:
            raise Exception("use `await aclose` insted")

        if not self.closed:
            self.session.close()
            self._closed = True

    async def aclose(self) -> Optional[NoReturn]:
        if self.sync:
            raise Exception("use `close` insted")

        if not self.closed:
            await self.session.close()
            # Zero-sleep to allow underlying connections to close
            await asyncio.sleep(0)

    @property
    def closed(self) -> bool:
        """
        Is client session closed.
        A readonly property.
        """
        if self.sync:
            return self._closed
        else:
            return self.session.closed
