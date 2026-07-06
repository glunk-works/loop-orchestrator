from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import ArtifactGate
from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona
from loop_engine.personas.architecture.persona import ArchitecturePersona
from loop_engine.personas.coder_iac.persona import CoderIacPersona
from loop_engine.personas.pm.persona import PMPersona

_pm = PMPersona()
_architect = ArchitecturePersona()
_sprint_breakdown = AgileSprintBreakdownPersona()
_coder = CoderIacPersona()

# The escalation ladder: Coder questions go to the Architect first, then the
# PM; Architect and Sprint Breakdown questions go to the PM. PM questions
# have no automated resolver — they go straight to the human via a GitHub
# issue.
DEFAULT_LOOP = Loop(
    stages=[
        Stage(
            persona=_pm,
            gate=ArtifactGate("project_spec", parse_json="object", require_nonempty_parse=True),
        ),
        Stage(
            persona=_architect,
            gate=ArtifactGate("architecture_definition"),
            resolvers=[_pm],
        ),
        Stage(
            persona=_sprint_breakdown,
            gate=ArtifactGate("sprint_plans", parse_json="list", require_nonempty_parse=True),
            resolvers=[_architect, _pm],
        ),
        Stage(
            persona=_coder,
            gate=ArtifactGate(
                "implementation_reports", parse_json="object", require_nonempty_parse=True
            ),
            resolvers=[_architect, _pm],
        ),
    ],
    # Blast-radius re-entry: "architecture" reruns the Architect (index 1)
    # and everything after it; "plan" reruns the Sprint Breakdown (index 2).
    impact_reentry={"architecture": 1, "plan": 2},
)
