from pathlib import Path

import pytest

from loop_engine.core.state import State, default_artifact_path
from loop_engine.tools import artifact_store
from loop_engine.tools.artifact_store import has_artifact, publish_artifacts


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state(**artifacts: str) -> State:
    return State(schema_version=3, run_id="run-001", stage_history=[], artifacts=artifacts)


def test_publish_writes_bodies_to_disk() -> None:
    state = _state(project_spec='{"scope": "x"}')
    result = publish_artifacts(state)

    assert result is None
    path = Path(default_artifact_path("run-001", "project_spec"))
    assert path.read_text() == '{"scope": "x"}'


def test_publish_is_idempotent_for_unchanged_bodies(monkeypatch) -> None:
    state = _state(spec="body")
    publish_artifacts(state)

    calls = []
    monkeypatch.setattr(artifact_store, "write_artifact", lambda content, path: calls.append(path))
    publish_artifacts(state)
    assert calls == []


def test_publish_overwrites_on_body_change() -> None:
    state = _state(spec="v1")
    publish_artifacts(state)

    changed = state.model_copy(update={"artifacts": {"spec": "v2"}})
    publish_artifacts(changed)

    path = Path(default_artifact_path("run-001", "spec"))
    assert path.read_text() == "v2"


def test_publish_lands_bodies_under_docs_artifacts_run_id() -> None:
    # The property flows/maintenance depends on to ship design docs in the PR.
    state = _state(architecture="design doc body", sprint_plan="plan body")
    publish_artifacts(state)

    run_dir = Path("docs/artifacts/run-001")
    assert (run_dir / "architecture").read_text() == "design doc body"
    assert (run_dir / "sprint_plan").read_text() == "plan body"


def test_has_artifact_reflects_nonempty_body() -> None:
    assert has_artifact(_state(spec="x"), "spec") is True
    assert has_artifact(_state(spec="  "), "spec") is False
    assert has_artifact(_state(), "spec") is False
