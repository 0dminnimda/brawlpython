# -*- coding: utf-8 -*-

import sys
from asyncio import ensure_future as ensure
from asyncio import gather
from collections.abc import ByteString, Collection, Mapping, Sized
from functools import update_wrapper
from typing import Dict, List, Union

from . import __name__, __version__
from .cache_utils import iscorofunc
from .typedefs import DICT_STR

__all__ = (
    "DEFAULT_HEADERS",
    "make_headers",
    "isliterals",
    "iscollection",
    "issized",
    "isunit",
    "isempty",
    "ismapping",
    "isrequiredcollection",
    "same",
    "unique",
    "prepare_param",
    "check_params",
    "_rearrange_params",
    "rearrange_params",
    "_rearrange_args",
    "rearrange_args",
    "multiparams",
    "add_api_name")


DEFAULT_HEADERS = {
    "dnt": "1",
    "user-agent": f"{__name__}/{__version__} (Python {sys.version[:5]})",
    "accept-encoding": ", ".join(("gzip", "deflate")),
    "cache-control": "no-cache",
    "content-type": "application/json",
    # "content-encoding": "utf-8"
    "pragma": "no-cache"}


def make_headers(api_key: str) -> DICT_STR:
    return {"authorization": f"Bearer {api_key}"}


def isliterals(obj):
    return isinstance(obj, (str, ByteString))


def iscollection(obj):
    return isinstance(obj, Collection)


def issized(obj):
    return isinstance(obj, Sized)


def isunit(obj):
    return issized(obj) and len(obj) == 1


def isempty(obj):
    return issized(obj) and len(obj) == 0


def ismapping(obj):
    return isinstance(obj, Mapping)


def isrequiredcollection(obj):
    return (
        iscollection(obj)
        and not isliterals(obj)
        and not ismapping(obj)
        and not isempty(obj))


def same(elements):
    return len(elements) == elements.count(elements[0])


def unique(x):
    seen = list()
    return not any(i in seen or seen.append(i) for i in x)  # type: ignore


def prepare_param(param, lengths):
    if isrequiredcollection(param):
        if isunit(param):
            return ("u", param[0])
        else:
            lengths.append(len(param))
            return ("m", iter(param))
    else:
        return ("u", param)


def check_params(args, kwargs):
    lengths: List[int] = []

    args = [prepare_param(param, lengths) for param in args]

    kwargs = {
        key: prepare_param(param, lengths) for key, param in kwargs.items()}

    if len(lengths) < 1:
        total_length = 1
    else:
        if not same(lengths):
            raise ValueError(
                "All allowed iterable parameters must be of the same length.")

        total_length = lengths[0]

    return args, kwargs, total_length


def _rearrange_params(args, kwargs):
    new_args, new_kwargs, length = check_params(args[:], kwargs.copy())

    for _ in range(length):
        current_args = []
        for (kind, val) in new_args:
            if kind == "m":
                val = next(val)
            current_args.append(val)

        current_kwargs = {}
        for key, (kind, val) in new_kwargs.items():
            if kind == "m":
                val = next(val)
            current_kwargs[key] = val

        yield tuple(current_args), current_kwargs


def rearrange_params(*args, **kwargs):
    return _rearrange_params(args, kwargs)


def _rearrange_args(args):
    for a, kw in _rearrange_params(args, {}):
        yield a


def rearrange_args(*args):
    return _rearrange_args(args)


def multiparams(func):
    if iscorofunc(func):
        async def wrapper(*args, **kwargs):
            params = _rearrange_params(args, kwargs)
            tasks = [ensure(func(*a, **kw)) for a, kw in params]
            return await gather(*tasks)
    else:
        def wrapper(*args, **kwargs):
            params = _rearrange_params(args, kwargs)
            return [func(*a, **kw) for a, kw in params]
    return update_wrapper(wrapper, func)
