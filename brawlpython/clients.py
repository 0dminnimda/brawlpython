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
    Iterable,
    Generic,
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
from .typedefs import (STRS, JSONSEQ, JSONS, HANDLER,
                       NUMBER, INTSTR, BOOLS, STRDICT)
import time

__all__ = (
    "AsyncClient",
    "SyncClient",
    "offic_gets_handler",
    "star_gets_handler",
    "gets_handler")


def offic_gets_handler(data_list: JSONSEQ) -> JSONSEQ:
    results = []
    for data in data_list:
        get_items = data.get("items")
        if get_items is not None and isinstance(get_items, list):
            results.append(get_items)
        else:
            results.append(data)
    return results


def star_gets_handler(data_list: JSONSEQ) -> JSONSEQ:
    results = []
    for data in data_list:
        data.pop("status", None)
        if len(data) == 1:
            results += list(data.values())
        else:
            results.append(data)
    return results


def gets_handler(self, data_list: JSONSEQ) -> JSONSEQ:
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


def _find_collectables(self, kind: str, match: INTSTR,
                  parameter: str = None) -> Optional[JSONS]:
    collectable = self._collectables[kind]
    count = len(collectable)

    if isinstance(match, int):
        if -count <= match < count:
            return collectable[match]
    elif isinstance(match, str):
        match = match.upper()

    if parameter is None:
        for part in collectable:
            if match in part.values():
                return part
    else:
        for part in collectable:
            if part.get(parameter) == match:
                return part

    return None  # returns explicitly


class AsyncClient(AsyncInitObject, AsyncWith):
    async def __init__(
            self, tokens: Union[str, STRDICT],
            api_s: Dict[str, API] = {},
            default_api: str = OFFIC,
            return_unit: bool = True,
            min_update_time: NUMBER = 60 * 10,
            data_handler: HANDLER = gets_handler,

            trust_env: bool = True,
            cache_ttl: NUMBER = 60,
            cache_limit: int = 1024,
            use_cache: bool = True,
            timeout: NUMBER = 30,
            repeat_failed: int = 3) -> None:

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

        self._return_unit = return_unit
        self._gets_handler = data_handler

        self._collectables = {}
        self._min_update_time = min_update_time
        await self.update_collectables(True)

    async def close(self) -> None:
        """Close session"""
        await self.session.close()

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    async def _gets(self, *args: Any, **kwargs: Any) -> JSONSEQ:
        resps = await self.session.gets(*args, **kwargs)
        return self._gets_handler(self, resps)

    def _get_api(self):
        if self._current_api is None:
            self._current_api = self._default_api

        return self.api_s[self._current_api]

    async def _fetch(self, path: str, from_json: bool = True,
                     **kwargs: Any) -> JSONS:

        api = self._get_api()

        return await self._gets(
            api.get(path, **kwargs), headers=api.headers, from_json=from_json)

    async def _fetchs(self, paths: STRS, from_json: BOOLS = True,
                      **kwargs: Any) -> JSONS:

        api = self._get_api()

        pars = rearrange_params(paths, **kwargs)
        urls = [api.get(*a, **kw) for a, kw in pars]

        return await self._gets(urls, headers=api.headers, from_json=from_json)

    @add_api_name(None)
    async def test_fetch(self, *args, **kwargs):
        return await self._fetchs(*args, **kwargs)

    @add_api_name(OFFIC)
    async def players(self, tag: str) -> JSONS:
        return await self._fetchs("players", tag=tag)

    @add_api_name(OFFIC)
    async def battlelog(self, tag: str) -> JSONS:
        return await self._fetchs("battlelog", tag=tag)

    @add_api_name(OFFIC)
    async def clubs(self, tag: str) -> JSONS:
        return await self._fetchs("clubs", tag=tag)

    @add_api_name(OFFIC)
    async def members(self, tag: str, limit: INTSTR = 100) -> JSONS:
        return await self._fetchs("members", tag=tag, limit=limit)

    @add_api_name(OFFIC)
    async def rankings(self, kind: str,
                       key: Optional[INTSTR] = None,
                       code: str = "global",
                       limit: INTSTR = 200) -> JSONS:

        if kind in KIND_KEYS:
            kind = KINDS[kind]

        if kind == KINDS["b"]:
            if key is None:
                raise ValueError(
                    "If the kind is b or brawlers, the key must be entered")

            brawler = self.find_collectables("b", key)
            if brawler is not None:
                key = brawler["id"]
        elif kind == KINDS["ps"]:
            if key is None:
                key = -1

            powerplay = self.find_collectables("ps", key)
            if powerplay is not None:
                key = powerplay["id"]

        return await self._fetchs("rankings", code=code,
                                  kind=kind, id=key, limit=limit)

    @add_api_name(OFFIC)
    async def brawlers(self, id: INTSTR = "",
                       limit: INTSTR = "") -> JSONS:
        return await self._fetchs("brawlers", id=id, limit=limit)

    @add_api_name(OFFIC)
    async def powerplay(self, code: str = "global", limit: int = 200) -> JSONS:
        return await self._fetchs("rankings", code=code, limit=limit,
                                  kind=KINDS["ps"], id="")

    @add_api_name(STAR)
    async def events(self) -> JSONS:
        return await self._fetchs("events")

    @add_api_name(STAR)
    async def icons(self) -> JSONS:
        return await self._fetchs("icons")

    @add_api_name(STAR)
    async def maps(self, id: INTSTR = "") -> JSONS:
        return await self._fetchs("maps", id=id)

    @add_api_name(STAR)
    async def gamemodes(self) -> JSONS:
        return await self._fetchs("gamemodes")

    @add_api_name(STAR)
    async def clublog(self, tag: str) -> JSONS:
        return await self._fetchs("clublog", tag=tag)

    @add_api_name(STAR)
    async def translations(self, code: str = "") -> JSONS:
        return await self._fetchs("translations", code=code)

    @add_api_name(OFFIC)
    async def update_collectables(self, now: bool = False) -> None:
        if now or time.time() - self._last_update >= self._min_update_time:
            self._collectables.update({
                "b": await self.brawlers(api=self._current_api),
                "ps": await self.powerplay(api=self._current_api)
            })
            self._last_update = time.time()

    find_collectables = _find_collectables


