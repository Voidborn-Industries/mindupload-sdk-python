# Mind Upload MCP: your AI meta harness

An **AI meta harness** lets your Mind Upload consciousness direct Codex, Claude
Code, Cursor, or another execution agent. `consult_mind` asks your chosen mind how to approach the task,
using its personal memories, values, and judgment. Before completion,
`review_work` asks the same mind to scrutinize the actual result and evidence:
does it satisfy your request, and does it fit your intent? Your agent can show it
screenshots, screen recordings and audio of the work privately, and, only with
your permission, save notes into your mind or help you go through memories
waiting for your review.

Start with [Mind Upload MCP](https://docs.mindupload.app/mcp), or use the install
routes below. Install the plugin when available: it bundles the server address
and a skill that asks for initial direction and completion scrutiny. Installing
the server alone makes tools available; the host still decides when to call them.

## Connect your mind

Add `https://mcp.mindupload.app/mcp` to your agent, then sign in when it asks:

1. Your agent opens a Mind Upload page that shows which agent is asking and
   where access will go. Continue only if you just asked your own agent to
   connect.
2. Mind Upload opens in a new tab. Sign in, choose the consciousness this agent
   may consult, and approve. Approve only requests you started yourself.
3. The first tab returns you to your agent. The connection lasts across agent
   restarts until you sign out, or until it goes unused for 30 days.

No partner key, account setup or environment variable is needed: the hosted
server holds the application credential. You need a consciousness in
[Mind Upload](https://mindupload.app); invoking it uses your account's
subscription. Signing in again from the same agent replaces the earlier
approval instead of adding another.

`connection_status` shows the approval this connection uses, its
consciousnesses, permissions and dates, and how to end it.

### Claude Code

```sh
claude plugin marketplace add https://github.com/Voidborn-Industries/mindupload-sdk-python
claude plugin install mindupload@mindupload
```

The plugin adds the hosted server and the review skill. Sign in with
`claude mcp login mindupload`, or open `/mcp`, select **mindupload** and choose
Authenticate. Run `/mindupload:mindupload-review` to request your mind's
direction and final scrutiny. Without the plugin:

```sh
claude mcp add --transport http mindupload https://mcp.mindupload.app/mcp
claude mcp login mindupload
```

The server lists its tools before you sign in, so agents can see what it
offers; every tool call needs the sign-in.

See the [plugin installation guide](https://code.claude.com/docs/en/plugins/install).

### Codex

```sh
codex plugin marketplace add https://github.com/Voidborn-Industries/mindupload-sdk-python
codex plugin add mindupload@mindupload
```

Alternatively, in the desktop app, open Plugins, select the **Mind Upload**
marketplace, and install **mindupload**. This adds our repository marketplace;
it does not imply listing in the universal public directory. Without the plugin:

```sh
codex mcp add mindupload --url https://mcp.mindupload.app/mcp
codex mcp login mindupload
```

### Cursor and other hosts that use `mcpServers`

Merge this entry into the host's MCP configuration and sign in when it asks:

```json
{
  "mcpServers": {
    "mindupload": {
      "url": "https://mcp.mindupload.app/mcp"
    }
  }
}
```

Cursor also accepts the portable plugin in this repository; public marketplace
listing requires a separate review. The [Cursor MCP guide](https://cursor.com/docs/mcp)
describes server configuration. A configuration entry alone does not install the
review skill; use the project guidance under [Direct, execute, scrutinize](#direct-execute-scrutinize).

### VS Code and GitHub Copilot

Run **MCP: Add Server**, choose an HTTP server and enter the address above, or
merge this entry into your workspace's `.vscode/mcp.json`:

```json
{
  "servers": {
    "mindupload": {
      "type": "http",
      "url": "https://mcp.mindupload.app/mcp"
    }
  }
}
```

See [VS Code's MCP guide](https://code.visualstudio.com/docs/agent-customization/mcp-servers).
If a host searches the official MCP Registry, search **mindupload** or the
publisher name **io.github.Voidborn-Industries/mindupload**. Registry publication,
downstream indexing, and each host's marketplace approval are separate steps.

## Bring your own partner key

Partner applications, and people who prefer a server on their own computer,
can run the connector locally with their own partner key instead. Each route
keeps the key out of other people's hands:

- **Personal local use.** Request your own partner key and keep it on your
  computer. Follow [Personal setup and owner consent](#personal-setup-and-owner-consent).
- **Trusted team testing.** A team owner may share one partner key with trusted
  colleagues. Each person runs a separate connector, uses a separate
  `MINDUPLOAD_EXTERNAL_SUBJECT`, and approves only their own consciousness.
  The team shares the key's limits.
- **Provider integration.** A service keeps the partner key on its own server
  and derives installation and user identifiers from the accounts it signs in.
  Never ship the key in an app, package, plugin, web page or shared
  configuration.

[Request partner access](https://docs.mindupload.app/) through the API
documentation's access form. Requesting a key, waiting for approval,
configuring the runtime and approving your consciousness are separate steps.
Until the runtime is configured, every local tool returns `setup_required` with
a setup link; no consciousness is consulted and no review runs.

MCP is language agnostic: your agent and project can use any language. The
local server uses Node.js 20 or later and does not require Python or `uv`; the
[Python alternative](#python-alternative) uses Python 3.11 or later. Both
expose the same tools and owner consent flow. With
[Node.js](https://nodejs.org/en/download) installed, the pinned launch command is:

```sh
npx --yes --package mindupload@1.15.34 mindupload-mcp
```

The server speaks MCP over standard input and output; add it to your host as a
command-based server instead of typing into that terminal. For example,
`codex mcp add mindupload -- npx --yes --package mindupload@1.15.34 mindupload-mcp`.

### Python alternative

If you prefer the Python server, [uv](https://docs.astral.sh/uv/getting-started/installation/)
can install it and obtain a compatible interpreter:

```sh
uvx --python ">=3.11" --from "mindupload[mcp]==1.15.34" mindupload-mcp
```

Use `uvx` and the arguments above in place of the Node command in your host.

### Existing Python installation

```sh
python -m pip install "mindupload[mcp]==1.15.34"
python -m mindupload.mcp
```

Use that interpreter's absolute path as your host's command and
`["-m", "mindupload.mcp"]` as its arguments. The optional MCP extra adds the
server dependencies; the base SDK keeps its existing requirements.

## Direct, execute, scrutinize

Ask: **“Use my Mind Upload consciousness to direct this task. Ask what matters
to me before execution. Before reporting completion, have it scrutinize the
result and actual verification evidence. Investigate and fix concrete findings.”**

For hosts without the bundled skill, add this to your project guidance:

> Before substantial execution, call `consult_mind` with my goal, constraints,
> relevant choices, and proposed approach. Ask for my mind's priorities and
> unacceptable outcomes. Consult again when an important decision changes.
> Before claiming completion, call `review_work` with my original request,
> the changed work or result excerpts, and actual verification output.
> Use completion phase, one stable task identifier, and a new review identifier
> when the supplied material changes. Check functional correctness and whether
> the result follows my mind's direction. Fix demonstrated problems and verify
> the changed version, then review changed evidence. Report unresolved
> findings and missing evidence honestly. Review consequential plans or changed
> assumptions when needed; avoid calls after every edit. If Mind Upload is not
> connected, ask me to sign in, and state that no mind was consulted or review performed.
> A mind's advice does not grant permission for actions or establish correctness.

`review_work` accepts `user_request`, `work`, `evidence`, `task_id`, `review_id`,
optional `phase` (`completion` by default, or `plan` / `progress`), and optional
evidence (below). Supply actual excerpts and observed output. The connector
cannot run tests and opens no file except evidence your agent names. Include
what was not tested. Keep all text within the tool's advertised size limit;
narrow the scope explicitly instead of silently dropping evidence. Never include
credentials or unrelated private data.

## Show screenshots, recordings and audio privately

Both tools can pass screenshots, screen recordings or audio of the work to your
mind without making them public. Mind Upload describes each file for that one
call; your mind reads the description alongside the agent's text. Evidence is
never kept as a memory, and its description expires after 24 hours.

- **Hosted server.** The agent calls `share_evidence` with the file's name,
  type and size, uploads the file to the address it returns (for example with
  `curl --upload-file`), then passes the returned `evidence_ids` to
  `consult_mind` or `review_work`.
- **Local server.** The agent passes `evidence_files`: absolute paths on your
  computer. The connector checks each file, uploads it and waits for its
  description itself. It reads no other file.

Up to 20 files per call. Accepted: images (PNG, JPEG, GIF, WebP, HEIC, HEIF) up
to 50 MB; audio (MP3, WAV, M4A, AAC, OGG, Opus, WEBA) up to 20 MB; video (MP4,
MOV, WebM, AVI, MKV, M4V, FLV, WMV, 3GP, OGV) up to 1 GB. The local server
refuses any other file, and any file over its limit, before contacting Mind
Upload. Video and audio descriptions can cover selected frames or a bounded
portion of a recording.

A `succeeded` reply lists each item with its `analysis_status` and reports
`media_analysis_status: "analyzed"`. The connector waits up to a minute for the
descriptions. If one is still being written, or could not be written, nothing
is sent to your mind and the message names the file: repeat the identical call
to continue without uploading again. Accounts in some regions cannot have media
described; the message then says so, and the agent should describe the
evidence in text instead.

Share only files that belong to the task and that you would show your own mind.
Say in the text when each file was captured, which version of the work it shows,
and which part or interaction to assess. A screenshot does not establish that an
interaction works: include the observed test output too.

### Media links

`media_evidence` still accepts HTTPS links you have authorized Mind Upload to
fetch, as a list of `kind` (`image`, `audio`, or `video`) and `url` pairs:

```json
{
  "kind": "image",
  "url": "https://example.com/authorized-task-screenshot.png"
}
```

Links and evidence cannot be combined in one call. Private-host URLs, local
file paths, and links behind browser sign-in are unsuitable; treat
access-bearing links as private task data. Use immutable or versioned URLs:
replacing content at the same URL can reuse a cached description, and a changed
`review_id` alone does not refresh it. Replies to a call with links report
`media_analysis_status: "requested_unverified"`: the links were requested, but
there is no receipt that each one was perceived. Ask the mind to say what it
could actually assess; missing perception remains missing verification.

## Save and review memories, and let your mind learn

These need permissions that start unticked when you approve the connection.
Tick only those you want this agent to use:

- **Save memories** (`clone:upload`): when you ask, `remember` saves a note,
  decision or fact into your mind. It waits for your review unless you chose to
  keep such memories automatically. Saving the same text again returns the
  earlier result.
- **Review pending memories** (`clone:review`): `list_pending_memories` shows
  memories waiting for your review; `review_pending_memory` approves, rejects or
  rewrites one, exactly as you decide. Each decision names the memory's
  `content_revision`, so a memory changed in the meantime is not overwritten.
- **Learn from these conversations** (`clone:learn`): `learn: true` on
  `consult_mind` or `review_work` lets your mind learn from that exchange. What
  it learns waits for your review in the same way. It cannot be combined with
  evidence, which is never kept.

A call that needs a permission you did not tick sends nothing and names the
permission. With the hosted server, run `disconnect`, sign in again and tick it.
With the local server, the reply has status `permission_required` and a
`verification_url`: approve again there with the permission ticked, then repeat
the call. Your existing approval keeps working if you decline.

An established consultation or review uses one existing invocation
request in the normal completed case; authorization and unfinished results can
require additional requests, and each evidence file adds an upload request, the
upload itself, one request to start its description and a status check every
3 seconds until it is ready. Existing partner API usage rules apply. A
`succeeded` response includes the selected consciousness's identifier and
nickname, its reply, and the invocation receipt. It reports delivery of that
mind's judgment, not approval or a guarantee that every defect was found.

## Personal setup and owner consent

Supply these variables through the environment that launches your server:

- `MINDUPLOAD_PARTNER_KEY`: your existing private partner key. Keep it in your
  trusted runtime; never distribute it with an application or paste it in chat.
- `MINDUPLOAD_INSTALLATION_ID`: a stable identifier for this installation.
- `MINDUPLOAD_EXTERNAL_SUBJECT`: a stable identifier for the person linking
  their mind in this installation. Both identifiers are labels, not passwords.
- `MINDUPLOAD_CLONE_ID` (optional): the exact mind to consult. Without it,
  approve exactly one mind during linking; multiple minds require this setting.

Partner access is required for both tools. Some hosts filter inherited variables.
Use that host's supported environment
forwarding settings and restart the server. For Codex's direct MCP configuration,
add `env_vars` with the three required names and optional clone name to its
`mcp_servers.mindupload` entry; never put credential values in the guide or tool
arguments.

The first personal call returns `authorization_required` and an owner
verification link. Open it yourself and approve the intended mind, then repeat
the exact call. Consulting and sharing task evidence are ticked; saving
memories, reviewing pending memories and learning start unticked. Approve only
links your own agent showed you:
approving a link someone else sends you connects your consciousness to their
agent. Authorization tokens remain in server memory;
a restart requires linking again. Personal invocations record history and send
the supplied question, review material and evidence to Mind Upload.

Keep the same material and identifiers on retries after linking, a timeout, or
an unfinished result so the service can replay the invocation. A changed review
needs a new `review_id`; a changed consultation needs a new `decision_id`.
`consult_mind` accepts `question`, `task_id`, `decision_id`, and the same
optional evidence and `learn` as `review_work`. Keep the same
`task_id` through initial direction, important decisions, and completion review
so the chosen mind receives the task's consultation history.

This section applies to the local server. The hosted server at
`https://mcp.mindupload.app/mcp` needs none of it: signing in in your agent links your mind.

## Access and privacy questions

**Does everyone need a partner key?** No. Add `https://mcp.mindupload.app/mcp` and sign
in: the hosted server holds the application credential, so nothing secret is
stored on your computer. A partner key is only for running the connector
yourself or building your own integration.

**Can someone using the same key reach my consciousness?** Not unless you
approve their request. Every call also needs the access token from an owner's
approval, issued for one installation and user identifier, and it reaches only
the consciousnesses that owner approved. The connector never asks for
`clone:invoke_shared`, the separate permission that would let another person's
agent call your consciousness in a shared group. People sharing a key do share
its limits, and reusing the same identifiers can mix their usage statistics.

**Which connection details must I never share?** Never approve a Mind Upload
sign-in someone else sends you: approving connects your consciousness to their
agent. Never let others use an agent session you have connected: anyone who can
send it requests acts as you. If you run the connector locally, also keep the
partner key private. Installation and user identifiers are labels, not
passwords: changing them protects nothing.

**What do restarting, disconnecting and revoking do?** With the hosted server,
restarting your agent keeps the connection; it signs in again only after 30
days unused. Asking your agent to run the `disconnect` tool ends the connection
and the approval in Mind Upload. Signing out of the connector in your agent
ends the connection; Mind Upload's approval then becomes unusable and is
replaced the next time you sign in from that agent. A local connector forgets
its tokens when it restarts, so it asks you to approve again. An approval
revoked in Mind Upload is refused on its next call. In the Mind Upload app
(version 1.14.1 or later), Profile → Last login → Connected agents and apps
lists every connection with the consciousness it uses, and disconnects any of
them.

**Where does my work material go, and what is kept?** The question, review
material, evidence files and media links you supply go to Mind Upload, where
your consciousness answers from its memories. Each exchange is stored encrypted
for 7 days, so a retry returns the same answer and later calls in the same
`task_id` include up to 20 earlier exchanges. An evidence file's description
expires after 24 hours and never becomes a memory. Mind Upload fetches media
links itself and can reuse a media description for up to 30 days. The connector
adds to your consciousness's memories only through `remember` or `learn`, with
the permissions you ticked, and those wait for your review unless you keep them
automatically. A local connector reads no file except the evidence files your
agent names. The privacy statement and terms in the Mind Upload app apply.

**Can a reply reveal private information?** Yes. The connector cannot read your
raw memories, but your consciousness answers from them, so a reply can contain
personal details. Replies appear in your agent's conversation and go wherever
that agent stores or sends it.

The host executes the work with its own tools and approvals. Mind Upload cannot
force a host to call these tools or act as a universal operating system for it.
Protocol and consent tests use simulated replies; they do not demonstrate the
quality of a real person's consciousness. A live owner-approved task is needed
to evaluate personal judgment and any improvement over the agent alone.
