# -*- coding: utf-8 -*-

from typing import Any

__all__ = (
    "ClientException",

    "ClientResponseError",
    "UnexpectedResponseCode",
    "BadRequest", "Forbidden", "NotFound",
    "TooManyRequests", "InternalServerError",
    "ServiceUnavailable", "WITH_CODE",
)


class ClientException(Exception):
    """Base class for all client exceptions."""


class ClientResponseError(ClientException):
    """Connection error during reading response."""

    def __init__(self, url: str, reason: str = "without a reason",
                 message: str = "no message"):
        self.url = url
        self.reason = reason
        self.message = message
        self.cause = "because " if reason != "without a reason" else ""

    def __repr__(self):
        return (
            "{0.__class__.__name__}({0.url!r}, "
            "{0.reason!r}, {0.message!r})").format(self)

    def __str__(self):
        return (
            "{0.url} -> {0.code}, {0.cause}"
            "{0.reason}, {0.message}").format(self)

    def __eq__(self, other):
        return (
            (dir(self) == dir(other))
            and (vars(self) == vars(other)))


class UnexpectedResponseCode(ClientResponseError):
    """Occurs if the response code was not described
    in the official api documentation.
    """

    def __init__(self, url: str, code: int, *args: Any, **kwargs: Any):
        self.code = code
        super().__init__(url, *args, **kwargs)

    def __repr__(self):
        return (
            "{0.__class__.__name__}({0.url!r}, {0.code!r}, "
            "{0.reason!r}, {0.message!r})").format(self)


class BadRequest(ClientResponseError):
    """Client provided incorrect parameters for the request."""

    code = 400


class Forbidden(ClientResponseError):
    """Access denied, either because of missing/incorrect credentials or
    used API token does not grant access to the requested resource.
    """

    code = 403


class NotFound(ClientResponseError):
    """Resource was not found."""

    code = 404


class TooManyRequests(ClientResponseError):
    """Request was throttled, because amount of requests
    was above the threshold defined for the used API token.
    """

    code = 429


class InternalServerError(ClientResponseError):
    """Unknown error happened when handling the request."""

    code = 500


class ServiceUnavailable(ClientResponseError):
    """Service is temprorarily unavailable because of maintenance."""

    code = 503


WITH_CODE = [
    BadRequest, Forbidden, NotFound,
    TooManyRequests, InternalServerError, ServiceUnavailable
]
