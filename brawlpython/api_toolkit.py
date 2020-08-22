from . import __version__, __name__
from .cache_utils import somecachedmethod, iscorofunc
from asyncio import ensure_future as ensure, gather
from collections.abc import Iterable, ByteString
from functools import update_wrapper
import sys
from typing import Dict, Union

__all__ = (
    "make_headers",
    "isiter_noliterals",
    "isunitlist",
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


def make_headers(token: str) -> Dict[str, str]:
    return {
        "dnt": "1",
        "authorization": f"Bearer {token}",
        "user-agent": f"{__name__}/{__version__} (Python {sys.version[:5]})",
        "accept-encoding": ", ".join(("gzip", "deflate")),
        "cache-control": "no-cache",
        "pragma": "no-cache",
    }


def isiter_noliterals(obj):
    return isinstance(obj, Iterable) and not isinstance(obj, (str, ByteString))


def isunitlist(obj):
    return isinstance(obj, list) and len(obj) == 1


def same(elements):
    return len(elements) == elements.count(elements[0])


def unique(x):
    seen = list()
    return not any(i in seen or seen.append(i) for i in x)


def check_kwargs(kwargs):
    lengths = []
    for key, param in kwargs.items():
        if isiter_noliterals(param):
            if isunitlist(param):
                kwargs[key] = ("u", param[0])
            else:
                lengths.append(len(param))
                kwargs[key] = ("m", iter(param))
        else:
            kwargs[key] = ("u", param)

    return kwargs, lengths


def check_args(args):
    args = list(args)
    lengths = []
    for i, param in enumerate(args):
        if isiter_noliterals(param):
            if isunitlist(param):
                args[i] = ("u", param[0])
            else:
                lengths.append(len(param))
                args[i] = ("m", iter(param))
        else:
            args[i] = ("u", param)

    return args, lengths


def check_params(args, kwargs):
    all_args, args_lengths = check_args(args)
    all_kwargs, kwargs_lengths = check_kwargs(kwargs)

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
    all_args, all_kwargs, length = check_params(args, kwargs)

    for _ in range(length):
        new_args = []
        for (type_, val) in all_args:
            if type_ == "m":
                val = next(val)
            new_args.append(val)

        new_kwargs = {}
        for key, (type_, val) in all_kwargs.items():
            if type_ == "m":
                val = next(val)
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


def multiparams_classcache(func):
    wrap = somecachedmethod(func)
    if iscorofunc(func):
        async def wrapper(self, *args, **kwargs):
            cache = self.cache
            params = rearrange_params(self, *args, **kwargs)
            if cache is None:
                tasks = [ensure(func(*a, **kw)) for a, kw in params]
            else:
                tasks = [ensure(wrap(*a, **kw)) for a, kw in params]
            return await gather(*tasks)
    else:
        def wrapper(self, *args, **kwargs):
            cache = self.cache
            params = rearrange_params(self, *args, **kwargs)
            if cache is None:
                res = [func(*a, **kw) for a, kw in params]
            else:
                res = [wrap(*a, **kw) for a, kw in params]
            return res
    return update_wrapper(wrapper, func)
