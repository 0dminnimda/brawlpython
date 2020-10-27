# -*- coding: utf-8 -*-

from typing import Any

__all__ = (
    "BrawlPythonException",

    "ClientException",

    "ClientResponseError",
    "UnexpectedResponseCode",
    "ExpectedResponseCode",
    "BadRequest", "Forbidden", "NotFound",
    "TooManyRequests", "InternalServerError",
    "ServiceUnavailable", "WITH_CODE")


class BrawlPythonException(Exception):
    """Base class for all brawlpython exceptions."""


class ClientException(BrawlPythonException):
    """Base class for all client exceptions."""


class ClientResponseError(ClientException):
    """Connection error during reading response."""

    code: int = 0

    def __init__(self, url: str, message: str = "no message") -> None:
        self.url = url
        self.message = message

    def __repr__(self) -> str:
        return "{0.__class__.__name__}({0.url!r}, {0.message!r})".format(self)

    def __str__(self) -> str:
        return "{0.url} -> {0.code}; {0.message}".format(self)

    def __eq__(self, other) -> bool:
        return ((dir(self) == dir(other))
                and (vars(self) == vars(other)))


class UnexpectedResponseCode(ClientResponseError):
    """Occurs if the response code was not described
    in the official api documentation.
    """

    def __init__(self, code: int, *args, **kwargs) -> None:
        self.code = code
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return ("{0.__class__.__name__}({0.url!r}, {0.code!r}, "
                "{0.message!r})").format(self)


class ExpectedResponseCode(ClientResponseError):
    """Occurs if the response code was described
    in the official api documentation.
    """


class BadRequest(ExpectedResponseCode):
    """Client provided incorrect parameters for the request."""

    code = 400


class Forbidden(ExpectedResponseCode):
    """Access denied, either because of missing/incorrect credentials or
    used API key/token does not grant access to the requested resource.
    """

    code = 403


class NotFound(ExpectedResponseCode):
    """Resource was not found."""

    code = 404


class TooManyRequests(ExpectedResponseCode):
    """Request was throttled, because amount of requests
    was above the threshold defined for the used API key/token.
    """

    code = 429


class InternalServerError(ExpectedResponseCode):
    """Unknown error happened when handling the request."""

    code = 500


class ServiceUnavailable(ExpectedResponseCode):
    """Service is temprorarily unavailable because of maintenance."""

    code = 503


WITH_CODE = [
    BadRequest, Forbidden, NotFound,
    TooManyRequests, InternalServerError, ServiceUnavailable
]
