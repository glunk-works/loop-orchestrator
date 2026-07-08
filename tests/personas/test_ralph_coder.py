import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import State
from loop_engine.personas.agile_sprint_breakdown.manifest import build_task_manifest
from loop_engine.personas.coder_iac.ralph import RalphCoderPersona, select_next_task
from loop_engine.tools.agent_state import (
    ScratchpadState,
    read_memory,
    read_scratchpad,
    write_scratchpad,
)

_SPRINT_A = {
    "path": "/sprints/01_foundation/sprint_plan.md",
    "content": (
        "**Dependencies:** None\n\n**Tasks:**\n\n"
        "- **Task 1: Set up CI**\n"
        "  - **Description:** Add CI.\n"
        "  - **Target Files:** `.github/workflows/ci.yml`\n"
        "  - **Acceptance Criteria:** CI runs.\n\n"
        "- **Task 2: Add linting**\n"
        "  - **Description:** Wire ruff.\n"
        "  - **Target Files:** `pyproject.toml`\n"
        "  - **Acceptance Criteria:** ruff passes.\n"
    ),
}
_SPRINT_B = {
    "path": "/sprints/02_feature/sprint_plan.md",
    "content": (
        "**Dependencies:** Sprint 01.\n\n**Tasks:**\n\n"
        "- **Task 1: Handler**\n"
        "  - **Description:** Write handler.\n"
        "  - **Target Files:** `src/handler.py`\n"
        "  - **Acceptance Criteria:** returns 200.\n"
    ),
}


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state(completed: list[str] | None = None, reports: dict[str, str] | None = None) -> State:
    manifest = build_task_manifest([_SPRINT_A, _SPRINT_B])
    artifacts = {
        "architecture_definition": "# Arch",
        "sprint_plans": json.dumps([_SPRINT_A, _SPRINT_B]),
        "task_manifest": json.dumps([t.model_dump() for t in manifest]),
    }
    if reports is not None:
        artifacts["implementation_reports"] = json.dumps(reports)
    if completed:
        write_scratchpad(ScratchpadState(completed_tasks=completed))
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts=artifacts)


def _llm(text: str) -> MagicMock:
    client = MagicMock()
    client.run_tool_loop.return_value = SimpleNamespace(text=text)
    return client


def test_select_next_task_respects_dependencies() -> None:
    manifest = build_task_manifest([_SPRINT_A, _SPRINT_B])
    # Nothing done: the first task with no deps is picked.
    assert select_next_task(manifest, []).id == "01_foundation::t01"
    # Sprint B's task is not eligible until all of Sprint A is done.
    assert select_next_task(manifest, ["01_foundation::t01"]).id == "01_foundation::t02"
    assert (
        select_next_task(manifest, ["01_foundation::t01", "01_foundation::t02"]).id
        == "02_feature::t01"
    )


def test_run_completes_exactly_one_task_and_checks_it_off() -> None:
    client = _llm("Implemented CI.")
    result = RalphCoderPersona().run(_state(), client)

    assert client.run_tool_loop.call_count == 1
    assert read_scratchpad().completed_tasks == ["01_foundation::t01"]
    reports = json.loads(result.artifacts["implementation_reports"])
    # Exactly the first sprint has a report; nothing else touched.
    assert set(reports) == {"/sprints/01_foundation/sprint_plan.md"}


def test_run_appends_one_memory_entry_per_increment() -> None:
    RalphCoderPersona().run(_state(), _llm("done"))
    assert len(read_memory()) == 1


def test_run_is_a_noop_when_all_tasks_done() -> None:
    all_ids = [t.id for t in build_task_manifest([_SPRINT_A, _SPRINT_B])]
    client = _llm("should not be called")
    result = RalphCoderPersona().run(_state(completed=all_ids), client)

    assert client.run_tool_loop.call_count == 0
    assert "implementation_reports" not in result.artifacts


def test_open_questions_escalate_and_task_is_not_checked_off() -> None:
    client = _llm("Partial.\n\n## Open Questions\n\n1. OIDC or API keys?")
    result = RalphCoderPersona().run(_state(), client)

    assert [q.text for q in result.questions] == ["OIDC or API keys?"]
    assert result.questions[0].origin_stage == "RalphCoderPersona"
    assert result.questions[0].origin_detail == "01_foundation::t01"
    # A blocked task is NOT marked done.
    assert read_scratchpad().completed_tasks == []
