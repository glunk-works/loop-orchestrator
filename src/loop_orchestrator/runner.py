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

from loop_orchestrator.core.engine import (
    PAUSED_STAGE_COUNTER,
    Loop,
    apply_resolved_answers,
    reentry_index,
)
from loop_orchestrator.core.graph_engine import run_graph_loop
from loop_orchestrator.core.state import CURRENT_SCHEMA_VERSION, State
from loop_orchestrator.loops.default.loop import DEFAULT_LOOP, build_default_loop
from loop_orchestrator.tools.llm.client import LLMClient
from loop_orchestrator.tools.worktree import worktree_run

NAMED_LOOPS: dict[str, Loop] = {"default": DEFAULT_LOOP}

DEFAULT_BUDGET_USD = 5.00


class LoopHasNoFoldAnswersPersonaError(ValueError):
    """`resume_run` can't resume: the named loop's stage-0 persona exposes no
    `fold_answers`. A distinct type (not a bare `ValueError`) so callers can
    catch exactly this signal without also swallowing a `ValueError` raised
    from deep inside the resumed loop itself (e.g. bad env-var config read at
    persona-build time) -- that must propagate uncaught, same as pre-refactor."""


def _resolve_loop(loop_name: str) -> Loop:
    """The named loop, rebuilt for "default" so the loop is constructed fresh
    per run; other names come from NAMED_LOOPS."""
    if loop_name == "default":
        return build_default_loop()
    return NAMED_LOOPS[loop_name]


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
        final_state = run_graph_loop(selected_loop, initial_state, llm_client, start_index=0)
    return final_state


def resume_run(
    state: State,
    resolved_answers: dict[int, str],
    *,
    resolved_by: str,
    budget_usd: float = DEFAULT_BUDGET_USD,
    loop_name: str = "default",
) -> State:
    """Fold a human's numbered answers into a paused run and drive it to its
    next terminal state -- the single resume-execution path shared by every
    escalation transport (`cli.resume`'s GitHub-issue round-trip today,
    `slack_control`'s thread-reply round-trip in T5). Callers differ only in
    how they read/parse the answers and what `resolved_by` provenance they
    pass; `resolved_by` is recorded but never branched on here (finding #4).
    """
    selected_loop = _resolve_loop(loop_name)
    pm_persona = selected_loop.stages[0].persona
    if not hasattr(pm_persona, "fold_answers"):
        raise LoopHasNoFoldAnswersPersonaError(
            f"Loop {loop_name!r} has no answer-folding persona at stage 0; cannot resume."
        )

    state, resolved_ids = apply_resolved_answers(state, resolved_answers, resolved_by)
    llm_client = LLMClient(budget_usd=budget_usd)

    # fold_answers and the engine both read the run's artifact tree, so run
    # them inside the run's worktree (reuse the one created on the original run).
    with worktree_run(state.run_id, reuse=True):
        state = pm_persona.fold_answers(state, llm_client)

        paused_index = state.counters.get(PAUSED_STAGE_COUNTER, 0)
        # The explicit ids this call resolved, re-fetched post-fold so
        # `reentry_index` sees the `impact` fold_answers just classified --
        # never a `resolved_by` string match (finding #4).
        resolved = [q for q in state.questions if q.id in resolved_ids]
        start_index = reentry_index(selected_loop, paused_index, resolved)

        findings = [
            f"Escalated question: {q.text}\n  Resolution (from human): {q.resolution}"
            for q in resolved
            if q.resolution is not None
        ]

        return run_graph_loop(
            selected_loop,
            state,
            llm_client,
            start_index=start_index,
            initial_findings=findings,
            resuming=True,
        )


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
        final_state = run_graph_loop(selected_loop, initial_state, llm_client, start_index=0)
    finally:
        os.chdir(origin)
    return final_state
