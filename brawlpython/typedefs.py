# -*- coding: utf-8 -*-

from typing import TypeVar

__all__ = (
    "R",
    "L",
    "URLS"
)

R = TypeVar("R", bound="Union[Dict[str, Any], List[Dict[str, Any]]]")

L = TypeVar("L", bound="List[Union[Dict[str, Any], List[Dict[str, Any]]]]")

URLS = TypeVar("URLS", bound="Union[List[str], str]")
