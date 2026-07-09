from loop_engine.core.coder_gate import CoderGate, RalphCoderGate
from loop_engine.core.engine import Loop
from loop_engine.core.gates import ArtifactGate
from loop_engine.loops.default.loop import DEFAULT_LOOP, build_default_loop
from loop_engine.personas.agile_sprint_breakdown.manifest import ManifestArtifactGate
from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona
from loop_engine.personas.architecture.persona import ArchitecturePersona
from loop_engine.personas.coder_iac.persona import CoderIacPersona
from loop_engine.personas.coder_iac.ralph import RalphCoderPersona
from loop_engine.personas.declarative.node import (
    ArchitectureGenerator,
    PMGenerator,
    SprintBreakdownGenerator,
)
from loop_engine.personas.pm.critic_gate import CriticGate
from loop_engine.personas.pm.persona import PMPersona


def test_default_loop_is_four_stages_in_pipeline_order() -> None:
    assert isinstance(DEFAULT_LOOP, Loop)
    expected_types = [
        PMPersona,
        ArchitecturePersona,
        AgileSprintBreakdownPersona,
        CoderIacPersona,
    ]
    assert [type(stage.persona) for stage in DEFAULT_LOOP.stages] == expected_types


def test_default_loop_escalation_ladder_routes_coder_through_architect_to_pm() -> None:
    coder_stage = DEFAULT_LOOP.stages[3]
    assert [type(r) for r in coder_stage.resolvers] == [ArchitecturePersona, PMPersona]

    architect_stage = DEFAULT_LOOP.stages[1]
    assert [type(r) for r in architect_stage.resolvers] == [PMPersona]

    pm_stage = DEFAULT_LOOP.stages[0]
    assert pm_stage.resolvers == []  # PM escalates straight to the human


def test_default_loop_blast_radius_reentry_targets() -> None:
    assert DEFAULT_LOOP.impact_reentry == {"architecture": 1, "plan": 2}


def test_default_loop_coder_stage_uses_the_evidence_gate() -> None:
    coder_stage = DEFAULT_LOOP.stages[3]
    assert isinstance(coder_stage.gate, CoderGate)
    assert coder_stage.gate.artifact_key == "implementation_reports"


def test_build_default_loop_is_classic_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LOOP_ENGINE_CODER", raising=False)
    loop = build_default_loop()
    coder_stage = loop.stages[3]
    assert isinstance(coder_stage.persona, CoderIacPersona)
    assert isinstance(coder_stage.gate, CoderGate)
    assert coder_stage.max_revisions == 2
    # The Sprint-Breakdown gate is the plain content gate, not manifest-aware.
    assert not isinstance(loop.stages[2].gate, ManifestArtifactGate)


def test_build_default_loop_uses_ralph_wiring_under_flag(monkeypatch) -> None:
    monkeypatch.setenv("LOOP_ENGINE_CODER", "ralph")
    monkeypatch.setenv("LOOP_ENGINE_RALPH_MAX_ITERS", "12")
    loop = build_default_loop()

    coder_stage = loop.stages[3]
    assert isinstance(coder_stage.persona, RalphCoderPersona)
    assert isinstance(coder_stage.gate, RalphCoderGate)
    # The Ralph self-loop bound is the Coder stage's max_revisions (iteration cap).
    assert coder_stage.max_revisions == 12
    # Escalation ladder is unchanged.
    assert [type(r) for r in coder_stage.resolvers] == [ArchitecturePersona, PMPersona]
    # The Sprint-Breakdown stage now validates the task_manifest.
    assert isinstance(loop.stages[2].gate, ManifestArtifactGate)


def test_build_default_loop_classic_personas_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LOOP_ENGINE_PERSONAS", raising=False)
    loop = build_default_loop()
    assert [type(s.persona) for s in loop.stages[:3]] == [
        PMPersona,
        ArchitecturePersona,
        AgileSprintBreakdownPersona,
    ]
    # PM gate is the plain content gate on the classic path.
    assert isinstance(loop.stages[0].gate, ArtifactGate)
    assert not isinstance(loop.stages[0].gate, CriticGate)
    # The flags are wired unconditionally but inert for classic: its PM gate
    # never returns REVISE, so neither can ever fire.
    assert loop.stages[0].max_revisions == 4
    assert loop.stages[0].escalate_on_exhaustion is True


def test_build_default_loop_uses_declarative_personas_under_flag(monkeypatch) -> None:
    monkeypatch.setenv("LOOP_ENGINE_PERSONAS", "declarative")
    monkeypatch.delenv("LOOP_ENGINE_CODER", raising=False)
    loop = build_default_loop()

    assert [type(s.persona) for s in loop.stages[:3]] == [
        PMGenerator,
        ArchitectureGenerator,
        SprintBreakdownGenerator,
    ]
    # PM stage carries the structural CriticGate.
    assert isinstance(loop.stages[0].gate, CriticGate)
    # PM's revision budget restores the retired internal loop's cap, and an
    # unconverging PM escalates to the human instead of hard-failing (PM's
    # only resolver is the human).
    assert loop.stages[0].max_revisions == 4
    assert loop.stages[0].escalate_on_exhaustion is True
    # Architecture/Sprint gates unchanged (declarative output is byte-identical).
    assert isinstance(loop.stages[1].gate, ArtifactGate)
    assert isinstance(loop.stages[2].gate, ArtifactGate)
    # Escalation ladder still wires the declarative ports as resolvers.
    assert [type(r) for r in loop.stages[3].resolvers] == [
        ArchitectureGenerator,
        PMGenerator,
    ]
    # The Coder stays classic (its own flag is off).
    assert isinstance(loop.stages[3].persona, CoderIacPersona)


def test_declarative_personas_compose_with_ralph_coder(monkeypatch) -> None:
    monkeypatch.setenv("LOOP_ENGINE_PERSONAS", "declarative")
    monkeypatch.setenv("LOOP_ENGINE_CODER", "ralph")
    loop = build_default_loop()
    assert isinstance(loop.stages[0].persona, PMGenerator)
    assert isinstance(loop.stages[0].gate, CriticGate)
    assert isinstance(loop.stages[2].gate, ManifestArtifactGate)
    assert isinstance(loop.stages[3].persona, RalphCoderPersona)
