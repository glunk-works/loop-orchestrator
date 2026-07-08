import json
from pathlib import Path

import pytest

from loop_engine.core.coder_gate import RALPH_REGRESSION_PREFIX, CoderGate, RalphCoderGate
from loop_engine.core.gates import GateDecision
from loop_engine.core.state import State
from loop_engine.tools.agent_state import ScratchpadState, write_scratchpad

SPRINT_PLANS = json.dumps(
    [
        {"path": "/sprints/01_foo/sprint_plan.md", "content": "S1."},
        {"path": "/sprints/02_bar/sprint_plan.md", "content": "S2."},
    ]
)


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _state(reports: dict[str, str]) -> State:
    return State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts={
            "sprint_plans": SPRINT_PLANS,
            "implementation_reports": json.dumps(reports),
        },
    )


def test_coder_gate_accepts_on_green_tests() -> None:
    Path("src").mkdir()
    Path("src/test_green.py").write_text("def test_ok():\n    assert True\n")

    result = CoderGate()(_state({"/sprints/01_foo/sprint_plan.md": "done"}), "CoderIacPersona")

    assert result.decision is GateDecision.ACCEPT


def test_coder_gate_revises_on_red_tests_with_output_and_sprint_prefix() -> None:
    Path("src").mkdir()
    Path("src/test_red.py").write_text("def test_broken():\n    assert 1 == 2\n")
    reports = {
        "/sprints/01_foo/sprint_plan.md": "done",
        "/sprints/02_bar/sprint_plan.md": "done",
    }

    result = CoderGate()(_state(reports), "CoderIacPersona")

    assert result.decision is GateDecision.REVISE
    (finding,) = result.findings
    # Blamed on the most recently executed sprint (last in plan order with a
    # report), so re-entry targets it.
    assert finding.startswith("/sprints/02_bar/sprint_plan.md:")
    assert "test_broken" in finding


def test_coder_gate_revises_when_no_tests_collected() -> None:
    Path("src").mkdir()
    Path("src/foo.py").write_text("def foo():\n    return 42\n")

    result = CoderGate()(_state({"/sprints/01_foo/sprint_plan.md": "done"}), "CoderIacPersona")

    assert result.decision is GateDecision.REVISE
    assert "Global Definition of Done requires tests" in result.findings[0]


def test_coder_gate_revises_when_no_src_tree_was_produced() -> None:
    result = CoderGate()(_state({"/sprints/01_foo/sprint_plan.md": "done"}), "CoderIacPersona")

    assert result.decision is GateDecision.REVISE
    assert "requires tests" in result.findings[0]


def test_coder_gate_revises_on_recorded_edit_failures_before_running_tests() -> None:
    reports = {
        "/sprints/01_foo/sprint_plan.md": (
            "done\n\n## Edit Application Failures\n\n- src/foo.py: SEARCH text not found"
        )
    }

    result = CoderGate()(_state(reports), "CoderIacPersona")

    assert result.decision is GateDecision.REVISE
    assert result.findings[0].startswith("/sprints/01_foo/sprint_plan.md:")
    assert "re-emit the corrected blocks" in result.findings[0]


def test_coder_gate_defers_to_content_gate_for_shape_problems() -> None:
    state = State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts={"sprint_plans": SPRINT_PLANS, "implementation_reports": "not json"},
    )

    result = CoderGate()(state, "CoderIacPersona")

    assert result.decision is GateDecision.REVISE
    assert "not valid JSON" in result.findings[0]


def test_coder_gate_refuses_in_process_pytest_under_container_isolation(monkeypatch) -> None:
    """The gate runs pytest in-process; under container/sandbox isolation that
    would execute untrusted model code in the orchestrator, so it must raise
    rather than run pytest. (Sandboxed gate verification is deferred host-side.)"""
    from loop_engine.core import coder_gate
    from loop_engine.tools.isolation import IsolationUnavailableError

    Path("src").mkdir()
    Path("src/test_green.py").write_text("def test_ok():\n    assert True\n")

    def _must_not_run(*args, **kwargs):
        raise AssertionError("run_pytest must not be called under container isolation")

    monkeypatch.setattr(coder_gate.run_tests_tool, "run_pytest", _must_not_run)
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "container")

    with pytest.raises(IsolationUnavailableError, match="deferred"):
        CoderGate()(_state({"/sprints/01_foo/sprint_plan.md": "done"}), "CoderIacPersona")


