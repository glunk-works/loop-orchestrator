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


def test_architecture_persona_puts_template_and_spec_in_cached_system_blocks() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text="# Architecture Definition\n...")

    ArchitecturePersona().run(
        _state({"project_spec": '{"problem_statement": "x"}'}), mock_llm_client
    )

    system_blocks = mock_llm_client.call.call_args.kwargs["system_blocks"]
    assert any("Expert Cloud and Security Architect" in block for block in system_blocks)
    assert any('{"problem_statement": "x"}' in block for block in system_blocks)
    # The volatile user prompt carries no copy of the artifact.
    assert '{"problem_statement": "x"}' not in mock_llm_client.call.call_args.args[0]


def test_architecture_persona_includes_findings_in_revision_prompt() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text="# Revised")

    ArchitecturePersona().run(
        _state({"project_spec": "{}"}),
        mock_llm_client,
        findings=["Resolution: use eu-west-1 only"],
    )

    # Findings are volatile: they live in the user prompt, never in the
    # cached system blocks (byte-identical prefix across attempts).
    prompt = mock_llm_client.call.call_args.args[0]
    assert "Resolution: use eu-west-1 only" in prompt
    system_blocks = mock_llm_client.call.call_args.kwargs["system_blocks"]
    assert all("eu-west-1" not in block for block in system_blocks)


PRIOR_ARCHITECTURE = (
    "# Architecture\n\n1. Overview.\n\n"
    "## Assumptions\n\n- Single region.\n\n"
    "## Open Questions\n\nNone.\n"
)


def test_architecture_persona_revises_prior_artifact_via_three_turn_call() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call_messages.return_value = SimpleNamespace(
        text="## Assumptions\n\n- Deployed to eu-west-1 only.\n"
    )

    result_state = ArchitecturePersona().run(
        _state({"project_spec": "{}", "architecture_definition": PRIOR_ARCHITECTURE}),
        mock_llm_client,
        findings=["Resolution: use eu-west-1 only"],
    )

    # Three-turn shape: attempt-1 instruction, prior artifact, findings.
    mock_llm_client.call.assert_not_called()
    messages = mock_llm_client.call_messages.call_args.args[0]
    assert [m["role"] for m in messages] == ["user", "assistant", "user"]
    assert messages[1]["content"] == PRIOR_ARCHITECTURE
    assert "Resolution: use eu-west-1 only" in messages[2]["content"]
    assert "ONLY the corrected sections" in messages[2]["content"]

    # Only the flagged section changed; everything else is byte-identical.
    revised = result_state.artifacts["architecture_definition"]
    assert "- Deployed to eu-west-1 only." in revised
    assert "- Single region." not in revised
    assert revised.startswith("# Architecture\n\n1. Overview.\n\n")
    assert "## Open Questions\n\nNone.\n" in revised


def test_architecture_persona_regenerates_fully_when_no_prior_artifact() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = SimpleNamespace(text="# Fresh document")

    ArchitecturePersona().run(
        _state({"project_spec": "{}"}),
        mock_llm_client,
        findings=["Resolution: use eu-west-1 only"],
    )

    # No prior artifact to merge into: single-turn full generation.
    mock_llm_client.call_messages.assert_not_called()
    assert "Resolution: use eu-west-1 only" in mock_llm_client.call.call_args.args[0]


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
