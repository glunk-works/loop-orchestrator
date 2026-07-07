import json
import uuid
from pathlib import Path
from typing import Annotated

import typer

from loop_engine.core.engine import (
    PAUSED_STAGE_COUNTER,
    Loop,
    reentry_index,
    run_loop,
)
from loop_engine.core.state import (
    CURRENT_SCHEMA_VERSION,
    RunStatus,
    State,
    migrate_state_payload,
)
from loop_engine.loops.default.loop import DEFAULT_LOOP
from loop_engine.tools import issue_io
from loop_engine.tools.llm.client import LLMClient

app = typer.Typer()

NAMED_LOOPS: dict[str, Loop] = {"default": DEFAULT_LOOP}

DEFAULT_BUDGET_USD = 5.00

_BUDGET_HELP = "Hard cap on cumulative LLM spend for the run, in USD."

_EXIT_CODES = {
    RunStatus.COMPLETED: 0,
    RunStatus.AWAITING_ISSUE: 2,
    RunStatus.BUDGET_EXCEEDED: 3,
}


@app.callback()
def main() -> None:
    """loop-engine: run a named persona loop against shared State."""


def _load_state(path: Path) -> State:
    payload = migrate_state_payload(json.loads(path.read_text()))
    return State.model_validate(payload)


def _start_index_for(state: State, loop: Loop) -> int:
    """Where a snapshot resumes: identity-checked, not just history-counted.

    Every recorded stage name must belong to the loop (resuming against a
    different loop fails loudly instead of silently misaligning artifacts).
    A paused run resumes at the stage it paused on; otherwise the run picks
    up after the last accepted stage.
    """
    names = loop.stage_names()
    unknown = [r.stage_name for r in state.stage_history if r.stage_name not in names]
    if unknown:
        raise typer.BadParameter(
            f"Snapshot records stage(s) {unknown} that do not exist in this loop; "
            "refusing to resume against a mismatched loop."
        )
    if PAUSED_STAGE_COUNTER in state.counters:
        return state.counters[PAUSED_STAGE_COUNTER]
    if not state.stage_history:
        return 0
    return names.index(state.stage_history[-1].stage_name) + 1


def _report_outcome(state: State) -> None:
    typer.echo(f"run {state.run_id}: {state.status.value}")
    if state.pending_issue is not None:
        typer.echo(
            f"Paused on questions for a human — answer on {state.pending_issue.url} "
            f"then run: loop-engine resume --from-issue {state.pending_issue.number}"
        )
    raise typer.Exit(code=_EXIT_CODES.get(state.status, 1))


@app.command()
def run(
    loop: Annotated[str, typer.Option("--loop")] = "default",
    input: Annotated[Path | None, typer.Option("--input")] = None,
    budget: Annotated[float, typer.Option("--budget", help=_BUDGET_HELP)] = DEFAULT_BUDGET_USD,
    resume_from: Annotated[Path | None, typer.Option("--resume-from")] = None,
) -> None:
    selected_loop = NAMED_LOOPS[loop]

    if resume_from is not None:
        initial_state = _load_state(resume_from)
        start_index = _start_index_for(initial_state, selected_loop)
    else:
        human_input = input.read_text() if input is not None else ""
        initial_state = State(
            schema_version=CURRENT_SCHEMA_VERSION,
            run_id=uuid.uuid4().hex,
            stage_history=[],
            artifacts={"human_input": human_input},
        )
        start_index = 0

    llm_client = LLMClient(budget_usd=budget)
    final_state = run_loop(selected_loop, initial_state, llm_client, start_index=start_index)
    _report_outcome(final_state)


