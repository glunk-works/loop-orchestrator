from loop_engine.core.coder_gate import CoderGate, RalphCoderGate
from loop_engine.core.engine import Loop
from loop_engine.loops.default.loop import DEFAULT_LOOP, build_default_loop
from loop_engine.personas.agile_sprint_breakdown.manifest import ManifestArtifactGate
from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona
from loop_engine.personas.architecture.persona import ArchitecturePersona
from loop_engine.personas.coder_iac.persona import CoderIacPersona
from loop_engine.personas.coder_iac.ralph import RalphCoderPersona
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
