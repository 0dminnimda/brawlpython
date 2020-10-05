# -*- coding: utf-8 -*-


from aiohttp import ClientSession, TCPConnector, ClientTimeout
from asyncio import get_event_loop, sleep

from .base_classes import AsyncInitObject, AsyncWith
from .api_toolkit import DEFAULT_HEADERS


class Session(AsyncInitObject, AsyncWith):
    async def __init__(self, trust_env: bool = True, timeout: NUMBER = 30):
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
