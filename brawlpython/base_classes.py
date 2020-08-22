from types import TracebackType
from typing import Any, Optional, Type, TypeVar

__all__ = (
    "AsyncInitObject",
    "AsyncWith",
    "SyncWith",
)


class AsyncInitObject(object):
    # Inheriting this class allows you to define an async __init__.
    # So you can create objects by doing something like `await MyClass(params)`

    async def __new__(cls, *args: Any, **kwargs: Any) -> "AsyncInitObject":
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
