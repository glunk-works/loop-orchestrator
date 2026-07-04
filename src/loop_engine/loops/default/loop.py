from loop_engine.personas.agile_sprint_breakdown.persona import AgileSprintBreakdownPersona
from loop_engine.personas.architecture.persona import ArchitecturePersona
from loop_engine.personas.base import BasePersona
from loop_engine.personas.coder_iac.persona import CoderIacPersona
from loop_engine.personas.pm.persona import PMPersona

DEFAULT_LOOP: list[BasePersona] = [
    PMPersona(),
    ArchitecturePersona(),
    AgileSprintBreakdownPersona(),
    CoderIacPersona(),
]
