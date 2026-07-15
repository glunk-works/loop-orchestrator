"""Graph-routing tests.

The engine's *behavioral* contract (propose → gate → accept/revise/escalate,
budget/tool-loop exhaustion, the resolver ladder, issue pauses, blast-radius
re-entry) lives in `tests/core/test_engine.py` — it is the `execute_stage`
primitive's contract, and the graph's stage nodes are thin wrappers over it.

What is graph-*specific* is the routing: a stage node that re-enters **itself**
along a conditional edge, repeatedly, until its gate goes green. The classic
`run_loop` did this with a plain `while`; the graph has to route the node back
to itself without tripping LangGraph's super-step recursion guard. That is the
Ralph coder's core mechanism, so it is pinned here without an LLM by a fake
incremental persona plus a coverage gate.

(Until Phase 6 this file was the classic-vs-graph parity harness. With the
classic engine deleted there is no second engine to compare against, so the
duplicated scenarios collapsed back into `test_engine.py`.)
"""

import json

import pytest

from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import GateDecision, GateResult
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import IssueRef, RunStatus
from loop_engine.personas.base import BasePersona
from tests.core.conftest import absolutize_mutmut_source_paths
from tests.core.test_engine import _initial_state, _stub_llm_client


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    absolutize_mutmut_source_paths(monkeypatch)
    monkeypatch.chdir(tmp_path)


class _IncrementalPersona(BasePersona):
    """Adds exactly one item per pass — converges only by re-entering."""

    produces = ("items",)

    def run(self, state, llm_client, findings=None):
        items = json.loads(state.artifacts.get("items", "[]"))
        items.append(f"t{len(items) + 1}")
        return state.model_copy(
            update={"artifacts": {**state.artifacts, "items": json.dumps(items)}}
        )


def _coverage_gate(target: int):
    def gate(state, stage_name):
        done = len(json.loads(state.artifacts.get("items", "[]")))
        if done < target:
            # A CHANGING finding each iteration ⇒ progress ⇒ keep looping
            # (identical findings would trip the engine's no-progress escalation).
            return GateResult(GateDecision.REVISE, findings=[f"{done}/{target}; next t{done + 1}"])
        return GateResult(GateDecision.ACCEPT)

    return gate


def _ralph_like_loop(target: int = 3, cap: int = 10) -> Loop:
    return Loop(
        stages=[
            Stage(persona=_IncrementalPersona(), gate=_coverage_gate(target), max_revisions=cap)
        ]
    )


def test_stage_node_self_reentry_drives_incremental_persona_to_coverage() -> None:
    final = run_graph_loop(_ralph_like_loop(), _initial_state("rg"), _stub_llm_client())

    # Three self-re-entries of the same node, each adding one item, until green.
    assert final.artifacts["items"] == '["t1", "t2", "t3"]'
    assert final.status is RunStatus.COMPLETED


def test_stage_node_self_reentry_survives_a_long_self_loop() -> None:
    # Guards LangGraph's super-step recursion limit: a legitimately long self
    # loop (well past the default guard) must still terminate COMPLETED rather
    # than raise. The classic `while` engine could not have tripped this.
    final = run_graph_loop(
        _ralph_like_loop(target=20, cap=30), _initial_state("rg-long"), _stub_llm_client()
    )

    assert len(json.loads(final.artifacts["items"])) == 20
    assert final.status is RunStatus.COMPLETED


def test_run_graph_loop_resets_stale_status_and_pending_issue_from_input_state() -> None:
    # Real gap (Sprint 38 T3, BL-23): every current test starts run_graph_loop
    # from a fresh State whose defaults (RUNNING, pending_issue=None) already
    # match what `run_graph_loop` forces, so the reset line is a no-op for
    # every existing test. Pass in a State shaped like a real resume (stale
    # AWAITING_ISSUE status + a leftover pending_issue) and assert the run
    # actually clears both.
    #
    # A `status`-key typo (e.g. `"XXstatusXX"`) in the reset's `update={...}`
    # dict is NOT caught by asserting only the run's FINAL status: the
    # completion node unconditionally stamps `status=COMPLETED` at the end
    # regardless of what happened at the start, masking the bug. Observe the
    # status a persona actually SEES mid-run instead.
    from loop_engine.core.gates import ArtifactGate

    seen_status: list[RunStatus] = []

    class RecordingPersona(BasePersona):
        produces = ("doc",)

        def run(self, state, llm_client, findings=None):
            seen_status.append(state.status)
            return state.model_copy(update={"artifacts": {**state.artifacts, "doc": "done"}})

    stale = _initial_state("rg-stale").model_copy(
        update={
            "status": RunStatus.AWAITING_ISSUE,
            "pending_issue": IssueRef(number=7, url="https://github.com/example/repo/issues/7"),
        }
    )
    loop = Loop(stages=[Stage(persona=RecordingPersona(), gate=ArtifactGate("doc"))])

    final = run_graph_loop(loop, stale, _stub_llm_client())

    assert seen_status == [RunStatus.RUNNING]
    assert final.status is RunStatus.COMPLETED
    assert final.pending_issue is None
