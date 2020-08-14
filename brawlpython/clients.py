# -*- coding: utf-8 -*-

from aiohttp import ClientSession, TCPConnector
import asyncio
from requests import Session
from types import TracebackType
from typing import (
    Any,
    Coroutine,
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
    "AsyncClient",
    "SyncClient",
)

TRUST_ENV = True


class AsyncClient:
    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()

        self.session = ClientSession(
            loop=self.loop,
            # connector=TCPConnector(ttl_dns_cache=60),
            trust_env=TRUST_ENV,
        )

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
    def __init__(self) -> None:
        self._closed = False

        self.session = Session()
        self.session.trust_env = TRUST_ENV

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
