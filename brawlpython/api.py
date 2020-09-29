# -*- coding: utf-8 -*-

from .api_toolkit import make_headers
from .typedefs import STRDICT

from pyformatting import defaultformatter
from typing import Any, Dict, Optional, Union
import urllib.parse as parse

__all__ = (
    "API",
    "api_defs",
    "KINDS",
    "KIND_VALS",
    "KIND_KEYS",
    "OFFIC",
    "CHI",
    "STAR",
    "OFFICS",
    "UNOFFICS")


default_format = defaultformatter(str)


class API:

    __slots__ = "base", "endpoints", "hashtag", "headers"

    def __init__(self, base: str, endpoints: STRDICT = {},
                 hashtag: bool = True) -> None:

        http = base.startswith("http://")
        https = base.startswith("https://")

        if not (http or https):
            base = "https://" + base
        elif http:
            base = "https://" + base[len("http://"):]

        if not base.endswith("/"):
            base += "/"

        self.base = base
        self.endpoints = {}
        self.append(endpoints)
        self.hashtag = hashtag

    def append(self, endpoints: STRDICT) -> None:
        for name, path in endpoints.items():
            if name == "base":
                raise ValueError("names must be not 'base'")
            endpoints[name] = parse.urljoin(self.base, path)

        self.endpoints.update(endpoints)

    def set_token(self, token: str) -> None:
        if token is None:
            self.headers = {}
        else:
            self.headers = make_headers(token)

    def get(self, name: str) -> str:
        if name == "base":
            return self.base

        get = self.endpoints.get(name)
        if get is None:
            raise ValueError("`name` must be specified")

        return get

    def make_url(self, name: str, **params) -> str:
        tag = params.get("tag")
        if tag is not None:
            params["tag"] = self.remake_tag(tag)

        return default_format(self.get(name), **params)

    def remake_tag(self, tag: str) -> str:
        tag = tag.strip("#")

        if self.hashtag:
            tag = "#" + tag

        return parse.quote_plus(tag)


# before and after - is so impractical that I suppose nobody will use this
# that's why I decided not to include it here
limit_str = "?limit={limit}"
official = {
    "players": "players/{tag}",
    "battlelog": "players/{tag}/battlelog",
    "clubs": "clubs/{tag}",
    "members": "clubs/{tag}/members" + limit_str,
    "rankings": "rankings/{code}/{kind}/{id}" + limit_str,
    "brawlers": "brawlers/{id}" + limit_str}


starlist = {
    "events": "events",
    "brawlers": "brawlers",
    "icons": "icons",
    "maps": "maps/{id}",
    "gamemodes": "gamemodes",
    "clublog": "clublog/{tag}",
    "translations": "translations/{code}"}

KINDS = {
    "b": "brawlers",
    "c": "clubs",
    "p": "players",
    "ps": "powerplay/seasons"}
KIND_VALS = list(KINDS.values())
KIND_KEYS = list(KINDS.keys())

OFFIC = "official"
CHI = "chinese"
STAR = "starlist"
OFFICS = (OFFIC, CHI)
UNOFFICS = (STAR,)

api_defs = {
    OFFIC: API("api.brawlstars.com/v1", official),
    CHI: API("api.brawlstars.cn/v1", official),
    STAR: API("api.starlist.pro", starlist, hashtag=False),
}
