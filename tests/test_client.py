"""Runtime tests for the Mind Upload SDK, using a mocked transport.

These verify the hand-written core: request shaping (URL, method, headers,
dropping unset params, injecting the client locale) and the envelope -> error
mapping. No network access.
"""
import io
import json
import socket
import unittest
import urllib.error
import urllib.request

from mindupload import (
    APIError,
    AuthenticationError,
    MindUpload,
    MindUploadConnectionError,
    MindUploadError,
    RateLimitError,
)


class _Resp(io.BytesIO):
    def __init__(self, payload, status=200):
        super().__init__(json.dumps(payload).encode("utf-8"))
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def getcode(self):
        return self.status


class Base(unittest.TestCase):
    def setUp(self):
        self.captured = {}
        self._orig = urllib.request.urlopen

    def tearDown(self):
        urllib.request.urlopen = self._orig

    def stub(self, responder):
        def fake(request, timeout=None):
            self.captured["url"] = request.full_url
            self.captured["method"] = request.get_method()
            self.captured["headers"] = {k.lower(): v for k, v in request.header_items()}
            self.captured["body"] = json.loads(request.data.decode("utf-8")) if request.data else {}
            self.captured["timeout"] = timeout
            return responder()

        urllib.request.urlopen = fake

    def respond(self, payload, status=200):
        def responder():
            return _Resp(payload, status)

        self.stub(responder)


class RequestShapeTest(Base):
    def test_request_shape_and_unset_params_dropped(self):
        self.respond({"success": True, "jwt": "tok", "decrypted_user": {"id": 1}})
        mu = MindUpload(partner_key="pk_test", preferred_language="en")
        result = mu.login(username="ada", password="pw")
        self.assertEqual(self.captured["method"], "POST")
        self.assertTrue(self.captured["url"].endswith("/v1/login"))
        self.assertEqual(self.captured["headers"]["x-partner-key"], "pk_test")
        self.assertIn("mindupload-python/", self.captured["headers"]["user-agent"])
        # unset params dropped; client locale injected
        self.assertEqual(self.captured["body"], {"username": "ada", "password": "pw", "preferred_language": "en"})
        self.assertEqual(result.jwt, "tok")
        self.assertEqual(result["decrypted_user"], {"id": 1})

    def test_per_call_language_overrides_client_default(self):
        self.respond({"success": True})
        mu = MindUpload(partner_key="pk_test", preferred_language="en")
        mu.check_username(username="ada", preferred_language="zh-cn")
        self.assertEqual(self.captured["body"]["preferred_language"], "zh-cn")

    def test_missing_partner_key_raises(self):
        with self.assertRaises(ValueError):
            MindUpload(partner_key="")


class ErrorMappingTest(Base):
    def test_logical_failure_raises_mindupload_error(self):
        self.respond({"success": False, "error_message": "no such user"})
        mu = MindUpload(partner_key="pk")
        with self.assertRaises(MindUploadError) as ctx:
            mu.get_user(username="nobody")
        self.assertEqual(ctx.exception.message, "no such user")
        self.assertEqual(ctx.exception.operation, "get_user")
        self.assertNotIsInstance(ctx.exception, APIError)

    def _http_error(self, status, payload, headers=None):
        def raise_it():
            raise urllib.error.HTTPError(
                "https://x/v1/op", status, "err", headers or {}, io.BytesIO(json.dumps(payload).encode("utf-8"))
            )
        return raise_it

    def test_401_is_authentication_error(self):
        self.stub(self._http_error(401, {"success": False, "error_message": "bad key"}))
        mu = MindUpload(partner_key="pk", max_retries=0)
        with self.assertRaises(AuthenticationError) as ctx:
            mu.login(username="a")
        self.assertEqual(ctx.exception.status, 401)

    def test_429_is_rate_limit_with_retry_after_after_retries(self):
        calls = {"n": 0}

        def responder():
            calls["n"] += 1
            raise urllib.error.HTTPError("https://x/v1/op", 429, "slow", {"Retry-After": "0"}, io.BytesIO(b"{}"))

        self.stub(responder)
        mu = MindUpload(partner_key="pk", max_retries=1)
        with self.assertRaises(RateLimitError) as ctx:
            mu.rag(username="a")
        self.assertEqual(ctx.exception.status, 429)
        self.assertEqual(ctx.exception.retry_after, 0.0)
        self.assertEqual(calls["n"], 2)  # 1 try + 1 retry

    def test_500_is_api_error_and_not_retried(self):
        calls = {"n": 0}

        def responder():
            calls["n"] += 1
            raise urllib.error.HTTPError(
                "https://x/v1/op", 500, "boom", {}, io.BytesIO(b'{"success":false,"error_message":"boom"}')
            )

        self.stub(responder)
        mu = MindUpload(partner_key="pk", max_retries=2)
        with self.assertRaises(APIError) as ctx:
            mu.rag(username="a")
        self.assertEqual(ctx.exception.status, 500)
        self.assertEqual(calls["n"], 1)  # 5xx is NOT retried (non-idempotent POST)

    def test_503_is_retried(self):
        calls = {"n": 0}

        def responder():
            calls["n"] += 1
            raise urllib.error.HTTPError("https://x/v1/op", 503, "down", {"Retry-After": "0"}, io.BytesIO(b"{}"))

        self.stub(responder)
        mu = MindUpload(partner_key="pk", max_retries=1)
        with self.assertRaises(APIError) as ctx:
            mu.rag(username="a")
        self.assertEqual(ctx.exception.status, 503)
        self.assertEqual(calls["n"], 2)  # 503 backpressure IS retried

    def test_network_error_is_connection_error_and_not_retried(self):
        calls = {"n": 0}

        def responder():
            calls["n"] += 1
            raise urllib.error.URLError("no route to host")

        self.stub(responder)
        mu = MindUpload(partner_key="pk", max_retries=2)
        with self.assertRaises(MindUploadConnectionError):
            mu.rag(username="a")
        self.assertEqual(calls["n"], 1)

    def test_read_timeout_is_connection_error(self):
        def responder():
            raise socket.timeout("timed out")

        self.stub(responder)
        mu = MindUpload(partner_key="pk", max_retries=2)
        with self.assertRaises(MindUploadConnectionError):
            mu.rag(username="a")


if __name__ == "__main__":
    unittest.main()
