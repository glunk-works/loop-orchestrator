"""LangGraph engine — the loop engine.

A `StateGraph` driving the inter-stage routing. It does NOT implement the
per-stage cycle: each stage node calls the shared `execute_stage` primitive.
The graph carries only control-flow routing state (the domain `State` plus a
stage cursor and carried findings) — the "lightweight routing hub" the
migration targeted.

This is the only engine. The classic `run_loop` driver it replaced was deleted
in Phase 6 (sprint 27) once the LangGraph path was verified end to end on a
real host run; it remains recoverable at the `pre-phase6-classic` tag.
"""

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from loop_engine.core.engine import (
    IssueFiler,
    Loop,
    StageOutcome,
    _finalize,
    _prime_resume,
    execute_stage,
)
from loop_engine.core.notify import EventKind, LifecycleEvent, Notifier
from loop_engine.core.state import RunStatus, State
from loop_engine.tools.llm.client import LLMClient
from loop_engine.tools.slack_io import build_notifier_from_env

_logger = logging.getLogger(__name__)

# Our own hard caps (MAX_ESCALATIONS_PER_STAGE, MAX_REPLANS_PER_RUN) already
# guarantee termination; this bound only needs enough headroom that a legitimate
# run — every stage revising, escalating, and replanning to its cap — never trips
# LangGraph's super-step guard. Scaled off the loop length, generously.
_RECURSION_HEADROOM = 50

# The four terminal `RunStatus` values map 1:1 to an `EventKind`; `RUNNING`
# never maps to one (an explicit dict, not `EventKind(status.value)`, so an
# unexpected `RUNNING` at this point is a no-emit rather than a raise).
_TERMINAL_EVENT_KINDS: dict[RunStatus, EventKind] = {
    RunStatus.COMPLETED: EventKind.COMPLETED,
    RunStatus.FAILED_STAGE: EventKind.FAILED_STAGE,
    RunStatus.BUDGET_EXCEEDED: EventKind.BUDGET_EXCEEDED,
    RunStatus.AWAITING_ISSUE: EventKind.AWAITING_ISSUE,
}


def _safe_emit(notifier: Notifier, event: LifecycleEvent) -> None:
    """Fail-open at the call site (E2): a raising notifier must never affect
    the run, so every emit is caught and swallowed here, not just inside the
    notifier's own implementation."""
    try:
        notifier.emit(event)
    except Exception:
        _logger.warning("notifier raised for event kind=%s", event.kind)


class GraphState(TypedDict):
    """Control-flow channels threaded through the graph (no chat history)."""

    state: State
    stage_index: int
    carried_findings: list[str]
    carried_until: int
    done: bool


_COMPLETE_NODE = "__complete__"


def _node_name(index: int) -> str:
    return f"stage_{index}"


def _make_stage_node(loop: Loop, index: int, llm_client: LLMClient, issue_filer: IssueFiler | None):
    def node(gs: GraphState) -> dict:
        outcome: StageOutcome = execute_stage(
            loop,
            index,
            gs["state"],
            gs["carried_findings"],
            gs["carried_until"],
            llm_client,
            issue_filer,
        )
        return {
            "state": outcome.state,
            "stage_index": outcome.next_index,
            "carried_findings": outcome.carried_findings,
            "carried_until": outcome.carried_until,
            "done": outcome.terminal,
        }

    return node


def _make_complete_node(loop: Loop):
    def node(gs: GraphState) -> dict:
        final = _finalize(gs["state"], len(loop.stages), RunStatus.COMPLETED)
        return {"state": final, "done": True}

    return node


def _next_target(loop: Loop, gs: GraphState) -> str:
    if gs["done"]:
        return END
    if gs["stage_index"] >= len(loop.stages):
        return _COMPLETE_NODE
    return _node_name(gs["stage_index"])


def build_state_graph(loop: Loop, llm_client: LLMClient, issue_filer: IssueFiler | None = None):
    """Compile the stage graph: one node per stage, a completion node, and
    conditional edges that advance, re-enter (blast radius), or terminate."""
    graph = StateGraph(GraphState)
    for index in range(len(loop.stages)):
        graph.add_node(_node_name(index), _make_stage_node(loop, index, llm_client, issue_filer))
    graph.add_node(_COMPLETE_NODE, _make_complete_node(loop))

    stage_targets = {_node_name(i): _node_name(i) for i in range(len(loop.stages))}
    entry_map = {**stage_targets, _COMPLETE_NODE: _COMPLETE_NODE}
    graph.add_conditional_edges(START, lambda gs: _next_target(loop, gs), entry_map)

    route_map = {**entry_map, END: END}
    for index in range(len(loop.stages)):
        graph.add_conditional_edges(_node_name(index), lambda gs: _next_target(loop, gs), route_map)
    graph.add_edge(_COMPLETE_NODE, END)
    return graph.compile()


def run_graph_loop(
    loop: Loop,
    initial_state: State,
    llm_client: LLMClient,
    start_index: int = 0,
    initial_findings: list[str] | None = None,
    issue_filer: IssueFiler | None = None,
    notifier: Notifier | None = None,
    resuming: bool = False,
) -> State:
    """Drive `loop` to a terminal state, returning the final, already-persisted
    `State`."""
    active_notifier = notifier or build_notifier_from_env()

    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
    state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)

    # A deep snapshot, not the live `state` reference: the CRASHED path must
    # never carry an object that later in-graph mutation could have touched.
    pre_invoke_state = state.model_copy(deep=True)

    # `resuming` (E1), not `start_index == 0` — a resume re-entering at stage 0
    # (e.g. after answering an escalation) is not a fresh run and must not fire
    # a spurious STARTED.
    if not resuming:
        _safe_emit(
            active_notifier,
            LifecycleEvent(
                kind=EventKind.STARTED, state=pre_invoke_state, budget_usd=llm_client.budget_usd
            ),
        )

    compiled = build_state_graph(loop, llm_client, issue_filer)
    init: GraphState = {
        "state": state,
        "stage_index": start_index,
        "carried_findings": carried_findings,
        "carried_until": carried_until,
        "done": False,
    }
    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
    try:
        result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
    except Exception as exc:
        # `result` is unbound here — only the pre-invoke primed snapshot is
        # meaningful; this is not a finalized/snapshotted exit path, so the
        # error is a short type/message string, never a traceback or secret.
        _safe_emit(
            active_notifier,
            LifecycleEvent(
                kind=EventKind.CRASHED,
                state=pre_invoke_state,
                budget_usd=llm_client.budget_usd,
                error=f"{type(exc).__name__}: {exc}",
            ),
        )
        raise

    final_state = result["state"]
    event_kind = _TERMINAL_EVENT_KINDS.get(final_state.status)
    if event_kind is not None:
        _safe_emit(
            active_notifier,
            LifecycleEvent(kind=event_kind, state=final_state, budget_usd=llm_client.budget_usd),
        )
    return final_state
