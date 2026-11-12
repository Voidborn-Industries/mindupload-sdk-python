#!/bin/sh
# Reminds the agent, once per stop, to call review_work before it says a file-changing task is done.
#
# Usage: review_gate.sh <claude|codex> <mark|clear|stop|end>, with the host's hook input as JSON on stdin.
#   mark   a tool changed files or shipped something: remember that this session owes a review
#   clear  review_work ran, or failed so the agent must say no review ran: nothing is owed
#   stop   the agent wants to stop: if a review is owed, ask for it once, then let it stop
#   end    the session ended: forget it
# review_gate.ps1 is its twin for a Windows host that runs the hook in PowerShell.
# Both Claude Code and Codex export CLAUDE_PLUGIN_DATA, the plugin's own folder that survives updates.
# It runs after every file edit, so it starts one grep, plus mkdir on the first mark and rm to remove a marker
# (each process costs about 40 ms on Windows, and Git Bash has no jq).

host="${1}"
action="${2}"
reminder='"This task changed files or shipped something, and review_work has not run since. Before you tell the user that a task which changed files, or ran a commit, push, release, deploy, migration or deletion, is done, call review_work with the original request, the diff excerpts and the test output you observed; if review_work is unavailable or fails, say plainly that no Mind Upload review ran."'
marker_directory="${CLAUDE_PLUGIN_DATA}/pending-review"

# One switch, on unless the Claude Code user turned it off in the plugin's settings.
[ "${CLAUDE_PLUGIN_OPTION_REMIND_REVIEW_BEFORE_DONE}" = "false" ] && exit 0

# grep reads the whole input in one pass and prints only the two keys the gate uses, each on its own line in input
# order: 0.24 to 0.27 s for a 3.6 MB Write in Git Bash, where the read builtin took 18 to 25 s. Only a key matches:
# a quote inside a JSON string is escaped, so a file's text that names these keys cannot.
hook_keys=$(LC_ALL=C grep -o -E '"session_id" *: *"[^"]*"|"stop_hook_active" *: *true')

session_id=
continued_by_stop_hook=false
set -f
IFS='
'
# Over grep's few printed lines. The first session_id is the input's own: Codex declares it first in every input
# (codex-rs/hooks/src/schema.rs), and Claude Code's hooks docs list it first but promise no key order. In any
# order, only a tool input whose own object has a session_id key could come before it.
for matched_key in $hook_keys; do
  case "$matched_key" in
    '"stop_hook_active"'*) continued_by_stop_hook=true ;;
    '"session_id"'*)
      if [ -z "$session_id" ]; then
        session_id="${matched_key%\"}"
        session_id="${session_id##*\"}"
      fi
      ;;
  esac
done
# The marker's file name comes from the input, so only a UUID-shaped id (hex digits and dashes) is used.
case "$session_id" in
  *[!0-9a-fA-F-]*) exit 0 ;;
esac
[ "${#session_id}" -eq 36 ] || exit 0
marker="${marker_directory}/${session_id}"

case "$action" in
  mark)
    [ -d "$marker_directory" ] || mkdir -p "$marker_directory"
    : > "$marker"
    ;;
  clear|end)
    [ -f "$marker" ] && rm -f "$marker"
    ;;
  stop)
    [ -f "$marker" ] || exit 0
    # A stop that a stop hook already continued is let through, so the reminder fires at most once.
    if [ "$continued_by_stop_hook" = true ]; then
      rm -f "$marker"
      exit 0
    fi
    case "$host" in
      # Claude Code shows additionalContext as hook feedback, not as an error, and continues the turn.
      claude) printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":%s}}\n' "$reminder" ;;
      # Codex documents no additionalContext for Stop; a block continues the turn with reason as the prompt.
      codex) printf '{"decision":"block","reason":%s}\n' "$reminder" ;;
    esac
    ;;
esac
exit 0
