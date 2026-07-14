import pytest
from pydantic import ValidationError

from loop_engine.core.state import (
    CURRENT_SCHEMA_VERSION,
    RunStatus,
    State,
    migrate_state_payload,
)

VALID_PAYLOAD = {
    "schema_version": 4,
    "run_id": "run-001",
    "status": "running",
    "questions": [],
    "pending_issue": None,
    "counters": {},
    "stage_history": [
        {
            "stage_name": "pm",
            "tokens_used": 100,
            "cost_usd": 0.05,
            "completed_at": "2026-07-02T00:00:00Z",
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        }
    ],
    "artifacts": {"spec": "docs/project_spec.json"},
}


def test_state_round_trips_through_json_without_field_loss() -> None:
    state = State.model_validate(VALID_PAYLOAD)
    rehydrated = State.model_validate_json(state.model_dump_json())
    assert rehydrated == state
    assert rehydrated.model_dump(mode="json") == VALID_PAYLOAD


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


def test_state_rejects_retired_artifact_refs_field() -> None:
    # A v3 payload's artifact_refs must go through migrate_state_payload, not
    # straight into State — extra="forbid" rejects it unmigrated.
    payload = {**VALID_PAYLOAD, "artifact_refs": {}}
    with pytest.raises(ValidationError):
        State.model_validate(payload)


def test_state_rejects_invalid_status_and_impact() -> None:
    with pytest.raises(ValidationError):
        State.model_validate({**VALID_PAYLOAD, "status": "definitely_fine"})
    with pytest.raises(ValidationError):
        State.model_validate(
            {
                **VALID_PAYLOAD,
                "questions": [
                    {
                        "id": "q1",
                        "origin_stage": "S",
                        "text": "t",
                        "impact": "cosmic",
                    }
                ],
            }
        )


def test_stage_record_without_cache_fields_still_validates() -> None:
    # Snapshots written before cache accounting existed must load unchanged.
    payload = {
        **VALID_PAYLOAD,
        "stage_history": [
            {
                "stage_name": "pm",
                "tokens_used": 100,
                "cost_usd": 0.05,
                "completed_at": "2026-07-02T00:00:00Z",
            }
        ],
    }
    state = State.model_validate(payload)
    assert state.stage_history[0].cache_creation_input_tokens == 0
    assert state.stage_history[0].cache_read_input_tokens == 0


def test_stage_record_rejects_negative_cache_counts() -> None:
    payload = {
        **VALID_PAYLOAD,
        "stage_history": [{**VALID_PAYLOAD["stage_history"][0], "cache_read_input_tokens": -1}],
    }
    with pytest.raises(ValidationError):
        State.model_validate(payload)


def test_question_without_origin_detail_still_validates() -> None:
    # Snapshots written before origin_detail existed must load unchanged.
    payload = {
        **VALID_PAYLOAD,
        "questions": [{"id": "q1", "origin_stage": "S", "text": "t"}],
    }
    state = State.model_validate(payload)
    assert state.questions[0].origin_detail is None


def test_question_rejects_non_string_origin_detail() -> None:
    payload = {
        **VALID_PAYLOAD,
        "questions": [{"id": "q1", "origin_stage": "S", "text": "t", "origin_detail": 42}],
    }
    with pytest.raises(ValidationError):
        State.model_validate(payload)


def test_migrate_v1_payload_fills_v2_defaults() -> None:
    v1_payload = {
        "schema_version": 1,
        "run_id": "run-legacy",
        "stage_history": [],
        "artifacts": {"human_input": "x"},
    }
    state = State.model_validate(migrate_state_payload(v1_payload))
    assert state.schema_version == CURRENT_SCHEMA_VERSION
    assert state.status is RunStatus.RUNNING
    assert state.questions == []
    assert state.pending_issue is None


def test_migrate_v2_payload_bumps_to_current() -> None:
    v2_payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "schema_version"}
    v2_payload["schema_version"] = 2
    state = State.model_validate(migrate_state_payload(v2_payload))
    assert state.schema_version == CURRENT_SCHEMA_VERSION
    # Inline bodies carry forward untouched.
    assert state.artifacts == {"spec": "docs/project_spec.json"}


def test_migrate_v3_payload_pops_populated_artifact_refs() -> None:
    # FD4 — the sharp edge. A naive pop-less migration would pass an empty
    # {} fixture; this one carries a REAL ref entry, so a missed pop surfaces
    # as a ValidationError under extra="forbid".
    v3_payload = {
        **VALID_PAYLOAD,
        "schema_version": 3,
        "artifact_refs": {
            "spec": {"path": "docs/artifacts/run-001/spec", "digest": "abc123", "size_bytes": 42}
        },
    }
    migrated = migrate_state_payload(v3_payload)
    assert "artifact_refs" not in migrated

    state = State.model_validate(migrated)
    assert state.schema_version == CURRENT_SCHEMA_VERSION
    # Every other field, including the inline artifacts bodies, carries forward.
    assert state.artifacts == {"spec": "docs/project_spec.json"}
    assert state.run_id == "run-001"


def test_migrate_unknown_version_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        migrate_state_payload({"schema_version": 99})
