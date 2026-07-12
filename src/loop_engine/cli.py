import json
from pathlib import Path
from typing import Annotated

import typer

from loop_engine import runner
from loop_engine.core.engine import (
    PAUSED_STAGE_COUNTER,
    Loop,
    reentry_index,
)
from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import (
    RunStatus,
    State,
    migrate_state_payload,
)
from loop_engine.loops.default.loop import DEFAULT_LOOP, build_default_loop
from loop_engine.runner import DEFAULT_BUDGET_USD
from loop_engine.tools import issue_io
from loop_engine.tools.issue_io import default_issue_reader
from loop_engine.tools.llm.client import LLMClient
from loop_engine.tools.repo_io import resolve_repo_slug
from loop_engine.tools.worktree import prune_all, worktree_run

app = typer.Typer()

NAMED_LOOPS: dict[str, Loop] = {"default": DEFAULT_LOOP}


def _resolve_loop(loop_name: str) -> Loop:
    """The named loop, rebuilt for "default" so the loop is constructed fresh
    per run; other names come from NAMED_LOOPS."""
    if loop_name == "default":
        return build_default_loop()
    return NAMED_LOOPS[loop_name]


_BUDGET_HELP = "Hard cap on cumulative LLM spend for the run, in USD."

_EXIT_CODES = {
    RunStatus.COMPLETED: 0,
    RunStatus.AWAITING_ISSUE: 2,
    RunStatus.BUDGET_EXCEEDED: 3,
}

# A human closing the pending issue without answers is a deliberate, documented
# abort — a distinct outcome from a crash (1) or a still-unanswered issue (2), and
# a supervising script has to be able to tell them apart.
ABORTED_BY_HUMAN_EXIT_CODE = 4


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
    resuming = resume_from is not None
    if resuming:
        selected_loop = _resolve_loop(loop)
        initial_state = _load_state(resume_from)
        start_index = _start_index_for(initial_state, selected_loop)

        # No `issue_filer` to thread: `default_issue_filer` resolves its own
        # destination from `worktree.origin_cwd()`, so every entrypoint —
        # here, `runner.run_new`, the trigger surface — gets it right without
        # each one remembering to.
        llm_client = LLMClient(budget_usd=budget)
        with worktree_run(initial_state.run_id, reuse=True):
            final_state = run_graph_loop(
                selected_loop, initial_state, llm_client, start_index=start_index
            )
    else:
        human_input = input.read_text() if input is not None else ""
        final_state = runner.run_new(human_input, budget_usd=budget, loop_name=loop)
    _report_outcome(final_state)


