from pathlib import Path

import pytest

from loop_engine.core.state import State
from loop_engine.tools.state_io.writer import write_artifact, write_state_snapshot

VALID_STATE = State(
    schema_version=1,
    run_id="run-001",
    stage_history=[],
    artifacts={},
)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_write_state_snapshot_round_trips_through_state_validate_json() -> None:
    path = write_state_snapshot(VALID_STATE, run_id="run-001", stage_index=2, stage_name="pm")

    assert path == Path("state") / "run-001" / "02_pm.json"
    rehydrated = State.model_validate_json(path.read_text())
    assert rehydrated == VALID_STATE


def test_write_state_snapshot_rejects_path_traversal_run_id() -> None:
    with pytest.raises(ValueError, match="run_id"):
        write_state_snapshot(VALID_STATE, run_id="../../etc", stage_index=0, stage_name="pm")

    assert not Path("state").exists()


def test_write_state_snapshot_rejects_path_traversal_stage_name() -> None:
    with pytest.raises(ValueError, match="stage_name"):
        write_state_snapshot(VALID_STATE, run_id="run-001", stage_index=0, stage_name="../../etc")

    assert not (Path("state") / "run-001").exists()


def test_write_artifact_succeeds_under_docs() -> None:
    path = write_artifact("hello", "docs/example.md")

    assert path == Path("docs") / "example.md"
    assert path.read_text() == "hello"


def test_write_artifact_rejects_absolute_path() -> None:
    with pytest.raises(ValueError):
        write_artifact("hello", "/etc/passwd")

    assert not Path("etc").exists()


def test_write_artifact_rejects_parent_traversal() -> None:
    with pytest.raises(ValueError):
        write_artifact("hello", "../outside.md")

    assert not Path("../outside.md").resolve().exists()
