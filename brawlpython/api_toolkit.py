from . import __version__, __name__
import asyncio
from collections.abc import Iterable, ByteString
from functools import update_wrapper
import sys
from typing import Dict, Union

__all__ = (
    "make_headers",
    "isiter_noliterals",
    "same",
    "rearrange_params",
    "multiple_params",
)


def make_headers(token: str) -> Dict[str, str]:
    return {
        "dnt": "1",
        "authorization": f"Bearer {token}",
        "user-agent": f"{__name__}/{__version__} (Python {sys.version[:5]})",
        "accept-encoding": ", ".join(("br", "gzip", "deflate")),
        "cache-control": "no-cache",
        "pragma": "no-cache",
    }


def isiter_noliterals(obj):
    return isinstance(obj, Iterable) and not isinstance(obj, (str, ByteString))


def same(elements):
    return len(elements) == elements.count(elements[0])


def rearrange_params(args, kwargs):
    params = list(args) + list(kwargs.values())

    lengths = [len(param) for param in params if isiter_noliterals(param)]

    if len(lengths) < 1:
        total_length = 1
    else:
        if not same(lengths):
            raise ValueError(
                "All allowed iterable parameters must be of the same length.")

        total_length = lengths[0]

    for i, param in enumerate(params):
        if not isiter_noliterals(param):
            params[i] = [param] * total_length

    pars = params[:len(args)]

    kwpars = zip(
        [tuple(kwargs.keys())] * total_length,
        zip(*params[len(args):])
    )

    return list(zip(zip(*pars), [dict(i) for i in kwpars]))


def multiple_params(func):
    if asyncio.iscoroutinefunction(func):
        async def wrapper(*args, **kwargs):
            params = rearrange_params(args, kwargs)
            tasks = [asyncio.ensure_future(func(*a, **kw)) for a, kw in params]
            return await asyncio.gather(*tasks)
    else:
        def wrapper(*args, **kwargs):
            params = rearrange_params(args, kwargs)
            return [func(*a, **kw) for a, kw in params]
    return update_wrapper(wrapper, func)
