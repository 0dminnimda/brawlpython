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
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from .typedefs import URLS, L, R, PARAMS
import time

__all__ = (
    "AsyncClient",
    "SyncClient",
    "OFFIC",
    "KINDS",
)


OFFIC = "official"

KINDS = {
    "b": "brawlers",
    "c": "clubs",
    "p": "players",
}

KIND_VALS = list(KINDS.values())
KIND_KEYS = list(KINDS.keys())


def _data_get(data: R) -> R:
    get_items = data.get("items")
    if get_items is not None and isinstance(get_items, list):
        return get_items
    return data


def _offic_data_gets(data_list: L) -> L:
    results = []
    for data in data_list:
        get_items = data.get("items")
        if get_items is not None and isinstance(get_items, list):
            results.append(get_items)
        else:
            results.append(data)
    return results


def _data_gets(self, api_name: str, data_list: L) -> L:
    if api_name == OFFIC:
        res = _offic_data_gets(data_list)
    else:
        res = data_list

    if self._return_unit and len(res) == 1:
        return res[0]

    return res


class AsyncClient(AsyncInitObject, AsyncWith):
    async def __init__(self, tokens: Union[str, Dict[str, str]],
                       api_s: Dict[str, API] = {},
                       default_api: str = OFFIC,
                       return_unit_list: bool = True,
                       min_update_time: Union[int, float] = 60 * 10,

                       trust_env: bool = True,
                       cache_ttl: Union[int, float] = 60,
                       cache_limit: int = 1024,
                       use_cache: bool = True,
                       timeout: Union[int, float] = 30,
                       repeat_failed: int = 3) -> None:

        self.session = await AsyncSession(
            trust_env=trust_env, cache_ttl=cache_ttl,
            cache_limit=cache_limit, use_cache=use_cache,
            timeout=timeout, repeat_failed=repeat_failed
        )
        self.api_s = {**api_defs, **api_s}
        self._default_api = default_api

        if isinstance(tokens, str):
            self.api_s[default_api].set_token(tokens)
        else:
            for name, token in tokens.items():
                self.api_s[name].set_token(token)

        self._return_unit = return_unit_list
        self._brawlers_update = None
        self._min_update_time = min_update_time

        await self.update_brawlers()

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
        resps = await self.session.gets(*args, **kwargs)
        return _data_gets(self, api_name, resps)

    async def _fetch(self, path: str,
                     api_name: Optional[str] = None,
                     **kwargs: Any) -> Dict[str, Any]:
        if api_name is None:
            api_name = self._default_api

        api = self.api_s[api_name]
        headers = api.headers
        urls = (api.get(path, **kwargs),)

        return await self._gets(api_name, urls, headers=headers)

    async def brawlers(self, brawler: Union[int, str] = "",
                       limit: Optional[int] = None,
                       api_name: Optional[str] = None) -> Dict[str, Any]:

        if limit is None:
            limit = ""
        return await self._fetch(
            "brawlers", api_name=api_name, id_=brawler, limit=limit)

    async def update_brawlers(self) -> None:
        if self._brawlers_update is None:
            self._brawlers_update = time.time()

        if time.time() - self._brawlers_update >= self._min_update_time:
            self._brawlers = await self.brawlers()


class SyncClient(SyncWith):
    def __init__(self, tokens: Union[str, Dict[str, str]],
                 api_s: Dict[str, API] = {},
                 default_api: str = OFFIC,
                 return_unit_list: bool = True,
                 min_update_time: Union[int, float] = 60 * 10,

                 trust_env: bool = True,
                 cache_ttl: Union[int, float] = 60,
                 cache_limit: int = 1024,
                 use_cache: bool = True,
                 timeout: Union[int, float] = 30,
                 repeat_failed: int = 3) -> None:

        self.session = SyncSession(
            trust_env=trust_env, cache_ttl=cache_ttl,
            cache_limit=cache_limit, use_cache=use_cache,
            timeout=timeout, repeat_failed=repeat_failed
        )
        self.api_s = {**api_defs, **api_s}
        self._default_api = default_api

        if isinstance(tokens, str):
            self.api_s[default_api].set_token(tokens)
        else:
            for name, token in tokens.items():
                self.api_s[name].set_token(token)

        self._return_unit = return_unit_list
        self._brawlers_update = None
        self._min_update_time = min_update_time

        self.update_brawlers()

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

    def _gets(self, api_name: str, *args: Any, **kwargs: Any) -> L:
        resps = self.session.gets(*args, **kwargs)
        return _data_gets(self, api_name, resps)

    def _fetch(self, path: str,
               api_name: Optional[str] = None,
               **kwargs: Any) -> Dict[str, Any]:
        if api_name is None:
            api_name = self._default_api

        api = self.api_s[api_name]
        headers = api.headers
        urls = (api.get(path, **kwargs),)

        return self._gets(api_name, urls, headers=headers)

    def brawlers(self, brawler: Union[int, str] = "",
                 limit: Optional[int] = None,
                 api_name: Optional[str] = None) -> Dict[str, Any]:

        if limit is None:
            limit = ""
        return self._fetch(
            "brawlers", api_name=api_name, id_=brawler, limit=limit)

    def update_brawlers(self) -> None:
        if self._brawlers_update is None:
            self._brawlers_update = time.time()

        if time.time() - self._brawlers_update >= self._min_update_time:
            self._brawlers = self.brawlers()
