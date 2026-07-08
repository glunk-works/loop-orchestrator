from loop_engine.core.coder_gate import CoderGate, RalphCoderGate
from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import ArtifactGate
from loop_engine.personas.agile_sprint_breakdown.manifest import ManifestArtifactGate
from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona
from loop_engine.personas.architecture.persona import ArchitecturePersona
from loop_engine.personas.coder_iac.mode import ralph_max_iterations, use_ralph_coder
from loop_engine.personas.coder_iac.persona import CoderIacPersona
from loop_engine.personas.coder_iac.ralph import RalphCoderPersona
from loop_engine.personas.pm.persona import PMPersona


def build_default_loop() -> Loop:
    """The PM → Architect → Sprint Breakdown → Coder pipeline.

    Under `LOOP_ENGINE_CODER=ralph` the Coder stage is the Ralph loop
    (one task per invocation, self-looping via `execute_stage`'s revise loop —
    the stage's `max_revisions` is the iteration cap) and the Sprint-Breakdown
    stage additionally validates the `task_manifest`. Default (`classic`) wiring
    is byte-identical to the pre-Ralph loop. Read at call time so the flag is
    honored at run time (like engine/tool selection), not baked in at import.
    """
    pm = PMPersona()
    architect = ArchitecturePersona()
    sprint_breakdown = AgileSprintBreakdownPersona()
    ralph = use_ralph_coder()

    sprint_gate = (
        ManifestArtifactGate()
        if ralph
        else ArtifactGate("sprint_plans", parse_json="list", require_nonempty_parse=True)
    )
    if ralph:
        coder_stage = Stage(
            persona=RalphCoderPersona(),
            gate=RalphCoderGate("implementation_reports"),
            resolvers=[architect, pm],
            # The Ralph self-loop bound: execute_stage re-enters the Coder until
            # the coverage-aware gate is green or this iteration cap is hit.
            max_revisions=ralph_max_iterations(),
        )
    else:
        coder_stage = Stage(
            # Evidence-based acceptance: content checks plus a deterministic
            # pytest run over the produced tree — a sprint is accepted on a
            # green test run, not on the model's say-so.
            persona=CoderIacPersona(),
            gate=CoderGate("implementation_reports"),
            resolvers=[architect, pm],
        )

    # The escalation ladder: Coder questions go to the Architect first, then the
    # PM; Architect and Sprint Breakdown questions go to the PM. PM questions
    # have no automated resolver — they go straight to the human via a GitHub
    # issue.
    return Loop(
        stages=[
            Stage(
                persona=pm,
                gate=ArtifactGate("project_spec", parse_json="object", require_nonempty_parse=True),
            ),
            Stage(
                persona=architect,
                gate=ArtifactGate("architecture_definition"),
                resolvers=[pm],
            ),
            Stage(
                persona=sprint_breakdown,
                gate=sprint_gate,
                resolvers=[architect, pm],
            ),
            coder_stage,
        ],
        # Blast-radius re-entry: "architecture" reruns the Architect (index 1)
        # and everything after it; "plan" reruns the Sprint Breakdown (index 2).
        impact_reentry={"architecture": 1, "plan": 2},
    )


# Built once at import with the flag defaulting to `classic`; the CLI resolves
# the loop at run time via build_default_loop() so a runtime flag is honored.
DEFAULT_LOOP = build_default_loop()
