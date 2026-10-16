"""Exercise owner consent and consultation through the actual MCP transport."""
import asyncio
import io
import importlib.util
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

if importlib.util.find_spec(name="mcp") is None:
    raise unittest.SkipTest("Install the optional MCP dependency to run connector tests.")

from mcp.client import Client
from mcp.client.stdio import StdioServerParameters
from mcp.types import CallToolResult

from mindupload import APIError, MindUpload, MindUploadError
from mindupload.mcp import create_server


_QUESTION = "Which of these options best fits my priorities?"
_TASK_IDENTIFIER = "task-one"
_DECISION_IDENTIFIER = "decision-one"
_INSTALLATION_IDENTIFIER = "test-installation"
_EXTERNAL_SUBJECT = "test-owner"
_CLONE_IDENTIFIER = "approved-clone"
_OTHER_CLONE_IDENTIFIER = "other-approved-clone"
_ACCESS_TOKEN = "private-test-access-token"
_REFRESH_TOKEN = "private-test-refresh-token"
_ROTATED_ACCESS_TOKEN = "private-rotated-access-token"
_ROTATED_REFRESH_TOKEN = "private-rotated-refresh-token"
_VERIFICATION_URL = "https://example.com/owner-consent"
_AUTHORIZATION_REQUIRED = "authorization_required"
_SUCCEEDED = "succeeded"
_MODULE = "mindupload.mcp"
_THREAD_WAIT_TIMEOUT_SECONDS = 5
_OVERLAP_OBSERVATION_SECONDS = 0.1


