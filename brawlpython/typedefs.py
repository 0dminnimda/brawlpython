# -*- coding: utf-8 -*-

from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generator,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)


__all__ = (
    "JSONV",
    "JSONT",
    "JSONSEQ",
    "URLS",
    "RETURN",
    "HANDLER",
    "NUMBER")

# SEE: https://github.com/python/typing/issues/182
JSONV = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONT = Union[Dict[str, JSONV], List[JSONV]]

JSONSEQ = Sequence[JSONT]

URLS = Union[List[str], str]

RETURN = Dict[str, Any]

HANDLER = Callable[["AsyncClient", JSONSEQ], JSONSEQ]

NUMBER = Union[int, float]
