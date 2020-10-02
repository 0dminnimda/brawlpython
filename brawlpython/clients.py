# -*- coding: utf-8 -*-

import asyncio

from .api import (
    default_api_dict, API, KINDS, KIND_VALS, KIND_KEYS,
    OFFIC, CHI, STAR, OFFICS, UNOFFICS,
)
from .api_toolkit import rearrange_params, add_api_name, _rearrange_args
from .base_classes import AsyncInitObject, AsyncWith, SyncWith
from .cache_utils import iscorofunc
from .sessions import AsyncSession, SyncSession

from configparser import ConfigParser
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
                       NUMBER, INTSTR, BOOLS, STRDICT, AKW)
import time

__all__ = (
    "AsyncClient",
    "SyncClient",
    "offic_gets_handler",
    "star_gets_handler",
    "gets_handler")


COLLECT = "collect"
RELEASE = "release"
DEFAULT = "default"


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


def _find_save(self, kind: str, match: INTSTR,
               parameter: str = None) -> Optional[JSONS]:
    collectable = self._saves[kind]
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


def _rankings(self, kind: str,
              key: Optional[INTSTR] = None,
              code: str = "global",
              limit: INTSTR = 200) -> JSONS:

    if kind in KIND_KEYS:
        kind = KINDS[kind]

    if kind == KINDS["b"]:
        if key is None:
            raise ValueError(
                "If the kind is b or brawlers, the key must be entered")

        brawler = self.find_save("b", key)
        if brawler is not None:
            key = brawler["id"]
    elif kind == KINDS["ps"]:
        if key is None:
            key = -1

        powerplay = self.find_save("ps", key)
        if powerplay is not None:
            key = powerplay["id"]

    if key is None:
        key = ""

    return ("rankings",), {"code": code, "kind": kind,
                           "id": key, "limit": limit}


def get_and_apply_api_keys(filename: str, section: str,
                           api_dict: Dict[str, API]) -> None:
    if filename.endswith(".env"):
        raise ValueError("this file extension is not accepted")

    # if filename.endswith(".ini"):
    config = ConfigParser()
    config.read(filename)
    config = config[section]

    for name, api in api_dict.items():
        if name in OFFICS:
            name = OFFIC

        api_key = config.get(name + "_api_key")
        api.set_api_key(api_key)


class AsyncClient(AsyncInitObject, AsyncWith):
    async def __init__(
            self,  # api_keys: Union[str, STRDICT],
            config_file_name: str = "config.ini",
            section: str = "DEFAULT",
            api_dict: Dict[str, API] = {},
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
            timeout=timeout, repeat_failed=repeat_failed)

        self.api_dict = {**default_api_dict, **api_dict}
        get_and_apply_api_keys(config_file_name, section, self.api_dict)
        self._current_api = self._default_api = default_api

        # if isinstance(api_keys, str):
        #     self.api_dict[default_api].set_api_key(api_keys)
        # else:
        #     for name, api_key in api_keys.items():
        #         self.api_dict[name].set_api_key(api_key)

        self._return_unit = return_unit
        self._gets_handler = data_handler
        self._requests = []
        self._mode = DEFAULT

        self._saves = {}
        self._min_update_time = min_update_time
        await self.update_saves(True)

    async def close(self) -> None:
        """Close session"""
        await self.session.close()

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    @property
    def mode(self) -> str:
        return self._mode

    async def _gets(self, *args) -> JSONSEQ:
        if self.mode == COLLECT:
            self._requests.extend(_rearrange_args(args))
            return None

        if self.mode == RELEASE:
            resps = await self.session._retrying_get(self._requests)
            self._requests.clear()
        elif self.mode == DEFAULT:
            resps = await self.session.gets(*args)
        else:
            raise ValueError("mode is invalid")

        return self._gets_handler(self, resps)

    def _get_api(self):
        if self._current_api is None:
            self._current_api = self._default_api

        return self.api_dict[self._current_api]

    async def _fetchs(self, paths: STRS, from_json: BOOLS = True,
                      **kwargs) -> JSONS:

        api = self._get_api()

        pars = rearrange_params(paths, **kwargs)
        urls = [api.make_url(*a, **kw) for a, kw in pars]

        headers = self.session.headers_handler(api.headers)
        return await self._gets(urls, from_json, headers)

    def collect(self):
        self._mode = COLLECT

    async def release(self):
        self._mode = RELEASE
        try:
            res = await self._gets()
        finally:
            self._mode = DEFAULT

        return res

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

        pars = rearrange_params(kind, key=key, code=code, limit=limit)

        self.collect()
        for args, kwargs in pars:
            a, kw = _rankings(self, *args, **kwargs)
            await self._fetchs(*a, **kw)

        return await self.release()

    @add_api_name(OFFIC)
    async def brawlers(self, id: INTSTR = "",
                       limit: Optional[INTSTR] = None) -> JSONS:
        return await self._fetchs("brawlers", id=id, limit=limit)

    @add_api_name(OFFIC)
    async def powerplay(self, code: str = "global", limit: int = 200) -> JSONS:
        return await self._fetchs("rankings", code=code, limit=limit,
                                  kind=KINDS["ps"])

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
    async def update_saves(self, now: bool = False) -> None:
        if now or time.time() - self._last_update >= self._min_update_time:
            self.collect()
            await self.brawlers(api=self._current_api)
            await self.powerplay(api=self._current_api)
            b, ps = await self.release()
            self._saves.update({"b": b, "ps": ps})
            self._last_update = time.time()

    find_save = _find_save


