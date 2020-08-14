import asyncio
from brawlpython import AsyncClient


async def fetch(client):
    # get data and do something with it
    pass


async def init():
    async with await AsyncClient() as client:
        await fetch(client)


asyncio.run(init())
