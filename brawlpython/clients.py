# -*- coding: utf-8 -*-

import asyncio

from .base_classes import AsyncInitObject, AsyncWith, SyncWith
from .sessions import AsyncSession, SyncSession

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


class AsyncClient(AsyncInitObject, AsyncWith):
    async def __init__(self, token: str) -> None:
        self.session = await AsyncSession(token)

    async def close(self) -> None:
        """Close session"""
        await self.session.close()

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed


class SyncClient(SyncWith):
    def __init__(self, token: str) -> None:
        self.session = SyncSession(token)

    def close(self) -> None:
        """Close session"""
        self.session.close()

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed
