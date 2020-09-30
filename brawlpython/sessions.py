# -*- coding: utf-8 -*-

from aiohttp import ClientSession, TCPConnector, ClientTimeout
import asyncio
from asyncio import ensure_future as ensure, gather
from cachetools import TTLCache
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import update_wrapper
from requests import Session

from .api_toolkit import (
    default_headers,
    isrequiredcollection,
    multiparams,
    rearrange_params,
    rearrange_args,
    isliterals)
from .base_classes import (AsyncInitObject, AsyncWith,
                           SyncWith, DefaultOrderedDict)
from .cache_utils import somecachedmethod, iscorofunc, NaN
from .exceptions import WITH_CODE, UnexpectedResponseCode
from .typedefs import (STRS, JSONSEQ, JSONTYPE, JSONS, ARGS,
                       NUMBER, BOOLS, STRJSON, AKW, STRBYTE)

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
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

try:
    import orjson as json
except ImportError:
    try:
        import ujson as json
    except ImportError:
        import json

# from unicodedata import normalize  # "NFKC" or "NFKD"

__all__ = (
    "AsyncSession",
    "SyncSession")


# FIXME: in both functions I need to find a suitable cache_limit
# 1024 is a relatively random choice and
# has nothing to do with the desired behavior

def _raise_for_status(self, url: str, code: int,
                      data: Union[JSONTYPE, str]) -> None:

    if isinstance(data, str):
        reason = "without a reason"
        message = data if len(data) > 0 else "no message"
    else:
        reason = data.get("reason", "without a reason")
        message = data.get("message", "no message")

    excp = next(filter(lambda x: x.code == code, WITH_CODE), None)
    if excp is not None:
        raise excp(url, reason, message)
    else:
        raise UnexpectedResponseCode(url, code, reason, message)


retry_end = RuntimeError(
    "self._attempts argument was changed"
    " causing it to work incorrectly")

not_scheduled = RuntimeError(
    "scheduled function calls with these parameters have"
    " already been executed, this call is not scheduled")


def _headers_handler(self, headers: JSONS) -> STRBYTE:
    # TODO: use self._headers_dumps to not dumps twice
    if isrequiredcollection(headers):
        res = []
        for hdrs in headers:
            dumps = json.dumps(hdrs)
            res.append(dumps)
            self._headers_dumps[dumps] = hdrs
        return res
    elif isliterals(headers):
        self._headers_dumps[headers] = json.loads(headers)
        return headers
    else:
        dumps = json.dumps(headers)
        self._headers_dumps[dumps] = headers
        return dumps


def loads_json(data: str, from_json: bool = True) -> STRJSON:
    if from_json:
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    return data


