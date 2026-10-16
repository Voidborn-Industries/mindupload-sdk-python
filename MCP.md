# Mind Upload for agent harnesses

Connect your Mind Upload consciousness to Codex, Cursor, or Claude Code. The
`consult_mind` tool asks your chosen mind for direction using its existing
memories and judgment; your agent carries out the work with its own tools.
MCP makes the consultation available. Your agent's instructions determine when
it consults and how it applies the answer.

## Install and configure

Use Python 3.11 or later:

```sh
python -m pip install "mindupload[mcp]"
python -c "import sys; print(sys.executable)"
```

Use the printed interpreter path in the configuration below. The optional MCP
integration adds dependencies; the base Python SDK keeps its existing dependency
and Python requirements. The launch command is `python -m mindupload.mcp`;
`mindupload-mcp` is also available after installation.

Supply these variables through the environment that launches your agent:

- `MINDUPLOAD_PARTNER_KEY`: your existing partner key. Keep this secret in your
  trusted runtime; never distribute it with an application or share it in chat.
- `MINDUPLOAD_INSTALLATION_ID`: a stable identifier for this installation.
- `MINDUPLOAD_EXTERNAL_SUBJECT`: a stable identifier for the person linking
  their mind in this installation.
- `MINDUPLOAD_CLONE_ID` (optional): the exact mind to consult. Without it, approve
  exactly one mind during linking. Multiple approved minds require this setting.

The examples forward variable references, never credential values. Restart the
agent after supplying its environment or changing its MCP configuration.

### Codex

Add to your Codex `config.toml`:

```toml
[mcp_servers.mindupload]
command = "/absolute/path/to/python"
args = ["-m", "mindupload.mcp"]
env_vars = ["MINDUPLOAD_PARTNER_KEY", "MINDUPLOAD_INSTALLATION_ID", "MINDUPLOAD_EXTERNAL_SUBJECT"]
tool_timeout_sec = 180
```

If selecting a mind explicitly, add `MINDUPLOAD_CLONE_ID` to `env_vars` too.
See the [Codex MCP configuration guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

### Cursor

Add to your user or project's `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mindupload": {
      "type": "stdio",
      "command": "/absolute/path/to/python",
      "args": ["-m", "mindupload.mcp"],
      "env": {
        "MINDUPLOAD_PARTNER_KEY": "${env:MINDUPLOAD_PARTNER_KEY}",
        "MINDUPLOAD_INSTALLATION_ID": "${env:MINDUPLOAD_INSTALLATION_ID}",
        "MINDUPLOAD_EXTERNAL_SUBJECT": "${env:MINDUPLOAD_EXTERNAL_SUBJECT}"
      }
    }
  }
}
```

For explicit mind selection, add `MINDUPLOAD_CLONE_ID` with the same environment
reference syntax. See the [Cursor MCP configuration guide](https://cursor.com/docs/mcp).

### Claude Code

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "mindupload": {
      "type": "stdio",
      "command": "/absolute/path/to/python",
      "args": ["-m", "mindupload.mcp"],
      "env": {
        "MINDUPLOAD_PARTNER_KEY": "${MINDUPLOAD_PARTNER_KEY}",
        "MINDUPLOAD_INSTALLATION_ID": "${MINDUPLOAD_INSTALLATION_ID}",
        "MINDUPLOAD_EXTERNAL_SUBJECT": "${MINDUPLOAD_EXTERNAL_SUBJECT}"
      }
    }
  }
}
```

For explicit mind selection, add `MINDUPLOAD_CLONE_ID` with the same environment
reference syntax. Open `/mcp` to check the connection. See the
[Claude Code MCP configuration guide](https://code.claude.com/docs/en/mcp).

## Link and consult

Ask your agent to call `consult_mind` with your goal and the relevant constraints.
Its first call returns `authorization_required` and an owner verification link.
Open that link yourself and approve `clone:invoke` for the intended mind. Then
ask the agent to repeat the same consultation.

The server holds authorization tokens only in its own memory and refreshes them
during use. Restarting the server requires linking again. Your credentials never
belong in tool arguments or answers. Linking does not delay MCP startup.

Use a stable `task_id` for one task and a distinct `decision_id` for each real
decision. Keep the same question and both identifiers when retrying after
linking, a timeout, or an unfinished result. This lets the service replay the
same consultation instead of charging for a second one. A changed question
needs a new `decision_id`; a separate task needs a new `task_id`.

Example tool arguments:

```json
{
  "question": "Help choose a delivery plan. My priorities are preserving existing work and avoiding recurring maintenance. What tradeoffs and acceptance criteria should guide the agent?",
  "task_id": "delivery-plan-2026-10-16",
  "decision_id": "initial-direction"
}
```

Consult at the start of a task and when new information changes a meaningful
decision. Keep the resulting brief in the agent's context while it works.
One consultation uses one existing clone invocation; slow replies may need
additional requests with the same event key. Normal invocation charging applies.
The tool also records invocation history, so it is not marked read-only.
It does not request learning or memory-upload permissions.

## Make the workflow consistent

Add this instruction to your agent's project guidance, such as `AGENTS.md`,
`CLAUDE.md`, or a Cursor rule:

> At task start, consult Mind Upload with the goal, relevant constraints, and
> decisions that depend on my preferences. Use one stable task identifier and
> one decision identifier per meaningful decision. If linking is required,
> show me the verification link and wait for approval before retrying the same
> question and identifiers. Keep the resulting direction in context, apply it
> while working, and consult again only when new evidence changes a major
> decision. Use the harness's existing tools to execute and verify the work.
> Never send credentials to the consultation or treat its answer as permission
> to bypass my instructions or the harness's controls.

This local connection requires the agent host to run the Python process and
reach the partner API. A cloud-only agent cannot use a process on your computer
unless its host explicitly supports that connection.
