# -*- coding: utf-8 -*-

from . import __version__, __name__
from .cache_utils import somecachedmethod, iscorofunc
from asyncio import ensure_future as ensure, gather
from collections.abc import Iterable, ByteString, Mapping
from functools import update_wrapper
import sys
from typing import Dict, Union

__all__ = (
    "default_headers",
    "make_headers",
    "isiter_noliterals",
    "isunit",
    "isempty",
    "ismapping",
    "same",
    "unique",
    "check_kwargs",
    "check_args",
    "check_params",
    "_rearrange_params",
    "rearrange_params",
    "multiparams",
    "multiparams_classcache"
)


def default_headers() -> Dict[str, str]:
    return {
        "dnt": "1",
        "user-agent": f"{__name__}/{__version__} (Python {sys.version[:5]})",
        "accept-encoding": ", ".join(("gzip", "deflate")),
        "cache-control": "no-cache",
        "pragma": "no-cache",
    }


def make_headers(token: str) -> Dict[str, str]:
    return {"authorization": f"Bearer {token}"}


def isiter_noliterals(obj):
    return isinstance(obj, Iterable) and not isinstance(obj, (str, ByteString))


def isunit(obj):
    return len(obj) == 1
    # isinstance(obj, tuple) and .


def isempty(obj):
    return len(obj) == 0


def ismapping(obj):
    return isinstance(obj, Mapping)


def isrequiredtype(obj):
    return (
        isiter_noliterals(obj) and not ismapping(obj)
        and not isempty(obj))


def same(elements):
    return len(elements) == elements.count(elements[0])


def unique(x):
    seen = list()
    return not any(i in seen or seen.append(i) for i in x)


def check_kwargs(kwargs):
    lengths = []
    for key, param in kwargs.items():
        p_type = type(param)
        if isrequiredtype(param):
            if isunit(param):
                kwargs[key] = ("u", param[0], p_type)
            else:
                lengths.append(len(param))
                kwargs[key] = ("m", iter(param), p_type)
        else:
            kwargs[key] = ("u", param, p_type)

    return kwargs, lengths


def check_args(args):
    args = list(args)
    lengths = []
    for i, param in enumerate(args):
        p_type = type(param)
        if isrequiredtype(param):
            if isunit(param):
                args[i] = ("u", param[0], p_type)
            else:
                lengths.append(len(param))
                args[i] = ("m", iter(param), p_type)
        else:
            args[i] = ("u", param, p_type)

    return args, lengths


def check_params(args, kwargs):
    all_args, args_lengths = check_args(args[:])
    all_kwargs, kwargs_lengths = check_kwargs(kwargs.copy())

    lengths = args_lengths + kwargs_lengths

    if len(lengths) < 1:
        total_length = 1
    else:
        if not same(lengths):
            raise ValueError(
                "All allowed iterable parameters must be of the same length.")

        total_length = lengths[0]

    return all_args, all_kwargs, total_length


def _rearrange_params(args, kwargs):
    all_args, all_kwargs, length = check_params(args[:], kwargs.copy())

    for _ in range(length):
        new_args = []
        for (kind, val, p_type) in all_args:
            if kind == "m":
                val = next(val)
                #val = p_type([val])
            new_args.append(val)

        new_kwargs = {}
        for key, (kind, val, p_type) in all_kwargs.items():
            if kind == "m":
                val = next(val)
                #val = p_type([val])
            new_kwargs[key] = val

        yield new_args, new_kwargs


def rearrange_params(*args, **kwargs):
    return _rearrange_params(args, kwargs)


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
