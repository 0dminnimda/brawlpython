# -*- coding: utf-8 -*-


from abc import ABC, abstractmethod, abstractproperty
from types import TracebackType
from typing import Any, Collection, Optional, Type, TypeVar

__all__ = ("AbcAsyncInit",
           "AbcAsyncWith",
           "AbcSyncWith",
           "AbcSession")


# SEE: https://stackoverflow.com/questions/33128325#45364670
class AbcAsyncInit(ABC):
    '''Inheritance from this class forces you to define asynchronous __init__
    and maintains its asynchronous behavior.
    '''

    async def __new__(cls, *args, **kwargs) -> "AsyncInitObject":
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    @abstractmethod
    async def __init__(self):
        ...


class AbcAsyncWith(ABC):
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

    @abstractmethod
    async def close(self):
        ...


class AbcSyncWith(ABC):
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

    @abstractmethod
    def close(self):
        ...


class AbcSession(ABC):
    @abstractmethod
    def close(self):
        ...

    @abstractproperty
    def closed(self):
        ...


class AbcRequest(ABC):
    @abstractmethod
    def send(self):
        ...
