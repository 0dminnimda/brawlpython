# -*- coding: utf-8 -*-


try:
    import orjson as json
except ImportError:
    try:
        import ujson as json  # type: ignore
    except ImportError:
        import json  # type: ignore

__all__ = ("json")
