# -*- coding: utf-8 -*-

from typing import (Any, Callable, Coroutine, Dict, Generator, Generic,
                    Iterable, List, Mapping, Optional, Sequence, Set, Tuple,
                    Type, TypeVar, Union)

from .abc import AbcRequest, AbcResponse

__all__ = (
    "JSONV",
    "JSONT",
    "BOTH_JSON",
    "STRJSON",
    "DICT_STR",
    "MAPPING_STR",
    "STRS",
    "BOOLS",
    "NUMBER",
    "INTSTR",
    "STRBYTE",
    "ARGS",
    "AKW",
    "REQRESP",
    "HANDLER")

# SEE: https://github.com/python/typing/issues/182
JSONV = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONT = Union[Dict[str, JSONV], List[JSONV]]
BOTH_JSON = Union[JSONT, Sequence[JSONT]]  # FIXME: better not to use this
STRJSON = Union[str, JSONT]

DICT_STR = Dict[str, str]
MAPPING_STR = Mapping[str, str]

STRS = Union[Sequence[str], str]
BOOLS = Union[Sequence[bool], bool]

NUMBER = Union[int, float]
INTSTR = Union[int, str]
STRBYTE = Union[str, bytes]

ARGS = Sequence[Any]
AKW = Tuple[ARGS, Mapping[str, Any]]

HANDLER = Callable[["AsyncClient", Sequence[JSONT]], Sequence[JSONT]]
REQRESP = Tuple[Optional[AbcRequest], Optional[AbcResponse]]
