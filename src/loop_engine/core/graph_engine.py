"""LangGraph engine (Phase 1d).

A `StateGraph` reimplementation of `run_loop`'s inter-stage routing. It does
NOT reimplement the per-stage cycle: each stage node calls the shared
`execute_stage` primitive, so the classic engine and this one are behaviorally
identical by construction. The graph carries only control-flow routing state
(the domain `State` plus a stage cursor and carried findings) — the "lightweight
routing hub" the migration targets.

Selected at runtime by `LOOP_ENGINE_ENGINE=langgraph`; the classic `run_loop`
remains the default until this path has proven out end to end.
"""

import os
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from loop_engine.core.engine import Loop, StageOutcome, _finalize, _prime_resume, execute_stage
from loop_engine.core.state import RunStatus, State
from loop_engine.tools.llm.client import LLMClient

ENGINE_ENV_VAR = "LOOP_ENGINE_ENGINE"
_LANGGRAPH_ENGINE = "langgraph"

# Our own hard caps (MAX_ESCALATIONS_PER_STAGE, MAX_REPLANS_PER_RUN) already
# guarantee termination; this bound only needs enough headroom that a legitimate
# run — every stage revising, escalating, and replanning to its cap — never trips
# LangGraph's super-step guard. Scaled off the loop length, generously.
_RECURSION_HEADROOM = 50


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


def use_langgraph_engine() -> bool:
    """Whether the LangGraph engine is selected via the environment flag."""
    return os.environ.get(ENGINE_ENV_VAR, "").strip().lower() == _LANGGRAPH_ENGINE


def _make_stage_node(loop: Loop, index: int, llm_client: LLMClient):
    def node(gs: GraphState) -> dict:
        outcome: StageOutcome = execute_stage(
            loop,
            index,
            gs["state"],
            gs["carried_findings"],
            gs["carried_until"],
            llm_client,
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


def build_state_graph(loop: Loop, llm_client: LLMClient):
    """Compile the stage graph: one node per stage, a completion node, and
    conditional edges that advance, re-enter (blast radius), or terminate."""
    graph = StateGraph(GraphState)
    for index in range(len(loop.stages)):
        graph.add_node(_node_name(index), _make_stage_node(loop, index, llm_client))
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
) -> State:
    """LangGraph-driven equivalent of `run_loop`, with the same signature and
    return contract (the final, already-persisted `State`)."""
    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
    state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)

    compiled = build_state_graph(loop, llm_client)
    init: GraphState = {
        "state": state,
        "stage_index": start_index,
        "carried_findings": carried_findings,
        "carried_until": carried_until,
        "done": False,
    }
    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
    result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
    return result["state"]
