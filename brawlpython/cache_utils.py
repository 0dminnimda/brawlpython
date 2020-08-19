import asyncio
from cachetools import keys, Cache
from functools import wraps, partial, update_wrapper

__all__ = (
    "async_cachedmethod",
    "cachedmethod",
    "iscorofunc",
    "get_decorator",
    "somecachedmethod",
    "classcache"
)


def async_cachedmethod(key=keys.hashkey, lock=None):
    """Decorator to wrap a class or instance method with a memoizing
    callable that saves results in a cache.
    """
    def decorator(method):
        if lock is None:
            async def wrapper(self, cache, args, kwargs):
                cache = self.cache
                k = key(*args, **kwargs)
                try:
                    return cache[k]
                except KeyError:
                    pass  # key not found
                v = await method(self, cache, *args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        else:
            async def wrapper(self, cache, args, kwargs):
                cache = self.cache
                k = key(*args, **kwargs)
                try:
                    with lock(self):
                        return cache[k]
                except KeyError:
                    pass  # key not found
                v = await method(self, cache, *args, **kwargs)
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
            def wrapper(self, cache, args, kwargs):
                k = key(*args, **kwargs)
                try:
                    return cache[k]
                except KeyError:
                    pass  # key not found
                v = method(self, cache, *args, **kwargs)
                try:
                    cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        else:
            def wrapper(self, cache, args, kwargs):
                k = key(*args, **kwargs)
                try:
                    with lock(self):
                        return cache[k]
                except KeyError:
                    pass  # key not found
                v = method(self, cache, *args, **kwargs)
                try:
                    with lock(self):
                        cache[k] = v
                except ValueError:
                    pass  # value too large
                return v
        return update_wrapper(wrapper, method)
    return decorator


def iscorofunc(func):
    return asyncio.iscoroutinefunction(func)


def get_decorator(func):
    if iscorofunc(func):
        return async_cachedmethod
    else:
        return cachedmethod


def somecachedmethod(func):
    key = partial(keys.hashkey, func.__name__)
    return get_decorator(func)(key=key)(func)


def classcache(func):
    wrap = somecachedmethod(func)
    if iscorofunc(func):
        async def wrapper(self, *args, **kwargs):
            cache = self.cache
            if cache is None:
                res = func(self, *args, **kwargs)
            else:
                res = wrap(self, cache, *args, **kwargs)
            return await res
    else:
        def wrapper(self, *args, **kwargs):
            cache = self.cache
            if cache is None:
                res = func(self, *args, **kwargs)
            else:
                res = wrap(self, cache, *args, **kwargs)
            return res
    return update_wrapper(wrapper, func)
