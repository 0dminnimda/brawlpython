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
    "same",
    "rearrange_params",
    "multiparams",
    "multiparams_classcache"
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


def isunitlist(obj):
    return isinstance(obj, list) and len(obj) == 1


def same(elements):
    return len(elements) == elements.count(elements[0])


def check_kwargs(kwargs):
    lengths = []
    for key, param in kwargs.items():
        if isiter_noliterals(param):
            if isunitlist(param):
                kwargs[key] = {"u": param[0]}
            else:
                lengths.append(len(param))
                kwargs[key] = {"m": (param)}#iter
        else:
            kwargs[key] = {"u": param}

    if len(lengths) < 1:
        total_length = 1
    else:
        if not same(lengths):
            raise ValueError(
                "All allowed iterable parameters must be of the same length.")

        total_length = lengths[0]

    return kwargs, total_length


def check_args(args):
    args = list(args)
    lengths = []
    for i, param in enumerate(args):
        if isiter_noliterals(param):
            if isunitlist(param):
                args[i] = {"u": param[0]}
            else:
                lengths.append(len(param))
                args[i] = {"m": (param)}#iter 
        else:
            args[i] = {"u": param}

    if len(lengths) < 1:
        total_length = 1
    else:
        if not same(lengths):
            raise ValueError(
                "All allowed iterable parameters must be of the same length.")

        total_length = lengths[0]

    return args, total_length


def check_params(args, kwargs):
    all_args, args_length = check_args(args)
    all_kwargs, kwargs_length = check_kwargs(kwargs)

    if args_length != kwargs_length:
        raise ValueError(
            "All allowed iterable parameters must be of the same length.")

    return all_args, all_kwargs, args_length


def _rearrange_params(args, kwargs):
    all_args, all_kwargs, length = check_params(args, kwargs)

    z = zip(all_args, all_kwargs.items())

    for a, (k, v) in z:
        print(a, k, v)

    for i, param in enumerate(params):
        if not isiter_noliterals(param):
            params[i] = [param] * total_length

    pars = params[:len(args)]

    kwpars = zip(
        [tuple(kwargs.keys())] * total_length,
        zip(*params[len(args):])
    )

    return list(zip(zip(*pars), [dict(i) for i in kwpars]))


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


def multiparams_classcache(f):
    wrap = somecachedmethod(f)
    if iscorofunc(f):
        async def wrapper(*args, **kwargs):
            params = rearrange_params(args, kwargs)
            tasks = [ensure(f(*a, **kw)) for a, kw in params]
            return await gather(*tasks)

        async def wrapper(self, *args, **kwargs):
            cache = self.cache
            if cache is None:
                params = rearrange_params(*args, **kwargs)
                tasks = [ensure(f(self, *a, **kw)) for a, kw in params]
                res = f(self, *args, **kwargs)
            else:
                params = rearrange_params(cache, *args, **kwargs)
                tasks = [ensure(f(self, cache, *a, **kw)) for a, kw in params]
                res = wrap(self, cache, *args, **kwargs)
            return await res
    else:
        def wrapper(self, *args, **kwargs):
            cache = self.cache
            if cache is None:
                res = f(self, *args, **kwargs)
            else:
                res = wrap(self, cache, *args, **kwargs)
            return res

        def wrapper(*args, **kwargs):
            params = rearrange_params(args, kwargs)
            return [f(*a, **kw) for a, kw in params]
    return update_wrapper(wrapper, f)
