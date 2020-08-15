import sys

from . import __version__, __name__

from typing import Dict, Union


def make_headers(token: str) -> Dict[str, Union[int, str]]:
    return {
        "dnt": 1,
        "authorization": f"Bearer {token}",
        "user-agent": f"{__name__}/{__version__} (Python {sys.version[:5]})",
        "accept-encoding": "br, gzip",
    }
