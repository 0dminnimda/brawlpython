from cachetools import keys, Cache, cached
from functools import wraps

__all__ = (
    "async_cached",
    "self_cache"
)


# annotating the remaining parameters of this function causes too many problems
def async_cached(cache: Cache, key=keys.hashkey, lock=None):
    def decorator(func):
        if lock is None:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                try:
                    return cache[k]
                except KeyError:
                    pass  # key not found

                val = await func(*args, **kwargs)

                try:
                    cache[k] = val
                except ValueError:
                    pass  # val too large

                return val
        else:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                k = key(*args, **kwargs)
                try:
                    async with lock:
                        return cache[k]
                except KeyError:
                    pass  # key not found

                val = await func(*args, **kwargs)

                try:
                    async with lock:
                        cache[k] = val
                except ValueError:
                    pass  # val too large

                return val
        return wrapper
    return decorator


def self_cache(*, sync: bool):
    def decorator(func):
        if not sync:
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                new_func = async_cached(cache=self.cache)(func)
                return await new_func(self, *args, **kwargs)
        else:
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                new_func = cached(cache=self.cache)(func)
                return new_func(self, *args, **kwargs)

        return wrapper
    return decorator
