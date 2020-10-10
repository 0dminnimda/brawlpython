# -*- coding: utf-8 -*-


from aiohttp import ClientSession, TCPConnector, ClientTimeout, ClientResponse
from asyncio import (get_event_loop, sleep, gather, ensure_future,
                     AbstractEventLoop)

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

__all__ = (
    "Session",
    "Request",
    "Response")


class Response(AbcResponse):
    __slots__ = "url", "code", "text"

    def __init__(self, url: str, code: int, text: str) -> None:
        self.url = url
        self.code = code
        self.text = text

    def json(self, default: Any = None) -> Optional[JSONTYPE]:
        stripped = self.text.strip()
        if not stripped:
            return default

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return default

    def message(self) -> str:
        json = self.json()
        if json is None:
            reason = ""
            message = self.text
        else:
            reason = json.get("reason", "")
            message = json.get("message", "")

        if len(reason) + len(message) == 0:
            message = "no message"

        if len(reason) > 0 and len(message) > 0:
            reason += ", "

        return reason + message

    def raise_code(self):
        message = self.message()

        excp = next(filter(lambda e: e.code == self.code, WITH_CODE), None)
        if excp is not None:
            raise excp(self.url, message)
        else:
            raise UnexpectedResponseCode(self.code, self.url, message)


class Request(AbcRequest):
    __slots__ = "url", "_session", "_response_class", "_headers"
    # "hashable_headers")

    def __init__(self, url: str, session: AbcSession,
                 response_class: AbcResponse = Response,
                 headers: JSONTYPE = {}) -> None:
        self.url = url
        self._session = session
        self._response_class = response_class
        self._headers = headers
        # self._hashable_headers = json.dumps(headers)

    async def send(self) -> AbcResponse:
        async with self._session.get(self.url, headers=self._headers) as resp:
            response = self._response_class(
                self.url, resp.status, await resp.text())

        return response


class Collector(AbcCollector):
    def __init__(self) -> None:
        self._reqresps = []

    def __getitem__(self, key) -> REQRESP:
        return self._reqresps[key]

    def __setitem__(self, key, value) -> None:
        self._reqresps[key] = value

    def add_request(self, request: AbcRequest) -> None:
        self._reqresps.append([request, None])

    def items(self) -> Iterator[Tuple[int, REQRESP]]:
        for i, reqresp in enumerate(self._reqresps):
            yield i, reqresp

    def clear(self) -> None:
        self._reqresps.clear()


class Session(AbcSession, AbcAsyncInit, AbcAsyncWith):
    async def __init__(self, repeat_failed: int = 3,
                       timeout: NUMBER = 30,
                       trust_env: bool = True,
                       loop: Optional[AbstractEventLoop] = None,
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

        self._reqresps = []
        self._success_codes = success_codes

        # make `number of attempts` + 1 (at least one), but last attempt is 0
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
            await self._session.close()
            await sleep(0.300)

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self._session.closed

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
                resp.raise_code()
            else:
                self._failure_counter += 1

    async def _run_attempt_cycle(self):
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

    def one_get(self, url: str, headers: JSONTYPE = {}) -> JSONTYPE:

        req = self._request_class(url, session=self._session,
                                  response_class=self._response_class,
                                  headers=headers)

        self._reqresps.append([req, None])
        return self._run_attempt_cycle()
