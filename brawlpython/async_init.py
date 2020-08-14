from typing import Any, Type, TypeVar


A = TypeVar('A', bound='AsyncInitObject')


class AsyncInitObject(object):
    # Inheriting this class allows you to define an async __init__.
    # So you can create objects by doing something like `await MyClass(params)`

    async def __new__(cls: Type[A], *args: Any, **kwargs: Any) -> A:
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(self):
        # the method must be overridden, therefore it does not need annotations
        pass
