# -*- coding: utf-8 -*-


from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Collection, Optional, Type, TypeVar

__all__ = ("AbcAsyncInit",
           "AbcAsyncWith",
           "AbcSyncWith",
           "AbcSession",
           "AbcRequest",
           "AbcResponse",
           "AbcAttemptCycle",
           "AbcCollector")


# SEE: https://stackoverflow.com/questions/33128325#45364670
class AbcAsyncInit(ABC):
    '''Inheritance from this class forces you to define asynchronous __init__
    and maintains its asynchronous behavior.
    '''

    __slots__ = ()

    async def __new__(cls, *args, **kwargs) -> "AsyncInitObject":
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    @abstractmethod
    async def __init__(self):
        ...


class AbcAsyncWith(ABC):
    __slots__ = ()

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
    __slots__ = ()

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
    __slots__ = ()

    @abstractmethod
    def close(self):
        ...

    @property
    @abstractmethod
    def closed(self):
        ...


class AbcRequest(ABC):
    __slots__ = ()

    @abstractmethod
    def send(self):
        ...


class AbcResponse(ABC):
    __slots__ = ()

    @abstractmethod
    def raise_code(self):
        ...

    @abstractmethod
    def json(self):
        ...


class AbcAttemptCycle(ABC):
    __slots__ = ()

    @abstractmethod
    def run(self):
        ...


class AbcCollector(ABC):
    __slots__ = ()

    @abstractmethod
    def add_request(self):
        ...
