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
    "JSONTYPE",
    "JSONSEQ",
    "STRS",
    "BOOLS",
    "JSONS",
    "HANDLER",
    "NUMBER",
    "INTSTR",
    "AKW",
    "STRBYTE")

# SEE: https://github.com/python/typing/issues/182
JSONVALS = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONTYPE = Union[Dict[str, JSONVALS], List[JSONVALS]]

JSONSEQ = Sequence[JSONTYPE]
JSONS = Union[JSONTYPE, JSONSEQ]

STRJSON = Union[str, JSONTYPE]

STRDICT = Dict[str, str]

# Tuple[]

STRS = Union[Sequence[str], str]

BOOLS = Union[Sequence[bool], bool]

HANDLER = Callable[["AsyncClient", JSONSEQ], JSONSEQ]

NUMBER = Union[int, float]

INTSTR = Union[int, str]

ARGS = Sequence[Any]

AKW = Tuple[ARGS, Mapping[str, Any]]

STRBYTE = Union[str, bytes]
