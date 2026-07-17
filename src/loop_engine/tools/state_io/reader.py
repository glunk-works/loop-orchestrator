"""Read-only correlation scan over persisted state snapshots.

Lives beside `writer.py` (the write-owning module) rather than in
`slack_control/`, so the daemon performs no raw file I/O of its own and its
"writes no files directly" boundary test stays honest.
"""

import json
from pathlib import Path

from loop_engine.core.state import RunStatus

_SNAPSHOT_GLOB = "*/*.json"


def find_paused_snapshot_by_slack_thread(message_ts: str) -> Path | None:
    """The AWAITING_SLACK snapshot paused on `message_ts`, or None.

    Scans the main-checkout `state/` tree with a plain glob -- run snapshots
    always land there (`writer.state_root()` pins it before any worktree
    chdir), never under `.worktrees/`. Each candidate is read as raw JSON
    rather than `State.model_validate`-ed: `state/` accumulates v4 and
    non-Slack snapshots that must be skipped, not raised on, so one foreign
    or malformed file can never crash the scan. Reads only -- no writes.
    """
    state_dir = Path("state")
    if not state_dir.is_dir():
        return None
    for path in sorted(state_dir.glob(_SNAPSHOT_GLOB)):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("status") != RunStatus.AWAITING_SLACK.value:
            continue
        pending_slack = payload.get("pending_slack")
        if not isinstance(pending_slack, dict):
            continue
        if pending_slack.get("message_ts") == message_ts:
            return path
    return None
