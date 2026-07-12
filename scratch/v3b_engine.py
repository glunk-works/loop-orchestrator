"""V3b -- engine-level issue round-trip: a forced pause files a REAL issue through
the issue MCP server, a human answers it, and the run resumes through the MCP reader.

Real Anthropic budget. Real GitHub side effects. Two phases, because a human answers
in between:

    # 1. pause (isolation=none is sufficient: a PM-stage pause executes NO model code)
    cd "$SCRATCH_CLONE"
    LOOP_ENGINE_ISOLATION=none hatch run python /workspace/scratch/v3b_engine.py pause \
        --input /workspace/scratch/v3b_forcing_input.md --budget 1.00

    # 2. answer the issue it prints, with a single ```answers block

    # 3. resume (isolation=container is MANDATORY: this leg reaches the Coder,
    #    which generates and executes code)
    cd "$SCRATCH_CLONE"
    LOOP_ENGINE_ISOLATION=container hatch run python /workspace/scratch/v3b_engine.py resume \
        --budget 5.00

WHY A HARNESS AND NOT THE BARE CLI: the MCP filer/reader are capability-only today
(no flag selects them, by design -- see CLAUDE.md / Sprint 26). This harness injects
what Task 8 will make the default: `issue_filer=mcp_issue_filer(provider)` into the
engine. The read seam is now `cli.default_issue_reader` (the `_issue_reader` module
global was retired in sprint 27 Task 8 — both seams are threaded collaborators).

B1 (cwd -> target repo): `create_issue` shells `gh issue create` with no `--repo`, so
gh resolves the repo from cwd. The issue server inherits THIS process's cwd at launch
(`"cwd": null` in loop_engine.mcp.json), so we enter the provider while cwd is the
scratch clone -- BEFORE `worktree_run` chdirs into loop-engine's own worktree. That is
exactly the trap that put issues #16/#19/#21 on glunk-works/loop-engine: with isolation
on, in-process `gh` inherits the worktree cwd (inside loop-engine), while an MCP server
launched from the scratch clone keeps its own. Step 0 refuses to run outside a scratch clone.
"""

import argparse
import json
import sys
from pathlib import Path

import typer

from loop_engine import cli
from loop_engine.core.gates import GateDecision, GateResult, new_question
from loop_engine.core.state import CURRENT_SCHEMA_VERSION, RunStatus, State
from loop_engine.loops.default.loop import build_default_loop
from loop_engine.tools.issue_io.mcp_client import mcp_issue_filer, mcp_issue_reader
from loop_engine.tools.llm.client import LLMClient
from loop_engine.tools.mcp.provider import build_issue_provider
from loop_engine.tools.worktree.manager import worktree_run

EVIDENCE = Path("v3b_evidence")
PAUSE_RECORD = EVIDENCE / "pause.json"


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    sys.exit(1)


def record(name: str, payload) -> None:
    EVIDENCE.mkdir(exist_ok=True)
    body = payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str)
    (EVIDENCE / name).write_text(body)


def guard_cwd() -> str:
    """B1: refuse to file escalation issues onto the project repo."""
    import subprocess

    target = json.loads(
        subprocess.run(  # noqa: S603 -- fixed executable, no shell, args not attacker-controlled
            ["gh", "repo", "view", "--json", "nameWithOwner"],  # noqa: S607 -- PATH, as issue_io does
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        ).stdout
    )["nameWithOwner"]
    if target.endswith("/loop-engine"):
        fail(
            f"cwd resolves to {target} -- refusing. Run from a disposable scratch clone, "
            "or this files real escalation issues on the project repo (B1: see #16/#19/#21)."
        )
    print(f"  target repo: {target}")
    return target


class ForcedEscalateGate:
    """Deterministic V3b trigger (fallback for --force-gate).

    A gate is just a callable `(state, stage_name) -> GateResult`. This one always
    ESCALATEs. Everything V3 must prove -- the MCP provider, the real `gh`, the real
    issue, both seams -- stays real; only the *trigger* is synthetic, and the PM
    gate's judgment is already covered hermetically.

    It works because the PM stage has `resolvers=[]`: the resolver ladder iterates an
    empty list, the questions stay unresolved, and `_pause_for_issue` fires at stage 0
    -- the cheapest reachable pause, and one that never reaches the Coder.
    """

    def __call__(self, state: State, stage_name: str) -> GateResult:
        return GateResult(
            decision=GateDecision.ESCALATE,
            questions=[
                new_question(
                    stage_name,
                    "The requirements are self-contradictory: entries must be immutable "
                    "and corrections must erase the original. Which wins?",
                ),
                new_question(
                    stage_name,
                    "The requirements demand memory-only storage AND durability across a "
                    "host hardware failure. Which constraint should be relaxed?",
                ),
            ],
        )


