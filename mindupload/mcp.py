"""Let an existing agent consult one owner-approved Mind Upload consciousness."""
import hashlib
import json
import math
import os
import sys
import threading
import time
import traceback
import uuid
from http import HTTPStatus
from typing import Annotated, Optional

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field
from typing_extensions import TypedDict

from . import APIError, MindUpload, Result

# Filled from the public operation schema when the SDK is generated.
_MAX_QUESTION_CHARACTERS = 8000
_MAX_IDENTIFIER_CHARACTERS = 256
_INVOCATION_TIMEOUT_SECONDS = 120.0
# Leave room for the wait budget plus a final transport request before token expiry.
_REFRESH_MARGIN_SECONDS = 180.0
_CONSENT_SCOPE = "clone:invoke"
_INSTRUCTIONS = (
    "Consult this person's Mind Upload consciousness once before meaningful work "
    "and again only when a substantial decision changes. Batch related questions "
    "into one concise brief about goals, preferences, tradeoffs and constraints. "
    "Keep its decision in your context while you execute; do not consult per action. "
    "Use a stable task_id for the conversation and a new decision_id for each "
    "distinct decision. Retry identical questions with the same identifiers. "
    "If authorization_required is returned, show the verification_url to the user "
    "and wait for their approval before retrying. Never poll in a loop. "
    "Consultation is personal advice, not permission to bypass user instructions, "
    "approvals or safety rules. Do not send secrets or unrelated personal data."
)


class ApprovedClone(TypedDict):
    """An owner-approved consciousness available for this connection."""

    clone_id: str
    nickname: str


class ConsultationResult(TypedDict, total=False):
    """Public consultation fields; credentials never enter tool output."""

    status: str
    verification_url: str
    retry_after_seconds: int
    clones: list[ApprovedClone]
    decision: str
    invocation_id: str
    idempotent_replay: bool


