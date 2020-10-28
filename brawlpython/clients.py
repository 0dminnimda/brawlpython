# -*- coding: utf-8 -*-

import asyncio
from configparser import ConfigParser
from typing import (Any, Callable, Coroutine, Dict, Generator, Generic,
                    Iterable, List, Mapping, Optional, Sequence, Set, Tuple,
                    Type, TypeVar, Union)
from functools import wraps, update_wrapper
from .abc import AbcAsyncInit, AbcAsyncWith
from .api import (API, CHI, KIND_KEYS, KIND_VALS, KINDS, OFFIC, OFFICS, STAR,
                  UNOFFICS, default_api_dict)
from .api_toolkit import rearrange_params
from .sessions import Session
from .typedefs import (AKW, BOOLS, BOTH_JSON, DICT_STR, HANDLER, INTSTR, JSONT,
                       NUMBER, STRS)

__all__ = (
    "Client"
)


class Client(AbcAsyncWith):
    async def __ainit__(self, session) -> None:
        if session is None:
            self.session = Session()
        else:
            self.session = session

    @classmethod
    async def init(cls, session: Optional[Session] = None) -> "Client":
        instance = cls()
        await instance.__ainit__(session)
        return instance

    async def close(self):
        pass