class AsyncSession(AsyncInitObject, AsyncWith):
    async def __init__(self, trust_env: bool = True,
                       cache_ttl: NUMBER = 60,
                       cache_limit: int = 1024,
                       use_cache: bool = True,
                       timeout: NUMBER = 30,
                       repeat_failed: int = 3) -> None:
        headers = default_headers()
        loop = asyncio.get_event_loop()
        self.session = ClientSession(
            loop=loop,
            connector=TCPConnector(use_dns_cache=False, loop=loop),
            trust_env=trust_env,
            headers=headers,
            timeout=ClientTimeout(total=timeout),
        )

        if use_cache:
            self._cache = TTLCache(maxsize=cache_limit, ttl=cache_ttl)
            self._current_get = self._basic_cached_get
        else:
            # self._cache = None
            self._current_get = self._basic_get
        self._cached = use_cache

        if repeat_failed < 0:
            repeat_failed = 0
        self._attempts = range(repeat_failed, -1, -1)

        self._retry = []
        self._headers_dumps = {}
        self._init_pars = DefaultOrderedDict(list)

        self._debug = False

    async def close(self) -> None:
        """Close underlying connector.
        Release all acquired resources.
        """
        if not self.closed:
            # SEE: https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await self.session.close()
            await asyncio.sleep(0.300)

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed

    raise_for_status = _raise_for_status

    headers_handler = _headers_handler

    @property
    def cached(self) -> bool:
        return self._cached

    async def _basic_get(self, url: str,
                         headers: JSONTYPE) -> Tuple[int, str]:

        async with self.session.get(url, headers=headers) as response:
            code = response.status
            data = await response.text()

        return code, data

    async def _basic_cached_get(self, url: str,
                                headers: JSONTYPE) -> Tuple[int, str]:

        get_key = self._cache.get(url, NaN)
        if get_key != NaN:
            return get_key

        value = await self._basic_get(url, headers)
        code, *_ = value

        if code == 200:
            try:
                self._cache[url] = value
            except ValueError:
                pass  # value too large

        return value

    async def _verified_json_get(self, url: str, from_json: bool,
                                 headers: STRBYTE) -> None:

        args = (url, from_json, headers)

        headers = self._headers_dumps[headers]
        code, data = await self._current_get(url, headers)

        data = loads_json(data, from_json)

        if code != 200:
            if self._i == 0:
                self.raise_for_status(url, code, data)
            self._retry.append(args)
        else:
            arr = self._init_pars[args]
            if None in arr:
                arr[arr.index(None)] = data
            else:
                raise not_scheduled

    async def _params_get(self, params: Tuple[ARGS]):
        tasks = [ensure(self._verified_json_get(*a)) for a in params]
        await gather(*tasks)

    async def _retrying_get(self, in_params: Iterable[ARGS]):
        self._init_pars.clear()
        self._retry.clear()

        in_params = tuple(in_params)

        self._retry.extend(in_params)
        for a in self._retry:
            self._init_pars[a].append(None)

        for self._i in self._attempts:
            params = self._retry.copy()
            self._retry.clear()
            await self._params_get(params)

            if len(self._retry) == 0:
                res = [self._init_pars[key].pop(0) for key in in_params]

                for value in self._init_pars.values():
                    if len(value) != 0:
                        raise RuntimeError(
                            "not all parameters were used for the answer")
                self._init_pars.clear()

                return res

        self._init_pars.clear()
        self._retry.clear()

        raise retry_end

    # async def get_params(self, params: Iterable[ARGS]) -> JSONSEQ:
    #     return await self._retrying_get(params)

    async def gets(self, urls: STRS, from_json: BOOLS = True,
                   headers: JSONS = {}) -> JSONSEQ:

        params = rearrange_args(
            urls, from_json, self.headers_handler(headers))

        return await self._retrying_get(params)


class SyncSession(SyncWith):
    def __init__(self, trust_env: bool = True,
                 cache_ttl: NUMBER = 60,
                 cache_limit: int = 1024, use_cache: bool = True,
                 timeout: NUMBER = 30,
                 repeat_failed: int = 3) -> None:
        self._closed = False

        headers = default_headers()
        self.session = Session()
        self.session.trust_env = trust_env
        self.session.headers.update(headers)

        if use_cache:
            self._cache = TTLCache(maxsize=cache_limit, ttl=cache_ttl)
        else:
            self._cache = None
        self._cached = use_cache

        self.timeout = timeout

        if repeat_failed > 1:
            self._attempts = range(repeat_failed - 1, -1, -1)
        else:
            self._attempts = (0)

        self._last_reqs = []
        self._last_urls = []

    def close(self) -> None:
        """Closes all adapters and as such the session"""
        if not self.closed:
            self.session.close()
            self._closed = True

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self._closed

    raise_for_status = _raise_for_status

    @property
    def cached(self) -> bool:
        return self._cached

    def _simple_get(
            self, url: str, from_json: bool = True,
            headers: Iterable[Iterable[str]] = {}) -> Tuple[int, STRJSON]:
        with self.session.get(
                url, timeout=self.timeout, headers=dict(headers)) as response:
            code = response.status_code
            data = response.text
            if from_json:
                data = json.loads(data)

        return code, data

    #_get = retry_to_get_data(mix_all_gets(False)(_simple_get))
    #_gets = retry_to_get_data(mix_all_gets(True)(_simple_get))

    def get(self, url: str, from_json: bool = True,
            headers: JSONTYPE = {}) -> JSONTYPE:
        return self._get(url, from_json=from_json,
                         headers=headers_handler(self, headers))[0]

    def gets(self, urls: STRS, from_json: BOOLS = True,
             headers: JSONS = {}) -> JSONSEQ:
        return self._gets(urls, from_json=from_json,
                          headers=headers_handler(self, headers))