# --- RalphCoderGate: coverage-aware (green necessary, not sufficient) ---


def _ralph_state(task_ids: list[str], reports: dict[str, str], completed: list[str]) -> State:
    write_scratchpad(ScratchpadState(completed_tasks=completed))
    manifest = [{"id": tid, "sprint_path": "/sprints/01_foo/sprint_plan.md"} for tid in task_ids]
    return State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts={
            "sprint_plans": SPRINT_PLANS,
            "task_manifest": json.dumps(manifest),
            "implementation_reports": json.dumps(reports),
        },
    )


def test_ralph_gate_accepts_when_all_tasks_done_and_green() -> None:
    Path("src").mkdir()
    Path("src/test_green.py").write_text("def test_ok():\n    assert True\n")
    state = _ralph_state(
        ["s::t01", "s::t02"], {"/sprints/01_foo/sprint_plan.md": "done"}, ["s::t01", "s::t02"]
    )

    result = RalphCoderGate()(state, "RalphCoderPersona")
    assert result.decision is GateDecision.ACCEPT


def test_ralph_gate_revises_when_a_task_is_unchecked_even_if_green() -> None:
    # The green-but-incomplete trap: pytest is green but a manifest task is not
    # yet done, so the gate must REVISE (not ACCEPT) and not stop the loop early.
    Path("src").mkdir()
    Path("src/test_green.py").write_text("def test_ok():\n    assert True\n")
    state = _ralph_state(
        ["s::t01", "s::t02"], {"/sprints/01_foo/sprint_plan.md": "done"}, ["s::t01"]
    )

    result = RalphCoderGate()(state, "RalphCoderPersona")
    assert result.decision is GateDecision.REVISE
    assert "s::t02" in result.findings[0]


def test_ralph_gate_revises_on_red_tests_when_all_checked() -> None:
    # All tasks checked but the suite is red: a cross-task regression. The gate
    # emits the regression-prefixed finding (which routes the persona to a repair
    # increment), not the incomplete-coverage status line.
    Path("src").mkdir()
    Path("src/test_red.py").write_text("def test_bad():\n    assert 1 == 2\n")
    state = _ralph_state(["s::t01"], {"/sprints/01_foo/sprint_plan.md": "done"}, ["s::t01"])

    result = RalphCoderGate()(state, "RalphCoderPersona")
    assert result.decision is GateDecision.REVISE
    assert result.findings[0].startswith(RALPH_REGRESSION_PREFIX)
    assert "test_bad" in result.findings[0]


def test_ralph_gate_incomplete_coverage_is_not_a_regression() -> None:
    # An unchecked task must NOT carry the regression prefix — it is ordinary
    # incomplete coverage, which the persona escalates rather than repairs.
    Path("src").mkdir()
    Path("src/test_green.py").write_text("def test_ok():\n    assert True\n")
    state = _ralph_state(
        ["s::t01", "s::t02"], {"/sprints/01_foo/sprint_plan.md": "done"}, ["s::t01"]
    )

    result = RalphCoderGate()(state, "RalphCoderPersona")
    assert result.decision is GateDecision.REVISE
    assert not result.findings[0].startswith(RALPH_REGRESSION_PREFIX)
    assert "s::t02" in result.findings[0]


def test_ralph_gate_revises_on_missing_manifest() -> None:
    state = State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts={
            "sprint_plans": SPRINT_PLANS,
            "implementation_reports": json.dumps({"/sprints/01_foo/sprint_plan.md": "done"}),
        },
    )
    result = RalphCoderGate()(state, "RalphCoderPersona")
    assert result.decision is GateDecision.REVISE
    assert "task_manifest" in result.findings[0]


def test_ralph_gate_refuses_in_process_pytest_under_container(monkeypatch) -> None:
    from loop_engine.core import coder_gate
    from loop_engine.tools.isolation import IsolationUnavailableError

    def _must_not_run(*args, **kwargs):
        raise AssertionError("run_pytest must not be called under container isolation")

    monkeypatch.setattr(coder_gate.run_tests_tool, "run_pytest", _must_not_run)
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "container")
    state = _ralph_state(["s::t01"], {"/sprints/01_foo/sprint_plan.md": "done"}, ["s::t01"])

    with pytest.raises(IsolationUnavailableError, match="deferred"):
        RalphCoderGate()(state, "RalphCoderPersona")
