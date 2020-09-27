# -*- coding: utf-8 -*-

from collections import OrderedDict, defaultdict
from reprlib import recursive_repr
from types import TracebackType
from typing import Any, Optional, Type, TypeVar

__all__ = (
    "AsyncInitObject",
    "AsyncWith",
    "SyncWith",
    "DefaultOrderedDict")


# SEE: https://stackoverflow.com/questions/33128325#45364670
class AsyncInitObject(object):
    # Inheriting this class allows you to define an async __init__.
    # So you can create objects by doing something like `await MyClass(params)`

    async def __new__(cls, *args, **kwargs) -> "AsyncInitObject":
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(self):
        # the method must be overridden, therefore it does not need annotations
        pass


class AsyncWith(object):
    def __enter__(self) -> None:
        raise TypeError("Use `async with` instead")

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        # __exit__ should exist in pair with __enter__ but never executed
        pass

    async def __aenter__(self) -> "AsyncWith":
        return self

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        await self.close()

    async def close(self):
        self.test_close = True


class SyncWith(object):
    def __enter__(self) -> "SyncWith":
        return self

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        self.close()

    async def __aenter__(self) -> None:
        raise TypeError("Use `with` instead")

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        # __aexit__ should exist in pair with __aenter__ but never executed
        pass

    def close(self):
        self.test_close = True


# a reworked version from this answer:
# SEE: https://stackoverflow.com/questions/6190331#6190500
class DefaultOrderedDict(OrderedDict):
    def __init__(self, default_factory=None, *a, **kw):
        if default_factory is not None and not callable(default_factory):
            raise TypeError('first argument must be callable')

        super().__init__(*a, **kw)
        self.default_factory = default_factory

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return self.default_factory()

    @recursive_repr()
    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__, self.default_factory, list(self.items()))

    def __reduce__(self):
        args = ()
        if self.default_factory is not None:
            args = (self.default_factory,)

        inst_dict = vars(self).copy()
        for k in vars(DefaultOrderedDict()):
            inst_dict.pop(k, None)

        inst_dict = inst_dict or None
        return self.__class__, args, inst_dict, None, iter(self.items())

    def copy(self):
        return self.__class__(self.default_factory, self)
