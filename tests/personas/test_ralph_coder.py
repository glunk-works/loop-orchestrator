import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.coder_gate import RALPH_REGRESSION_PREFIX
from loop_engine.core.state import State
from loop_engine.personas.agile_sprint_breakdown.manifest import build_task_manifest
from loop_engine.personas.coder_iac.ralph import (
    RalphCoderPersona,
    _build_repair_prompt,
    _build_task_prompt,
    select_next_task,
)
from loop_engine.tools.agent_state import (
    ScratchpadState,
    read_memory,
    read_scratchpad,
    write_scratchpad,
)
from loop_engine.tools.llm.client import ToolLoopExceededError


def _prompt_of(client: MagicMock) -> str:
    return client.run_tool_loop.call_args.args[0][0]["content"]


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


def test_tool_loop_exhaustion_degrades_to_no_output_and_task_not_checked_off() -> None:
    # A stuck inner tool loop must not crash the run: the increment is treated
    # as no output, the task stays unchecked, and the loop can re-select it.
    client = MagicMock()
    client.run_tool_loop.side_effect = ToolLoopExceededError("did not converge")

    result = RalphCoderPersona().run(_state(), client)

    assert client.run_tool_loop.call_count == 1
    assert read_scratchpad().completed_tasks == []
    assert "implementation_reports" not in result.artifacts
    assert result.questions == []


def test_open_questions_escalate_and_task_is_not_checked_off() -> None:
    client = _llm("Partial.\n\n## Open Questions\n\n1. OIDC or API keys?")
    result = RalphCoderPersona().run(_state(), client)

    assert [q.text for q in result.questions] == ["OIDC or API keys?"]
    assert result.questions[0].origin_stage == "RalphCoderPersona"
    assert result.questions[0].origin_detail == "01_foundation::t01"
    # A blocked task is NOT marked done.
    assert read_scratchpad().completed_tasks == []


# --- (d) the model sees carried resolutions + the latest status, not findings[-1] ---


def test_prompt_keeps_all_resolutions_and_only_the_latest_status() -> None:
    client = _llm("done")
    findings = [
        "Escalated question: Which auth?\n  Resolution: Use OIDC.",
        "Ralph status — next task: 01_foundation::t01; STALE middle status.",
        "Ralph status — next task: 01_foundation::t01; FRESH latest status.",
    ]
    RalphCoderPersona().run(_state(), client, findings=findings)

    prompt = _prompt_of(client)
    assert "Use OIDC." in prompt  # the resolution answer survives
    assert "FRESH latest status." in prompt  # the newest status is included
    assert "STALE middle status." not in prompt  # stale intermediate status dropped


# --- (c) re-running a task upserts its report section (no duplicates) ---


def test_rerunning_a_task_replaces_its_report_section() -> None:
    # First increment escalates (open questions) so the task is not checked off
    # and gets re-selected on the next invocation.
    first = RalphCoderPersona().run(
        _state(), _llm("Attempt 1.\n\n## Open Questions\n\n1. Which datastore?")
    )
    second = RalphCoderPersona().run(first, _llm("Attempt 2 — final implementation."))

    reports = json.loads(second.artifacts["implementation_reports"])
    body = reports["/sprints/01_foundation/sprint_plan.md"]
    assert body.count("### Task 01_foundation::t01:") == 1  # not duplicated
    assert "Attempt 2 — final implementation." in body
    assert "Attempt 1." not in body  # the stale section was replaced


def test_rerun_replaces_a_section_whose_body_contains_h3_subheaders() -> None:
    # A model report body routinely contains its own `### ` subheadings. The
    # upsert terminator must key off *this module's* section headers (`### Task `
    # / `### Regression fix`), not any `### ` — otherwise the re-run stops
    # mid-body and orphans the tail, leaking stale content across iterations.
    first = RalphCoderPersona().run(
        _state(),
        _llm(
            "Attempt 1.\n\n### Internal notes\n\nstale internals here.\n\n"
            "## Open Questions\n\n1. Which datastore?"
        ),
    )
    second = RalphCoderPersona().run(first, _llm("Attempt 2 — final implementation."))

    body = json.loads(second.artifacts["implementation_reports"])[
        "/sprints/01_foundation/sprint_plan.md"
    ]
    assert body.count("### Task 01_foundation::t01:") == 1
    assert "Attempt 2 — final implementation." in body
    # The whole prior section — including content *after* its `### ` subheader —
    # is gone, not orphaned. (Pre-fix, "### Internal notes" truncated the match.)
    assert "stale internals here." not in body
    assert "### Internal notes" not in body


