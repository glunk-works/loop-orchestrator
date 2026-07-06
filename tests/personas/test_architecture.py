from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import Question, State
from loop_engine.personas.architecture.persona import ArchitecturePersona


def _state(artifacts: dict[str, str]) -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts=artifacts)


def test_architecture_persona_raises_key_error_when_project_spec_missing() -> None:
    mock_llm_client = MagicMock()

    with pytest.raises(KeyError):
        ArchitecturePersona().run(_state({}), mock_llm_client)


def test_architecture_persona_returns_populated_architecture_definition() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text="# Architecture Definition\n...")

    result_state = ArchitecturePersona().run(
        _state({"project_spec": '{"problem_statement": "x"}'}), mock_llm_client
    )

    assert result_state.artifacts["architecture_definition"] == "# Architecture Definition\n..."


def test_architecture_persona_includes_findings_in_revision_prompt() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text="# Revised")

    ArchitecturePersona().run(
        _state({"project_spec": "{}"}),
        mock_llm_client,
        findings=["Resolution: use eu-west-1 only"],
    )

    prompt = mock_llm_client.call.call_args.args[0]
    assert "Resolution: use eu-west-1 only" in prompt


def test_architecture_persona_resolves_coder_questions_from_document() -> None:
    state = _state({"architecture_definition": "# Arch\n\nAll compute in eu-west-1."})
    questions = [Question(id="q1", origin_stage="CoderIacPersona", text="Which region?")]

    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(
        text='{"q1": {"resolution": "eu-west-1", "impact": "task"}}'
    )

    resolved = ArchitecturePersona().resolve_questions(questions, state, mock_llm_client)

    assert resolved[0].resolution == "eu-west-1"
    assert resolved[0].resolved_by == "architect"
    assert resolved[0].impact == "task"


def test_architecture_persona_resolver_leaves_unanswerable_untouched() -> None:
    state = _state({"architecture_definition": "# Arch"})
    questions = [Question(id="q1", origin_stage="CoderIacPersona", text="Budget ceiling?")]

    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text='{"q1": null}')

    resolved = ArchitecturePersona().resolve_questions(questions, state, mock_llm_client)

    assert resolved[0].resolution is None
    assert resolved[0].resolved_by is None


def test_architecture_persona_resolver_with_no_document_resolves_nothing() -> None:
    questions = [Question(id="q1", origin_stage="CoderIacPersona", text="Which region?")]
    mock_llm_client = MagicMock()

    resolved = ArchitecturePersona().resolve_questions(questions, _state({}), mock_llm_client)

    assert resolved == questions
    mock_llm_client.call.assert_not_called()
