# -*- coding: utf-8 -*-


from aiohttp import ClientSession, TCPConnector, ClientTimeout
from asyncio import get_event_loop, sleep

from .abc import AbcSession, AbcAsyncInit, AbcAsyncWith, AbcRequest
from .api_toolkit import DEFAULT_HEADERS
from .helpers import json
from .typedefs import (STRS, JSONSEQ, JSONTYPE, JSONS, ARGS,
                       NUMBER, BOOLS, STRJSON, AKW, STRBYTE)

__all__ = ("Session", "Request")


class Session(AbcSession, AbcAsyncInit, AbcAsyncWith):
    async def __init__(self, timeout: NUMBER = 30, trust_env: bool = True):
        loop = get_event_loop()
        self.session = ClientSession(
            connector=TCPConnector(use_dns_cache=False, loop=loop),
            loop=loop,
            headers=DEFAULT_HEADERS,
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


class Response:
    pass


class Request(AbcRequest):
    def __init__(self, session: AbcSession, url: str,
                 from_json: bool = True, headers: JSONTYPE = {}):
        self.hashable_headers = json.dumps(headers)
        self.session = session
        self.url = url
        self.from_json = from_json

    def send(self):
        pass
