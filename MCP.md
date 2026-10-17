# Mind Upload MCP: your AI meta harness

An **AI meta harness** lets your Mind Upload consciousness direct Codex, Claude
Code, Cursor, or another execution agent. `consult_mind` asks your chosen mind how to approach the task,
using its personal memories, values, and judgment. Before completion,
`review_work` asks the same mind to scrutinize the actual result and evidence:
does it satisfy your request, and does it fit your intent?

Start with [Mind Upload MCP](https://docs.mindupload.app/mcp), or use the install
routes below. Install the plugin when available: it bundles both the MCP server
and a skill that asks for initial direction and completion scrutiny. Installing
the server alone makes tools available; the host still decides when to call them.

## Connect your mind

You need a consciousness in [Mind Upload](https://mindupload.app), partner API
access, and owner consent. [Request partner access](https://docs.mindupload.app/)
through the API documentation's access form if you do not already have it.
Partner access is currently required; installing this package does not create
an account or provide a shared key.

You can install and discover the connector before setup. Both tools return
`setup_required` with a setup link until the trusted runtime is configured;
no consciousness is consulted and no review runs.

Supply the runtime values under **Personal setup and owner consent** below,
then open the verification link returned by the first call and approve the
intended consciousness. Keep the private partner key out of chat and tool
arguments.

## Install the connector

MCP is language agnostic: your agent and project can use any language. Choose
either local server implementation. The default uses Node.js 20 or later and
does not require Python or `uv`; the [Python alternative](#python-alternative)
uses Python 3.11 or later. Both expose the same tools and owner consent flow.

With [Node.js](https://nodejs.org/en/download) installed, the pinned launch command is:

```sh
npx --yes --package mindupload@1.15.16 mindupload-mcp
```

The server speaks MCP over standard input and output; an interactive terminal
waits for protocol messages. Add it to your host instead of typing questions
into that terminal.

### Codex plugin

```sh
codex plugin marketplace add https://github.com/Voidborn-Industries/mindupload-sdk-python
codex plugin add mindupload@mindupload
```

Alternatively, in the desktop app, open Plugins, select the **Mind Upload**
marketplace, and install **mindupload**. This adds our repository marketplace;
it does not imply listing in the universal public directory. For configuration
without the plugin:

```sh
codex mcp add mindupload -- npx --yes --package mindupload@1.15.16 mindupload-mcp
```

### Claude Code plugin

```sh
claude plugin marketplace add https://github.com/Voidborn-Industries/mindupload-sdk-python
claude plugin install mindupload@mindupload
```

Run `/mindupload:mindupload-review` to request your mind's direction and final
scrutiny. Check `/mcp` for the server connection.
See the [plugin installation guide](https://code.claude.com/docs/en/plugins/install).

### Cursor, Claude Desktop, Cline, and other local MCP hosts

Add this server using the host's MCP configuration interface. For hosts whose
configuration uses `mcpServers`, merge the following entry into that object:

```json
{
  "mcpServers": {
    "mindupload": {
      "command": "npx",
      "args": ["--yes", "--package", "mindupload@1.15.16", "mindupload-mcp"]
    }
  }
}
```

Cursor also accepts the portable plugin in this repository; public marketplace
listing requires a separate review. The [Cursor MCP guide](https://cursor.com/docs/mcp)
describes server configuration. A configuration entry alone does not install the
review skill; use the project guidance under [Direct, execute, scrutinize](#direct-execute-scrutinize).

### VS Code and GitHub Copilot

Run **MCP: Add Server** and select a command-based server with the command above,
or merge this entry into your workspace's `.vscode/mcp.json`:

```json
{
  "servers": {
    "mindupload": {
      "type": "stdio",
      "command": "npx",
      "args": ["--yes", "--package", "mindupload@1.15.16", "mindupload-mcp"]
    }
  }
}
```

See [VS Code's MCP guide](https://code.visualstudio.com/docs/agent-customization/mcp-servers).
If a host searches the official MCP Registry, search **mindupload** or the
publisher name **io.github.Voidborn-Industries/mindupload**. Registry publication,
downstream indexing, and each host's marketplace approval are separate steps.

### Python alternative

If you prefer the Python server, [uv](https://docs.astral.sh/uv/getting-started/installation/)
can install it and obtain a compatible interpreter:

```sh
uvx --python ">=3.11" --from "mindupload[mcp]==1.15.16" mindupload-mcp
```

Use `uvx` and the arguments above in place of the Node command in your host.

### Existing Python installation

```sh
python -m pip install "mindupload[mcp]==1.15.16"
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
> assumptions when needed; avoid calls after every edit. If setup is required,
> show the setup link and state that no mind was consulted or review performed.
> A mind's advice does not grant permission for actions or establish correctness.

`review_work` accepts `user_request`, `work`, `evidence`, `task_id`, `review_id`,
optional `phase` (`completion` by default, or `plan` / `progress`), and optional
`media_evidence`. Supply actual excerpts and observed output. The connector
cannot open local files or run tests. Include what was not tested. Keep all text
and media references within
the tool's advertised size limit; narrow the scope explicitly instead of
silently dropping evidence. Never include credentials or unrelated private data.

## Review screenshots, audio, and video

Both tools accept `media_evidence`: a list of `kind` (`image`, `audio`, or
`video`) and `url` pairs. For example, attach a screenshot of the completed UI
and ask whether it follows the owner's intended design:

```json
{
  "kind": "image",
  "url": "https://example.com/authorized-task-screenshot.png"
}
```

Use HTTPS links that the owner authorizes Mind Upload to access and that remain
available during the invocation. The connector forwards them to the
consciousness's existing multimedia analysis. It does not upload local files or
accept inline binary data. Private-host URLs, local file paths, and links behind
browser sign-in are unsuitable. Treat access-bearing links as private task data.
Use immutable or versioned media URLs: replacing content at the same URL can
reuse a cached description. A changed `review_id` alone does not refresh media.
Include capture time, artifact version, and the segment or interaction to assess.

Successful replies echo submitted media references and report
`media_analysis_status: "requested_unverified"`. This confirms what was
requested, **not** that every item was perceived: access failures, processing
limits, or account routing can leave analysis missing or partial. The current
API does not return a separate analysis receipt for each item. Video and audio
analysis can cover selected frames or a bounded portion of a recording. Ask the
mind to identify what it could actually assess; missing perception remains
missing verification. A screenshot also does not establish that an interaction works.

An established consultation or review uses one existing invocation
request in the normal completed case; authorization and unfinished results can
require additional requests. Existing partner API usage rules apply. A
`succeeded` response includes the selected consciousness's identifier and
nickname, its reply, and the invocation receipt. It reports delivery of that
mind's judgment, not approval or a guarantee that every defect was found.

## Personal setup and owner consent

Supply these variables through the environment that launches your server:

- `MINDUPLOAD_PARTNER_KEY`: your existing private partner key. Keep it in your
  trusted runtime; never distribute it with an application or paste it in chat.
- `MINDUPLOAD_INSTALLATION_ID`: a stable identifier for this installation.
- `MINDUPLOAD_EXTERNAL_SUBJECT`: a stable identifier for the person linking
  their mind in this installation.
- `MINDUPLOAD_CLONE_ID` (optional): the exact mind to consult. Without it,
  approve exactly one mind during linking; multiple minds require this setting.

Partner access is required for both tools. Some hosts filter inherited variables.
Use that host's supported environment
forwarding settings and restart the server. For Codex's direct MCP configuration,
add `env_vars` with the three required names and optional clone name to its
`mcp_servers.mindupload` entry; never put credential values in the guide or tool
arguments.

The first personal call returns `authorization_required` and an owner
verification link. Open it yourself and approve `clone:invoke` for the intended
mind, then repeat the exact call. Authorization tokens remain in server memory;
a restart requires linking again. The connection requests no learning or
memory-upload permission, but personal invocations record history and send the
supplied question or review material to Mind Upload.

Keep the same material and identifiers on retries after linking, a timeout, or
an unfinished result so the service can replay the invocation. A changed review
needs a new `review_id`; a changed consultation needs a new `decision_id`.
`consult_mind` accepts `question`, `task_id`, and `decision_id`. Keep the same
`task_id` through initial direction, important decisions, and completion review
so the chosen mind receives the task's consultation history.

This is a local stdio server. Web-only hosts need explicit support for a local
connection; this package is not a hosted remote MCP endpoint.

The host executes the work with its own tools and approvals. Mind Upload cannot
force a host to call these tools or act as a universal operating system for it.
Protocol and consent tests use simulated replies; they do not demonstrate the
quality of a real person's consciousness. A live owner-approved task is needed
to evaluate personal judgment and any improvement over the agent alone.
