# Mind Upload MCP: scrutiny before your agent says it is done

Give your AI agent a review checkpoint for completed work, plans, and risky
changes. `review_work` compares the user's request, the deliverable, and supplied
evidence. Without an account or key it returns a structured brief for the host
agent to perform self-review. With an owner-linked Mind Upload consciousness,
it requests a personal review informed by that mind's memories and judgment.
`consult_mind` also provides direction when personal preferences matter.

Start with [Mind Upload MCP](https://docs.mindupload.app/mcp), or use the install
routes below. Install the plugin when available: it bundles both the MCP server
and a skill that asks for completion scrutiny. Installing the server alone makes
tools available; the host still decides when to call them.

## Install without a key

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and make
`uvx` available to your agent. The server requires Python 3.11 or later; `uv`
can obtain a compatible interpreter. The pinned launch command is:

```sh
uvx --python ">=3.11" --from "mindupload[mcp]==1.15.12" mindupload-mcp
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
codex mcp add mindupload -- uvx --python ">=3.11" --from "mindupload[mcp]==1.15.12" mindupload-mcp
```

### Claude Code plugin

```sh
claude plugin marketplace add https://github.com/Voidborn-Industries/mindupload-sdk-python
claude plugin install mindupload@mindupload
```

Run `/mindupload:mindupload-review` to request scrutiny, or ask the agent to use
Mind Upload before its final response. Check `/mcp` for the server connection.
See the [plugin installation guide](https://code.claude.com/docs/en/plugins/install).

### Cursor, Claude Desktop, Cline, and other local MCP hosts

Add this server using the host's MCP configuration interface. For hosts whose
configuration uses `mcpServers`, merge the following entry into that object:

```json
{
  "mcpServers": {
    "mindupload": {
      "command": "uvx",
      "args": ["--python", ">=3.11", "--from", "mindupload[mcp]==1.15.12", "mindupload-mcp"]
    }
  }
}
```

Cursor also accepts the portable plugin in this repository; public marketplace
listing requires a separate review. The [Cursor MCP guide](https://cursor.com/docs/mcp)
describes server configuration. A configuration entry alone does not install the
review skill; add the instruction under **Use scrutiny consistently** below.

### VS Code and GitHub Copilot

Run **MCP: Add Server** and select a command-based server with the command above,
or merge this entry into your workspace's `.vscode/mcp.json`:

```json
{
  "servers": {
    "mindupload": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--python", ">=3.11", "--from", "mindupload[mcp]==1.15.12", "mindupload-mcp"]
    }
  }
}
```

See [VS Code's MCP guide](https://code.visualstudio.com/docs/agent-customization/mcp-servers).
If a host searches the official MCP Registry, search **mindupload** or the
publisher name **io.github.Voidborn-Industries/mindupload**. Registry publication,
downstream indexing, and each host's marketplace approval are separate steps.

### Existing Python installation

```sh
python -m pip install "mindupload[mcp]==1.15.12"
python -m mindupload.mcp
```

Use that interpreter's absolute path as your host's command and
`["-m", "mindupload.mcp"]` as its arguments. The optional MCP extra adds the
server dependencies; the base SDK keeps its existing requirements.

## Use scrutiny consistently

Ask: **“Use Mind Upload to scrutinize the completed work against my request
and the actual verification evidence. Investigate and fix concrete findings
before your final response.”**

For hosts without the bundled skill, add this to your project guidance:

> Before claiming substantive work is complete, call `review_work` with my
> request, the changed work or result excerpts, and actual verification output.
> Use completion phase, one stable task identifier, and a new review identifier
> when the supplied material changes. If it returns `self_review_required`,
> perform the returned critique yourself and identify it as self-review. Fix
> demonstrated problems and verify the changed version. Report unresolved
> findings and missing evidence honestly. Review consequential plans or changed
> assumptions when needed; avoid calls after every edit. A review does not grant
> permission for actions or establish that a deliverable is correct.

`review_work` accepts `user_request`, `work`, `evidence`, `task_id`, `review_id`,
and optional `phase` (`completion` by default, or `plan` / `progress`). Supply
actual excerpts and observed output: the server cannot open host files or fetch
links. Include what was not tested. Keep the complete review material within
the tool's advertised size limit; narrow the scope explicitly instead of
silently dropping evidence. Never include credentials or unrelated private data.

A local review brief makes zero partner API requests and uses the host's model
when it performs the critique. Personal review uses one existing invocation
request in the normal completed case; authorization and unfinished results can
require additional requests. Normal invocation charging applies. Neither mode
guarantees that every defect will be found. `succeeded` reports delivery of a
personal review, not approval of the work.

## Optional personal consciousness review

Supply these variables through the environment that launches your server:

- `MINDUPLOAD_PARTNER_KEY`: your existing private partner key. Keep it in your
  trusted runtime; never distribute it with an application or paste it in chat.
- `MINDUPLOAD_INSTALLATION_ID`: a stable identifier for this installation.
- `MINDUPLOAD_EXTERNAL_SUBJECT`: a stable identifier for the person linking
  their mind in this installation.
- `MINDUPLOAD_CLONE_ID` (optional): the exact mind to consult. Without it,
  approve exactly one mind during linking; multiple minds require this setting.

No key is needed for local review briefs. Partner access is required for
personal review; installing this package does not create a partner account.
Some hosts filter inherited variables. Use that host's supported environment
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
`consult_mind` accepts `question`, `task_id`, and `decision_id`. Use it for
decisions that need the owner's perspective, while retaining final scrutiny.

This is a local stdio server. Web-only hosts need explicit support for a local
connection; this package is not a hosted remote MCP endpoint.
