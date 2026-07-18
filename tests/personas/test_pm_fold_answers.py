"""`pm.persona.fold_answers` — the PM logic that outlived the classic PMPersona.

Driven on resume after a GitHub-issue round-trip (`cli.resume` → stage 0's
`fold_answers`), it folds a human's answers into the project spec and classifies
each answer's blast radius, which decides how far back the run re-enters.

`PMGenerator.fold_answers` delegates straight to the module-level function, so
this pins the behavior at its source. (Phase 6 deleted `PMPersona`, which used
to be the other caller; these assertions came from that class's test.)
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_orchestrator.core.state import Question, State
from loop_orchestrator.personas.declarative.node import PMGenerator
from loop_orchestrator.personas.pm.fields import CHECKLIST_FIELDS
from loop_orchestrator.personas.pm.persona import fold_answers


def _complete_answers() -> dict[str, str]:
    answers = {field: f"Answer for {field}." for field in CHECKLIST_FIELDS}
    answers["acceptance_criteria"] = "A user can create, complete, and delete a habit."
    answers["out_of_scope"] = "Multi-tenant billing and mobile apps."
    return answers


def _answered_state() -> State:
    return State(
        schema_version=3,
        run_id="run-1",
        stage_history=[],
        artifacts={"project_spec": json.dumps(_complete_answers())},
        questions=[
            Question(
                id="q1",
                origin_stage="ArchitectureGenerator",
                text="Which region?",
                resolution="EU only",
                resolved_by="human:42",
            )
        ],
    )


def _mock_client(payload) -> MagicMock:
    client = MagicMock()
    text = payload if isinstance(payload, str) else json.dumps(payload)
    client.call.return_value = SimpleNamespace(text=text)
    return client


def test_fold_answers_updates_spec_and_classifies_impact() -> None:
    client = _mock_client(
        {
            "spec_updates": {"regulatory_and_compliance_constraints": "EU data residency."},
            "impacts": {"q1": "architecture"},
        }
    )

    result = fold_answers(_answered_state(), client)

    assert (
        json.loads(result.artifacts["project_spec"])["regulatory_and_compliance_constraints"]
        == "EU data residency."
    )
    assert result.questions[0].impact == "architecture"


def test_pm_generator_delegates_fold_answers_to_the_module_function() -> None:
    client = _mock_client({"spec_updates": {}, "impacts": {"q1": "task"}})

    result = PMGenerator().fold_answers(_answered_state(), client)

    assert result.questions[0].impact == "task"


def test_fold_answers_is_a_noop_when_nothing_was_answered() -> None:
    client = MagicMock()
    state = _answered_state().model_copy(update={"questions": []})

    assert fold_answers(state, client) is state
    client.call.assert_not_called()


@pytest.mark.parametrize("payload", ["not json at all", {"spec_updates": [], "impacts": "nope"}])
def test_fold_answers_defaults_unclassified_answers_to_plan(payload) -> None:
    # An unparseable or malformed classification must not silently narrow the
    # rework scope to "task" — re-planning is wasteful but correct; skipping
    # required rework is not.
    result = fold_answers(_answered_state(), _mock_client(payload))

    assert result.questions[0].impact == "plan"
