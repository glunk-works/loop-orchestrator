from loop_engine.core.coder_gate import CoderGate, RalphCoderGate
from loop_engine.core.engine import Loop
from loop_engine.core.gates import ArtifactGate
from loop_engine.loops.default.loop import DEFAULT_LOOP, build_default_loop
from loop_engine.personas.agile_sprint_breakdown.manifest import ManifestArtifactGate
from loop_engine.personas.coder_iac.persona import CoderIacPersona
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
        CoderIacPersona,
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


def test_document_personas_are_the_generators_with_no_flag(monkeypatch) -> None:
    # Phase 6: the declarative nodes are unconditional — no LOOP_ENGINE_PERSONAS,
    # no classic persona classes to fall back to.
    monkeypatch.delenv("LOOP_ENGINE_CODER", raising=False)
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
    # Architecture/Sprint gates are the plain content gates.
    assert isinstance(loop.stages[1].gate, ArtifactGate)
    assert isinstance(loop.stages[2].gate, ArtifactGate)


def test_coder_is_classic_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LOOP_ENGINE_CODER", raising=False)
    loop = build_default_loop()

    coder_stage = loop.stages[3]
    assert isinstance(coder_stage.persona, CoderIacPersona)
    assert isinstance(coder_stage.gate, CoderGate)
    assert coder_stage.gate.artifact_key == "implementation_reports"
    assert coder_stage.max_revisions == 2
    # The Sprint-Breakdown gate is the plain content gate, not manifest-aware.
    assert not isinstance(loop.stages[2].gate, ManifestArtifactGate)


def test_coder_uses_ralph_wiring_under_flag(monkeypatch) -> None:
    monkeypatch.setenv("LOOP_ENGINE_CODER", "ralph")
    monkeypatch.setenv("LOOP_ENGINE_RALPH_MAX_ITERS", "12")
    loop = build_default_loop()

    coder_stage = loop.stages[3]
    assert isinstance(coder_stage.persona, RalphCoderPersona)
    assert isinstance(coder_stage.gate, RalphCoderGate)
    # The Ralph self-loop bound is the Coder stage's max_revisions (iteration cap).
    assert coder_stage.max_revisions == 12
    # Escalation ladder is unchanged.
    assert [type(r) for r in coder_stage.resolvers] == [ArchitectureGenerator, PMGenerator]
    # The Sprint-Breakdown stage now validates the task_manifest.
    assert isinstance(loop.stages[2].gate, ManifestArtifactGate)