# --- (a) regression repair increment: self-heal a red suite when all tasks done ---


def _all_done_state(reports: dict[str, str] | None = None) -> State:
    all_ids = [t.id for t in build_task_manifest([_SPRINT_A, _SPRINT_B])]
    return _state(completed=all_ids, reports=reports if reports is not None else {})


def test_regression_finding_triggers_a_repair_increment() -> None:
    client = _llm("Diagnosed and fixed the regression.")
    finding = f"{RALPH_REGRESSION_PREFIX} suite red: src/x.py::test_x failed"

    result = RalphCoderPersona().run(_all_done_state(), client, findings=[finding])

    assert client.run_tool_loop.call_count == 1
    # A repair marks no task done or undone.
    all_ids = [t.id for t in build_task_manifest([_SPRINT_A, _SPRINT_B])]
    assert read_scratchpad().completed_tasks == all_ids
    # The repair is attributed to the last sprint in plan order as one section.
    body = json.loads(result.artifacts["implementation_reports"])[
        "/sprints/02_feature/sprint_plan.md"
    ]
    assert "### Regression fix" in body
    assert "Diagnosed and fixed the regression." in body
    assert len(read_memory()) == 1  # exactly one lesson appended
    # The repair prompt is scoped to fixing, not new features.
    assert "regressed" in _prompt_of(client)


def test_all_tasks_done_without_a_regression_finding_is_a_noop() -> None:
    client = _llm("must not be called")
    status = (
        "Ralph status — next task: none; tasks still to complete: none. Implement the next unit."
    )

    result = RalphCoderPersona().run(_all_done_state(), client, findings=[status])

    assert client.run_tool_loop.call_count == 0
    # The incomplete-coverage-shaped status line is NOT a regression signal.
    assert "implementation_reports" in result.artifacts  # unchanged from input


def test_repeated_repairs_keep_a_single_regression_section() -> None:
    finding = [f"{RALPH_REGRESSION_PREFIX} still red"]
    first = RalphCoderPersona().run(_all_done_state(), _llm("fix one"), findings=finding)
    second = RalphCoderPersona().run(first, _llm("fix two"), findings=finding)

    body = json.loads(second.artifacts["implementation_reports"])[
        "/sprints/02_feature/sprint_plan.md"
    ]
    assert body.count("### Regression fix") == 1
    assert "fix two" in body
    assert "fix one" not in body


def test_repair_that_escalates_does_not_record_a_fix_it_did_not_make() -> None:
    # A genuinely ambiguous regression makes the repair increment raise a
    # question instead of fixing the suite. The ledger must reflect the
    # escalation, not claim a repair that never happened.
    client = _llm("Investigating.\n\n## Open Questions\n\n1. Is the flaky test load-bearing?")
    finding = [f"{RALPH_REGRESSION_PREFIX} still red"]

    result = RalphCoderPersona().run(_all_done_state(), client, findings=finding)

    # The question escalates (surfaced on state; the content gate routes it).
    assert [q.text for q in result.questions] == ["Is the flaky test load-bearing?"]
    assert result.questions[0].origin_stage == "RalphCoderPersona"
    # No task is marked/unmarked by a repair.
    all_ids = [t.id for t in build_task_manifest([_SPRINT_A, _SPRINT_B])]
    assert read_scratchpad().completed_tasks == all_ids
    # The lesson records the escalation, not a false "repaired" claim.
    lesson = read_memory()[-1].body
    assert "escalated" in lesson.lower()
    assert "Repaired a cross-task test regression" not in lesson


# --- (b) sprint 30 (F-RALPH-OVERSPEC-TEST): self-fix-before-escalate guardrail ---


def test_task_prompt_carries_self_fix_before_escalate_guardrail() -> None:
    task = build_task_manifest([_SPRINT_A, _SPRINT_B])[0]
    prompt = _build_task_prompt(task, _SPRINT_A["content"], None, [])

    assert "fix or remove that test" in prompt
    assert "never" in prompt and "test of your own authorship" in prompt
    # The narrowed Open-Questions carve-out is preserved, not deleted.
    assert "Open Questions" in prompt


def test_repair_prompt_carries_self_fix_before_escalate_guardrail() -> None:
    prompt = _build_repair_prompt(None, [])

    assert "fix or remove that test" in prompt
    assert "test of your own authorship" in prompt
    assert "Open Questions" in prompt
    # The existing repair-scope directive is preserved.
    assert "Do NOT add new features, new tasks, or new scope" in prompt
