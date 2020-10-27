# -*- coding: utf-8 -*-


from asyncio import (AbstractEventLoop, ensure_future, gather, get_event_loop,
                     sleep, wait)
from typing import (Any, Callable, Container, Coroutine, Dict, Generator,
                    Generic, Iterable, Iterator, List, Mapping, Optional, Set,
                    Tuple, Type, TypeVar, Union, Sequence)

from aiohttp import ClientResponse, ClientSession, ClientTimeout, TCPConnector

from .abc import AbcAsyncInit, AbcAsyncWith
from .api_toolkit import DEFAULT_HEADERS, rearrange_args
from .exceptions import WITH_CODE, UnexpectedResponseCode
from .helpers import json
from .typedefs import (AKW, ARGS, BOOLS, BOTH_JSON, JSONT, NUMBER, REQRESP,
                       STRBYTE, STRJSON, STRS)

__all__ = (
    "Session",
    "Request",
    "Response",
    "COLLECT",
    "DEFAULT")


class Response:
    __slots__ = "url", "code", "text"

    def __init__(self, url: str, code: int, text: str) -> None:
        self.url = url
        self.code = code
        self.text = text

    def json(self, default: Any = None) -> Optional[JSONT]:
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


class Request:
    __slots__ = "url", "_session", "_response_class", "_headers"
    # "hashable_headers")

    def __init__(self, url: str, session: Session,
                 response_class: Type[Response] = Response,
                 headers: JSONT = {}) -> None:
        self.url = url
        self._session = session
        self._response_class = response_class
        self._headers = headers
        # self._hashable_headers = json.dumps(headers)

    async def send(self) -> Response:
        async with self._session.get(self.url, headers=self._headers) as resp:
            response = self._response_class(
                self.url, resp.status, await resp.text())

        return response


class Collector:
    __slots__ = "_reqresps"

    def __init__(self) -> None:
        self._reqresps = []

    def __getitem__(self, key) -> REQRESP:
        return self._reqresps[key]

    def __setitem__(self, key, value) -> None:
        self._reqresps[key] = value

    def __iter__(self) -> Iterator[REQRESP]:
        return iter(self._reqresps)

    def items(self) -> Generator[Tuple[int, REQRESP], None, None]:
        for i, reqresp in enumerate(self._reqresps):
            yield i, reqresp

    def clear(self) -> None:
        self._reqresps.clear()

    def append_request(self, request: Request) -> None:
        self._reqresps.append([request, None])

    def get_responses(self) -> List[Optional[Response]]:
        return [resp for req, resp in self]


class AttemptCycle:
    def __init__(self, repeat_failed: int = 3,
                 success_codes: Container[int] = (200,)) -> None:

        if repeat_failed < 0:
            raise ValueError("repeat_failed must be a positive integer")

        # will make at least one attempt, last attempt is 0
        self._attempts = range(repeat_failed, -1, -1)
        self._success_codes = success_codes

    async def _reqresp_handler(self, collector: Collector, attempt: int,
                               i: int, req: Request, resp: Response):

        # recent attempts with this req have been unsuccessful
        if resp is None:
            resp = await req.send()
            if resp.code in self._success_codes:
                # set the current resp to successful
                collector[i][1] = resp
                # set the current req to None, because it is no longer needed
                collector[i][0] = None
            elif attempt == 0:  # last attempt
                resp.raise_code()
            else:
                self._failure_counter += 1

    async def run(self, collector: Collector) -> List[Response]:
        if len(self._attempts) == 0:
            raise RuntimeError("self._attempts attribute was changed"
                               " causing it to work incorrectly")

        for attempt in self._attempts:
            tasks = []
            self._failure_counter = 0
            for i, reqresp in collector.items():
                tasks.append(ensure_future(
                    self._reqresp_handler(collector, attempt, i, *reqresp)))

            await wait(tasks)
            # await gather(*tasks)

            if self._failure_counter == 0:
                return collector.get_responses()

        raise RuntimeError("While running nothing happend (raise or return)")


COLLECT = "collect"
DEFAULT = "default"

DEFAULT_CYCLE = AttemptCycle(repeat_failed=3, success_codes=(200,))


class Session(AbcAsyncInit, AbcAsyncWith):

    _mode = DEFAULT
    _collectors = []

    async def __init__(  # type: ignore
            self, timeout: NUMBER = 30,
            trust_env: bool = True,
            loop: Optional[AbstractEventLoop] = None,
            cycle: Optional[Cycle] = None,
            request_class: Type[Request] = Request,
            response_class: Type[Response] = Response,
            collector_class: Type[Collector] = Collector) -> None:

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
        self._collector_class = collector_class

        if cycle is None:
            self._cycle = DEFAULT_CYCLE
        else:
            self._cycle = cycle

    async def close(self) -> None:
        """Close underlying connector.
        Release all acquired resources.
        """
        if not self.closed:
            # SEE: https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await self._session.close()
            await sleep(0.250)

    @property
    def closed(self) -> bool:
        """Is client session closed.
        A readonly property.
        """
        return self._session.closed

    @property
    def mode(self) -> str:
        return self._mode

    def collect(self):
        self._mode = COLLECT
        self._collectors.append(self._collector_class())

    async def release(self):
        if self.mode == COLLECT:
            self._mode = DEFAULT
            responses = await self._cycle.run(self._collectors[-1])
            del self._collectors[-1]
            return responses

        raise RuntimeError(f"release called when mode == {DEFAULT}")

    async def get(self, url: str,
                  headers: JSONT = {}) -> Optional[JSONT]:

        req = self._request_class(url, session=self._session,
                                  response_class=self._response_class,
                                  headers=headers)

        if self.mode == COLLECT:
            self._collectors[-1].append_request(req)
        else:
            self.collect()
            self._collectors[-1].append_request(req)
            return (await self.release())[0]

    async def gets(self, url: str,
                   headers: Sequence[JSONT] = {}) -> Optional[Sequence[JSONT]]:

        params = rearrange_args(url, headers)

        if self.mode == COLLECT:
            for a in params:
                await self.get(*a)
        else:
            self.collect()
            for a in params:
                await self.get(*a)
            return await self.release()