class SyncClient(SyncWith):
    def __init__(
            self, api_keys: Union[str, STRDICT],
            api_dict: Dict[str, API] = {},
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
        self.api_dict = {**default_api_dict, **api_dict}
        self._current_api = self._default_api = default_api

        if isinstance(api_keys, str):
            self.api_dict[default_api].set_api_key(api_keys)
        else:
            for name, api_key in api_keys.items():
                self.api_dict[name].set_api_key(api_key)

        self._return_unit = return_unit
        self._gets_handler = data_handler

        self._saves = {}
        self._min_update_time = min_update_time
        self.update_saves(True)

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

    def _get_api(self):
        if self._current_api is None:
            self._current_api = self._default_api

        return self.api_dict[self._current_api]

    def _fetch(self, path: str, from_json: bool = True,
               **kwargs: Any) -> JSONS:

        api = self._get_api()

        return self._gets(
            api.get(path, **kwargs), headers=api.headers, from_json=from_json)

    def _fetchs(self, paths: Union[STRS, AKW], from_json: BOOLS = True,
                rearrange: bool = True, **kwargs: Any) -> JSONS:

        api = self._get_api()

        if rearrange:
            pars = rearrange_params(paths, **kwargs)
        else:
            pars = paths
        urls = [api.get(*a, **kw) for a, kw in pars]

        return self._gets(urls, headers=api.headers, from_json=from_json)

    @add_api_name(None)
    def test_fetch(self, *args, **kwargs):
        return self._fetchs(*args, **kwargs)

    @add_api_name(OFFIC)
    def players(self, tag: str) -> JSONS:
        return self._fetchs("players", tag=tag)

    @add_api_name(OFFIC)
    def battlelog(self, tag: str) -> JSONS:
        return self._fetchs("battlelog", tag=tag)

    @add_api_name(OFFIC)
    def clubs(self, tag: str) -> JSONS:
        return self._fetchs("clubs", tag=tag)

    @add_api_name(OFFIC)
    def members(self, tag: str, limit: INTSTR = 100) -> JSONS:
        return self._fetchs("members", tag=tag, limit=limit)

    @add_api_name(OFFIC)
    def rankings(self, kind: str,
                 key: Optional[INTSTR] = None,
                 code: str = "global",
                 limit: INTSTR = 200) -> JSONS:
        pars = rearrange_params(
            kind, key=key, code=code, limit=limit)

        return self._fetchs(
            [_rankings(self, *a, **kw) for a, kw in pars], rearrange=False)

    @add_api_name(OFFIC)
    def brawlers(self, id: INTSTR = "",
                 limit: INTSTR = "") -> JSONS:
        return self._fetchs("brawlers", id=id, limit=limit)

    @add_api_name(OFFIC)
    def powerplay(self, code: str = "global", limit: int = 200) -> JSONS:
        return self._fetchs("rankings", code=code, limit=limit,
                            kind=KINDS["ps"], id="")

    @add_api_name(STAR)
    def events(self) -> JSONS:
        return self._fetchs("events")

    @add_api_name(STAR)
    def icons(self) -> JSONS:
        return self._fetchs("icons")

    @add_api_name(STAR)
    async def maps(self, id: INTSTR = "") -> JSONS:
        return self._fetchs("maps", id=id)

    @add_api_name(STAR)
    def gamemodes(self) -> JSONS:
        return self._fetchs("gamemodes")

    @add_api_name(STAR)
    def clublog(self, tag: str) -> JSONS:
        return self._fetchs("clublog", tag=tag)

    @add_api_name(STAR)
    def translations(self, code: str = "") -> JSONS:
        return self._fetchs("translations", code=code)

    @add_api_name(OFFIC)
    def update_saves(self, now: bool = False) -> None:
        if now or time.time() - self._last_update >= self._min_update_time:
            self._saves.update({
                "b": self.brawlers(api=self._current_api),
                "ps": self.powerplay(api=self._current_api)
            })
            self._last_update = time.time()

    find_save = _find_save
