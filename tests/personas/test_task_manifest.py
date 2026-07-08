import json

import pytest
from pydantic import ValidationError

from loop_engine.core.gates import GateDecision
from loop_engine.core.state import State
from loop_engine.personas.agile_sprint_breakdown.manifest import (
    ManifestArtifactGate,
    TaskEntry,
    build_task_manifest,
    validate_manifest,
)


def _manifest_state(sprint_blocks: list[dict], manifest: list[dict] | None = None) -> State:
    if manifest is None:
        manifest = [task.model_dump() for task in build_task_manifest(sprint_blocks)]
    return State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts={
            "sprint_plans": json.dumps(sprint_blocks),
            "task_manifest": json.dumps(manifest),
        },
    )


_SPRINT_A = {
    "path": "/sprints/01_foundation/sprint_plan.md",
    "content": (
        "**Sprint Goal:** Lay the foundation.\n\n"
        "**Dependencies:** None\n\n"
        "**Tasks:**\n\n"
        "- **Task 1: Set up CI**\n"
        "  - **Description:** Add the CI workflow.\n"
        "  - **Target Files:** `.github/workflows/ci.yml`\n"
        "  - **Acceptance Criteria:** CI runs on push.\n\n"
        "- **Task 2: Add linting**\n"
        "  - **Description:** Wire ruff.\n"
        "  - **Target Files:** `pyproject.toml`, `ruff.toml`\n"
        "  - **Acceptance Criteria:** ruff check passes.\n"
    ),
}

_SPRINT_B = {
    "path": "/sprints/02_feature/sprint_plan.md",
    "content": (
        "**Sprint Goal:** Build the feature.\n\n"
        "**Dependencies:** Sprint 01 (CI + linting).\n\n"
        "**Tasks:**\n\n"
        "- **Task 1: Implement handler**\n"
        "  - **Description:** Write the request handler.\n"
        "  - **Target Files:** `src/handler.py`\n"
        "  - **Acceptance Criteria:** handler returns 200.\n"
    ),
}


def test_build_manifest_parses_one_entry_per_task() -> None:
    manifest = build_task_manifest([_SPRINT_A, _SPRINT_B])

    ids = [task.id for task in manifest]
    assert ids == [
        "01_foundation::t01",
        "01_foundation::t02",
        "02_feature::t01",
    ]
    ci = manifest[0]
    assert ci.title == "Set up CI"
    assert ci.description == "Add the CI workflow."
    assert ci.acceptance_criteria == "CI runs on push."
    assert ci.target_files == [".github/workflows/ci.yml"]
    assert manifest[1].target_files == ["pyproject.toml", "ruff.toml"]


def test_intra_sprint_deps_are_sequential() -> None:
    manifest = build_task_manifest([_SPRINT_A, _SPRINT_B])
    by_id = {task.id: task for task in manifest}

    assert by_id["01_foundation::t01"].deps == []
    assert by_id["01_foundation::t02"].deps == ["01_foundation::t01"]


def test_cross_sprint_dep_covers_every_task_of_the_named_sprint() -> None:
    manifest = build_task_manifest([_SPRINT_A, _SPRINT_B])
    by_id = {task.id: task for task in manifest}

    # Sprint B names Sprint 01, so its task depends on every task of Sprint A.
    assert set(by_id["02_feature::t01"].deps) == {
        "01_foundation::t01",
        "01_foundation::t02",
    }


def test_sprint_with_no_parseable_tasks_contributes_nothing() -> None:
    empty = {
        "path": "/sprints/03_prose/sprint_plan.md",
        "content": "Just some prose with no task bullets at all.",
    }
    manifest = build_task_manifest([empty])
    assert manifest == []


def test_task_entry_rejects_malformed_input() -> None:
    # Negative-input test for the new Pydantic boundary: missing required field.
    with pytest.raises(ValidationError):
        TaskEntry(sprint_path="/s/x", title="t")  # no id

    # extra="forbid": an unknown field is rejected.
    with pytest.raises(ValidationError):
        TaskEntry(id="x", sprint_path="/s/x", title="t", bogus="nope")


def test_gate_accepts_a_valid_manifest() -> None:
    state = _manifest_state([_SPRINT_A, _SPRINT_B])
    result = ManifestArtifactGate()(state, "AgileSprintBreakdownPersona")
    assert result.decision is GateDecision.ACCEPT


def test_gate_revises_when_a_sprint_yields_no_tasks() -> None:
    prose_sprint = {"path": "/sprints/03_prose/sprint_plan.md", "content": "No tasks here."}
    # The prose sprint contributes nothing, so it is uncovered by the manifest.
    state = _manifest_state([_SPRINT_A, prose_sprint])
    result = ManifestArtifactGate()(state, "AgileSprintBreakdownPersona")
    assert result.decision is GateDecision.REVISE
    assert any("03_prose" in finding for finding in result.findings)


def test_validate_flags_dangling_dependency() -> None:
    tasks = [
        {"id": "s::t01", "sprint_path": "/s", "title": "t", "deps": ["s::t99"]},
    ]
    findings = validate_manifest(json.dumps(tasks), json.dumps([{"path": "/s"}]))
    assert any("unknown task" in finding for finding in findings)


def test_validate_flags_dependency_cycle() -> None:
    tasks = [
        {"id": "s::t01", "sprint_path": "/s", "title": "a", "deps": ["s::t02"]},
        {"id": "s::t02", "sprint_path": "/s", "title": "b", "deps": ["s::t01"]},
    ]
    findings = validate_manifest(json.dumps(tasks), json.dumps([{"path": "/s"}]))
    assert any("cycle" in finding for finding in findings)


def test_validate_flags_empty_manifest() -> None:
    findings = validate_manifest("[]", json.dumps([{"path": "/s"}]))
    assert findings and "empty" in findings[0]
