from loop_engine.loops.default.loop import DEFAULT_LOOP
from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona
from loop_engine.personas.architecture.persona import ArchitecturePersona
from loop_engine.personas.base import BasePersona
from loop_engine.personas.coder_iac.persona import CoderIacPersona
from loop_engine.personas.pm.persona import PMPersona


def test_default_loop_is_four_personas_in_pipeline_order() -> None:
    assert isinstance(DEFAULT_LOOP, list)
    assert len(DEFAULT_LOOP) == 4
    assert all(isinstance(persona, BasePersona) for persona in DEFAULT_LOOP)

    expected_types = [
        PMPersona,
        ArchitecturePersona,
        AgileSprintBreakdownPersona,
        CoderIacPersona,
    ]
    assert [type(persona) for persona in DEFAULT_LOOP] == expected_types
