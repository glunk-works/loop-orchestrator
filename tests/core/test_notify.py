import dataclasses

import pytest

from loop_engine.core.notify import EventKind, LifecycleEvent, NoOpNotifier
from loop_engine.core.state import CURRENT_SCHEMA_VERSION, RunStatus, State


def _state() -> State:
    return State(
        schema_version=CURRENT_SCHEMA_VERSION,
        run_id="run-1",
        status=RunStatus.RUNNING,
        stage_history=[],
        artifacts={},
    )


def test_event_kind_has_exactly_seven_members() -> None:
    assert {kind.value for kind in EventKind} == {
        "started",
        "completed",
        "failed_stage",
        "budget_exceeded",
        "awaiting_issue",
        "awaiting_slack",
        "crashed",
    }


def test_lifecycle_event_is_frozen() -> None:
    event = LifecycleEvent(kind=EventKind.STARTED, state=_state())
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.kind = EventKind.CRASHED  # type: ignore[misc]


def test_lifecycle_event_defaults_budget_and_error_to_none() -> None:
    event = LifecycleEvent(kind=EventKind.STARTED, state=_state())
    assert event.budget_usd is None
    assert event.error is None


def test_noop_notifier_emit_is_a_no_op() -> None:
    NoOpNotifier().emit(LifecycleEvent(kind=EventKind.COMPLETED, state=_state()))
