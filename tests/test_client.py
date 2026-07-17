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
from unittest.mock import MagicMock, patch

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

    def test_wait_for_external_authorization_returns_exchanged_credentials(self):
        self.respond({
            "success": True,
            "status": "exchanged",
            "access_token": "access",
            "refresh_token": "refresh",
        })
        mu = MindUpload(partner_key="pk_test")
        result = mu.wait_for_external_authorization(
            device_code="mindupload_external_device_test",
            timeout=1,
        )
        self.assertEqual(result.access_token, "access")
        self.assertEqual(
            self.captured["body"]["device_code"],
            "mindupload_external_device_test",
        )

    def test_authorization_polling_backs_off_and_honors_slow_down(self):
        mu = MindUpload(partner_key="pk_test")
        mu.exchange_external_authorization = MagicMock(side_effect=[
            {"success": True, "status": "pending", "poll_interval": 5},
            {"success": True, "status": "slow_down", "poll_interval": 5},
            {"success": True, "status": "exchanged", "access_token": "access"},
        ])
        with patch("mindupload._operations.random.random", return_value=0.0), patch(
            "mindupload._operations.time.sleep"
        ) as sleep:
            result = mu.wait_for_external_authorization(
                device_code="mindupload_external_device_test",
                timeout=60,
            )

        self.assertEqual(result["access_token"], "access")
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [7.5, 12.5],
        )

    def test_authorization_polling_never_undercuts_server_interval(self):
        mu = MindUpload(partner_key="pk_test")
        mu.exchange_external_authorization = MagicMock(side_effect=[
            {"success": True, "status": "pending", "poll_interval": 60},
            {"success": True, "status": "slow_down", "poll_interval": 60},
            {"success": True, "status": "exchanged", "access_token": "access"},
        ])
        with patch("mindupload._operations.random.random", return_value=0.0), patch(
            "mindupload._operations.time.sleep"
        ) as sleep:
            mu.wait_for_external_authorization(
                device_code="mindupload_external_device_test",
                timeout=180,
            )

        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [60.0, 60.0],
        )

    def test_invocation_wait_replays_processing_until_succeeded(self):
        mu = MindUpload(partner_key="pk_test")
        mu.invoke_external_clone = MagicMock(side_effect=[
            # retry_after distinct from the 2.0 default so the assertion below
            # actually proves the server-advised delay is honored.
            {"success": True, "status": "processing", "retry_after_seconds": 5},
            {"success": True, "status": "succeeded", "response_text": "hi there"},
        ])
        with patch("mindupload._operations.random.random", return_value=0.0), patch(
            "mindupload._operations.time.sleep"
        ) as sleep:
            result = mu.wait_for_external_clone_invocation(
                access_token="mindupload_external_grant_test",
                installation_id="workspace-1",
                external_subject="member-1",
                clone_id="clone-1",
                text="hello",
                idempotency_key="event-1",
                timeout=60,
            )
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["response_text"], "hi there")
        self.assertEqual(mu.invoke_external_clone.call_count, 2)
        # Honored the server-advised retry_after (5s) before replaying.
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [5.0])

    def test_invocation_wait_retries_through_timeout_and_gateway_fault(self):
        mu = MindUpload(partner_key="pk_test")
        mu.invoke_external_clone = MagicMock(side_effect=[
            MindUploadConnectionError("timed out", operation="invoke_external_clone"),
            APIError("gateway", status=504, operation="invoke_external_clone"),
            {"success": True, "status": "succeeded", "response_text": "done"},
        ])
        with patch("mindupload._operations.random.random", return_value=0.0), patch(
            "mindupload._operations.time.sleep"
        ):
            result = mu.wait_for_external_clone_invocation(
                access_token="mindupload_external_grant_test",
                installation_id="workspace-1",
                external_subject="member-1",
                clone_id="clone-1",
                text="hello",
                idempotency_key="event-2",
                timeout=60,
            )
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(mu.invoke_external_clone.call_count, 3)

    def test_invocation_wait_surfaces_client_error_without_retrying(self):
        mu = MindUpload(partner_key="pk_test")
        mu.invoke_external_clone = MagicMock(side_effect=APIError(
            "bad request", status=400, operation="invoke_external_clone",
        ))
        with self.assertRaises(APIError) as ctx:
            mu.wait_for_external_clone_invocation(
                access_token="mindupload_external_grant_test",
                installation_id="workspace-1",
                external_subject="member-1",
                clone_id="clone-1",
                text="hello",
                idempotency_key="event-3",
                timeout=60,
            )
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(mu.invoke_external_clone.call_count, 1)

    def test_invocation_wait_does_not_retry_rate_limit(self):
        mu = MindUpload(partner_key="pk_test")
        mu.invoke_external_clone = MagicMock(side_effect=RateLimitError(
            "slow down", status=429, operation="invoke_external_clone",
        ))
        with self.assertRaises(RateLimitError):
            mu.wait_for_external_clone_invocation(
                access_token="mindupload_external_grant_test",
                installation_id="workspace-1",
                external_subject="member-1",
                clone_id="clone-1",
                text="hello",
                idempotency_key="event-4",
                timeout=60,
            )
        # A 429 is surfaced immediately, never retried into an infinite loop.
        self.assertEqual(mu.invoke_external_clone.call_count, 1)

    def test_invocation_wait_propagates_failed_receipt(self):
        mu = MindUpload(partner_key="pk_test")
        # A failed receipt surfaces as a logical failure (base MindUploadError,
        # not APIError), so it must propagate as terminal, not be replayed.
        mu.invoke_external_clone = MagicMock(side_effect=MindUploadError(
            "the external clone invocation failed and will not be retried",
            operation="invoke_external_clone",
        ))
        with self.assertRaises(MindUploadError) as ctx:
            mu.wait_for_external_clone_invocation(
                access_token="mindupload_external_grant_test",
                installation_id="workspace-1",
                external_subject="member-1",
                clone_id="clone-1",
                text="hello",
                idempotency_key="event-5",
                timeout=60,
            )
        self.assertNotIsInstance(ctx.exception, APIError)
        self.assertEqual(mu.invoke_external_clone.call_count, 1)


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

    def test_503_is_not_retried(self):
        calls = {"n": 0}

        def responder():
            calls["n"] += 1
            raise urllib.error.HTTPError("https://x/v1/op", 503, "down", {"Retry-After": "0"}, io.BytesIO(b"{}"))

        self.stub(responder)
        mu = MindUpload(partner_key="pk", max_retries=1)
        with self.assertRaises(APIError) as ctx:
            mu.rag(username="a")
        self.assertEqual(ctx.exception.status, 503)
        self.assertEqual(calls["n"], 1)

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
