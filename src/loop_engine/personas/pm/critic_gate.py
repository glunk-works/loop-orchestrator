"""Structural gate carrying the PM critic *checks* (Phase 4 · part 2).

The classic `PMPersona.run` owned a `MAX_REVISION_CYCLES` followup loop with
hand-rolled no-progress detection. That is misplaced control flow: *personas
generate, gates accept, the graph routes*. This gate re-expresses `critic.review`
as a stage gate so the engine's existing revise loop drives re-extraction and
its identical-findings→escalate is the no-progress detector.

Kept out of `core/` (the import-boundary test forbids `core` importing any
persona module but `base`) — this is the "core-safe home" the plan calls for,
the same pattern as `agile_sprint_breakdown/manifest.ManifestArtifactGate`. It
imports the pure `critic.review` checks, never the `PMPersona` class.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property

from loop_engine.core.gates import ArtifactGate, GateDecision, GateResult
from loop_engine.core.state import State
from loop_engine.personas.pm import critic


def _finding_line(finding: critic.CriticFinding) -> str:
    # Matches classic `_format_findings` per-item shape (`field: issue`), so the
    # key_merge followup prompt the declarative PM builds is unchanged.
    return f"{finding.field}: {finding.issue}"


@dataclass(frozen=True)
class CriticGate:
    """Content gate for `project_spec`, then the PM critic checks.

    Composes the plain `ArtifactGate` (non-empty JSON object, plus its Open
    Questions escalation) exactly as `CoderGate`/`ManifestArtifactGate` do, then
    runs `critic.review` on the parsed spec: any findings ⇒ REVISE naming each
    blank/vague field; none ⇒ ACCEPT.
    """

    artifact_key: str = "project_spec"

    @cached_property
    def _content_gate(self) -> ArtifactGate:
        return ArtifactGate(self.artifact_key, parse_json="object", require_nonempty_parse=True)

    def __call__(self, state: State, stage_name: str) -> GateResult:
        content_result = self._content_gate(state, stage_name)
        if content_result.decision is not GateDecision.ACCEPT:
            return content_result

        spec = json.loads(state.artifacts[self.artifact_key])
        findings = critic.review(spec)
        if findings:
            return GateResult(GateDecision.REVISE, findings=[_finding_line(f) for f in findings])
        return GateResult(GateDecision.ACCEPT)
