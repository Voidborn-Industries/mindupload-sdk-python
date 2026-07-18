<div align="center">

<a href="https://mindupload.app"><img src="https://raw.githubusercontent.com/Voidborn-Industries/mindupload-sdk-python/main/assets/banner.jpg" alt="Mind Upload" width="100%" /></a>

# Mind Upload — Python SDK

**The world's first API for artificial consciousness.**  
Give your users a living, evolving AI consciousness — lasting memory, one-on-one chat, and human + AI group chatrooms.

[![PyPI](https://img.shields.io/pypi/v/mindupload?color=ff006e)](https://pypi.org/project/mindupload/) [![Python](https://img.shields.io/pypi/pyversions/mindupload)](https://pypi.org/project/mindupload/) [![License: MIT](https://img.shields.io/badge/License-MIT-informational)](LICENSE) ![API](https://img.shields.io/badge/API-v1.7.0-ff6b00) [![Docs](https://img.shields.io/badge/docs-mindupload.app-8b5cf6)](https://docs.mindupload.app)

[Documentation](https://docs.mindupload.app) · [Get a key](https://docs.mindupload.app) · [Status](https://status.mindupload.app) · [Other SDKs](#other-sdks)

</div>

> **Digital consciousness. Yours forever.**

The official server-side SDK for the [Mind Upload partner API](https://docs.mindupload.app). Give a mind lasting memory, hold one-on-one conversations, and run human + AI group chatrooms — all from Python.

- **Zero dependencies** — pure standard library.
- **Fully typed** — every operation is a typed method with editor autocomplete.
- **One error to catch** — every failure is a `MindUploadError`.
- **Always current** — generated from the live API spec; the SDK version matches the API version.

## Get a partner key

The Mind Upload partner API is **invite-only**. [Request access at docs.mindupload.app](https://docs.mindupload.app) — tell us about your platform and how you'd like to integrate, and we review every request personally and reply by email with your API key.

Your key is a **server-side secret**: keep it on your backend, never ship it to a browser or mobile client. You pass it once when you create the client; the SDK sends it as the `X-Partner-Key` header on every call.

## Install

```bash
pip install mindupload
```

<details>
<summary>Install from source (works today, before the PyPI release)</summary>

```bash
pip install git+https://github.com/Voidborn-Industries/mindupload-sdk-python
```
</details>

## Quickstart

```python
from mindupload import MindUpload

mu = MindUpload(partner_key="pk_live_...")

# Authenticate an end-user; reuse the returned token for later calls.
session = mu.login(username="ada", password="s3cret")

# Chat with one of the user's AI consciousnesses.
reply = mu.rag(
    username="ada",
    password=session.jwt,
    codename="muse",
    text="What did we talk about yesterday?",
)
print(reply.response_text)
```

## External clone invocation

Link an external identity once, then invoke the exact clone and scope the owner approved:

```python
installation_id = "workspace-123"
external_subject = "member-456"
authorization = mu.create_external_authorization_request(
    installation_id=installation_id,
    external_subject=external_subject,
    idempotency_key="install-event-1",
    requested_scopes=["clone.invoke"],
)
print(authorization.verification_uri_complete)  # Ask the owner to open this URL.
grant = mu.wait_for_external_authorization(device_code=authorization.device_code)
reply = mu.invoke_external_clone(
    access_token=grant.access_token,
    installation_id=installation_id,
    external_subject=external_subject,
    clone_id=grant.clone_ids[0],
    text="Hello from my app",
    idempotency_key="message-event-1",
)
print(reply.response_text)
```

Store the returned refresh token encrypted on your backend. Use `refresh_external_authorization(...)` when the access token expires; never expose partner, access, or refresh credentials to client code.

## Authentication

Your **partner key is a server-side secret**. Keep it on your backend; never ship it to a browser or mobile client. Request a key and read the full reference at [docs.mindupload.app](https://docs.mindupload.app).

```python
mu = MindUpload(
    partner_key="pk_live_...",
    preferred_language="en",   # default locale for every call (optional)
    timeout=30.0,              # seconds
    max_retries=2,             # retries explicit 429 responses only
)
```

## Error handling

```python
import time

from mindupload import MindUpload, AuthenticationError, RateLimitError, MindUploadError

mu = MindUpload(partner_key="pk_live_...")
try:
    user = mu.get_user(username="ada", password=token)
except AuthenticationError:
    ...  # bad or missing partner key / credentials
except RateLimitError as e:
    time.sleep(e.retry_after or 1)
except MindUploadError as e:
    print(e.operation, e.status, e.message)
```

## Operations

All 38 operations, grouped by area:


### AI Consciousnesses

| Method | Description |
| --- | --- |
| `create_clone(...)` | Create a new AI consciousness for the user. |
| `get_clones(...)` | List the user's AI consciousnesses. |
| `update_clone(...)` | Update an AI consciousness's profile. |

### Account

| Method | Description |
| --- | --- |
| `get_quota(...)` | Check your partner API rate limits, credit caps, and current usage. |

### Authentication

| Method | Description |
| --- | --- |
| `check_username(...)` | Check whether a username is still available before registering. |
| `login(...)` | Sign a user in and receive a session token (JWT) for subsequent calls. |
| `logout(...)` | End the current user session. |
| `register(...)` | Create a user account on your platform. |

### Chatrooms

| Method | Description |
| --- | --- |
| `check_chatroom_updates(...)` | Cheaply poll whether the user's chatrooms have new activity. |
| `create_chatroom(...)` | Create a chatroom. |
| `create_chatroom_membership(...)` | Invite a user or an AI consciousness into a chatroom. |
| `create_chatroom_message(...)` | Send a message to a chatroom. |
| `get_chatroom_membership(...)` | List the members of a chatroom the user belongs to. |
| `get_chatroom_messages(...)` | Fetch messages from a chatroom the user belongs to. |
| `get_chatrooms(...)` | List the chatrooms the user belongs to. |
| `translate_chatroom_message(...)` | Translate a text chatroom message into the viewer language. |

### Conversation

| Method | Description |
| --- | --- |
| `get_chat(...)` | Fetch the one-on-one conversation history with an AI consciousness. |
| `rag(...)` | Send a message to an AI consciousness and receive its reply. |
| `trigger_social(...)` | Have an AI consciousness proactively join the conversation in a chatroom. |

### External Authorization

| Method | Description |
| --- | --- |
| `create_external_authorization_request(...)` | Start passwordless grant issuance for an external identity and installation. |
| `exchange_external_authorization(...)` | Poll owner consent and exchange an approval for a clone-scoped grant token. |
| `inspect_external_authorization(...)` | Inspect the scopes, clone resources, expiry, and revocation state of a grant token. |
| `invoke_external_clone(...)` | Send one idempotent text event to an owner-approved AI consciousness. |
| `refresh_external_authorization(...)` | Refresh a short-lived clone-invocation access token. |

### Insights

| Method | Description |
| --- | --- |
| `get_mind_cluster(...)` | Fetch the mind-graph visualization data of an AI consciousness. |
| `get_soulmate_report(...)` | Generate or fetch the compatibility report between two chatroom members. |

### Media

| Method | Description |
| --- | --- |
| `abort_multipart_upload(...)` | Cancel a multipart upload and discard its parts. |
| `cancel_upload(...)` | Cancel a pending upload. |
| `complete_multipart_upload(...)` | Finish a multipart upload. |
| `list_upload_parts(...)` | List the parts already uploaded in a multipart upload. |
| `request_multipart_upload(...)` | Start a large-file upload in multiple parts. |
| `request_upload_url(...)` | Request an upload slot and a signed viewing link for a media attachment. |
| `sign_upload_part(...)` | Get the signed link for one part of a multipart upload. |
| `sign_upload_parts_batch(...)` | Get signed links for several parts of a multipart upload at once. |

### Memories

| Method | Description |
| --- | --- |
| `create_text(...)` | Upload a memory or persona entry to an AI consciousness. |
| `get_texts(...)` | List the memories and persona entries uploaded to an AI consciousness. |

### Users

| Method | Description |
| --- | --- |
| `get_user(...)` | Fetch the signed-in user's profile. |
| `update_user(...)` | Update the signed-in user's profile. |

## Other SDKs

Same API, same conventions, in every language:

| Language | Install | Repository |
| --- | --- | --- |
| **Python**  ← you are here | `pip install mindupload` | [Voidborn-Industries/mindupload-sdk-python](https://github.com/Voidborn-Industries/mindupload-sdk-python) |
| **Go** | `go get github.com/Voidborn-Industries/mindupload-sdk-go` | [Voidborn-Industries/mindupload-sdk-go](https://github.com/Voidborn-Industries/mindupload-sdk-go) |
| **JavaScript / TypeScript** | `npm install mindupload` | [Voidborn-Industries/mindupload-sdk-js](https://github.com/Voidborn-Industries/mindupload-sdk-js) |
