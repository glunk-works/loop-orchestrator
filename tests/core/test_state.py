import pytest
from pydantic import ValidationError

from loop_engine.core.state import State

VALID_PAYLOAD = {
    "schema_version": 1,
    "run_id": "run-001",
    "stage_history": [
        {
            "stage_name": "pm",
            "tokens_used": 100,
            "cost_usd": 0.05,
            "completed_at": "2026-07-02T00:00:00Z",
        }
    ],
    "artifacts": {"spec": "docs/project_spec.json"},
}


def test_state_round_trips_through_json_without_field_loss() -> None:
    state = State.model_validate(VALID_PAYLOAD)
    rehydrated = State.model_validate_json(state.model_dump_json())
    assert rehydrated == state
    assert rehydrated.model_dump() == VALID_PAYLOAD


def test_state_rejects_missing_schema_version() -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "schema_version"}
    with pytest.raises(ValidationError):
        State.model_validate(payload)


def test_state_rejects_negative_tokens_used() -> None:
    payload = {
        **VALID_PAYLOAD,
        "stage_history": [{**VALID_PAYLOAD["stage_history"][0], "tokens_used": -1}],
    }
    with pytest.raises(ValidationError):
        State.model_validate(payload)


def test_state_rejects_unrecognized_top_level_field() -> None:
    payload = {**VALID_PAYLOAD, "api_key": "sk-should-not-exist"}
    with pytest.raises(ValidationError):
        State.model_validate(payload)
