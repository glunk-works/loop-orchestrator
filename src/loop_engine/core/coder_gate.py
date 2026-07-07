"""Evidence-based gate for the Coder stage.

The content ArtifactGate checks the reports artifact's shape; this gate then
executes the produced tests deterministically, so ACCEPT is based on a green
pytest run — evidence — not on the model's claim that the work is done.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from loop_engine.core.gates import ArtifactGate, GateDecision, GateResult
from loop_engine.core.state import State
from loop_engine.tools.coder_tools import run_tests as run_tests_tool

# The persona appends this section to a report when model-emitted edit
# blocks failed to apply; its presence is a deterministic REVISE signal.
EDIT_FAILURES_HEADER = "## Edit Application Failures"


def _last_reported_sprint(state: State, reports: dict[str, str]) -> str:
    """The most recently executed sprint: sprints run in plan order, so the
    last plan entry holding a report is where a red test run is attributed
    (and therefore which sprint the persona re-runs)."""
    try:
        plan_order = [block["path"] for block in json.loads(state.artifacts["sprint_plans"])]
    except (KeyError, json.JSONDecodeError, TypeError):
        plan_order = []
    for sprint_path in reversed(plan_order):
        if sprint_path in reports:
            return sprint_path
    return next(reversed(reports), "unknown-sprint")


@dataclass(frozen=True)
class CoderGate:
    """Content checks, then a deterministic pytest run before ACCEPT."""

    artifact_key: str = "implementation_reports"
    test_path: str = "src"

    def __call__(self, state: State, stage_name: str) -> GateResult:
        content_gate = ArtifactGate(
            self.artifact_key, parse_json="object", require_nonempty_parse=True
        )
        content_result = content_gate(state, stage_name)
        if content_result.decision is not GateDecision.ACCEPT:
            return content_result

        reports: dict[str, str] = json.loads(state.artifacts[self.artifact_key])

        # Edit blocks that failed to apply are already a known defect with
        # exact sprint attribution — no point paying for a test run first.
        edit_findings = [
            f"{sprint_path}: {EDIT_FAILURES_HEADER.lstrip('# ')} recorded in the "
            "implementation report; re-emit the corrected blocks so they apply cleanly"
            for sprint_path, report in reports.items()
            if EDIT_FAILURES_HEADER in report
        ]
        if edit_findings:
            return GateResult(GateDecision.REVISE, findings=edit_findings)

        blamed_sprint = _last_reported_sprint(state, reports)

        if not Path(self.test_path).exists():
            exit_code: int = run_tests_tool.PYTEST_NO_TESTS_COLLECTED
            output = f"no {self.test_path}/ tree was produced"
        else:
            exit_code, output = run_tests_tool.run_pytest(self.test_path)

        if exit_code == run_tests_tool.PYTEST_NO_TESTS_COLLECTED:
            return GateResult(
                GateDecision.REVISE,
                findings=[
                    f"{blamed_sprint}: no tests were produced; the Global "
                    f"Definition of Done requires tests.\n{output}"
                ],
            )
        if exit_code != 0:
            return GateResult(
                GateDecision.REVISE,
                findings=[
                    f"{blamed_sprint}: the produced tests fail (pytest exit "
                    f"code {exit_code}):\n{output}"
                ],
            )
        return GateResult(GateDecision.ACCEPT)
