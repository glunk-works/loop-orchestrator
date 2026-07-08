import json
from pathlib import Path

import pytest

from loop_engine.core.coder_gate import CoderGate
from loop_engine.core.gates import GateDecision
from loop_engine.core.state import State

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
