# Mind Upload MCP: your AI meta harness

You ask your coding agent to ship a release. It says “done”, but it only pushed a tag: no release was created, and your users still get the old version. Mind Upload is an AI meta harness. A harness for your harnesses: your Mind Upload consciousness, built from your memories, tacit knowledge, values and judgment, is the brain, and the agents you already use are its hands and tools.
It checks Codex, Claude Code, Cursor or another execution agent at two moments. `consult_mind` asks your chosen mind how to approach the
task, using its personal memories, values, and judgment. Before completion,
`review_work` asks it to check the actual result and evidence against your
request and stored rules. Your agent can show it screenshots, screen recordings
and audio of the work privately, and, only with your permission, save notes
into your mind or help you go through memories waiting for your review.

## When to call it, and what we measured

Before you tell the user that a task which changed files, or ran a commit, push, release, deploy, migration or deletion, is done, call review_work with the original request, the diff excerpts and the test output you observed; if review_work is unavailable or fails, say plainly that no Mind Upload review ran. Call `consult_mind` before such a task, and
again when a consequential decision changes the plan; skip it only for
questions that change nothing. Each reply is advice, not approval.

Measured on 5 November 2026 with a blind grader: a coding agent reviewing alone caught 85% of planted breaches of rules the owner had stored; with the owner's consciousness reviewing the same work as well, 100% were caught, against 90% when the same agent reviewed twice. Each consciousness review took a median 12.6 s, against 24.6 s for a second agent review, and raised 0.2 unsupported findings instead of 1.8. Call it for the rules and past lessons you keep in Mind Upload and not in your agent's instruction files. It adds what only you know to your agent's own review; it does not replace it. The charts and how it
was measured are on [Mind Upload MCP](https://docs.mindupload.app/mcp#measured).

Start with [Mind Upload MCP](https://docs.mindupload.app/mcp), or use the install
routes below. Install the plugin when available: it bundles the server address,
a skill that asks for initial direction and completion scrutiny, and a reminder
that keeps review the default. Installing the server alone makes tools
available; the host still decides when to call them, so
[make the review the default](#make-the-review-the-default) for your agent.

## Connect your mind

Add `https://mcp.mindupload.app/mcp` to your agent, then sign in when it asks:

1. Your agent opens a Mind Upload page that shows which agent is asking and
   where access will go. Continue only if you just asked your own agent to
   connect.
2. Mind Upload opens in the same tab. Sign in and approve: your consciousness
   and every permission start ticked, and you can untick any. Approve only
   requests you started yourself.
3. Approving takes that tab straight back to your agent. The connection lasts
   across agent restarts until you sign out, or until it goes unused for 30
   days.

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

The plugin adds the hosted server and the Mind Upload skill. Sign in with
`claude mcp login mindupload`, or open `/mcp`, select **mindupload** and choose
Authenticate. Run `/mindupload:mindupload` to request your mind's
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
Mind Upload skill; use the project guidance under [Direct, execute, scrutinize](#direct-execute-scrutinize).

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
npx --yes --package mindupload@1.15.46 mindupload-mcp
```

The server speaks MCP over standard input and output; add it to your host as a
command-based server instead of typing into that terminal. For example,
`codex mcp add mindupload -- npx --yes --package mindupload@1.15.46 mindupload-mcp`.

### Python alternative

If you prefer the Python server, [uv](https://docs.astral.sh/uv/getting-started/installation/)
can install it and obtain a compatible interpreter:

```sh
uvx --python ">=3.11" --from "mindupload[mcp]==1.15.46" mindupload-mcp
```

Use `uvx` and the arguments above in place of the Node command in your host.

### Existing Python installation

```sh
python -m pip install "mindupload[mcp]==1.15.46"
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
> findings and missing evidence honestly. Review once per finished task, and
> again after material fixes. If Mind Upload is not
> connected, ask me to sign in, and state that no mind was consulted or review performed.
> A mind's advice does not grant permission for actions or establish correctness.

`review_work` accepts `user_request`, `work`, `evidence`, `task_id`, `review_id`,
optional `phase` (`completion` by default, or `plan` / `progress`), and optional
evidence (below). Supply actual excerpts and observed output. The connector
cannot run tests and opens no file except evidence your agent names. Include
what was not tested. The three text fields share one size limit with the review
instructions the connector adds: about 6,400 characters together after JSON
escaping, less with media links. Narrow the scope explicitly instead of silently
dropping evidence. Never include credentials or unrelated private data.

Each call tells Mind Upload whether it is a decision (`consult_mind`) or a
review (`review_work`), so your consciousness answers it as a task, not as a
chat message:

- The reply is written in the language of the question, or of the request for
  the work under review.
- A review lists findings by severity (critical, major, minor). Each finding
  gives the supporting excerpt, the correction and how to verify it. Then come
  the remaining unknowns and a readiness assessment limited to the supplied
  evidence.
- When one of your memories backs a finding or a direction, the reply says so
  and cites it, for example "I remember: …". A finding that rests on general
  engineering practice instead says "Not from my memory, but as a general
  practice: …".
- Facts about the work come only from what you supply. Anything it does not
  establish is called unknown, not guessed.

A connector from before this change does not say which kind it sends, and gets
a chat reply as before.

## Make the review the default

Every Mind Upload surface states the same rule:

> Before you tell the user that a task which changed files, or ran a commit, push, release, deploy, migration or deletion, is done, call review_work with the original request, the diff excerpts and the test output you observed; if review_work is unavailable or fails, say plainly that no Mind Upload review ran.

The server sends this rule to agents that read server instructions, and every
reply from `consult_mind` names the review as its `next_step`. Some agents
never show server instructions, so give yours the rule where it always reads it.

### Claude Code

The plugin does it. Its hook notices file edits and `git commit`, `git push`,
`gh release` and `gh pr create` commands; when the agent then tries to finish
without calling `review_work`, the hook reminds it once and lets the next stop
through. When you enable the plugin, Claude Code asks about the option
**Remind the agent to ask for a review**, which is on unless you turn it off.
The hook runs wherever Claude Code does: in sh, in Git Bash on Windows, and in
PowerShell on Windows without Git Bash. Without the plugin, add the rule to
`~/.claude/CLAUDE.md`.

### Codex

The plugin carries the same reminder as a Codex hook. Codex runs a plugin hook
only after you review and trust it: run `/hooks` once and trust the
**mindupload** hooks. On Windows the hook runs through PowerShell. Without the
plugin, add the rule to `~/.codex/AGENTS.md`.

### GitHub Copilot

Save the rule as `~/.copilot/instructions/mindupload.instructions.md` for the
Copilot CLI and app, or as `.github/instructions/mindupload.instructions.md` in
a project for VS Code:

```markdown
---
applyTo: "**"
---

Before you tell the user that a task which changed files, or ran a commit, push, release, deploy, migration or deletion, is done, call review_work with the original request, the diff excerpts and the test output you observed; if review_work is unavailable or fails, say plainly that no Mind Upload review ran.
```

The plugin carries the same file as a Copilot rule. The Copilot CLI shows a
server's instructions up front only for allowlisted servers; start it with
`copilot --allow-all-mcp-server-instructions` to include ours. The plugin
ships no Copilot hook, because Copilot does not document the name its hooks
see for an MCP tool, so a hook could not tell that `review_work` ran.

### Cursor

Cursor does not read server instructions. Save the rule as
`.cursor/rules/mindupload.mdc` in your project:

```markdown
---
description: Ask the Mind Upload consciousness to review work before saying it is done
alwaysApply: true
---

Before you tell the user that a task which changed files, or ran a commit, push, release, deploy, migration or deletion, is done, call review_work with the original request, the diff excerpts and the test output you observed; if review_work is unavailable or fails, say plainly that no Mind Upload review ran.
```

For a reminder as well, add a stop hook to `~/.cursor/hooks.json`. It costs one
extra agent turn every time the agent stops, including tasks that changed
nothing, and `loop_limit` keeps it to one per stop:

```json
{
  "version": 1,
  "hooks": {
    "stop": [
      {
        "command": "echo '{\"followup_message\":\"Before you tell the user that a task which changed files, or ran a commit, push, release, deploy, migration or deletion, is done, call review_work with the original request, the diff excerpts and the test output you observed; if review_work is unavailable or fails, say plainly that no Mind Upload review ran.\"}'",
        "loop_limit": 1
      }
    ]
  }
}
```

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
`review_id` alone does not refresh it. Replies to a call with links report, for
each link in the order supplied, what actually happened to it:

```json
{
  "media_analysis_status": "partially_analyzed",
  "media_analysis": [
    {"kind": "image", "status": "analyzed"},
    {"kind": "audio", "status": "refused", "reason": "hosted_by_mind_upload"},
    {"kind": "video", "status": "failed", "reason": "download_failed"}
  ]
}
```

| `status` | Meaning |
| --- | --- |
| `analyzed` | The consciousness received a description of the link, including one reused from an earlier analysis. |
| `refused` | The link was never opened. `reason` is `hosted_by_mind_upload` (a link to media stored by Mind Upload) or `export_not_allowed` (the data-handling rules that apply to your application do not allow its media to be sent for analysis). |
| `failed` | The link was meant to be analyzed but no description resulted. `reason` is `download_failed`, `analysis_failed`, `content_filtered` (the analysis declined to describe the content), `empty_analysis`, `time_budget_exhausted`, `item_limit_reached` or `analysis_unavailable`. |

One call analyzes a bounded number of new links. Links analyzed recently are
reused and do not count. The rest are analyzed in the order supplied, and each
link past the bound reports `item_limit_reached`; split a long list across
separate reviews, each with its own `review_id`. A link that reported
`content_filtered` or `empty_analysis` reports it again for the next 24 hours
without being analyzed again, and does not count either.

`media_analysis_status` summarizes the list: `analyzed` when every link was
analyzed, `partially_analyzed` when some were, and `not_analyzed` when none
were. It is `requested_unverified`, with no `media_analysis` list, when the
service returned no per-link report that lines up with the links supplied: for
example on a retry of a call made before these reports existed, or when an
entry is malformed or describes a different kind of media. Retries of the same
identifiers return the stored report unchanged. Only `analyzed` links were
perceived. Ask the mind to say what it could actually assess; missing
perception remains missing verification.

## Save and review memories, and let your mind learn

These need permissions that start ticked when you approve the connection.
Untick any you do not want this agent to use:

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
verification link. Open it yourself and approve, then repeat the exact call.
Your consciousness and every permission start ticked; untick anything you do
not want this agent to have. Approve only
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

The host executes the work with its own tools and approvals, and decides
whether to call these tools. Protocol and consent tests use simulated replies;
they do not show the quality of a real person's consciousness.
