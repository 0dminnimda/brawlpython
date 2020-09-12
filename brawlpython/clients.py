# -*- coding: utf-8 -*-

import asyncio

from .api import (
    api_defs, API, KINDS, KIND_VALS, KIND_KEYS,
    OFFIC, CHI, STAR, OFFICS, UNOFFICS,
)
from .api_toolkit import rearrange_params, add_api_name
from .base_classes import AsyncInitObject, AsyncWith, SyncWith
from .cache_utils import iscorofunc
from .sessions import AsyncSession, SyncSession

from functools import update_wrapper
from types import TracebackType
from typing import (
    Any,
    Callable,
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
from .typedefs import URLS, L, R, PARAMS, RETURN, HANDLER
import time

__all__ = (
    "AsyncClient",
    "SyncClient",
    "offic_gets_handler",
    "star_gets_handler",
    "gets_handler")


def offic_gets_handler(data_list: L) -> L:
    results = []
    for data in data_list:
        get_items = data.get("items")
        if get_items is not None and isinstance(get_items, list):
            results.append(get_items)
        else:
            results.append(data)
    return results


def star_gets_handler(data_list: L) -> L:
    results = []
    for data in data_list:
        data.pop("status", None)
        if len(data) == 1:
            results += list(data.values())
        else:
            results.append(data)
    return results


def gets_handler(self, data_list: L) -> L:
    name = self._current_api
    if name in OFFICS:
        res = offic_gets_handler(data_list)
    elif name == STAR:
        res = star_gets_handler(data_list)
    else:
        res = data_list

    if self._return_unit and len(res) == 1:
        return res[0]

    return res


class AsyncClient(AsyncInitObject, AsyncWith):
    async def __init__(
            self, tokens: Union[str, Dict[str, str]],
            api_s: Dict[str, API] = {},
            default_api: str = OFFIC,
            return_unit_list: bool = True,
            min_update_time: Union[int, float] = 60 * 10,

            trust_env: bool = True,
            cache_ttl: Union[int, float] = 60,
            cache_limit: int = 1024,
            use_cache: bool = True,
            timeout: Union[int, float] = 30,
            repeat_failed: int = 3,
            data_handler: HANDLER = gets_handler) -> None:

        self.session = await AsyncSession(
            trust_env=trust_env, cache_ttl=cache_ttl,
            cache_limit=cache_limit, use_cache=use_cache,
            timeout=timeout, repeat_failed=repeat_failed
        )
        self.api_s = {**api_defs, **api_s}
        self._current_api = self._default_api = default_api

        if isinstance(tokens, str):
            self.api_s[default_api].set_token(tokens)
        else:
            for name, token in tokens.items():
                self.api_s[name].set_token(token)

        self._return_unit = return_unit_list
        self._brawlers_update = None
        self._min_update_time = min_update_time

        await self.update_brawlers()

        self._gets_handler = data_handler

    async def close(self) -> None:
        """Close session"""
        await self.session.close()

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    async def _gets(self, *args: Any, **kwargs: Any) -> L:
        resps = await self.session.gets(*args, **kwargs)
        return self._gets_handler(self, resps)

    async def _fetch(self, path: str, from_json: bool = True,
                     **kwargs: Any) -> RETURN:

        if self._current_api is None:
            self._current_api = self._default_api

        api = self.api_s[self._current_api]

        return await self._gets(
            api.get(path, **kwargs), headers=api.headers, from_json=from_json)

    @add_api_name(None)
    async def test_fetch(self, *args, **kwargs):
        return await self._fetch(*args, **kwargs)

    @add_api_name(OFFIC)
    async def brawlers(self, brawler: Union[int, str] = "",
                       limit: Optional[int] = None) -> RETURN:

        if limit is None:
            limit = ""
        return await self._fetch("brawlers", id=brawler, limit=limit)

    @add_api_name(OFFIC)
    async def player(self, tag: str) -> RETURN:
        return await self._fetch("players", tag=tag)

    async def update_brawlers(self) -> None:
        if self._brawlers_update is None:
            self._brawlers_update = time.time()

        if time.time() - self._brawlers_update >= self._min_update_time:
            self._brawlers = await self.brawlers()

    def find_brawler(self, match, parameter=None) -> Optional[RETURN]:
        # FIXME: raw code

        brawlers = self._brawlers

        if parameter == "name":
            if isinstance(match, str):
                match = match.upper()
        elif parameter in ("number", "rank"):
            if -len(brawlers) <= match < len(brawlers):
                return brawlers[match]

        if parameter is None:
            for brawler in brawlers:
                if match in brawler.values():
                    return brawler
        else:
            for brawler in brawlers:
                if brawler.get(parameter) == match:
                    return brawler

        return None  # returns explicitly


class SyncClient(SyncWith):
    def __init__(
            self, tokens: Union[str, Dict[str, str]],
            api_s: Dict[str, API] = {},
            default_api: str = OFFIC,
            return_unit_list: bool = True,
            min_update_time: Union[int, float] = 60 * 10,

            trust_env: bool = True,
            cache_ttl: Union[int, float] = 60,
            cache_limit: int = 1024,
            use_cache: bool = True,
            timeout: Union[int, float] = 30,
            repeat_failed: int = 3,
            data_handler: HANDLER = gets_handler) -> None:

        self.session = SyncSession(
            trust_env=trust_env, cache_ttl=cache_ttl,
            cache_limit=cache_limit, use_cache=use_cache,
            timeout=timeout, repeat_failed=repeat_failed
        )
        self.api_s = {**api_defs, **api_s}
        self._current_api = self._default_api = default_api

        if isinstance(tokens, str):
            self.api_s[default_api].set_token(tokens)
        else:
            for name, token in tokens.items():
                self.api_s[name].set_token(token)

        self._return_unit = return_unit_list
        self._brawlers_update = None
        self._min_update_time = min_update_time

        self.update_brawlers()

        self._gets_handler = data_handler

    def close(self) -> None:
        """Close session"""
        self.session.close()

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    def _gets(self, *args: Any, **kwargs: Any) -> L:
        resps = self.session.gets(*args, **kwargs)
        return self._gets_handler(self, resps)

    def _fetch(self, path: str, from_json: bool = True,
               **kwargs: Any) -> RETURN:

        if self._current_api is None:
            self._current_api = self._default_api

        api = self.api_s[self._current_api]

        return self._gets(
            api.get(path, **kwargs), headers=api.headers, from_json=from_json)

    @add_api_name(None)
    def test_fetch(self, *args, **kwargs):
        return self._fetch(*args, **kwargs)

    @add_api_name(OFFIC)
    def brawlers(self, brawler: Union[int, str] = "",
                 limit: Optional[int] = None) -> RETURN:

        if limit is None:
            limit = ""
        return self._fetch("brawlers", id=brawler, limit=limit)

    @add_api_name(OFFIC)
    def player(self, tag: str) -> RETURN:
        return self._fetch("players", tag=tag)

    def update_brawlers(self) -> None:
        if self._brawlers_update is None:
            self._brawlers_update = time.time()

        if time.time() - self._brawlers_update >= self._min_update_time:
            self._brawlers = self.brawlers()