@app.command()
def resume(
    from_issue: Annotated[int, typer.Option("--from-issue")],
    loop: Annotated[str, typer.Option("--loop")] = "default",
    budget: Annotated[float, typer.Option("--budget", help=_BUDGET_HELP)] = DEFAULT_BUDGET_USD,
    snapshot: Annotated[
        Path | None,
        typer.Option("--snapshot", help="Override the snapshot path recorded in the issue."),
    ] = None,
) -> None:
    """Resume a run paused on a GitHub issue, folding in the human's answers."""
    selected_loop = NAMED_LOOPS[loop]

    issue_data = issue_io.read_issue(from_issue)
    snapshot_path = snapshot or (
        Path(p) if (p := issue_io.parse_snapshot_path(issue_data)) else None
    )
    if snapshot_path is None:
        raise typer.BadParameter(
            f"Issue #{from_issue} does not reference a snapshot; pass --snapshot explicitly."
        )
    state = _load_state(snapshot_path)

    if state.pending_issue is None or state.pending_issue.number != from_issue:
        raise typer.BadParameter(
            f"Snapshot {snapshot_path} is not paused on issue #{from_issue} "
            f"(pending issue: {state.pending_issue})."
        )

    answers = issue_io.read_issue_answers(from_issue, issue_data)
    if not answers:
        typer.echo(f"Issue #{from_issue} has no answers comment yet; nothing to resume.")
        raise typer.Exit(code=2)

    # Filing order == unresolved order at pause time == unresolved order in
    # the snapshot (the snapshot was written at filing time).
    filed = [q for q in state.questions if q.resolution is None]
    state = state.model_copy(
        update={
            "questions": issue_io.apply_answers_to_questions(
                state.questions, filed, answers, from_issue
            )
        }
    )

    llm_client = LLMClient(budget_usd=budget)

    # PM folds the answers into the spec and classifies each answer's blast
    # radius, which decides how far back the run re-enters.
    pm_persona = selected_loop.stages[0].persona
    if not hasattr(pm_persona, "fold_answers"):
        raise typer.BadParameter(
            f"Loop {loop!r} has no answer-folding persona at stage 0; cannot resume from an issue."
        )
    state = pm_persona.fold_answers(state, llm_client)

    paused_index = state.counters.get(PAUSED_STAGE_COUNTER, 0)
    resolved = [q for q in state.questions if q.resolved_by == f"human:{from_issue}"]
    start_index = reentry_index(selected_loop, paused_index, resolved)

    findings = [
        f"Escalated question: {q.text}\n  Resolution (from human): {q.resolution}"
        for q in resolved
        if q.resolution is not None
    ]

    final_state = run_loop(
        selected_loop,
        state,
        llm_client,
        start_index=start_index,
        initial_findings=findings,
    )
    _report_outcome(final_state)


@app.command(name="cost-summary")
def cost_summary(run_id: Annotated[str, typer.Option("--run-id")]) -> None:
    run_dir = Path("state") / run_id

    # Terminal/status snapshots duplicate the history of the last accepted
    # stage; summing every file double-counts. The most complete history is
    # authoritative: every accepted stage (including replays) appears in it
    # exactly once.
    best: State | None = None
    for snapshot_path in sorted(run_dir.glob("*.json")):
        state = State.model_validate(migrate_state_payload(json.loads(snapshot_path.read_text())))
        if best is None or len(state.stage_history) > len(best.stage_history):
            best = state

    typer.echo(f"{'Stage':<40}{'Tokens':>10}{'Cache W':>10}{'Cache R':>10}{'Cost (USD)':>14}")
    total_tokens = 0
    total_cache_w = 0
    total_cache_r = 0
    total_cost = 0.0
    if best is not None:
        for record in best.stage_history:
            total_tokens += record.tokens_used
            total_cache_w += record.cache_creation_input_tokens
            total_cache_r += record.cache_read_input_tokens
            total_cost += record.cost_usd
            typer.echo(
                f"{record.stage_name:<40}{record.tokens_used:>10}"
                f"{record.cache_creation_input_tokens:>10}"
                f"{record.cache_read_input_tokens:>10}{record.cost_usd:>14.4f}"
            )
    typer.echo(
        f"{'TOTAL':<40}{total_tokens:>10}{total_cache_w:>10}{total_cache_r:>10}{total_cost:>14.4f}"
    )


if __name__ == "__main__":
    app()
