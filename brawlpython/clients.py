# -*- coding: utf-8 -*-

import asyncio

from .api import api_defs, API
from .api_toolkit import rearrange_params
from .base_classes import AsyncInitObject, AsyncWith, SyncWith
from .sessions import AsyncSession, SyncSession
from .api_toolkit import isiter_noliterals

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


OFFIC = "official"


class AsyncClient(AsyncInitObject, AsyncWith):
    async def __init__(self, tokens: Union[str, Dict[str, str]],
                       api_s: Dict[str, API] = {},
                       default_api: str = OFFIC) -> None:
        self.session = await AsyncSession()
        self.api_s = api_defs.update(api_s)
        self._default_api = default_api

        if isinstance(tokens, str):
            self.api_s[default_api].set_token(tokens)
        else:
            for name, token in tokens.items():
                self.api_s[name].set_token(token)

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

    async def _gets(self, api_name: str, *args: Any, **kwargs: Any) -> L:
        res = await self.session.gets(*args, **kwargs)
        if api_name == OFFIC:
            return _data_gets(res)
        else:
            return res

    async def _fetch(self, path: str, api_name: Optional[str] = None,
                     **kwargs: Any) -> Dict[str, Any]:
        if api_name is None:
            api_name = self._default_api

        api = self.api_s[api_name]
        headers = api.headers
        urls = []
        for _, kw in rearrange_params(**kwargs):
            urls.append(api.get(path, **kw))

        return await self._gets(api_name, urls, headers=headers)

class SyncClient(SyncWith):
    def __init__(self, token: str, *args: Any, **kwargs: Any) -> None:
        self.session = SyncSession(*args, **kwargs)

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
