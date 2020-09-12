# -*- coding: utf-8 -*-

from typing import TypeVar

__all__ = (
    "R",
    "L",
    "URLS",
    "PARAMS",
    "RETURN",
    "HANDLER")

R = TypeVar("R", bound="Union[Dict[str, Any], List[Dict[str, Any]]]")

L = TypeVar("L", bound="List[Union[Dict[str, Any], List[Dict[str, Any]]]]")

URLS = TypeVar("URLS", bound="Union[List[str], str]")

PARAMS = TypeVar(
    "PARAMS", bound="Sequence[Sequence[Sequence[Any], Mapping[Any, Any]]]")

RETURN = TypeVar("RETURN", bound="Dict[str, Any]")

HANDLER = TypeVar("HANDLER", bound="Callable[[AsyncClient, L], L]")
