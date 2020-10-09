# -*- coding: utf-8 -*-


from aiohttp import ClientSession, TCPConnector, ClientTimeout, ClientResponse
from asyncio import get_event_loop, sleep, gather, ensure_future

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
from .exceptions import WITH_CODE, UnexpectedResponseCode
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
                       loop: Optional[asyncio.AbstractEventLoop] = None,
                       request_class: AbcRequest = Request,
                       response_class: AbcResponse = Response,
                       success_codes: Container[int] = (200,)) -> None:

        if loop is None:
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

    async def _reqresp_handler(self, attempt, i, req, resp):
        # recent attempts with this req have been unsuccessful
        if resp is None:
            resp = await req.send()
            if resp.code in self._success_codes:
                # set the current resp to successful
                self._reqresps[i][1] = resp
                # set the current req to None
                # because it is no longer needed
                self._reqresps[i][0] = None
            elif attempt == 0:  # last attempt
                resp._raise_for_status()
            else:
                self._failure_counter += 1

    async def _start_attempt_cycle(self):
        if len(self._attempts) == 0:
            raise RuntimeError(
                "self._attempts argument was changed"
                " causing it to work incorrectly")

        for attempt in self._attempts:
            tasks = []
            self._failure_counter = 0
            for i, (req, resp) in enumerate(self._reqresps):
                tasks.append(ensure_future(
                    self._reqresp_handler(attempt, i, req, resp)))

            await gather(*tasks)

            if self._failure_counter == 0:
                # collect resps
                result = [resp for req, resp in self._reqresps]
                self._reqresps.clear()
                return result

    def one_get(self, url: str, to_json: bool = True,
                headers: JSONTYPE = {}) -> JSONTYPE:
        req = self._request_class(url, session=self._session,
                                  response_class=self._response_class,
                                  to_json=to_json, headers=headers)

        self._reqresps.append([req, None])
        return self._attempt_cycle()


class Response(AbcAsyncInit, AbcResponse):
    __slots__ = "url", "code", "text", "json"

    async def __init__(self, url: str, resp: ClientResponse,
                       to_json: bool) -> None:
        self.url = url
        self.code = resp.status
        self.text = await resp.text()
        self.json = None
        if to_json:
            self.json = await resp.json(loads=json.loads)

    def try_json_loads(self, default: Any = None) -> Optional[JSONTYPE]:
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return default

    def message(self) -> str:
        json = self.json
        if json is None:
            json = self.try_json_loads()

        if json is None:
            reason = ""
            message = self.text
        else:
            reason = self.json.get("reason", "")
            message = self.json.get("message", "")

        if len(reason) + len(message) == 0:
            message = "no message"

        if len(reason) > 0 and len(message) > 0:
            reason += ", "

        return reason + message

    def _raise_for_status(self) -> None:
        message = self.message()

        excp = next(filter(lambda excp: excp.code == code, WITH_CODE), None)
        if excp is not None:
            raise excp(url, message)
        else:
            raise UnexpectedResponseCode(code, url, message)


class Request(AbcRequest):
    __slots__ = "url", "session", "response_class", "to_json", "headers"
    # "hashable_headers")

    def __init__(self, url: str, session: AbcSession,
                 response_class: AbcResponse = Response,
                 to_json: bool = True, headers: JSONTYPE = {}) -> None:
        self.url = url
        self._session = session
        self._response_class = response_class
        self.to_json = to_json
        self._headers = headers
        # self._hashable_headers = json.dumps(headers)

    async def send(self) -> AbcResponse:
        async with self._session.get(self.url, headers=self._headers) as resp:
            response = self._response_class(self.url, resp, self.to_json)

        return await response
