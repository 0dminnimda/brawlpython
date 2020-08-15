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
    "AsyncClient",
    "SyncClient",
    "make_headers",
)


def make_headers(token: str) -> Dict[str, Union[int, str]]:
    return {
        "dnt": 1,
        "authorization": f"Bearer {token}",
        "user-agent": f"brawlpython/{__version__} (Python {sys.version[:5]})",
        "accept-encoding": "br, gzip",
    }


class AsyncClient(AsyncInitObject):
    async def __init__(self, token: str) -> None:
        self.loop = asyncio.get_event_loop()
        self.session = ClientSession(
            loop=self.loop,
            # connector=TCPConnector(ttl_dns_cache=60),
            trust_env=True,
        )

        self.headers = make_headers(token)

    async def close(self) -> None:
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
        return self.session.closed

    def __enter__(self) -> None:
        raise TypeError("Use `async with` instead")

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        # __exit__ should exist in pair with __enter__ but never executed
        pass

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        await self.close()


class SyncClient:
    def __init__(self, token: str) -> None:
        self._closed = False

        self.session = Session()
        self.session.trust_env = True

        self.headers = make_headers(token)

    def close(self) -> None:
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

    def __enter__(self) -> "SyncClient":
        return self

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        self.close()

    async def __aenter__(self) -> None:
        raise TypeError("Use `with` instead")

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        # __aexit__ should exist in pair with __aenter__ but never executed
        pass
