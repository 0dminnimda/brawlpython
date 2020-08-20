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
from .typedefs import URLS, L, R

__all__ = (
    "AsyncClient",
    "SyncClient",
    "make_headers",
)


def _data_get(data: R) -> R:
    get_items = data.get("items")
    if get_items is not None and isinstance(get_items, list):
        return get_items
    return data


def _data_gets(data_list: L) -> L:
    results = []
    for data in data_list:
        get_items = data.get("items")
        if get_items is not None and isinstance(get_items, list):
            results.append(get_items)
        else:
            results.append(data)
    return results


class AsyncClient(AsyncInitObject, AsyncWith):
    async def __init__(self, token: str, *args: Any, **kwargs: Any) -> None:
        self.session = await AsyncSession(token, *args, **kwargs)

    async def close(self) -> None:
        """Close session"""
        await self.session.close()

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    async def _get(self, url: str) -> R:
        return _data_get(await self.session.get(url))

    async def _gets(self, urls: URLS) -> L:
        return _data_gets(await self.session.gets(urls))


class SyncClient(SyncWith):
    def __init__(self, token: str, *args: Any, **kwargs: Any) -> None:
        self.session = SyncSession(token, *args, **kwargs)

    def close(self) -> None:
        """Close session"""
        self.session.close()

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    def _get(self, url: str) -> R:
        return _data_get(self.session.get(url))

    def _gets(self, urls: URLS) -> L:
        return _data_gets(self.session.gets(urls))