class MindConsultationTest(unittest.IsolatedAsyncioTestCase):
    """Keep the network boundary mocked while the protocol remains real."""

    def setUp(self) -> None:
        """Prepare process-local consent and a controllable connector clock.

        Returns:
            None.
        """
        self.partner_client = MagicMock(spec=MindUpload)
        self.partner_client.create_external_authorization_request.return_value = {
            "device_code": "private-test-device-code",
            "verification_uri_complete": _VERIFICATION_URL,
            "poll_interval": 5,
            "expires_in": 600,
        }
        self.grant = {
            "status": "exchanged",
            "access_token": _ACCESS_TOKEN,
            "refresh_token": _REFRESH_TOKEN,
            "access_token_expires_at": 10000,
            "clone_ids": [_CLONE_IDENTIFIER],
            "clone_nicknames": {_CLONE_IDENTIFIER: "My consciousness"},
        }
        self.partner_client.exchange_external_authorization.return_value = self.grant
        self.partner_client.wait_for_external_clone_invocation.return_value = {
            "response_text": "Choose the option that protects time with family.",
            "invocation_id": "test-invocation",
            "idempotent_replay": False,
            "access_token": _ACCESS_TOKEN,
        }
        clock_patch = patch(target=_MODULE + ".time")
        self.clock = clock_patch.start()
        self.addCleanup(clock_patch.stop)
        self.clock.monotonic.return_value = 100
        self.clock.time.return_value = 1000
        self.server = create_server(
            client=self.partner_client,
            installation_id=_INSTALLATION_IDENTIFIER,
            external_subject=_EXTERNAL_SUBJECT,
        )

    async def _consult(
        self,
        connection: Client,
        question: str = _QUESTION,
        task_id: str = _TASK_IDENTIFIER,
        decision_id: str = _DECISION_IDENTIFIER,
    ) -> CallToolResult:
        """Send one real protocol call with no hidden authorization arguments.

        Args:
            connection: Connected in-memory MCP client.
            question: Personal decision to consult about.
            task_id: Conversation identity.
            decision_id: Retry identity.

        Returns:
            CallToolResult: Public protocol response.
        """
        return await connection.call_tool(
            name="consult_mind",
            arguments={"question": question, "task_id": task_id, "decision_id": decision_id},
        )

    async def _approve(self, connection: Client) -> CallToolResult:
        """Complete consent after the server-advised polling interval.

        Args:
            connection: Connected in-memory MCP client.

        Returns:
            CallToolResult: First authorized consultation result.
        """
        initial = await self._consult(connection=connection)
        self.assertEqual(first=initial.structured_content["status"], second=_AUTHORIZATION_REQUIRED)
        self.clock.monotonic.return_value += 5
        return await self._consult(connection=connection)

    async def test_initialization_exposes_one_bounded_tool_without_network(self) -> None:
        """Listing tools must disclose no account credentials or selectable clone.

        Returns:
            None.
        """
        async with Client(server=self.server) as connection:
            tools = await connection.list_tools()
        self.assertEqual(first=len(tools.tools), second=1)
        tool = tools.tools[0]
        self.assertEqual(first=tool.name, second="consult_mind")
        self.assertEqual(
            first=set(tool.input_schema["properties"]),
            second={"question", "task_id", "decision_id"},
        )
        self.assertGreater(a=tool.input_schema["properties"]["question"]["maxLength"], b=0)
        self.assertEqual(first=self.partner_client.mock_calls, second=[])

    async def test_stdio_entrypoint_discovers_tool_without_network_or_stdout_noise(self) -> None:
        """Start the installed entrypoint from outside its checkout.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory(prefix="mindupload-mcp-test-") as working_directory:
            launcher = StdioServerParameters(
                command=sys.executable,
                args=["-m", "mindupload.mcp"],
                cwd=working_directory,
                env={
                    "PYTHONPATH": str(Path(__file__).resolve().parent.parent),
                    "MINDUPLOAD_PARTNER_KEY": "private-test-partner-key",
                    "MINDUPLOAD_INSTALLATION_ID": _INSTALLATION_IDENTIFIER,
                    "MINDUPLOAD_EXTERNAL_SUBJECT": _EXTERNAL_SUBJECT,
                },
            )
            async with Client(server=launcher) as connection:
                tools = await connection.list_tools()
        self.assertEqual(first=len(tools.tools), second=1)
        self.assertEqual(first=tools.tools[0].name, second="consult_mind")
        self.assertIsNotNone(obj=tools.tools[0].output_schema)
        self.assertIn(member="decision", container=tools.tools[0].output_schema["properties"])

    async def test_consent_waits_then_invokes_once_and_whitelists_output(self) -> None:
        """Consent is owner-visible, rate bounded and limited to clone invocation.

        Returns:
            None.
        """
        async with Client(server=self.server) as connection:
            initial = await self._consult(connection=connection)
            self.assertEqual(first=initial.structured_content["verification_url"], second=_VERIFICATION_URL)
            self.assertEqual(first=initial.structured_content["retry_after_seconds"], second=5)
            await self._consult(connection=connection)
            self.partner_client.exchange_external_authorization.assert_not_called()
            self.clock.monotonic.return_value = 105
            result = await self._consult(connection=connection)
        self.assertEqual(first=result.structured_content["status"], second=_SUCCEEDED)
        self.assertEqual(
            first=set(result.structured_content),
            second={"status", "decision", "invocation_id", "idempotent_replay"},
        )
        self.assertEqual(
            first=self.partner_client.create_external_authorization_request.call_args.kwargs["requested_scopes"],
            second=["clone:invoke"],
        )
        self.partner_client.wait_for_external_clone_invocation.assert_called_once()
        invocation = self.partner_client.wait_for_external_clone_invocation.call_args.kwargs
        self.assertEqual(first=invocation["text"], second=_QUESTION)
        self.assertEqual(first=invocation["clone_id"], second=_CLONE_IDENTIFIER)
        self.assertNotIn(member="learn", container=invocation)
        self.assertNotIn(member="is_group", container=invocation)
        self.assertNotIn(member=_ACCESS_TOKEN, container=result.model_dump_json())

    async def test_slow_down_never_polls_before_server_interval(self) -> None:
        """Each consent response governs the next single exchange request.

        Returns:
            None.
        """
        self.partner_client.exchange_external_authorization.side_effect = [
            {"status": "slow_down", "poll_interval": 15},
            self.grant,
        ]
        async with Client(server=self.server) as connection:
            await self._consult(connection=connection)
            self.clock.monotonic.return_value = 105
            waiting = await self._consult(connection=connection)
            self.assertEqual(first=waiting.structured_content["retry_after_seconds"], second=15)
            self.clock.monotonic.return_value = 119
            await self._consult(connection=connection)
            self.assertEqual(first=self.partner_client.exchange_external_authorization.call_count, second=1)
            self.clock.monotonic.return_value = 120
            result = await self._consult(connection=connection)
        self.assertEqual(first=result.structured_content["status"], second=_SUCCEEDED)
        self.partner_client.wait_for_external_clone_invocation.assert_called_once()

    async def test_expired_or_denied_consent_can_request_fresh_owner_approval(self) -> None:
        """An expired request is replaced and a denial never invokes the clone.

        Returns:
            None.
        """
        self.partner_client.exchange_external_authorization.return_value = {"status": "denied"}
        async with Client(server=self.server) as connection:
            await self._consult(connection=connection)
            first_request = self.partner_client.create_external_authorization_request.call_args.kwargs.copy()
            self.clock.monotonic.return_value = 700
            await self._consult(connection=connection)
            self.partner_client.exchange_external_authorization.assert_not_called()
            second_request = self.partner_client.create_external_authorization_request.call_args.kwargs
            self.assertNotEqual(first=first_request["idempotency_key"], second=second_request["idempotency_key"])
            self.clock.monotonic.return_value = 705
            denied = await self._consult(connection=connection)
            self.assertTrue(expr=denied.is_error)
            retry = await self._consult(connection=connection)
        self.assertEqual(first=retry.structured_content["status"], second=_AUTHORIZATION_REQUIRED)
        self.assertEqual(first=self.partner_client.create_external_authorization_request.call_count, second=3)
        self.partner_client.wait_for_external_clone_invocation.assert_not_called()

    async def test_multiple_clones_require_configuration_and_foreign_choice_is_denied(self) -> None:
        """Owner consent cannot be widened by the local clone configuration.

        Returns:
            None.
        """
        self.grant["clone_ids"] = [_CLONE_IDENTIFIER, _OTHER_CLONE_IDENTIFIER]
        self.grant["clone_nicknames"][_OTHER_CLONE_IDENTIFIER] = "Other consciousness"
        async with Client(server=self.server) as connection:
            selection = await self._approve(connection=connection)
        self.assertEqual(first=selection.structured_content["status"], second="clone_selection_required")
        self.assertEqual(first=len(selection.structured_content["clones"]), second=2)
        self.partner_client.wait_for_external_clone_invocation.assert_not_called()
        self.server = create_server(
            client=self.partner_client,
            installation_id=_INSTALLATION_IDENTIFIER,
            external_subject=_EXTERNAL_SUBJECT,
            clone_id="not-approved",
        )
        async with Client(server=self.server) as connection:
            denied = await self._approve(connection=connection)
        self.assertTrue(expr=denied.is_error)
        self.partner_client.wait_for_external_clone_invocation.assert_not_called()
        self.server = create_server(
            client=self.partner_client,
            installation_id=_INSTALLATION_IDENTIFIER,
            external_subject=_EXTERNAL_SUBJECT,
            clone_id=_OTHER_CLONE_IDENTIFIER,
        )
        async with Client(server=self.server) as connection:
            approved = await self._approve(connection=connection)
        self.assertEqual(first=approved.structured_content["status"], second=_SUCCEEDED)
        self.assertEqual(
            first=self.partner_client.wait_for_external_clone_invocation.call_args.kwargs["clone_id"],
            second=_OTHER_CLONE_IDENTIFIER,
        )

    async def test_task_isolation_and_identical_retry_identity_survive_transport(self) -> None:
        """Retry keys stay stable while separate tasks and decisions stay distinct.

        Returns:
            None.
        """
        async with Client(server=self.server) as connection:
            await self._approve(connection=connection)
            await self._consult(connection=connection)
            await self._consult(connection=connection, decision_id="decision-two")
            await self._consult(connection=connection, task_id="task-two")
        invocations = self.partner_client.wait_for_external_clone_invocation.call_args_list
        first, retry, next_decision, next_task = invocations
        self.assertEqual(first=first.kwargs, second=retry.kwargs)
        self.assertEqual(first=first.kwargs["conversation_id"], second=next_decision.kwargs["conversation_id"])
        self.assertNotEqual(first=first.kwargs["idempotency_key"], second=next_decision.kwargs["idempotency_key"])
        self.assertNotEqual(first=first.kwargs["conversation_id"], second=next_task.kwargs["conversation_id"])
        self.assertNotEqual(first=first.kwargs["idempotency_key"], second=next_task.kwargs["idempotency_key"])
        self.partner_client.refresh_external_authorization.assert_not_called()
        # The backend receipt namespace is installation-wide, so subject and clone must separate keys too.
        for external_subject, approved_clone_id in (
            ("another-owner", _CLONE_IDENTIFIER),
            (_EXTERNAL_SUBJECT, _OTHER_CLONE_IDENTIFIER),
        ):
            self.grant["clone_ids"] = [approved_clone_id]
            self.server = create_server(
                client=self.partner_client,
                installation_id=_INSTALLATION_IDENTIFIER,
                external_subject=external_subject,
            )
            async with Client(server=self.server) as connection:
                await self._approve(connection=connection)
            self.assertNotEqual(
                first=first.kwargs["idempotency_key"],
                second=self.partner_client.wait_for_external_clone_invocation.call_args.kwargs["idempotency_key"],
            )

    async def test_refresh_retains_both_rotated_tokens_without_refreshing_each_decision(self) -> None:
        """The next rotation uses the retained refresh token inside this process.

        Returns:
            None.
        """
        rotated = dict(self.grant)
        rotated.update(
            access_token=_ROTATED_ACCESS_TOKEN,
            refresh_token=_ROTATED_REFRESH_TOKEN,
            access_token_expires_at=20000,
        )
        self.partner_client.refresh_external_authorization.return_value = rotated
        async with Client(server=self.server) as connection:
            await self._approve(connection=connection)
            self.clock.time.return_value = self.grant["access_token_expires_at"] - 120
            await self._consult(connection=connection)
            self.partner_client.refresh_external_authorization.assert_called_once_with(
                refresh_token=_REFRESH_TOKEN,
                installation_id=_INSTALLATION_IDENTIFIER,
                external_subject=_EXTERNAL_SUBJECT,
            )
            await self._consult(connection=connection)
            self.assertEqual(first=self.partner_client.refresh_external_authorization.call_count, second=1)
            self.clock.time.return_value = rotated["access_token_expires_at"] - 120
            await self._consult(connection=connection)
        self.assertEqual(
            first=self.partner_client.refresh_external_authorization.call_args.kwargs["refresh_token"],
            second=_ROTATED_REFRESH_TOKEN,
        )
        self.assertEqual(
            first=self.partner_client.wait_for_external_clone_invocation.call_args.kwargs["access_token"],
            second=_ROTATED_ACCESS_TOKEN,
        )

    async def test_uncertain_refresh_requests_fresh_consent_without_replaying_stale_token(self) -> None:
        """A missing rotation response cannot revoke the grant on a later retry.

        Returns:
            None.
        """
        self.partner_client.refresh_external_authorization.side_effect = MindUploadError(
            message="private-uncertain-refresh-response",
        )
        async with Client(server=self.server) as connection:
            await self._approve(connection=connection)
            self.clock.time.return_value = self.grant["access_token_expires_at"] - 120
            with redirect_stderr(new_target=io.StringIO()):
                failed = await self._consult(connection=connection)
            self.assertTrue(expr=failed.is_error)
            retry = await self._consult(connection=connection)
        self.assertEqual(first=retry.structured_content["status"], second=_AUTHORIZATION_REQUIRED)
        self.partner_client.refresh_external_authorization.assert_called_once()
        self.assertEqual(first=self.partner_client.create_external_authorization_request.call_count, second=2)
        self.partner_client.wait_for_external_clone_invocation.assert_called_once()

    async def test_revoked_grant_requests_new_consent_instead_of_reusing_denied_access(self) -> None:
        """Server-side revocation is immediately reflected in the next tool call.

        Returns:
            None.
        """
        self.partner_client.wait_for_external_clone_invocation.side_effect = APIError(
            message="private-revoked-access-token",
            status=403,
        )
        async with Client(server=self.server) as connection:
            with redirect_stderr(new_target=io.StringIO()):
                denied = await self._approve(connection=connection)
            retry = await self._consult(connection=connection)
        self.assertTrue(expr=denied.is_error)
        self.assertEqual(first=retry.structured_content["status"], second=_AUTHORIZATION_REQUIRED)
        self.assertEqual(first=self.partner_client.create_external_authorization_request.call_count, second=2)
        self.partner_client.wait_for_external_clone_invocation.assert_called_once()

    async def test_concurrent_consultations_serialize_consent_rotation_and_invocation(self) -> None:
        """Two queued decisions share one exchange and rotation without paid fanout.

        Returns:
            None.
        """
        invocation_started = threading.Event()
        invocation_released = threading.Event()
        overlap_detected = threading.Event()
        invocation_count = 0
        result = self.partner_client.wait_for_external_clone_invocation.return_value.copy()

        def invoke(**arguments: Any) -> dict[str, Any]:
            """Hold the first API request while observing whether the next overlaps.

            Args:
                arguments: Forwarded SDK invocation fields.

            Returns:
                dict[str, Any]: Fake completed consultation.
            """
            nonlocal invocation_count
            invocation_count += 1
            if invocation_count == 1:
                invocation_started.set()
                if not invocation_released.wait(timeout=_THREAD_WAIT_TIMEOUT_SECONDS):
                    raise TimeoutError("The concurrency test did not release its first request.")
            else:
                overlap_detected.set()
            return result

        self.partner_client.wait_for_external_clone_invocation.side_effect = invoke
        self.grant["access_token_expires_at"] = self.clock.time.return_value
        refreshed = dict(self.grant)
        refreshed.update(access_token=_ROTATED_ACCESS_TOKEN, access_token_expires_at=20000)
        self.partner_client.refresh_external_authorization.return_value = refreshed
        async with Client(server=self.server) as connection:
            await self._consult(connection=connection)
            self.clock.monotonic.return_value = 105
            first_consultation = asyncio.create_task(coro=self._consult(connection=connection))
            self.assertTrue(
                expr=await asyncio.to_thread(invocation_started.wait, timeout=_THREAD_WAIT_TIMEOUT_SECONDS),
            )
            second_consultation = asyncio.create_task(
                coro=self._consult(connection=connection, decision_id="concurrent-decision"),
            )
            try:
                self.assertFalse(
                    expr=await asyncio.to_thread(overlap_detected.wait, timeout=_OVERLAP_OBSERVATION_SECONDS),
                )
            finally:
                invocation_released.set()
            # Exactly two independent decisions contend for the connector's one-request budget.
            first_result, second_result = await asyncio.gather(first_consultation, second_consultation)
        self.assertEqual(first=first_result.structured_content["status"], second=_SUCCEEDED)
        self.assertEqual(first=second_result.structured_content["status"], second=_SUCCEEDED)
        self.partner_client.exchange_external_authorization.assert_called_once()
        self.partner_client.refresh_external_authorization.assert_called_once()
        self.assertEqual(first=self.partner_client.wait_for_external_clone_invocation.call_count, second=2)

    async def test_invalid_input_is_rejected_before_any_authorization_request(self) -> None:
        """Protocol and handler validation both precede chargeable work.

        Returns:
            None.
        """
        async with Client(server=self.server) as connection:
            tools = await connection.list_tools()
            properties = tools.tools[0].input_schema["properties"]
            invalid_inputs = [
                {"question": "   "},
                {"task_id": "\x00"},
                {"decision_id": " "},
                {"question": "q" * (properties["question"]["maxLength"] + 1)},
                {"task_id": "t" * (properties["task_id"]["maxLength"] + 1)},
            ]
            # Distinct trust-boundary cases share one connection and make zero API requests.
            for arguments in invalid_inputs:
                with self.subTest(arguments=arguments):
                    result = await self._consult(connection=connection, **arguments)
                    self.assertTrue(expr=result.is_error)
            self.assertEqual(first=self.partner_client.mock_calls, second=[])
            accepted = await self._consult(
                connection=connection,
                question="q" * properties["question"]["maxLength"],
                task_id="t" * properties["task_id"]["maxLength"],
                decision_id="d" * properties["decision_id"]["maxLength"],
            )
        self.assertEqual(first=accepted.structured_content["status"], second=_AUTHORIZATION_REQUIRED)
        self.partner_client.create_external_authorization_request.assert_called_once()

    async def test_private_sdk_error_is_redacted_from_protocol_and_diagnostics(self) -> None:
        """A failed consultation exposes neither tokens nor private exception text.

        Returns:
            None.
        """
        private_message = "private-question-and-token-should-not-be-logged"
        self.partner_client.wait_for_external_clone_invocation.side_effect = MindUploadError(message=private_message)
        diagnostics = io.StringIO()
        with redirect_stderr(new_target=diagnostics):
            async with Client(server=self.server) as connection:
                result = await self._approve(connection=connection)
        self.assertTrue(expr=result.is_error)
        combined_output = result.model_dump_json() + diagnostics.getvalue()
        # All markers are local test values; checking one combined artifact covers both output channels.
        for marker in (private_message, _ACCESS_TOKEN, _REFRESH_TOKEN):
            self.assertNotIn(member=marker, container=combined_output)
        self.partner_client.wait_for_external_clone_invocation.assert_called_once()


if __name__ == "__main__":
    unittest.main()
