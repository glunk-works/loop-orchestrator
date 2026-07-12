#!/usr/bin/env python
"""V2 host-run harness — Ralph convergence to terminal COMPLETED under container isolation.

Drives the target production config (LangGraph engine + declarative personas +
Ralph coder + MCP tools + container isolation) against a spec file, with an
INJECTED non-crashing ``issue_filer`` so a stray escalation records the questions
and pauses cleanly (AWAITING_ISSUE) instead of crashing on ``gh issue create``.

This is escalation-free STAGING, not a bypass of the real issue path. The Seuss27
PAT is scoped only to glunk-works/loop-engine and cannot create a throwaway repo,
so there is no usable scratch remote for a stray escalation to file into; the real
gh round-trip is V3's job. V2 only needs Ralph to converge without a crash masking
the result.

Run with cwd = a throwaway git tree (pre-seeded ``pyproject.toml``, one HEAD commit):

    V2_ESCALATION_LOG=/path/escalations.jsonl \\
    LOOP_ENGINE_ENGINE=langgraph LOOP_ENGINE_TOOLS=mcp LOOP_ENGINE_PERSONAS=declarative \\
    LOOP_ENGINE_CODER=ralph LOOP_ENGINE_ISOLATION=container \\
    python /path/v2_run_harness.py /path/v2_requirements_min.md 5.00

Exit 0 iff the run reached terminal COMPLETED.
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from loop_engine.core.graph_engine import run_graph_loop
from loop_engine.core.state import CURRENT_SCHEMA_VERSION, IssueRef, Question, RunStatus, State
from loop_engine.loops.default.loop import build_default_loop
from loop_engine.tools.llm.client import LLMClient
from loop_engine.tools.worktree import worktree_run

ESCALATION_LOG = Path(os.environ.get("V2_ESCALATION_LOG", "escalations.jsonl"))


def recording_filer(state: State, questions: list[Question], snapshot_hint: str) -> IssueRef:
    """Non-crashing stand-in for ``file_question_issue``: record the escalation
    and return a synthetic ref so the engine pauses AWAITING_ISSUE cleanly."""
    payload = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "run_id": state.run_id,
        "snapshot_hint": snapshot_hint,
        "questions": [{"origin_stage": q.origin_stage, "text": q.text} for q in questions],
    }
    with ESCALATION_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")
    print(
        f"\n*** INJECTED FILER: recorded {len(questions)} question(s); NOT filing a gh issue; "
        "pausing AWAITING_ISSUE cleanly ***\n",
        flush=True,
    )
    return IssueRef(number=1, url="local://escalation-recorded-no-gh")


def main() -> int:
    spec_path = Path(sys.argv[1])
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 5.00
    human_input = spec_path.read_text(encoding="utf-8")

    loop = build_default_loop()  # honors LOOP_ENGINE_PERSONAS / LOOP_ENGINE_CODER at call time
    run_id = uuid.uuid4().hex
    state = State(
        schema_version=CURRENT_SCHEMA_VERSION,
        run_id=run_id,
        stage_history=[],
        artifacts={"human_input": human_input},
    )
    llm = LLMClient(budget_usd=budget)

    print(
        f"V2 harness start {datetime.now(timezone.utc).isoformat()} "
        f"run_id={run_id} budget=${budget:.2f}",
        flush=True,
    )
    print(
        "  config: "
        f"ENGINE={os.environ.get('LOOP_ENGINE_ENGINE')} "
        f"TOOLS={os.environ.get('LOOP_ENGINE_TOOLS')} "
        f"PERSONAS={os.environ.get('LOOP_ENGINE_PERSONAS')} "
        f"CODER={os.environ.get('LOOP_ENGINE_CODER')} "
        f"ISOLATION={os.environ.get('LOOP_ENGINE_ISOLATION')}",
        flush=True,
    )

    with worktree_run(run_id):
        final = run_graph_loop(loop, state, llm, start_index=0, issue_filer=recording_filer)

    print(f"\n=== FINAL STATUS: {final.status.value} ===", flush=True)
    print(f"=== run_id: {run_id} ===", flush=True)
    print(f"=== cost_used: ${llm.cost_used:.4f} of ${budget:.2f} ===", flush=True)
    if ESCALATION_LOG.exists() and ESCALATION_LOG.stat().st_size > 0:
        print(f"=== escalations recorded: {ESCALATION_LOG} ===", flush=True)
    return 0 if final.status == RunStatus.COMPLETED else 1


if __name__ == "__main__":
    sys.exit(main())
