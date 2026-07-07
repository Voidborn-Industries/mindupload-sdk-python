"""Mind Upload \u2014 official server-side SDK for the partner API.

    from mindupload import MindUpload

    mu = MindUpload(partner_key="pk_live_...")
    session = mu.login(username="ada", password="...")
    reply = mu.rag(username="ada", password=session.jwt, codename="muse", text="hi")
    print(reply.response_text)

Digital consciousness. Yours forever.
"""
from ._client import Result
from ._errors import (
    APIError,
    AuthenticationError,
    MindUploadConnectionError,
    MindUploadError,
    RateLimitError,
)
from ._operations import MindUpload
from ._version import __version__

__all__ = [
    "MindUpload",
    "Result",
    "MindUploadError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "MindUploadConnectionError",
    "__version__",
]
