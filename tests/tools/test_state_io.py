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


def test_write_artifact_writes_exact_utf8_bytes_with_no_newline_translation() -> None:
    # F1: Path.write_text defaults to newline=None, which translates "\n" to
    # os.linesep on write. On Windows that means the on-disk bytes no longer
    # equal body.encode("utf-8"), which artifact_store.py's idempotence check
    # assumes. Pinning newline="\n" makes the write byte-exact on every platform.
    #
    # F27: unlike the LC_CTYPE-forcing tests in test_artifact_store.py /
    # scaffold/test_writer.py, this assertion can't be made to actually fail
    # on the newline= regression it names: os.linesep-driven translation is
    # resolved at the platform/interpreter level, not re-read from Python's
    # `os` module, so monkeypatching os.linesep here doesn't reproduce it, and
    # CI runs ubuntu-latest only (os.linesep == "\n" already, a no-op
    # translation). This is a round-trip sanity check, not a regression guard;
    # the real, platform-independent backstop for the newline= pin is the AST
    # structural guard in test_encoding_boundary.py
    # (test_write_owning_modules_pin_newline_on_write_text).
    body = "line one\nline two\n"
    path = write_artifact(body, "docs/example.md")

    assert path.read_bytes() == body.encode("utf-8")


def test_write_state_snapshot_writes_exact_utf8_bytes_with_no_newline_translation() -> None:
    # F27: same caveat as the sibling test above -- sanity check, not a
    # regression guard; test_encoding_boundary.py's AST guard is the backstop.
    path = write_state_snapshot(VALID_STATE, run_id="run-001", stage_index=2, stage_name="pm")

    assert path.read_bytes() == VALID_STATE.model_dump_json().encode("utf-8")


def test_write_artifact_rejects_absolute_path() -> None:
    with pytest.raises(ValueError):
        write_artifact("hello", "/etc/passwd")

    assert not Path("etc").exists()


def test_write_artifact_rejects_parent_traversal() -> None:
    with pytest.raises(ValueError):
        write_artifact("hello", "../outside.md")

    assert not Path("../outside.md").resolve().exists()
