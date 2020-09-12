# -*- coding: utf-8 -*-

from .api_toolkit import make_headers

from pyformatting import optional_format
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


class API:
    def __init__(self, base: str, paths: Optional[Dict[str, str]] = None,
                 params: Optional[Dict[str, Dict[str, str]]] = None,
                 token: Optional[str] = None) -> None:

        if paths is None:
            paths = {}
        if params is None:
            params = {}

        if not (base.startswith("http://") or base.startswith("https://")):
            base = "https://" + base
        elif base.startswith("http://"):
            base = "https://" + base[len("http://"):]

        if not base.endswith("/"):
            base += "/"

        if len(set(params) - set(paths)) != 0:
            raise ValueError(
                "'params.keys()' must be in the 'paths.keys()'")

        for name, path in paths.items():
            paths[name] = parse.urljoin(base, path)

            if params.get(name) is None:
                params[name] = {}

        self.base = base
        self.paths = paths
        self.params = params
        self.set_token(token)

    def __getattr__(self, name):
        get = self.paths.get(name)
        if get is None:
            raise AttributeError(f"'API' object has no attribute '{name}'")

        return get

    def set_token(self, token: str):
        if token is None:
            self.headers = {}
        else:
            self.headers = make_headers(token)

    def get(self, name: str, **params: Any) -> str:
        url = getattr(self, name)
        if len(params) == 0:
            return url

        for_format = {}
        used_parameters = []

        for param, val in params.items():
            get = self.params[name].get(param)
            if get is None:
                for_format.update({param: val})
            elif get != val:
                used_parameters.append(f"{param}={val}")

        if len(used_parameters) != 0:
            url += "?" + "&".join(used_parameters)

        return optional_format(url, **params)


official = {
    "players": "players/{tag}",
    "battlelog": "players/{tag}/battlelog",
    "clubs": "clubs/{tag}",
    "members": "clubs/{tag}/members",
    "rankings": "rankings/{code}/{kind}/{id}",
    "brawlers": "brawlers/{id}",
}

# before and after - this is so impractical that I suppose nobody will use this
# that's why I decided not to include it here
offic_params = {
    "members": {"limit": "100"},
    "rankings": {"limit": "200"},
    "brawlers": {"limit": ""},
}

starlist = {
    "events": "events",
    "brawlers": "brawlers",
    "icons": "icons",
    "maps": "maps/{id}",
    "gamemodes": "gamemodes",
    "clublog": "clublog/{tag}",
    "translations": "translations/{code}",
}

KINDS = {
    "b": "brawlers",
    "c": "clubs",
    "p": "players",
    "ps": "powerplay/seasons",
}

KIND_VALS = list(KINDS.values())
KIND_KEYS = list(KINDS.keys())


OFFIC = "official"
CHI = "chinese"
STAR = "starlist"
OFFICS = (OFFIC, CHI)
UNOFFICS = (STAR,)

api_defs = {
    OFFIC: API("api.brawlstars.com/v1", official, offic_params),
    CHI: API("api.brawlstars.cn/v1", official, offic_params),
    STAR: API("api.starlist.pro", starlist),
}
