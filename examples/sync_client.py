from brawlpython import SyncClient


def fetch(client):
    # get data and do something with it
    pass


def init():
    with SyncClient() as client:
        fetch(client)


init()
