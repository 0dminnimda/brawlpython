# -*- coding: utf-8 -*-


from aiohttp import ClientSession, TCPConnector, ClientTimeout
from asyncio import get_event_loop, sleep

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
    Union)

from .abc import (AbcSession, AbcAsyncInit, AbcAsyncWith, AbcRequest,
                  AbcResponse)
from .api_toolkit import DEFAULT_HEADERS
from .helpers import json
from .typedefs import (STRS, JSONSEQ, JSONTYPE, JSONS, ARGS,
                       NUMBER, BOOLS, STRJSON, AKW, STRBYTE)

__all__ = ("Session",
           "Request",
           "Response")


class Session(AbcSession, AbcAsyncInit, AbcAsyncWith):
    async def __init__(self, timeout: NUMBER = 30, trust_env: bool = True):
        loop = get_event_loop()
        self.session = ClientSession(
            connector=TCPConnector(use_dns_cache=False, loop=loop),
            loop=loop,
            headers=DEFAULT_HEADERS,
            json_serialize=json.dumps,
            timeout=ClientTimeout(total=timeout),
            trust_env=trust_env)

    async def close(self) -> None:
        """Close underlying connector.
        Release all acquired resources.
        """
        if not self.closed:
            # SEE: https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await self.session.close()
            await sleep(0.300)

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self.session.closed


class Response(AbcAsyncInit, AbcResponse):
    __slots__ = "code", "data"

    async def __init__(self, resp, to_json: bool):
        code = resp.status
        if to_json:
            data = await resp.json(loads=json.loads)
        else:
            data = await resp.text()


class Request(AbcRequest):
    __slots__ = "session", "url", "to_json", "hashable_headers"

    def __init__(self, url: str, session: AbcSession,
                 response_class: AbcResponse = Response,
                 to_json: bool = True, headers: JSONTYPE = {}):
        self.hashable_headers = json.dumps(headers)
        self.session = session
        self.url = url
        self.to_json = to_json

    async def send(self):
        async with self.session.get(self.url, headers=self.headers) as resp:
            response = self.response_class(resp, self.to_json)

        return await response
