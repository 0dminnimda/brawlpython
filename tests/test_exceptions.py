# -*- coding: utf-8 -*-

import pytest
from brawlpython.exceptions import ClientResponseError, UnexpectedResponseCode


def test_repr():
    exc = ClientResponseError("1", "2", "3")
    assert eval(repr(exc)) == exc

    exc = UnexpectedResponseCode("1", 2, "3", "4")
    assert eval(repr(exc)) == exc


if __name__ == "__main__":
    import run_tests

    run_tests.run(__file__)
