"""Architecture: declarative GeneratorNode is a strict byte-parity port."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from loop_engine.core.state import Question, State
from loop_engine.personas.architecture.persona import ArchitecturePersona
from loop_engine.personas.declarative.node import ArchitectureGenerator


def _state(artifacts: dict[str, str]) -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts=artifacts)


def _mock(text: str) -> MagicMock:
    m = MagicMock()
    m.call.return_value = SimpleNamespace(text=text)
    m.call_messages.return_value = SimpleNamespace(text=text)
    return m


SPEC = '{"problem_statement": "build a thing"}'
RESP = "# Architecture Definition\n\n1. Context.\n\n## Open Questions\n\n1. Which region?\n"


def test_initial_generation_byte_identical() -> None:
    classic = ArchitecturePersona().run(_state({"project_spec": SPEC}), _mock(RESP))
    declarative = ArchitectureGenerator().run(_state({"project_spec": SPEC}), _mock(RESP))
    assert (
        declarative.artifacts["architecture_definition"]
        == classic.artifacts["architecture_definition"]
        == RESP
    )


def test_initial_system_blocks_identical() -> None:
    cm, dm = _mock(RESP), _mock(RESP)
    ArchitecturePersona().run(_state({"project_spec": SPEC}), cm)
    ArchitectureGenerator().run(_state({"project_spec": SPEC}), dm)
    assert dm.call.call_args.kwargs["system_blocks"] == cm.call.call_args.kwargs["system_blocks"]
    # And the user prompt (volatile turn) matches too.
    assert dm.call.call_args.args[0] == cm.call.call_args.args[0]


PRIOR = (
    "# Architecture\n\n1. Overview.\n\n"
    "## Assumptions\n\n- Single region.\n\n"
    "## Open Questions\n\nNone.\n"
)
CORRECTION = "## Assumptions\n\n- Deployed to eu-west-1 only.\n"


def test_section_merge_revision_byte_identical() -> None:
    findings = ["Resolution: use eu-west-1 only"]
    classic = ArchitecturePersona().run(
        _state({"project_spec": SPEC, "architecture_definition": PRIOR}),
        _mock(CORRECTION),
        findings=findings,
    )
    declarative = ArchitectureGenerator().run(
        _state({"project_spec": SPEC, "architecture_definition": PRIOR}),
        _mock(CORRECTION),
        findings=findings,
    )
    assert (
        declarative.artifacts["architecture_definition"]
        == classic.artifacts["architecture_definition"]
    )


def test_section_merge_three_turn_messages_identical() -> None:
    findings = ["Resolution: use eu-west-1 only"]
    cm, dm = _mock(CORRECTION), _mock(CORRECTION)
    ArchitecturePersona().run(
        _state({"project_spec": SPEC, "architecture_definition": PRIOR}), cm, findings=findings
    )
    ArchitectureGenerator().run(
        _state({"project_spec": SPEC, "architecture_definition": PRIOR}), dm, findings=findings
    )
    assert dm.call_messages.call_args.args[0] == cm.call_messages.call_args.args[0]
    assert (
        dm.call_messages.call_args.kwargs["system_blocks"]
        == cm.call_messages.call_args.kwargs["system_blocks"]
    )


def test_cache_stable_system_blocks_across_attempts() -> None:
    dm = _mock(CORRECTION)
    node = ArchitectureGenerator()
    node.run(_state({"project_spec": SPEC}), dm)
    initial_blocks = dm.call.call_args.kwargs["system_blocks"]
    dm2 = _mock(CORRECTION)
    node.run(
        _state({"project_spec": SPEC, "architecture_definition": PRIOR}),
        dm2,
        findings=["fix it"],
    )
    revision_blocks = dm2.call_messages.call_args.kwargs["system_blocks"]
    assert initial_blocks == revision_blocks


def test_resolver_parity() -> None:
    state = _state({"architecture_definition": "# Arch\n\nAll compute in eu-west-1."})
    questions = [Question(id="q1", origin_stage="CoderIacPersona", text="Which region?")]
    verdict = '{"q1": {"resolution": "eu-west-1", "impact": "task"}}'

    classic = ArchitecturePersona().resolve_questions(questions, state, _mock(verdict))
    declarative = ArchitectureGenerator().resolve_questions(questions, state, _mock(verdict))
    assert declarative[0].resolution == classic[0].resolution == "eu-west-1"
    assert declarative[0].resolved_by == classic[0].resolved_by == "architect"
    assert declarative[0].impact == classic[0].impact == "task"


def test_consumes_produces_match() -> None:
    node = ArchitectureGenerator()
    assert node.consumes == ("project_spec",)
    assert node.produces == ("architecture_definition",)
