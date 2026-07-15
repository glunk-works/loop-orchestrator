#!/usr/bin/env bash
# SessionStart hook: surface the .ai/ dev-workflow cursor at the top of every
# session so the ASSIGNED model/persona for the next action can't be missed.
# Automates the manual "you're on the wrong model for this" reminder — see
# CLAUDE.md "Working here: personas & model routing" and .ai/context/workflow.md.
#
# Reads .ai/state.json (relative to the session cwd = project root). Emits a
# SessionStart additionalContext block. No-ops silently outside the repo root
# or if jq/the cursor file is missing — a hook that errors is worse than none.
set -euo pipefail

state=".ai/state.json"
[ -f "$state" ] || exit 0
command -v jq >/dev/null 2>&1 || exit 0

jq '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: (
      "[.ai cursor] Assigned: \(.assigned_persona)/\(.assigned_model) for \(.current_sprint_id) (sprint_status: \(.sprint_status)).\n"
      + "Next action: \((.next_action // "unset") | split(". ")[0]).\n"
      + "If THIS session is not running \(.assigned_model), it is the wrong session for planning/review/architecture work: /handoff -> new session -> /model \(.assigned_model) -> /resume (CLAUDE.md model-routing rule). Mechanical/coder tasks are fine on any model."
    )
  }
}' "$state" 2>/dev/null || exit 0
