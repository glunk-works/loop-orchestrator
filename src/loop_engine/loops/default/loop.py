from loop_engine.core.coder_gate import RalphCoderGate
from loop_engine.core.engine import Loop, Stage
from loop_engine.core.gates import ArtifactGate
from loop_engine.personas.agile_sprint_breakdown.manifest import ManifestArtifactGate
from loop_engine.personas.coder_iac.mode import ralph_max_iterations
from loop_engine.personas.coder_iac.ralph import RalphCoderPersona
from loop_engine.personas.declarative.node import (
    ArchitectureGenerator,
    PMGenerator,
    SprintBreakdownGenerator,
)
from loop_engine.personas.pm.critic_gate import CriticGate


def build_default_loop() -> Loop:
    """The PM → Architect → Sprint Breakdown → Coder pipeline.

    One wiring, no flags (Phase 6 collapsed them):

    - The three document personas are the config-driven `GeneratorNode` ports,
      loading their prompts from `prompts/`.
    - The PM stage gate is the structural `CriticGate` — the PM critic *loop* is
      retired, and the engine's revise loop supplies the cycle its internal
      MAX_REVISION_CYCLES loop used to.
    - The Coder is the Ralph loop: one task per invocation, re-entering itself
      until the coverage-aware `RalphCoderGate` is green, with the
      Sprint-Breakdown stage emitting the `task_manifest` that gate checks
      against (hence `ManifestArtifactGate`).

    Still rebuilt per run rather than reused from `DEFAULT_LOOP`, so
    `ralph_max_iterations()` is read at run time, not baked in at import.
    """
    pm = PMGenerator()
    architect = ArchitectureGenerator()
    sprint_breakdown = SprintBreakdownGenerator()

    # The escalation ladder: Coder questions go to the Architect first, then the
    # PM; Architect and Sprint Breakdown questions go to the PM. PM questions
    # have no automated resolver — they go straight to the human via a GitHub
    # issue.
    return Loop(
        stages=[
            Stage(
                persona=pm,
                gate=CriticGate(),
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
                gate=ManifestArtifactGate(),
                resolvers=[architect, pm],
            ),
            Stage(
                # Evidence-based acceptance: content checks plus a deterministic
                # pytest run over the produced tree — a task is accepted on a
                # green test run, not on the model's say-so.
                persona=RalphCoderPersona(),
                gate=RalphCoderGate("implementation_reports"),
                resolvers=[architect, pm],
                # The Ralph self-loop bound: execute_stage re-enters the Coder
                # until the coverage-aware gate is green or this cap is hit.
                max_revisions=ralph_max_iterations(),
            ),
        ],
        # Blast-radius re-entry: "architecture" reruns the Architect (index 1)
        # and everything after it; "plan" reruns the Sprint Breakdown (index 2).
        impact_reentry={"architecture": 1, "plan": 2},
    )


DEFAULT_LOOP = build_default_loop()
