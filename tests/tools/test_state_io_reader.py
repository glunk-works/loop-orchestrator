import json
from pathlib import Path

import pytest

from loop_engine.tools.state_io.reader import find_paused_snapshot_by_slack_thread

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