def phase_pause(args: argparse.Namespace) -> None:
    print("V3b.1 -- forced pause, issue filed through the MCP server\n")
    guard_cwd()

    loop = build_default_loop()
    if args.force_gate:
        loop.stages[0].gate = ForcedEscalateGate()
        print("  trigger: ForcedEscalateGate on the PM stage (deterministic)")
    else:
        print("  trigger: unsatisfiable requirements doc (PM CriticGate exhaustion)")
        print(f"  budget guard: ${args.budget:.2f} -- a PM that converges anyway dies cheap")

    human_input = Path(args.input).read_text()
    run_id = args.run_id
    state = State(
        schema_version=CURRENT_SCHEMA_VERSION,
        run_id=run_id,
        stage_history=[],
        artifacts={"human_input": human_input},
    )
    llm_client = LLMClient(budget_usd=args.budget)

    # Provider entered BEFORE worktree_run: the server subprocess's cwd is pinned to
    # the scratch clone, so `gh issue create` targets the scratch repo even after the
    # orchestrator chdirs into loop-engine's worktree (B1).
    with build_issue_provider() as provider:
        with worktree_run(run_id):
            final = run_graph_loop_with_filer(loop, state, llm_client, provider)

    print(f"\n  run_id:      {run_id}")
    print(f"  status:      {final.status}")
    print(f"  cost:        ${llm_client.cost_used:.4f}")

    if final.status is not RunStatus.AWAITING_ISSUE:
        record("pause_FAILED_state.json", final.model_dump())
        fail(
            f"expected AWAITING_ISSUE, got {final.status}. The PM converged (or the run "
            "died on budget) -- re-run with --force-gate for the deterministic trigger."
        )
    ok("run reached AWAITING_ISSUE (exit-code-2 equivalent)")

    if final.pending_issue is None:
        fail("AWAITING_ISSUE but state.pending_issue is None -- the filer seam did not fire")
    issue = final.pending_issue
    ok(f"issue filed through the MCP server: #{issue.number} {issue.url}")

    filed = [q for q in final.questions if q.resolution is None]
    ok(f"{len(filed)} question(s) filed, in the engine's unresolved order")

    record(
        "pause.json",
        {"run_id": run_id, "issue": issue.model_dump(), "cost": llm_client.cost_used},
    )
    record("pause_state.json", final.model_dump())
    record("pause_questions.txt", "\n".join(f"{i}. {q.text}" for i, q in enumerate(filed, 1)))

    print("\nNEXT -- answer the issue with exactly ONE ```answers block")
    print("       (R6: only one block per comment is parsed):")
    print(f"\n  gh issue comment {issue.number} --body \"$(printf '```answers\\n%s\\n```')\" \\")
    print("    # one `N: answer` line per question, numbers matching the issue body")
    print(f"\nThen: LOOP_ENGINE_ISOLATION=container hatch run python {__file__} \\")
    print("        resume --budget 5.00")


def run_graph_loop_with_filer(loop, state, llm_client, provider):
    """The one line Task 8 will make the default."""
    from loop_engine.core.graph_engine import run_graph_loop

    return run_graph_loop(
        loop, state, llm_client, start_index=0, issue_filer=mcp_issue_filer(provider)
    )


def phase_resume(args: argparse.Namespace) -> None:
    print("V3b.3 -- resume through the MCP reader\n")
    guard_cwd()

    if not PAUSE_RECORD.exists():
        fail(f"{PAUSE_RECORD} not found -- run the `pause` phase first (from this same cwd).")
    paused = json.loads(PAUSE_RECORD.read_text())
    number = paused["issue"]["number"]
    print(f"  resuming from issue #{number} (run {paused['run_id']})")

    with build_issue_provider() as provider:
        # The read seam. Task 8 made the MCP reader the runtime default; patch the
        # name `cli` resolves so this harness still pins the provider it built.
        # (was: `cli._issue_reader`, a module global defaulting to the
        # classic `issue_io.read_issue`; injecting here is exactly the shape R1/R2/R3
        # will make the default in Task 8.
        cli.default_issue_reader = lambda n, repo=None: mcp_issue_reader(provider)(n)
        ok("cli.default_issue_reader patched: reads go through the issue MCP server")

        # WATCH (R2): cli.resume threads NO issue_filer into its inner run_graph_loop.
        # If this resumed run escalates AGAIN, that second issue is filed through the
        # CLASSIC gh path -- and under isolation=container, classic gh inherits the
        # worktree cwd, so it would land on glunk-works/loop-engine. That is the seam
        # gap R2 names, and it is observable right here.
        try:
            cli.resume(from_issue=number, loop="default", budget=args.budget, snapshot=None)
            exit_code = 0
        except typer.Exit as exc:
            exit_code = exc.exit_code

    print(f"\n  resume exit code: {exit_code}")
    record("resume_exit_code.txt", str(exit_code))

    if exit_code == 2:
        fail(
            "resume exited 2 -- either the issue had no parseable answers comment, or the "
            "run RE-PAUSED. If it re-paused, check WHICH repo the second issue landed in: "
            "that is finding R2 firing (classic filer + worktree cwd)."
        )
    ok(
        "resume consumed the MCP-read answers and drove the run to a terminal state "
        f"(exit {exit_code})"
    )
    print("\n  Verify from the run's snapshots:")
    print("    - the filed questions carry resolution + resolved_by == 'human:%d'" % number)
    print("    - stage_history advances PAST the stage the run paused on")
    print("    - exit 0 == COMPLETED (strongest); exit 3 == BUDGET_EXCEEDED after the")
    print("      resume demonstrably took effect is acceptable -- V3's obligation is the")
    print("      issue seam, not another happy-path proof (V1 already did that).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="phase", required=True)

    p = sub.add_parser("pause", help="force a pause; file the issue through the MCP server")
    p.add_argument("--input", default="/workspace/scratch/v3b_forcing_input.md")
    p.add_argument("--budget", type=float, default=1.00)
    p.add_argument("--run-id", default="v3b" + "0" * 29)
    p.add_argument(
        "--force-gate",
        action="store_true",
        help="deterministic trigger: swap the PM gate for one that always ESCALATEs",
    )
    p.set_defaults(func=phase_pause)

    r = sub.add_parser("resume", help="resume through the MCP reader after answering")
    r.add_argument("--budget", type=float, default=5.00)
    r.set_defaults(func=phase_resume)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
