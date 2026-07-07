"""Exceptions raised by the Mind Upload SDK.

Every failure — a logical failure (`success: false`), an authentication or
rate-limit rejection, an unexpected HTTP status, or a network problem — is a
`MindUploadError`, so a single `except MindUploadError` catches everything.
"""


class MindUploadError(Exception):
    """Base class for every Mind Upload error."""

    def __init__(self, message, *, operation=None, response=None):
        super().__init__(message)
        self.message = message
        self.operation = operation
        self.response = response
        self.status = None  # overridden by APIError; always present so e.status is safe


class APIError(MindUploadError):
    """The API returned an error HTTP status (or an unexpected response)."""

    def __init__(self, message, *, status=None, operation=None, response=None):
        super().__init__(message, operation=operation, response=response)
        self.status = status


class AuthenticationError(APIError):
    """The partner key was missing, malformed, or rejected (HTTP 401)."""


class RateLimitError(APIError):
    """A rate limit or credit cap was hit (HTTP 429).

    `retry_after` is the server-advised wait in seconds, when provided.
    """

    def __init__(self, message, *, status=None, operation=None, response=None, retry_after=None):
        super().__init__(message, status=status, operation=operation, response=response)
        self.retry_after = retry_after


class MindUploadConnectionError(MindUploadError):
    """The API could not be reached (DNS, TLS, timeout, or network failure)."""
