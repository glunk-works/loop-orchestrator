import json
from pathlib import Path

import pytest

from loop_engine.core.coder_gate import RALPH_REGRESSION_PREFIX, RalphCoderGate
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


class _FakeGateProvider:
    """Stands in for the sandboxed coder-tools provider: `run_tests` returns a
    canned formatted result string instead of spawning anything."""

    def __init__(self, result_text: str) -> None:
        self._result_text = result_text

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, name, arguments):
        assert name == "run_tests"
        return self._result_text


@pytest.mark.parametrize(
    ("result_text", "expected_decision"),
    [
        ("pytest exit code: 0\n\n1 passed", GateDecision.ACCEPT),
        ("pytest exit code: 5\n\nno tests ran", GateDecision.REVISE),
        ("pytest exit code: 1\n\nFAILED src/test_red.py", GateDecision.REVISE),
    ],
)
# --- RalphCoderGate: coverage-aware (green necessary, not sufficient) ---
#
# Phase 6 deleted CoderGate (the classic per-sprint evidence gate). The paths the
# two gates shared — the pre-pytest edit-failure short-circuit, no-tests-collected,
# and deferral to the content gate on a malformed artifact — were only covered
# through CoderGate's tests, so they are ported onto RalphCoderGate below rather
# than lost with it.


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


@pytest.mark.parametrize(
    ("result_text", "expected_decision"),
    [
        ("pytest exit code: 0\n\n1 passed", GateDecision.ACCEPT),
        ("pytest exit code: 5\n\nno tests ran", GateDecision.REVISE),
        ("pytest exit code: 1\n\nFAILED src/test_bad.py", GateDecision.REVISE),
    ],
)
def test_ralph_gate_verifies_through_sandboxed_provider_under_container(
    monkeypatch, result_text, expected_decision
) -> None:
    """Same sandboxed-verification behavior as CoderGate — the Ralph gate no
    longer refuses under container/sandbox isolation."""
    from loop_engine.tools.mcp import provider as mcp_provider

    Path("src").mkdir()
    Path("src/test_placeholder.py").write_text("def test_ok():\n    assert True\n")
    monkeypatch.setattr(mcp_provider, "sandbox_runtime_mode", lambda: "container")
    monkeypatch.setattr(
        mcp_provider, "build_coder_tool_provider", lambda cwd=None: _FakeGateProvider(result_text)
    )
    state = _ralph_state(["s::t01"], {"/sprints/01_foo/sprint_plan.md": "done"}, ["s::t01"])

    result = RalphCoderGate()(state, "RalphCoderPersona")

    assert result.decision is expected_decision


def test_ralph_gate_revises_on_recorded_edit_failures_before_running_tests() -> None:
    # Edit blocks that failed to apply are a known defect with exact attribution:
    # short-circuit to REVISE rather than paying for a test run first. Checked
    # before the coverage check, so it fires even with tasks outstanding.
    reports = {
        "/sprints/01_foo/sprint_plan.md": (
            "done\n\n## Edit Application Failures\n\n- src/foo.py: SEARCH text not found"
        )
    }
    state = _ralph_state(["s::t01"], reports, [])

    result = RalphCoderGate()(state, "RalphCoderPersona")

    assert result.decision is GateDecision.REVISE
    assert result.findings[0].startswith("/sprints/01_foo/sprint_plan.md:")
    assert "re-emit the corrected blocks" in result.findings[0]


def test_ralph_gate_revises_when_all_tasks_done_but_no_tests_collected() -> None:
    # Every task checked off, source produced, but pytest collected nothing: the
    # Definition of Done requires tests, so green-by-vacuum must not ACCEPT.
    Path("src").mkdir()
    Path("src/foo.py").write_text("def foo():\n    return 42\n")
    state = _ralph_state(["s::t01"], {"/sprints/01_foo/sprint_plan.md": "done"}, ["s::t01"])

    result = RalphCoderGate()(state, "RalphCoderPersona")

    assert result.decision is GateDecision.REVISE
    assert "Global Definition of Done requires tests" in result.findings[0]


def test_ralph_gate_revises_when_no_src_tree_was_produced() -> None:
    state = _ralph_state(["s::t01"], {"/sprints/01_foo/sprint_plan.md": "done"}, ["s::t01"])

    result = RalphCoderGate()(state, "RalphCoderPersona")

    assert result.decision is GateDecision.REVISE
    assert "requires tests" in result.findings[0]


def test_ralph_gate_defers_to_the_content_gate_for_shape_problems() -> None:
    # A malformed implementation_reports artifact is a shape problem: the composed
    # content gate owns that finding, and the Ralph gate must not run pytest at all.
    write_scratchpad(ScratchpadState(completed_tasks=[]))
    state = State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts={
            "sprint_plans": SPRINT_PLANS,
            "task_manifest": json.dumps([{"id": "s::t01", "sprint_path": "/s/p.md"}]),
            "implementation_reports": "not json",
        },
    )

    result = RalphCoderGate()(state, "RalphCoderPersona")

    assert result.decision is GateDecision.REVISE
    assert "not valid JSON" in result.findings[0]
