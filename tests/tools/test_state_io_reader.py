import json
import os
from pathlib import Path

import pytest

from loop_orchestrator.tools.state_io.reader import find_paused_snapshot_by_slack_thread, load_state

MESSAGE_TS = "1700000000.000100"


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _write(run_id: str, name: str, payload: dict) -> Path:
    run_dir = Path("state") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_at(run_id: str, name: str, payload: dict, *, mtime: float) -> Path:
    """Like `_write`, but pins the file's mtime explicitly -- deterministic
    stand-in for "written at time T", since real wall-clock write order can
    be sub-resolution-close in a fast test run."""
    path = _write(run_id, name, payload)
    os.utime(path, (mtime, mtime))
    return path


def test_find_paused_snapshot_by_slack_thread_returns_the_matching_snapshot() -> None:
    match = _write(
        "run-1",
        "02_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": MESSAGE_TS},
            "stage_history": [],
            "artifacts": {},
        },
    )

    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) == match


def test_find_paused_snapshot_by_slack_thread_returns_none_on_no_match() -> None:
    _write(
        "run-1",
        "02_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": "9999999999.000000"},
            "stage_history": [],
            "artifacts": {},
        },
    )

    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) is None


def test_find_paused_snapshot_by_slack_thread_returns_none_when_state_dir_absent() -> None:
    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) is None


def test_find_paused_snapshot_by_slack_thread_ignores_v4_pre_slack_snapshots() -> None:
    # v4 predates pending_slack entirely -- the field is just absent, not null.
    _write(
        "run-1",
        "01_awaiting_issue.json",
        {
            "schema_version": 4,
            "run_id": "run-1",
            "status": "awaiting_issue",
            "pending_issue": {"number": 17, "url": "https://github.com/acme/repo/issues/17"},
            "stage_history": [],
            "artifacts": {},
        },
    )

    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) is None


def test_find_paused_snapshot_by_slack_thread_ignores_malformed_json_without_raising() -> None:
    run_dir = Path("state") / "run-broken"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "00_broken.json").write_text("{not valid json", encoding="utf-8")
    match = _write(
        "run-1",
        "02_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": MESSAGE_TS},
            "stage_history": [],
            "artifacts": {},
        },
    )

    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) == match


def test_find_paused_snapshot_by_slack_thread_ignores_a_non_dict_json_payload() -> None:
    run_dir = Path("state") / "run-weird"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "00_list.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) is None


def test_find_paused_snapshot_by_slack_thread_returns_none_for_an_already_resumed_snapshot() -> (
    None
):
    # A pause leaves a contradictory awaiting_issue placeholder beside the
    # real awaiting_slack snapshot (dedupe finding); a resumed run's terminal
    # snapshot may also still carry a stale pending_slack -- status is what
    # decides "still paused", not the presence of pending_slack.
    _write(
        "run-1",
        "01_awaiting_issue.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_issue",
            "pending_issue": {"number": 17, "url": "https://github.com/acme/repo/issues/17"},
            "stage_history": [],
            "artifacts": {},
        },
    )
    _write(
        "run-1",
        "03_completed.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "completed",
            "pending_slack": {"channel_id": "C123", "message_ts": MESSAGE_TS},
            "stage_history": [],
            "artifacts": {},
        },
    )

    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) is None


def test_find_paused_snapshot_by_slack_thread_ignores_stale_awaiting_slack_file() -> None:
    # T4-review finding #1: a resume never rewrites or removes the paused
    # run's own NN_awaiting_slack.json, so it lingers with status still
    # "awaiting_slack" and the same message_ts. A later snapshot in the same
    # run directory (the resume's own terminal write) shows the run has
    # actually moved on -- the scan must trust the LATEST snapshot per run,
    # not any matching file, or a second thread reply would double-resume.
    _write(
        "run-1",
        "02_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": MESSAGE_TS},
            "stage_history": [],
            "artifacts": {},
        },
    )
    _write(
        "run-1",
        "03_completed.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "completed",
            "pending_slack": {"channel_id": "C123", "message_ts": MESSAGE_TS},
            "stage_history": [],
            "artifacts": {},
        },
    )

    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) is None


def test_find_paused_snapshot_by_slack_thread_matches_latest_of_several_awaiting_slack() -> None:
    # The still-current case: the run's latest snapshot IS awaiting_slack
    # (no resume has happened yet), even though an earlier stage also paused
    # on a (different, already-answered) Slack thread.
    _write(
        "run-1",
        "01_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": "1111111111.000000"},
            "stage_history": [],
            "artifacts": {},
        },
    )
    match = _write(
        "run-1",
        "02_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": MESSAGE_TS},
            "stage_history": [],
            "artifacts": {},
        },
    )

    assert find_paused_snapshot_by_slack_thread(MESSAGE_TS) == match


def test_find_paused_snapshot_by_slack_thread_uses_mtime_not_filename_on_backward_reentry() -> None:
    # Architect/security-critic finding on this PR: a run's stage_index is
    # the loop STAGE POSITION, not a monotonic write counter, and
    # blast-radius re-entry (core.engine.reentry_index) can re-enter at an
    # EARLIER stage than a prior pause. So a run can pause a second time
    # (chronologically later) at a lower stage index than its first pause,
    # writing "01_awaiting_slack.json" AFTER "03_awaiting_slack.json" --
    # picking "highest filename" as latest would pick the stale, higher-
    # numbered-but-older file, both silently dropping the live thread's
    # answer and leaving the dead thread able to double-resume.
    OLD_TS = "1111111111.000000"
    NEW_TS = "2222222222.000000"
    old_pause = _write_at(
        "run-1",
        "03_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": OLD_TS},
            "stage_history": [],
            "artifacts": {},
        },
        mtime=1000.0,
    )
    new_pause = _write_at(
        "run-1",
        "01_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": NEW_TS},
            "stage_history": [],
            "artifacts": {},
        },
        mtime=2000.0,
    )

    # The live thread (the chronologically later pause, despite the lower
    # stage-index filename) must still resolve -- not be dropped.
    assert find_paused_snapshot_by_slack_thread(NEW_TS) == new_pause
    # The dead thread (the earlier pause, despite the higher-numbered
    # filename) must NOT resolve -- no double-resume on a stale thread.
    assert find_paused_snapshot_by_slack_thread(OLD_TS) is None
    assert old_pause != new_pause


def test_load_state_migrates_a_v4_snapshot_and_validates() -> None:
    path = _write(
        "run-1",
        "01_awaiting_issue.json",
        {
            "schema_version": 4,
            "run_id": "run-1",
            "status": "awaiting_issue",
            "pending_issue": {"number": 17, "url": "https://github.com/acme/repo/issues/17"},
            "stage_history": [],
            "artifacts": {},
        },
    )

    state = load_state(path)

    assert state.schema_version == 5
    assert state.pending_slack is None
    assert state.run_id == "run-1"


def test_find_paused_snapshot_by_slack_thread_writes_nothing() -> None:
    _write(
        "run-1",
        "02_awaiting_slack.json",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "status": "awaiting_slack",
            "pending_slack": {"channel_id": "C123", "message_ts": MESSAGE_TS},
            "stage_history": [],
            "artifacts": {},
        },
    )
    before = {p: p.read_bytes() for p in Path("state").rglob("*.json")}

    find_paused_snapshot_by_slack_thread(MESSAGE_TS)

    after = {p: p.read_bytes() for p in Path("state").rglob("*.json")}
    assert before == after