@app.command()
def resume(
    from_issue: Annotated[
        int | None, typer.Option("--from-issue", help="Issue number to resume from.")
    ] = None,
    loop: Annotated[str, typer.Option("--loop")] = "default",
    budget: Annotated[float, typer.Option("--budget", help=_BUDGET_HELP)] = DEFAULT_BUDGET_USD,
    snapshot: Annotated[
        Path | None,
        typer.Option(
            "--snapshot",
            help="Resume this snapshot directly. The issue number and repo are "
            "derived from its own pending_issue -- unambiguous, never from CWD "
            "or a passed --from-issue/--repo.",
        ),
    ] = None,
    repo: Annotated[
        str | None,
        typer.Option(
            "--repo",
            help="owner/repo the issue lives on, when using --from-issue without "
            "--snapshot. Defaults to the repo of the current directory — pass "
            "this when resuming a run whose issue was filed on a managed repo "
            "(e.g. a flows/maintenance run).",
        ),
    ] = None,
) -> None:
    """Resume a run paused on a GitHub issue, folding in the human's answers."""
    selected_loop = _resolve_loop(loop)

    if snapshot is not None:
        # F1a: --snapshot is the unambiguous path. The snapshot's own
        # pending_issue -- recorded at pause time by the process that
        # actually filed the issue -- is the only first-hand record of where
        # it lives. Neither CWD nor a passed --from-issue/--repo enters.
        state = _load_state(snapshot)
        if state.pending_issue is None:
            raise typer.BadParameter(f"Snapshot {snapshot} is not paused on any issue.")
        from_issue = state.pending_issue.number
        read_repo = issue_io.repo_from_issue_url(state.pending_issue.url)
        snapshot_path = snapshot
    else:
        if from_issue is None:
            raise typer.BadParameter("Pass --from-issue, or --snapshot to resume unambiguously.")
        # F1b: never leave the destination to gh's implicit CWD resolution.
        # The echo below is the actual defense here -- the reframe behind
        # F1/F2 is that no comparison downstream can detect a human resuming
        # from the wrong checkout; only a human reading this line can.
        read_repo = repo or resolve_repo_slug(Path.cwd())
        typer.echo(f"Reading issue #{from_issue} from {read_repo}")
        snapshot_path = None

    issue_data = default_issue_reader(from_issue, repo=read_repo)

    if snapshot_path is None:
        snapshot_path = Path(p) if (p := issue_io.parse_snapshot_path(issue_data)) else None
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

    # F1c: a snapshot<->issue integrity check (did the link survive?), not a
    # wrong-repo defense -- the repo actually queried above was already
    # pinned, either by the snapshot's own pending_issue (--snapshot) or
    # explicitly resolved and echoed (--from-issue), so this can only catch
    # link corruption (e.g. a repo rename or issue transfer).
    issue_url = issue_data.get("url")
    if issue_url is None:
        # F5: read_issue always requests `url`; a missing one means something
        # already went wrong, which is exactly when skipping is worst.
        raise typer.BadParameter(
            f"Issue #{from_issue} read from {read_repo} returned no URL; refusing "
            "to resume without confirming which issue was read."
        )
    if issue_url != state.pending_issue.url:
        raise typer.BadParameter(
            f"Issue #{from_issue} read from {issue_url}, but snapshot {snapshot_path} "
            f"is paused on {state.pending_issue.url}. The issue's own link does not "
            "match what was recorded at pause time."
        )

    try:
        answers = issue_io.parse_issue_answers(issue_data, from_issue)
    except issue_io.IssueClosedWithoutAnswersError as exc:
        # The documented way a human aborts a paused run, so it exits with its
        # own code — not 1, which would be indistinguishable from a crash.
        typer.echo(str(exc))
        raise typer.Exit(code=ABORTED_BY_HUMAN_EXIT_CODE) from exc
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

    # fold_answers and the engine both read the run's artifact tree, so run
    # them inside the run's worktree (reuse the one created on the original run).
    with worktree_run(state.run_id, reuse=True):
        state = pm_persona.fold_answers(state, llm_client)

        paused_index = state.counters.get(PAUSED_STAGE_COUNTER, 0)
        resolved = [q for q in state.questions if q.resolved_by == f"human:{from_issue}"]
        start_index = reentry_index(selected_loop, paused_index, resolved)

        findings = [
            f"Escalated question: {q.text}\n  Resolution (from human): {q.resolution}"
            for q in resolved
            if q.resolution is not None
        ]

        final_state = run_graph_loop(
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


@app.command(name="prune-worktrees")
def prune_worktrees(
    run_id: Annotated[
        str | None,
        typer.Option("--run-id", help="Remove only this run's worktree and branch."),
    ] = None,
    all_: Annotated[
        bool,
        typer.Option("--all", help="Remove every per-run worktree under the worktree root."),
    ] = False,
) -> None:
    """Remove retained per-run worktrees. Worktrees are kept by default (resume,
    PR source, inspection); this reclaims them once a run is truly done."""
    if run_id is not None:
        from loop_engine.tools.worktree import cleanup

        cleanup(run_id)
        typer.echo(f"removed worktree for run {run_id}")
    elif all_:
        removed = prune_all()
        typer.echo(f"removed {len(removed)} worktree(s): {', '.join(removed) or '(none)'}")
    else:
        raise typer.BadParameter("pass --run-id <id> or --all")


if __name__ == "__main__":
    app()
