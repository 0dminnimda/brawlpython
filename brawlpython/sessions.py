# -*- coding: utf-8 -*-


from aiohttp import ClientSession, TCPConnector, ClientTimeout
from asyncio import get_event_loop, sleep

from typing import (
    Any,
    Container,
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
    async def __init__(self, repeat_failed: int = 3,
                       timeout: NUMBER = 30,
                       trust_env: bool = True,
                       request_class: AbcRequest = Request,
                       response_class: AbcResponse = Response,
                       success_codes: Container[int] = (200,)):
        loop = get_event_loop()
        self._session = ClientSession(
            connector=TCPConnector(use_dns_cache=False, loop=loop),
            loop=loop,
            headers=DEFAULT_HEADERS,
            json_serialize=json.dumps,
            timeout=ClientTimeout(total=timeout),
            trust_env=trust_env)

        self._request_class = request_class
        self._response_class = response_class

        self._reqrespss = []
        self._success_codes = success_codes

        # make `number of attempts` + 1 (at least one), but last attempt - 0
        if repeat_failed < 0:
            repeat_failed = 0
        self._attempts = range(repeat_failed, -1, -1)

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

    def one_get(self, url: str, to_json: bool = True,
                headers: JSONTYPE = {}) -> JSONTYPE:
        req = self._request_class(url, session=self._session,
                                  response_class=self._response_class,
                                  to_json=to_json, headers=headers)

        self._reqresps.append([req, None])
        return self._attempt_cycle

    def _raise_for_status(self):
        raise Exception("test run")

    async def _start_attempt_cycle(self):
        for attempt in self._attempts:
            failure_counter = 0
            for i, (req, resp) in enumerate(self._reqresps):
                # recent attempts with this req have been unsuccessful
                if resp is None:
                    resp = await req.send()
                    if resp.code in self._success_codes:
                        # set current resp to successful
                        self._reqresps[i][1] = resp
                    elif attempt == 0:  # last attempt
                        self._raise_for_status
                    else:
                        failure_counter += 1

            if failure_counter == 0:
                # collect resps
                result = [resp for req, resp in self._reqresps]
                self._reqresps.clear()
                return result


class Response(AbcAsyncInit, AbcResponse):
    __slots__ = "code", "data"

    async def __init__(self, resp, to_json: bool) -> None:
        self.code = resp.status
        if to_json:
            self.data = await resp.json(loads=json.loads)
        else:
            self.data = await resp.text()


class Request(AbcRequest):
    __slots__ = ("url", "session", "response_class", "to_json", "headers",
                 "hashable_headers")

    def __init__(self, url: str, session: AbcSession,
                 response_class: AbcResponse = Response,
                 to_json: bool = True, headers: JSONTYPE = {}) -> None:
        self.url = url
        self._session = session
        self._response_class = response_class
        self.to_json = to_json
        self._headers = headers
        self._hashable_headers = json.dumps(headers)

    async def send(self) -> AbcResponse:
        async with self._session.get(self.url, headers=self._headers) as resp:
            response = self._response_class(resp, self.to_json)

        return await response
