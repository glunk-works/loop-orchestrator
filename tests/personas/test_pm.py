import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.core.state import State
from loop_engine.personas.pm.fields import CHECKLIST_FIELDS
from loop_engine.personas.pm.persona import PMPersona, RevisionCapReached


def _initial_state() -> State:
    return State(
        schema_version=1,
        run_id="run-1",
        stage_history=[],
        artifacts={"human_input": "We need a habit tracker for busy parents."},
    )


def _complete_answers() -> dict[str, str]:
    answers = {field: f"Answer for {field}." for field in CHECKLIST_FIELDS}
    answers["acceptance_criteria"] = "A user can create, complete, and delete a habit."
    answers["out_of_scope"] = "Multi-tenant billing and mobile apps."
    return answers


def _mock_response(payload: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(text=json.dumps(payload))


def test_pm_persona_returns_state_with_valid_project_spec_json() -> None:
    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response(_complete_answers())

    result_state = PMPersona().run(_initial_state(), mock_llm_client)

    project_spec = json.loads(result_state.artifacts["project_spec"])
    assert "problem_statement" in project_spec


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


def test_pm_persona_raises_revision_cap_reached_when_findings_never_resolve() -> None:
    always_incomplete = _complete_answers()
    del always_incomplete["security_and_risk_considerations"]

    mock_llm_client = MagicMock()
    mock_llm_client.call.return_value = _mock_response(always_incomplete)

    with pytest.raises(RevisionCapReached):
        PMPersona().run(_initial_state(), mock_llm_client)
