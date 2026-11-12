# Reminds the agent on Windows, once per stop, to call review_work before it says a file-changing task is done.
# The PowerShell twin of review_gate.sh, for a host that runs the hook in PowerShell: Codex on Windows, and
# Claude Code on Windows without Git Bash. -HostName is claude or codex; the actions mean the same:
#   mark   a tool changed files or shipped something: remember that this session owes a review
#   clear  review_work ran, or failed so the agent must say no review ran: nothing is owed
#   stop   the agent wants to stop: if a review is owed, ask for it once, then let it stop
#   end    the session ended: forget it
# Codex's command, run by cmd.exe, starts this with -File; either host's command, run by PowerShell, runs this
# text as a script block in that process. Both ways the hook input is UTF-8 JSON on that process's standard input.
param(
    [ValidateSet('claude', 'codex')]
    [string]$HostName,
    [ValidateSet('mark', 'clear', 'stop', 'end')]
    [string]$Action
)

# Load the two modules this script's commands come from by name, and never search for a command: a search reads
# every module installed ahead of PowerShell's own, as Microsoft.Graph's are on GitHub's Ubuntu runners, and a
# process this short never saves what it read (AnalysisCache.cs saves 13 s later), so each start would read them all.
$PSModuleAutoLoadingPreference = 'None'
Import-Module -Name Microsoft.PowerShell.Utility, Microsoft.PowerShell.Management

$Reminder = '"This task changed files or shipped something, and review_work has not run since. Before you tell the user that a task which changed files, or ran a commit, push, release, deploy, migration or deletion, is done, call review_work with the original request, the diff excerpts and the test output you observed; if review_work is unavailable or fails, say plainly that no Mind Upload review ran."'
# Both hosts export CLAUDE_PLUGIN_DATA (Codex beside PLUGIN_DATA); the sh twin reads the same name.
$MarkerDirectory = Join-Path -Path $env:CLAUDE_PLUGIN_DATA -ChildPath 'pending-review'

# One switch, on unless the Claude Code user turned it off in the plugin's settings.
if ($env:CLAUDE_PLUGIN_OPTION_REMIND_REVIEW_BEFORE_DONE -eq 'false') { exit 0 }

# Read as UTF-8 bytes, not through $input, which decodes with the console's code page: under Chinese Windows' 936,
# a Chinese character before an escaped quote swallows the quote, and the JSON no longer parses.
$Utf8WithoutMark = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
$StandardInput = New-Object -TypeName System.IO.StreamReader -ArgumentList ([Console]::OpenStandardInput()), $Utf8WithoutMark
$HookInput = $StandardInput.ReadToEnd() | ConvertFrom-Json
$SessionId = [string]$HookInput.session_id
# The marker's file name comes from the input, so only a session id shaped like a UUID is used.
if ($SessionId -notmatch '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$') { exit 0 }
$Marker = Join-Path -Path $MarkerDirectory -ChildPath $SessionId

switch ($Action) {
    'mark' {
        New-Item -ItemType Directory -Force -Path $MarkerDirectory | Out-Null
        New-Item -ItemType File -Force -Path $Marker | Out-Null
    }
    { $_ -in 'clear', 'end' } {
        Remove-Item -Force -ErrorAction SilentlyContinue -Path $Marker
    }
    'stop' {
        if (-not (Test-Path -Path $Marker)) { exit 0 }
        # A stop that a stop hook already continued is let through, so the reminder fires at most once.
        if ($HookInput.stop_hook_active -eq $true) {
            Remove-Item -Force -Path $Marker
            exit 0
        }
        if ($HostName -eq 'claude') {
            # Claude Code shows additionalContext as hook feedback, not as an error, and continues the turn.
            Write-Output ('{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":' + $Reminder + '}}')
        } else {
            # Codex documents no additionalContext for Stop; a block continues the turn with reason as the prompt.
            Write-Output ('{"decision":"block","reason":' + $Reminder + '}')
        }
    }
}
exit 0
