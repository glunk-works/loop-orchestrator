from loop_engine.core.coder_gate import CoderGate, RalphCoderGate
from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import ArtifactGate
from loop_engine.personas.agile_sprint_breakdown.manifest import ManifestArtifactGate
from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona
from loop_engine.personas.architecture.persona import ArchitecturePersona
from loop_engine.personas.coder_iac.mode import ralph_max_iterations, use_ralph_coder
from loop_engine.personas.coder_iac.persona import CoderIacPersona
from loop_engine.personas.coder_iac.ralph import RalphCoderPersona
from loop_engine.personas.declarative.mode import use_declarative_personas
from loop_engine.personas.declarative.node import (
    ArchitectureGenerator,
    PMGenerator,
    SprintBreakdownGenerator,
)
from loop_engine.personas.pm.critic_gate import CriticGate
from loop_engine.personas.pm.persona import PMPersona


def build_default_loop() -> Loop:
    """The PM → Architect → Sprint Breakdown → Coder pipeline.

    Two independent runtime flags shape the wiring, read at call time so they are
    honored at run time (not baked in at import):

    - `LOOP_ENGINE_PERSONAS=declarative` swaps the three document personas (PM,
      Architecture, Sprint Breakdown) for their config-driven `GeneratorNode`
      ports and swaps the PM stage gate for the structural `CriticGate` (the PM
      critic *loop* retired). Architecture/Sprint output is byte-identical, so
      their gates are unchanged. Default (`classic`) keeps the persona classes.
    - `LOOP_ENGINE_CODER=ralph` makes the Coder a Ralph loop and the
      Sprint-Breakdown gate manifest-aware. Default (`classic`) is the per-sprint
      Coder.

    The two flags compose (`declarative` personas × `ralph` Coder is valid).
    """
    declarative = use_declarative_personas()
    ralph = use_ralph_coder()

    if declarative:
        pm = PMGenerator()
        architect = ArchitectureGenerator()
        sprint_breakdown = SprintBreakdownGenerator()
        # The PM critic checks now drive the stage gate; the engine's revise loop
        # supplies the cycle the internal MAX_REVISION_CYCLES loop used to.
        pm_gate = CriticGate()
    else:
        pm = PMPersona()
        architect = ArchitecturePersona()
        sprint_breakdown = AgileSprintBreakdownPersona()
        pm_gate = ArtifactGate("project_spec", parse_json="object", require_nonempty_parse=True)

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
                # fail there is a dead end. Inert for classic: its PM gate
                # (ArtifactGate) never returns REVISE, so neither flag fires.
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


# Built once at import with both flags defaulting off; the CLI resolves the loop
# at run time via build_default_loop() so runtime flags are honored.
DEFAULT_LOOP = build_default_loop()
