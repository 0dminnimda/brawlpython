# -*- coding: utf-8 -*-

import asyncio
from functools import partial, update_wrapper, wraps

from cachetools import Cache, keys

__all__ = (
    "NaN",
    "async_cachedmethod",
    "cachedmethod",
    "iscorofunc",
    "get_decorator",
    "somecachedmethod")


class NaN:
    "NaN"
    pass


def async_cachedmethod(key=keys.hashkey, lock=None):
    """Decorator to wrap a class or instance method with a memoizing
    callable that saves results in a cache.
    """
    def decorator(method):
        if lock is None:
            async def wrapper(self, *args, **kwargs):
                k = key(*args, **kwargs)
                cache = self.cache
                get_k = cache.get(k, NaN)
                if get_k != NaN:
                    return get_k
                v = await method(self, *args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        else:
            async def wrapper(self, *args, **kwargs):
                k = key(*args, **kwargs)
                cache = self.cache
                with lock(self):
                    get_k = cache.get(k, NaN)
                if get_k != NaN:
                    return get_k
                v = await method(self, *args, **kwargs)
                try:
                    with lock(self):
                        cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        return update_wrapper(wrapper, method)
    return decorator


def cachedmethod(key=keys.hashkey, lock=None):
    """Decorator to wrap a class or instance method with a memoizing
    callable that saves results in a cache.
    """
    def decorator(method):
        if lock is None:
            def wrapper(self, *args, **kwargs):
                k = key(*args, **kwargs)
                cache = self.cache
                get_k = cache.get(k, NaN)
                if get_k != NaN:
                    return get_k
                v = method(self, *args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        else:
            def wrapper(self, *args, **kwargs):
                k = key(*args, **kwargs)
                cache = self.cache
                with lock(self):
                    get_k = cache.get(k, NaN)
                if get_k != NaN:
                    return get_k
                v = method(self, *args, **kwargs)
                try:
                    with lock(self):
                        cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        return update_wrapper(wrapper, method)
    return decorator


def halfcachedmethod(func):
    def wrapper(self, *args, **kwargs):
        self._k = key(*args, **kwargs)
        get_k = self.cache.get(self._k, NaN)
        if get_k != NaN:
            return get_k
        return method(self, *args, **kwargs)


def async_halfcachedmethod(func):
    def wrapper(self, *args, **kwargs):
        self._k = key(*args, **kwargs)
        get_k = self.cache.get(self._k, NaN)
        if get_k != NaN:
            return get_k
        return method(self, *args, **kwargs)


def iscorofunc(func):
    return asyncio.iscoroutinefunction(func)


def iscoro(func):
    return asyncio.iscoroutine(func)


def get_decorator(func):
    if iscorofunc(func):
        return async_cachedmethod
    else:
        return cachedmethod


def somecachedmethod(func):
    # key = partial(keys.hashkey, func.__name__)
    return get_decorator(func)()(func)  # key=key
