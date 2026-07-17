"""Runtime core for the Mind Upload SDK — transport, retries, error mapping.

Hand-written and stable; the per-operation methods live in the generated
`_operations.py`. Built entirely on the standard library.
"""
import json
import socket
import time
import urllib.error
import urllib.request

from ._errors import (
    APIError,
    AuthenticationError,
    MindUploadConnectionError,
    MindUploadError,
    RateLimitError,
)
from ._version import __version__

DEFAULT_BASE_URL = "https://partner.mindupload.app"
_AUTH_HEADER = "X-Partner-Key"
# Only server backpressure is retried. Operations are non-idempotent POSTs (rag
# spends credits, create_* mutate), so 5xx / network / timeout failures are
# surfaced immediately rather than risking a duplicate side effect.
_RETRY_STATUSES = frozenset({429})


class Result(dict):
    """A response envelope with attribute access.

    `result.success`, `result.jwt`, `result["jwt"]` all work; any field the API
    returns is available without the SDK needing to know it in advance.
    """

    __slots__ = ()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


class _BaseClient:
    """Transport, retry, and error handling shared by every operation."""

    def __init__(
        self,
        partner_key,
        *,
        base_url=DEFAULT_BASE_URL,
        preferred_language=None,
        timeout=30.0,
        max_retries=2,
        user_agent=None,
    ):
        if not partner_key:
            raise ValueError(
                "partner_key is required. It is a server-side secret \u2014 "
                "never expose it to a browser or ship it in client code."
            )
        self._partner_key = partner_key
        self._base_url = base_url.rstrip("/")
        self._preferred_language = preferred_language
        self._timeout = timeout
        self._max_retries = max_retries
        self._user_agent = user_agent or ("mindupload-python/" + __version__)

    def _request(self, operation, params):
        body = {key: value for key, value in params.items() if value is not None}
        if "preferred_language" not in body and self._preferred_language is not None:
            body["preferred_language"] = self._preferred_language
        data = json.dumps(body).encode("utf-8")
        url = self._base_url + "/v1/" + operation
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            _AUTH_HEADER: self._partner_key,
            "User-Agent": self._user_agent,
        }

        attempt = 0
        while True:
            request = urllib.request.Request(url, data=data, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    status = getattr(response, "status", None) or response.getcode()
                    raw = response.read()
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except urllib.error.HTTPError as exc:
                status = exc.code
                try:
                    raw = exc.read()
                    payload = json.loads(raw.decode("utf-8")) if raw else {}
                except ValueError:
                    payload = {}
                if status in _RETRY_STATUSES and attempt < self._max_retries:
                    attempt += 1
                    time.sleep(self._backoff(attempt, exc.headers))
                    continue
                self._raise(status, payload, operation, exc.headers)
            except urllib.error.URLError as exc:
                # Not retried: the request may already have reached the backend.
                raise MindUploadConnectionError(
                    "Could not reach the Mind Upload API for '" + operation + "': " + str(exc.reason),
                    operation=operation,
                ) from exc
            except (TimeoutError, socket.timeout) as exc:
                # A read/response timeout (socket.timeout is a bare TimeoutError,
                # not a URLError, so it must be caught explicitly).
                raise MindUploadConnectionError(
                    "Request to the Mind Upload API timed out for '" + operation + "'.",
                    operation=operation,
                ) from exc

            if not payload.get("success", False):
                raise MindUploadError(
                    payload.get("error_message") or (operation + " failed"),
                    operation=operation,
                    response=Result(payload),
                )
            return Result(payload)

    def _backoff(self, attempt, headers):
        if headers is not None:
            retry_after = headers.get("Retry-After")
            if retry_after:
                try:
                    return min(float(retry_after), 60.0)
                except (TypeError, ValueError):
                    pass
        return min(0.5 * (2 ** (attempt - 1)), 8.0)

    def _raise(self, status, payload, operation, headers):
        message = (payload.get("error_message") if isinstance(payload, dict) else None) or ("HTTP " + str(status))
        response = Result(payload if isinstance(payload, dict) else {})
        if status == 401:
            raise AuthenticationError(message, status=status, operation=operation, response=response)
        if status == 429:
            retry_after = None
            if headers is not None and headers.get("Retry-After"):
                try:
                    retry_after = float(headers.get("Retry-After"))
                except (TypeError, ValueError):
                    retry_after = None
            raise RateLimitError(message, status=status, operation=operation, response=response, retry_after=retry_after)
        raise APIError(message, status=status, operation=operation, response=response)
