"""GeneratorNode: generic single-shot behaviors independent of a specific port."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_orchestrator.core.state import Question, State
from loop_orchestrator.personas.declarative.config import load_named_config
from loop_orchestrator.personas.declarative.node import (
    ArchitectureGenerator,
    GeneratorNode,
    PMGenerator,
    SprintBreakdownGenerator,
)


def _state(artifacts: dict[str, str]) -> State:
    return State(schema_version=2, run_id="r", stage_history=[], artifacts=artifacts)


def _mock(text: str) -> MagicMock:
    m = MagicMock()
    m.call.return_value = SimpleNamespace(text=text)
    m.call_messages.return_value = SimpleNamespace(text=text)
    return m


def test_generator_node_produces_markdown_artifact_from_config() -> None:
    node = GeneratorNode(load_named_config("architecture"))
    result = node.run(_state({"project_spec": "{}"}), _mock("# Doc"))
    assert result.artifacts["architecture_definition"] == "# Doc"


def test_distinct_ports_have_distinct_stage_names() -> None:
    # Each port must have its own type name so the engine gives it its own
    # escalation counter / question origin (no cross-stage contamination).
    names = {
        type(PMGenerator()).__name__,
        type(ArchitectureGenerator()).__name__,
        type(SprintBreakdownGenerator()).__name__,
    }
    assert len(names) == 3


def test_construction_validates_strategy_names(monkeypatch) -> None:
    cfg = load_named_config("architecture")
    bad = cfg.model_copy(update={"output_adapter": "bogus"})
    with pytest.raises(ValueError, match="unknown output-adapter"):
        GeneratorNode(bad)


def test_resolver_absent_returns_questions_unchanged() -> None:
    # Sprint Breakdown config has no resolver ⇒ BasePersona default behavior.
    node = SprintBreakdownGenerator()
    questions = [Question(id="q1", origin_stage="X", text="?")]
    llm = MagicMock()
    assert node.resolve_questions(questions, _state({}), llm) == questions
    llm.call.assert_not_called()


def test_resolver_present_invokes_document_resolution() -> None:
    node = ArchitectureGenerator()
    state = _state({"architecture_definition": "# Arch body"})
    questions = [Question(id="q1", origin_stage="CoderIacPersona", text="?")]
    llm = _mock('{"q1": {"resolution": "eu-west-1", "impact": "task"}}')
    resolved = node.resolve_questions(questions, state, llm)
    assert resolved[0].resolution == "eu-west-1"
