import asyncio
from cachetools import keys, Cache, cachedmethod
from functools import wraps, partial, update_wrapper

__all__ = (
    "async_cachedmethod",
    "self_cache"
)


# annotating the remaining parameters of this function causes too many problems
def async_cachedmethod(cache: Cache, key=keys.hashkey, lock=None):
    """Decorator to wrap a class or instance method with a memoizing
    callable that saves results in a cache.
    """
    def decorator(method):
        if lock is None:
            async def wrapper(self, *args, **kwargs):
                c = cache(self)
                k = key(*args, **kwargs)
                try:
                    return c[k]
                except KeyError:
                    pass  # key not found
                v = await method(self, *args, **kwargs)
                try:
                    c[k] = v
                except ValueError:
                    pass  # value too large
                return v
        else:
            async def wrapper(self, *args, **kwargs):
                c = cache(self)
                k = key(*args, **kwargs)
                try:
                    with lock(self):
                        return c[k]
                except KeyError:
                    pass  # key not found
                v = await method(self, *args, **kwargs)
                try:
                    with lock(self):
                        c[k] = v
                except ValueError:
                    pass  # value too large
                return v
        return update_wrapper(wrapper, method)
    return decorator


def cache(self):
    return self.cache


def self_cache(func):
    key = partial(keys.hashkey, func.__name__)
    if asyncio.iscoroutinefunction(func):
        wrapper = async_cachedmethod(cache=cache, key=key)(func)
    else:
        wrapper = cachedmethod(cache=cache, key=key)(func)
    return update_wrapper(wrapper, func)
