import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from loop_engine.core.state import Question, State
from loop_engine.personas.pm.fields import CHECKLIST_FIELDS
from loop_engine.personas.pm.persona import MAX_REVISION_CYCLES, PMPersona


def _initial_state() -> State:
    return State(
        schema_version=2,
        run_id="run-1",
        stage_history=[],
        artifacts={"human_input": "We need a habit tracker for busy parents."},
    )


def _complete_answers() -> dict[str, str]:
    answers = {field: f"Answer for {field}." for field in CHECKLIST_FIELDS}
    answers["acceptance_criteria"] = "A user can create, complete, and delete a habit."
    answers["out_of_scope"] = "Multi-tenant billing and mobile apps."
    return answers


def _mock_response(payload) -> SimpleNamespace:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return SimpleNamespace(text=text)


def test_pm_persona_returns_state_with_valid_project_spec_json() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response(_complete_answers())

    result_state = PMPersona().run(_initial_state(), mock_llm_client)

    project_spec = json.loads(result_state.artifacts["project_spec"])
    assert "problem_statement" in project_spec
    assert result_state.questions == []


def test_pm_persona_skips_followup_call_when_first_pass_is_clean() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response(_complete_answers())

    PMPersona().run(_initial_state(), mock_llm_client)

    assert mock_llm_client.call.call_count == 1


def test_pm_persona_critic_loop_resolves_findings_via_followup_call() -> None:
    incomplete = _complete_answers()
    del incomplete["security_and_risk_considerations"]

    mock_llm_client = MagicMock()
    mock_llm_client.call.side_effect = [
        _mock_response(incomplete),
        _mock_response({"security_and_risk_considerations": "We store no PII."}),
    ]

    result_state = PMPersona().run(_initial_state(), mock_llm_client)

    project_spec = json.loads(result_state.artifacts["project_spec"])
    assert project_spec["security_and_risk_considerations"] == "We store no PII."
    assert mock_llm_client.call.call_count == 2
    assert len(project_spec["revision_history"]) == 1
    assert project_spec["revision_history"][0]["trigger"] == "critic_review"


def test_pm_persona_no_progress_stops_after_one_wasted_cycle_and_escalates() -> None:
    """Identical findings two cycles running means the remaining calls would
    be identical re-rolls: exactly 2 calls (initial + one followup), never
    1 + MAX_REVISION_CYCLES."""
    always_incomplete = _complete_answers()
    del always_incomplete["security_and_risk_considerations"]

    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response(always_incomplete)

    result_state = PMPersona().run(_initial_state(), mock_llm_client)

    assert mock_llm_client.call.call_count == 2
    assert mock_llm_client.call.call_count < 1 + MAX_REVISION_CYCLES
    # Paid work survives: the partial spec is still written.
    assert "project_spec" in result_state.artifacts
    # The unresolved finding became an escalatable question.
    assert any(
        "security_and_risk_considerations" in q.text and q.resolution is None
        for q in result_state.questions
    )


def test_pm_persona_unparseable_response_escalates_instead_of_fabricating() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response("I couldn't find any of that, sorry!")

    result_state = PMPersona().run(_initial_state(), mock_llm_client)

    # Unparseable ≠ "artifact answers nothing": every field escalates as a
    # question rather than silently producing an empty accepted spec.
    assert result_state.questions
    assert all(q.resolution is None for q in result_state.questions)


def test_pm_persona_resolve_questions_answers_from_spec() -> None:
    state = _initial_state().model_copy(
        update={"artifacts": {"project_spec": json.dumps(_complete_answers())}}
    )
    questions = [Question(id="q1", origin_stage="ArchitecturePersona", text="Which region?")]

    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response(
        {"q1": {"resolution": "eu-west-1 only", "impact": "task"}}
    )

    resolved = PMPersona().resolve_questions(questions, state, mock_llm_client)

    assert resolved[0].resolution == "eu-west-1 only"
    assert resolved[0].resolved_by == "pm"
    assert resolved[0].impact == "task"


def test_pm_persona_resolve_questions_leaves_unanswerable_unresolved() -> None:
    state = _initial_state().model_copy(
        update={"artifacts": {"project_spec": json.dumps(_complete_answers())}}
    )
    questions = [Question(id="q1", origin_stage="CoderIacPersona", text="Which region?")]

    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response({"q1": None})

    resolved = PMPersona().resolve_questions(questions, state, mock_llm_client)

    assert resolved[0].resolution is None


def test_pm_persona_fold_answers_updates_spec_and_classifies_impact() -> None:
    spec = _complete_answers()
    state = _initial_state().model_copy(
        update={
            "artifacts": {"project_spec": json.dumps(spec)},
            "questions": [
                Question(
                    id="q1",
                    origin_stage="ArchitecturePersona",
                    text="Which region?",
                    resolution="EU only",
                    resolved_by="human:42",
                )
            ],
        }
    )

    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response(
        {
            "spec_updates": {"regulatory_and_compliance_constraints": "EU data residency."},
            "impacts": {"q1": "architecture"},
        }
    )

    result = PMPersona().fold_answers(state, mock_llm_client)

    updated_spec = json.loads(result.artifacts["project_spec"])
    assert updated_spec["regulatory_and_compliance_constraints"] == "EU data residency."
    assert result.questions[0].impact == "architecture"
