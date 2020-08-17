class ClientException(Exception):
    """
    Base class for all client exceptions.
    """


class ClientResponseError(ClientException):
    """
    Connection error during reading response.
    """

    def __init__(self, reason: str = "", message: str = ""):
        self.reason = reason
        self.message = message


class UnexpectedResponseCode(ClientResponseError):
    """
    Occurs if the response code was not described
    in the official api documentation.
    """

    def __init__(self, code: int, **kwargs):
        self.code = code
        super().__init__(**kwargs)


class BadRequest(ClientResponseError):
    """
    Client provided incorrect parameters for the request.
    """

    code = 400


class Forbidden(ClientResponseError):
    """
    Access denied, either because of missing/incorrect credentials or
    used API token does not grant access to the requested resource.
    """

    code = 403


class NotFound(ClientResponseError):
    """
    Resource was not found.
    """

    code = 404


class TooManyRequests(ClientResponseError):
    """
    Request was throttled, because amount of requests
    was above the threshold defined for the used API token.
    """

    code = 429


class InternalServerError(ClientResponseError):
    """
    Unknown error happened when handling the request.
    """

    code = 500


class ServiceUnavailable(ClientResponseError):
    """
    Service is temprorarily unavailable because of maintenance.
    """

    code = 503