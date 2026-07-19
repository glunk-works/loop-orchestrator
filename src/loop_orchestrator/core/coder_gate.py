"""Evidence-based gate for the Coder stage.

The content ArtifactGate checks the reports artifact's shape; this gate then
executes the produced tests deterministically, so ACCEPT is based on a green
pytest run — evidence — not on the model's claim that the work is done.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from loop_orchestrator.core.gates import ArtifactGate, GateDecision, GateResult
from loop_orchestrator.core.state import State
from loop_orchestrator.tools.agent_state import read_scratchpad
from loop_orchestrator.tools.coder_tools import run_tests as run_tests_tool
from loop_orchestrator.tools.mcp import run_gate_pytest

# The persona appends this section to a report when model-emitted edit
# blocks failed to apply; its presence is a deterministic REVISE signal.
EDIT_FAILURES_HEADER = "## Edit Application Failures"

# Stable prefix on the finding the Ralph gate emits when EVERY manifest task is
# checked off but the suite is red — a cross-task regression, not incomplete
# coverage. The Ralph persona keys its repair increment off this prefix, so it
# must never be sniffed from raw pytest output. Distinct from the
# incomplete-coverage status line so the two "no selectable task" states
# (repair vs escalate-blocked) are unambiguous.
RALPH_REGRESSION_PREFIX = "Ralph regression —"


def _run_gate_pytest(test_path: str) -> tuple[int, str]:
    """Isolation-aware pytest run for a Coder gate: in-process on none/worktree,
    dispatched through the sandboxed coder-tools provider on container/sandbox
    (no tree ⇒ 'no tests collected' in either case). The gate runs immediately
    after the Coder stage in the same process, so Path.cwd() is the worktree —
    passed explicitly so the sandbox provider mounts/`-w`s the same tree the
    in-process branch would key off.
    """
    return run_gate_pytest(test_path, cwd=Path.cwd())


def _manifest_task_ids(state: State, manifest_key: str) -> list[str] | None:
    """Task ids from the `task_manifest` artifact — parsed core-safely (no persona
    import), returning None if the artifact is missing or malformed."""
    try:
        manifest = json.loads(state.artifacts.get(manifest_key, ""))
        return [entry["id"] for entry in manifest]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


@dataclass(frozen=True)
class RalphCoderGate:
    """Coverage-aware gate for the Ralph-loop Coder: green is necessary, not
    sufficient. ACCEPT requires **every** manifest task checked off in the
    `.agent/STATE.md` checklist AND a green pytest run. Every REVISE returns a
    single self-contained status finding so the accumulated-findings list stays
    authoritative-by-latest.
    """

    artifact_key: str = "implementation_reports"
    manifest_key: str = "task_manifest"
    test_path: str = "src"

    def __call__(self, state: State, stage_name: str) -> GateResult:
        content_gate = ArtifactGate(
            self.artifact_key, parse_json="object", require_nonempty_parse=True
        )
        content_result = content_gate(state, stage_name)
        if content_result.decision is not GateDecision.ACCEPT:
            return content_result

        task_ids = _manifest_task_ids(state, self.manifest_key)
        if task_ids is None:
            return GateResult(
                GateDecision.REVISE,
                findings=["task_manifest is missing or malformed; cannot gate Ralph coverage"],
            )

        reports: dict[str, str] = json.loads(state.artifacts[self.artifact_key])
        edit_findings = [
            f"{sprint_path}: {EDIT_FAILURES_HEADER.lstrip('# ')} recorded in the "
            "implementation report; re-emit the corrected blocks so they apply cleanly"
            for sprint_path, report in reports.items()
            if EDIT_FAILURES_HEADER in report
        ]
        if edit_findings:
            return GateResult(GateDecision.REVISE, findings=edit_findings)

        # Coverage: every manifest task must be checked off in .agent/STATE.md.
        done = set(read_scratchpad().completed_tasks)
        outstanding = [tid for tid in task_ids if tid not in done]
        if outstanding:
            return GateResult(
                GateDecision.REVISE,
                findings=[_status_finding(outstanding)],
            )

        exit_code, output = _run_gate_pytest(self.test_path)
        if exit_code == run_tests_tool.PYTEST_NO_TESTS_COLLECTED:
            return GateResult(
                GateDecision.REVISE,
                findings=[
                    "Ralph status — all tasks checked off but no tests were produced; "
                    f"the Global Definition of Done requires tests.\n{output}"
                ],
            )
        if exit_code != 0:
            # All tasks are checked off, yet the suite is red: a change regressed
            # a previously-passing test. This is NOT incomplete coverage, so it
            # carries the regression prefix that routes the persona to a repair
            # increment instead of the escalate-when-blocked path.
            return GateResult(
                GateDecision.REVISE,
                findings=[
                    f"{RALPH_REGRESSION_PREFIX} every manifest task is complete but the "
                    f"suite is red; a change regressed a previously-passing test "
                    f"(pytest exit {exit_code}):\n{output}"
                ],
            )
        return GateResult(GateDecision.ACCEPT)


def _status_finding(outstanding: list[str]) -> str:
    """Incomplete-coverage status: tasks remain (possibly all dep-blocked). The
    red-suite-with-all-tasks-done case uses `RALPH_REGRESSION_PREFIX` instead."""
    next_task = outstanding[0] if outstanding else "none"
    remaining = ", ".join(outstanding) if outstanding else "none"
    return (
        f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
        "Implement the next unit."
    )