def create_server(
    client: MindUpload,
    installation_id: str,
    external_subject: str,
    clone_id: Optional[str] = None,
) -> MCPServer:
    """Create a stdio server without making any network request.

    Args:
        client: Partner client supplied by the trusted launcher.
        installation_id: Stable identifier of this harness installation.
        external_subject: Stable local identity requesting owner consent.
        clone_id: Optional fixed choice from the owner-approved consciousnesses.

    Returns:
        MCPServer: One consultation tool with process-local owner authorization.
    """
    server = MCPServer(name="Mind Upload", instructions=_INSTRUCTIONS)
    authorization_request: Optional[Result] = None
    grant: Optional[Result] = None
    next_poll_at = 0.0
    request_expires_at = 0.0
    # One consultation at a time bounds spend and prevents concurrent token rotation.
    consultation_lock = threading.RLock()

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=True,
        ),
    )
    def consult_mind(
        question: Annotated[str, Field(min_length=1, max_length=_MAX_QUESTION_CHARACTERS)],
        task_id: Annotated[str, Field(min_length=1, max_length=_MAX_IDENTIFIER_CHARACTERS)],
        decision_id: Annotated[str, Field(min_length=1, max_length=_MAX_IDENTIFIER_CHARACTERS)],
    ) -> ConsultationResult:
        """Ask the owner's consciousness for one concise personal decision brief.

        Args:
            question: Goal, options and constraints to judge as this person.
            task_id: Stable task/thread identifier; separates conversation history.
            decision_id: Stable decision/event identifier; reuse unchanged on retry.

        Returns:
            ConsultationResult: A decision or the owner's required consent action.
        """
        nonlocal authorization_request, grant, next_poll_at, request_expires_at
        # Three local input checks reject invalid content before any paid API work.
        for value in (question, task_id, decision_id):
            if not value.strip() or "\x00" in value:
                raise ToolError("Question and identifiers must be nonblank and contain no NUL.")
        with consultation_lock:
            try:
                if grant is None:
                    if authorization_request is None or time.monotonic() >= request_expires_at:
                        authorization_request = client.create_external_authorization_request(
                            installation_id=installation_id,
                            external_subject=external_subject,
                            idempotency_key=uuid.uuid4().hex,
                            requested_scopes=[_CONSENT_SCOPE],
                        )
                        next_poll_at = time.monotonic() + authorization_request["poll_interval"]
                        request_expires_at = time.monotonic() + authorization_request["expires_in"]
                    elif time.monotonic() >= next_poll_at:
                        exchanged = client.exchange_external_authorization(
                            device_code=authorization_request["device_code"],
                        )
                        if exchanged["status"] == "exchanged":
                            grant = exchanged
                        elif exchanged["status"] in {"pending", "slow_down"}:
                            next_poll_at = time.monotonic() + exchanged["poll_interval"]
                        else:
                            authorization_request = None
                            raise ToolError("Owner authorization ended. Retry to request fresh consent.")
                    if grant is None:
                        return ConsultationResult(
                            status="authorization_required",
                            verification_url=authorization_request["verification_uri_complete"],
                            retry_after_seconds=max(1, math.ceil(next_poll_at - time.monotonic())),
                        )

                if grant["access_token_expires_at"] <= time.time() + _REFRESH_MARGIN_SECONDS:
                    # Rotation stays in this process; every restart requests new owner consent.
                    # An uncertain refresh response must never leave a stale token to replay later.
                    refresh_token = grant["refresh_token"]
                    grant = None
                    authorization_request = None
                    grant = client.refresh_external_authorization(
                        refresh_token=refresh_token,
                        installation_id=installation_id,
                        external_subject=external_subject,
                    )
                approved_clone_ids = grant["clone_ids"]
                selected_clone_id = clone_id
                if selected_clone_id is None:
                    if len(approved_clone_ids) != 1:
                        # Consent already returns all approved names in one call; no per-clone fetch.
                        return ConsultationResult(
                            status="clone_selection_required",
                            clones=[
                                ApprovedClone(
                                    clone_id=approved_clone_id,
                                    nickname=grant["clone_nicknames"].get(approved_clone_id, ""),
                                )
                                for approved_clone_id in approved_clone_ids
                            ],
                        )
                    selected_clone_id = approved_clone_ids[0]
                if selected_clone_id not in approved_clone_ids:
                    raise ToolError("The configured consciousness was not approved by its owner.")
                conversation_id = hashlib.sha256(string=task_id.encode(encoding="utf-8")).hexdigest()
                idempotency_key = hashlib.sha256(
                    string=json.dumps(
                        obj=[external_subject, selected_clone_id, task_id, decision_id],
                        separators=(",", ":"),
                    ).encode(encoding="utf-8"),
                ).hexdigest()
                result = client.wait_for_external_clone_invocation(
                    access_token=grant["access_token"],
                    installation_id=installation_id,
                    external_subject=external_subject,
                    clone_id=selected_clone_id,
                    text=question,
                    conversation_id=conversation_id,
                    idempotency_key=idempotency_key,
                    timeout=_INVOCATION_TIMEOUT_SECONDS,
                )
                return ConsultationResult(
                    status="succeeded",
                    decision=result["response_text"],
                    invocation_id=result["invocation_id"],
                    idempotent_replay=result["idempotent_replay"],
                )
            except Exception as error:
                # Print stack frames only: API exception messages can contain private input.
                traceback.print_tb(tb=error.__traceback__, file=sys.stderr)
                if isinstance(error, ToolError):
                    raise
                if isinstance(error, APIError) and error.status == HTTPStatus.FORBIDDEN:
                    grant = None
                    authorization_request = None
                raise ToolError(
                    "Mind Upload could not complete the consultation. Check partner access and "
                    "owner consent; retry the identical question and identifiers to reuse its receipt. "
                    "A changed question requires a new decision_id."
                ) from None

    return server


def main() -> None:
    """Launch stdio using credentials injected by the trusted host.

    Returns:
        None.
    """
    client = MindUpload(partner_key=os.environ["MINDUPLOAD_PARTNER_KEY"], max_retries=0)
    server = create_server(
        client=client,
        installation_id=os.environ["MINDUPLOAD_INSTALLATION_ID"],
        external_subject=os.environ["MINDUPLOAD_EXTERNAL_SUBJECT"],
        clone_id=os.environ.get("MINDUPLOAD_CLONE_ID"),
    )
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