class SyncClient(SyncWith):
    def __init__(
            self, tokens: Union[str, STRDICT],
            api_s: Dict[str, API] = {},
            default_api: str = OFFIC,
            return_unit: bool = True,
            min_update_time: NUMBER = 60 * 10,
            data_handler: HANDLER = gets_handler,

            trust_env: bool = True,
            cache_ttl: NUMBER = 60,
            cache_limit: int = 1024,
            use_cache: bool = True,
            timeout: NUMBER = 30,
            repeat_failed: int = 3) -> None:

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

        self._return_unit = return_unit
        self._last_update = None
        self._min_update_time = min_update_time

        self._gets_handler = data_handler

        self._brawlers = self.brawlers()
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

    def _gets(self, *args: Any, **kwargs: Any) -> JSONSEQ:
        resps = self.session.gets(*args, **kwargs)
        return self._gets_handler(self, resps)

    def _fetch(self, path: str, from_json: bool = True,
               **kwargs: Any) -> JSONS:

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
                 limit: Optional[int] = None) -> JSONS:

        if limit is None:
            limit = ""
        return self._fetch("brawlers", id=brawler, limit=limit)

    @add_api_name(OFFIC)
    def player(self, tag: str) -> JSONS:
        return self._fetch("players", tag=tag)

    def update_brawlers(self) -> None:
        if self._last_update is None:
            self._last_update = time.time()

        if time.time() - self._last_update >= self._min_update_time:
            self._brawlers = self.brawlers()

    find_collectables = _find_collectables
