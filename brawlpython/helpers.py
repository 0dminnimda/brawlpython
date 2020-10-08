# -*- coding: utf-8 -*-


try:
    import orjson as json
except ImportError:
    try:
        import ujson as json
    except ImportError:
        import json

__all__ = ("json")
