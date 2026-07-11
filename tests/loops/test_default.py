from loop_engine.core.coder_gate import RalphCoderGate
from loop_engine.core.engine import Loop
from loop_engine.core.gates import ArtifactGate
from loop_engine.loops.default.loop import DEFAULT_LOOP, build_default_loop
from loop_engine.personas.agile_sprint_breakdown.manifest import ManifestArtifactGate
from loop_engine.personas.coder_iac.ralph import RalphCoderPersona
from loop_engine.personas.declarative.node import (
    ArchitectureGenerator,
    PMGenerator,
    SprintBreakdownGenerator,
)
from loop_engine.personas.pm.critic_gate import CriticGate


def test_default_loop_is_four_stages_in_pipeline_order() -> None:
    assert isinstance(DEFAULT_LOOP, Loop)
    expected_types = [
        PMGenerator,
        ArchitectureGenerator,
        SprintBreakdownGenerator,
        RalphCoderPersona,
    ]
    assert [type(stage.persona) for stage in DEFAULT_LOOP.stages] == expected_types


def test_default_loop_escalation_ladder_routes_coder_through_architect_to_pm() -> None:
    coder_stage = DEFAULT_LOOP.stages[3]
    assert [type(r) for r in coder_stage.resolvers] == [ArchitectureGenerator, PMGenerator]

    architect_stage = DEFAULT_LOOP.stages[1]
    assert [type(r) for r in architect_stage.resolvers] == [PMGenerator]

    pm_stage = DEFAULT_LOOP.stages[0]
    assert pm_stage.resolvers == []  # PM escalates straight to the human


def test_default_loop_blast_radius_reentry_targets() -> None:
    assert DEFAULT_LOOP.impact_reentry == {"architecture": 1, "plan": 2}


def test_document_personas_are_the_generators_with_no_flag() -> None:
    # Phase 6: the declarative nodes are unconditional — no LOOP_ENGINE_PERSONAS,
    # no classic persona classes to fall back to.
    loop = build_default_loop()

    assert [type(s.persona) for s in loop.stages[:3]] == [
        PMGenerator,
        ArchitectureGenerator,
        SprintBreakdownGenerator,
    ]
    # PM stage carries the structural CriticGate (the PM critic *loop* retired;
    # the engine's revise loop supplies the cycle).
    assert isinstance(loop.stages[0].gate, CriticGate)
    # PM's revision budget restores the retired internal loop's cap, and an
    # unconverging PM escalates to the human instead of hard-failing (PM's only
    # resolver is the human, so a hard fail there is a dead end).
    assert loop.stages[0].max_revisions == 4
    assert loop.stages[0].escalate_on_exhaustion is True
    # The Architecture gate is the plain content gate.
    assert isinstance(loop.stages[1].gate, ArtifactGate)


def test_coder_is_the_ralph_loop_with_no_flag(monkeypatch) -> None:
    # Phase 6: Ralph is the only Coder — no LOOP_ENGINE_CODER, no classic
    # per-sprint Coder to fall back to.
    monkeypatch.setenv("LOOP_ENGINE_RALPH_MAX_ITERS", "12")
    loop = build_default_loop()

    coder_stage = loop.stages[3]
    assert isinstance(coder_stage.persona, RalphCoderPersona)
    assert isinstance(coder_stage.gate, RalphCoderGate)
    assert coder_stage.gate.artifact_key == "implementation_reports"
    # The Ralph self-loop bound is the Coder stage's max_revisions (iteration cap),
    # read at build time so a runtime override is honored.
    assert coder_stage.max_revisions == 12
    # Escalation ladder is unchanged.
    assert [type(r) for r in coder_stage.resolvers] == [ArchitectureGenerator, PMGenerator]


def test_sprint_breakdown_gate_is_manifest_aware(monkeypatch) -> None:
    # The Ralph gate checks the produced tree against the task_manifest, so the
    # Sprint-Breakdown stage must emit and validate one.
    assert isinstance(build_default_loop().stages[2].gate, ManifestArtifactGate)
