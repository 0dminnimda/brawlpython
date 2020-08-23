# -*- coding: utf-8 -*-

from .api_toolkit import make_headers
from .optional_format import optional_format

from typing import Any, Dict, Optional, Union
import urllib.parse as parse

__all__ = (
    "API",
    "api_defs"
)


class API:
    def __init__(self, base: str, paths: Dict[str, str],
                 params: Dict[str, Dict[str, str]] = {},
                 token: Optional[str] = None) -> None:
        if not (base.startswith("http://") or base.startswith("https://")):
            base = "https://" + base
        elif base.startswith("http://"):
            base = "https://" + base[len("http://"):]

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
    "rankings": "rankings/{code}/{type}/{id_}",
    "brawlers": "brawlers",
    "brawler_id": "brawlers/{id_}",
}

# "club_rankings": "rankings/{code}/clubs",
# "brawler_rankings": "rankings/{code}/brawlers/{id_}",
# "player_rankings": "rankings/{code}/players",

# "club_rankings": rankings_params,
# "brawler_rankings": rankings_params,
# "player_rankings": rankings_params,

# before and after - this is so impractical that I suppose nobody will use this
offic_params = {
    "members": {"limit": "100"},
    "rankings": {"limit": "200"},
    "brawlers": {"limit": ""},
}

api_defs = {
    "official": API("https://api.brawlstars.com/v1", official, offic_params),
}
