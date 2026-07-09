"""Shared "start a fresh run from human input" orchestration.

The single source of truth for `cli.run`'s fresh-run path and the trigger
surface's dispatcher (`trigger/dispatch.py`) — both start a new run from raw
`human_input` the same way; only where the input comes from differs.
`run_in_tree` (Phase 5 piece 3) is a third entrypoint for `flows/maintenance`:
it runs the same default-loop build over a *foreign* clone rather than the
orchestrator's own worktree.
"""

import os
import uuid
from pathlib import Path

from loop_engine.core.engine import Loop, run_loop
from loop_engine.core.graph_engine import run_graph_loop, use_langgraph_engine
from loop_engine.core.state import CURRENT_SCHEMA_VERSION, State
from loop_engine.loops.default.loop import DEFAULT_LOOP, build_default_loop
from loop_engine.tools.llm.client import LLMClient
from loop_engine.tools.worktree import worktree_run

NAMED_LOOPS: dict[str, Loop] = {"default": DEFAULT_LOOP}

DEFAULT_BUDGET_USD = 5.00


def _resolve_loop(loop_name: str) -> Loop:
    """The named loop, rebuilt for "default" so a runtime `LOOP_ENGINE_CODER`
    flag is honored (like `_select_engine`); other names come from NAMED_LOOPS."""
    if loop_name == "default":
        return build_default_loop()
    return NAMED_LOOPS[loop_name]


def _select_engine():
    """The engine entrypoint for this run: LangGraph when the flag is set,
    else the classic `run_loop`. Resolved through the module global so tests
    that patch `runner.run_loop` still take effect on the fresh-run path."""
    return run_graph_loop if use_langgraph_engine() else run_loop


def run_new(
    human_input: str,
    *,
    budget_usd: float = DEFAULT_BUDGET_USD,
    loop_name: str = "default",
) -> State:
    """Start and run a brand-new run from `human_input`, returning the final State."""
    selected_loop = _resolve_loop(loop_name)
    run_id = uuid.uuid4().hex
    initial_state = State(
        schema_version=CURRENT_SCHEMA_VERSION,
        run_id=run_id,
        stage_history=[],
        artifacts={"human_input": human_input},
    )
    llm_client = LLMClient(budget_usd=budget_usd)
    with worktree_run(run_id):
        final_state = _select_engine()(selected_loop, initial_state, llm_client, start_index=0)
    return final_state


def run_in_tree(
    human_input: str,
    tree_path: str | Path,
    *,
    budget_usd: float = DEFAULT_BUDGET_USD,
    loop_name: str = "default",
) -> State:
    """Start and run a brand-new run from `human_input` with cwd pinned to
    `tree_path` (a foreign clone, e.g. `flows/maintenance`'s target repo).

    Unlike `run_new`, this does **not** open `worktree_run`: `tree_path` is
    itself the isolation boundary, and `worktree_run` would chdir into the
    orchestrator's own `.worktrees/<run_id>` instead — the wrong tree. Cwd is
    restored on every exit path, including an engine exception.

    State snapshots are left to follow the engine's normal (cwd-relative)
    behavior rather than pinned back to the original cwd — the clone *is*
    the run's tree here, so its snapshots belong alongside it, not the
    orchestrator's own checkout.
    """
    selected_loop = _resolve_loop(loop_name)
    run_id = uuid.uuid4().hex
    initial_state = State(
        schema_version=CURRENT_SCHEMA_VERSION,
        run_id=run_id,
        stage_history=[],
        artifacts={"human_input": human_input},
    )
    llm_client = LLMClient(budget_usd=budget_usd)
    origin = Path.cwd()
    os.chdir(tree_path)
    try:
        final_state = _select_engine()(selected_loop, initial_state, llm_client, start_index=0)
    finally:
        os.chdir(origin)
    return final_state
