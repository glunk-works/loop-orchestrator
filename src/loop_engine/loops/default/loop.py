from loop_engine.core.coder_gate import CoderGate, RalphCoderGate
from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import ArtifactGate
from loop_engine.personas.agile_sprint_breakdown.manifest import ManifestArtifactGate
from loop_engine.personas.coder_iac.mode import ralph_max_iterations, use_ralph_coder
from loop_engine.personas.coder_iac.persona import CoderIacPersona
from loop_engine.personas.coder_iac.ralph import RalphCoderPersona
from loop_engine.personas.declarative.node import (
    ArchitectureGenerator,
    PMGenerator,
    SprintBreakdownGenerator,
)
from loop_engine.personas.pm.critic_gate import CriticGate


def build_default_loop() -> Loop:
    """The PM → Architect → Sprint Breakdown → Coder pipeline.

    The three document personas (PM, Architecture, Sprint Breakdown) are the
    config-driven `GeneratorNode` ports, and the PM stage gate is the structural
    `CriticGate` (the PM critic *loop* is retired — the engine's revise loop
    supplies the cycle its internal MAX_REVISION_CYCLES loop used to).

    One runtime flag still shapes the wiring, read at call time so it is honored
    at run time (not baked in at import):

    - `LOOP_ENGINE_CODER=ralph` makes the Coder a Ralph loop and the
      Sprint-Breakdown gate manifest-aware. Default (`classic`) is the per-sprint
      Coder.
    """
    ralph = use_ralph_coder()

    pm = PMGenerator()
    architect = ArchitectureGenerator()
    sprint_breakdown = SprintBreakdownGenerator()
    pm_gate = CriticGate()

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
                gate=pm_gate,
                # Restores the retired PM internal loop's MAX_REVISION_CYCLES
                # cap (the engine's implicit default of 2 silently halved it),
                # and escalates to the human on an unconverging PM instead of
                # hard-failing — PM's only resolver is the human, so a hard
                # fail there is a dead end.
                max_revisions=4,
                escalate_on_exhaustion=True,
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


# Built once at import with the Coder flag defaulting off; the CLI resolves the
# loop at run time via build_default_loop() so the runtime flag is honored.
DEFAULT_LOOP = build_default_loop()
