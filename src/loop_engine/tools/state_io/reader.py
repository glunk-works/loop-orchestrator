"""Read-only correlation scan over persisted state snapshots.

Lives beside `writer.py` (the write-owning module) rather than in
`slack_control/`, so the daemon performs no raw file I/O of its own and its
"writes no files directly" boundary test stays honest.
"""

import json
from pathlib import Path

from loop_engine.core.state import RunStatus, State, migrate_state_payload


def find_paused_snapshot_by_slack_thread(message_ts: str) -> Path | None:
    """The AWAITING_SLACK snapshot paused on `message_ts`, or None.

    Scans the main-checkout `state/` tree -- run snapshots always land there
    (`writer.state_root()` pins it before any worktree chdir), never under
    `.worktrees/`. Each candidate is read as raw JSON rather than
    `State.model_validate`-ed: `state/` accumulates v4 and non-Slack
    snapshots that must be skipped, not raised on, so one foreign or
    malformed file can never crash the scan. Reads only -- no writes.

    Considers only the **latest** snapshot file per run directory (T4-review
    finding #1): a resume never rewrites or removes the paused run's own
    `NN_awaiting_slack.json`, so a plain glob over every file would keep
    re-matching that stale file's still-`awaiting_slack` status even after a
    later snapshot in the same directory shows the run has moved on --
    causing a second thread reply to double-resume the same run. Snapshot
    filenames are `{stage_index:02d}_{stage_name}.json`
    (`writer.write_state_snapshot`), so a plain lexicographic sort within a
    run's directory is also a stage-index sort; the last one is the run's
    current status.
    """
    state_dir = Path("state")
    if not state_dir.is_dir():
        return None
    for run_dir in sorted(p for p in state_dir.iterdir() if p.is_dir()):
        candidates = sorted(run_dir.glob("*.json"))
        if not candidates:
            continue
        latest = candidates[-1]
        try:
            payload = json.loads(latest.read_text(encoding="utf-8"))
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
            return latest
    return None


def load_state(path: Path) -> State:
    """Load and validate a persisted snapshot, migrating it to
    `CURRENT_SCHEMA_VERSION` first -- the read-side counterpart to
    `write_state_snapshot`, so `slack_control/` (and any other reader) never
    needs its own raw `open`/`json.loads` of a snapshot file."""
    payload = migrate_state_payload(json.loads(path.read_text(encoding="utf-8")))
    return State.model_validate(payload)
