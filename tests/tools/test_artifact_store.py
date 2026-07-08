from pathlib import Path

import pytest

from loop_engine.core.state import State, artifact_digest, default_artifact_path
from loop_engine.tools.artifact_store import get_artifact, has_artifact, mirror_to_disk


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state(**artifacts: str) -> State:
    return State(schema_version=3, run_id="run-001", stage_history=[], artifacts=artifacts)


def test_mirror_writes_bodies_to_disk_and_points_refs() -> None:
    state = _state(project_spec='{"scope": "x"}')
    mirrored = mirror_to_disk(state)

    ref = mirrored.artifact_refs["project_spec"]
    assert ref.path == default_artifact_path("run-001", "project_spec")
    assert ref.digest == artifact_digest('{"scope": "x"}')
    assert Path(ref.path).read_text() == '{"scope": "x"}'


def test_mirror_is_idempotent_for_unchanged_bodies() -> None:
    state = mirror_to_disk(_state(spec="body"))
    # Re-mirroring an unchanged state returns the same object (no I/O, no churn).
    assert mirror_to_disk(state) is state


def test_mirror_repoints_on_body_change() -> None:
    state = mirror_to_disk(_state(spec="v1"))
    changed = state.model_copy(update={"artifacts": {"spec": "v2"}})
    remirrored = mirror_to_disk(changed)

    assert remirrored.artifact_refs["spec"].digest == artifact_digest("v2")
    assert Path(remirrored.artifact_refs["spec"].path).read_text() == "v2"


def test_get_artifact_prefers_disk_then_inline_then_default() -> None:
    mirrored = mirror_to_disk(_state(spec="on-disk"))
    assert get_artifact(mirrored, "spec") == "on-disk"

    # Inline fallback when no ref exists yet (dual-field phase).
    inline_only = _state(spec="inline")
    assert get_artifact(inline_only, "spec") == "inline"

    assert get_artifact(inline_only, "missing", default="fallback") == "fallback"


def test_has_artifact_reflects_nonempty_body() -> None:
    assert has_artifact(_state(spec="x"), "spec") is True
    assert has_artifact(_state(spec="  "), "spec") is False
    assert has_artifact(_state(), "spec") is False
