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
import sys

import pytest

from loop_engine.core.engine import InvalidStateTransitionError, Loop, Stage
from loop_engine.core.gates import ArtifactGate, GateDecision, GateResult
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.notify import EventKind, LifecycleEvent
from loop_engine.core.state import IssueRef, RunStatus, StageRecord
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


class _FakeNotifier:
    """Captures emitted events; can also simulate a buggy notifier that
    raises on every call, for the fail-open regression."""

    def __init__(self, raise_on_emit: bool = False) -> None:
        self.events: list[LifecycleEvent] = []
        self.raise_on_emit = raise_on_emit

    def emit(self, event: LifecycleEvent) -> None:
        if self.raise_on_emit:
            raise RuntimeError("notifier boom")
        self.events.append(event)


def test_run_graph_loop_emits_started_and_terminal_event_for_a_fresh_run() -> None:
    notifier = _FakeNotifier()
    final = run_graph_loop(
        _ralph_like_loop(), _initial_state("rg-notify"), _stub_llm_client(), notifier=notifier
    )

    assert [e.kind for e in notifier.events] == [EventKind.STARTED, EventKind.COMPLETED]
    assert final.status is RunStatus.COMPLETED


def test_run_graph_loop_resuming_true_emits_no_started_only_the_terminal_event() -> None:
    # E1: resuming=True must suppress STARTED even though this loop re-enters
    # at start_index's default of 0 -- exactly the "start_index == 0 on a
    # resume" case the fixed `resuming` param (not start_index) guards against.
    notifier = _FakeNotifier()
    final = run_graph_loop(
        _ralph_like_loop(),
        _initial_state("rg-resume"),
        _stub_llm_client(),
        notifier=notifier,
        resuming=True,
    )

    assert [e.kind for e in notifier.events] == [EventKind.COMPLETED]
    assert final.status is RunStatus.COMPLETED


def test_run_graph_loop_crash_emits_crashed_with_pre_invoke_state_and_still_reraises() -> None:
    class CorruptingPersona(BasePersona):
        produces = ("x",)

        def run(self, state, llm_client, findings=None):
            record = StageRecord(
                stage_name="corrupt", tokens_used=1, cost_usd=0.0, completed_at="t1"
            )
            state.stage_history.append(record)
            state.stage_history[0].tokens_used = -5  # bypasses construction-time validation
            return state

    loop = Loop(stages=[Stage(persona=CorruptingPersona(), gate=ArtifactGate("x"))])
    notifier = _FakeNotifier()

    with pytest.raises(InvalidStateTransitionError):
        run_graph_loop(loop, _initial_state("rg-crash"), _stub_llm_client(), notifier=notifier)

    assert [e.kind for e in notifier.events] == [EventKind.STARTED, EventKind.CRASHED]
    crashed_event = notifier.events[1]
    # The pre-invoke primed snapshot, not the in-flight corrupted object --
    # stage_history is empty because the run never got past stage 0's node.
    assert crashed_event.state.stage_history == []
    assert "InvalidStateTransitionError" in crashed_event.error
    assert "Traceback" not in crashed_event.error


def test_run_graph_loop_fail_open_a_raising_notifier_never_changes_the_outcome() -> None:
    baseline = run_graph_loop(
        _ralph_like_loop(), _initial_state("rg-fo-baseline"), _stub_llm_client()
    )

    result = run_graph_loop(
        _ralph_like_loop(),
        _initial_state("rg-fo-raising"),
        _stub_llm_client(),
        notifier=_FakeNotifier(raise_on_emit=True),
    )

    assert result.status == baseline.status
    assert result.artifacts == baseline.artifacts


def test_run_graph_loop_unconfigured_default_notifier_is_inert(monkeypatch) -> None:
    monkeypatch.delenv("LOOP_ENGINE_SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("LOOP_ENGINE_SLACK_CHANNEL", raising=False)
    # Any attempt to import slack_sdk raises ImportError -- proves the
    # notifier resolved by `notifier or build_notifier_from_env()` (with no
    # env vars set) never pulls it in, without depending on whatever earlier
    # tests happened to leave in sys.modules.
    monkeypatch.setitem(sys.modules, "slack_sdk", None)

    final = run_graph_loop(_ralph_like_loop(), _initial_state("rg-noop"), _stub_llm_client())

    assert final.status is RunStatus.COMPLETED
