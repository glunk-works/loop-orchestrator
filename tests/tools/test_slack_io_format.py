from loop_engine.core.notify import EventKind, LifecycleEvent
from loop_engine.core.state import CURRENT_SCHEMA_VERSION, IssueRef, RunStatus, StageRecord, State
from loop_engine.tools.slack_io.format import format_event


def _state(**overrides) -> State:
    defaults = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "run_id": "run-1",
        "status": RunStatus.RUNNING,
        "stage_history": [],
        "artifacts": {},
    }
    defaults.update(overrides)
    return State(**defaults)


def test_started_includes_run_id_human_input_and_budget() -> None:
    state = _state(artifacts={"human_input": "Ship the widget."})
    event = LifecycleEvent(kind=EventKind.STARTED, state=state, budget_usd=5.0)
    text = format_event(event)
    assert "run-1" in text
    assert "Ship the widget." in text
    assert "5.00" in text


def test_started_degrades_gracefully_with_no_human_input_artifact() -> None:
    event = LifecycleEvent(kind=EventKind.STARTED, state=_state(), budget_usd=5.0)
    text = format_event(event)
    assert "run-1" in text


def test_completed_sums_cost_from_stage_history_and_shows_budget() -> None:
    state = _state(
        stage_history=[
            StageRecord(stage_name="A", tokens_used=100, cost_usd=1.25, completed_at="t1"),
            StageRecord(stage_name="B", tokens_used=200, cost_usd=2.50, completed_at="t2"),
        ]
    )
    event = LifecycleEvent(kind=EventKind.COMPLETED, state=state, budget_usd=10.0)
    text = format_event(event)
    assert "3.75" in text
    assert "10.00" in text


def test_failed_stage_shows_spent_vs_budget() -> None:
    state = _state(
        stage_history=[StageRecord(stage_name="A", tokens_used=1, cost_usd=0.5, completed_at="t1")]
    )
    event = LifecycleEvent(kind=EventKind.FAILED_STAGE, state=state, budget_usd=5.0)
    text = format_event(event)
    assert "0.50" in text
    assert "5.00" in text


def test_budget_exceeded_shows_spent_vs_budget() -> None:
    state = _state(
        stage_history=[StageRecord(stage_name="A", tokens_used=1, cost_usd=5.0, completed_at="t1")]
    )
    event = LifecycleEvent(kind=EventKind.BUDGET_EXCEEDED, state=state, budget_usd=5.0)
    text = format_event(event)
    assert "5.00" in text


def test_awaiting_issue_includes_pending_issue_url_and_number() -> None:
    state = _state(
        pending_issue=IssueRef(number=42, url="https://github.com/acme/widgets/issues/42")
    )
    event = LifecycleEvent(kind=EventKind.AWAITING_ISSUE, state=state, budget_usd=1.0)
    text = format_event(event)
    assert "42" in text
    assert "https://github.com/acme/widgets/issues/42" in text


def test_awaiting_issue_degrades_gracefully_when_pending_issue_is_none() -> None:
    event = LifecycleEvent(kind=EventKind.AWAITING_ISSUE, state=_state(pending_issue=None))
    text = format_event(event)
    assert "run-1" in text


def test_crashed_includes_run_id_and_error_only() -> None:
    event = LifecycleEvent(kind=EventKind.CRASHED, state=_state(), error="ValueError: boom")
    text = format_event(event)
    assert "run-1" in text
    assert "ValueError: boom" in text


def test_crashed_message_never_contains_a_token_or_traceback() -> None:
    event = LifecycleEvent(
        kind=EventKind.CRASHED,
        state=_state(),
        error="RuntimeError: engine bug",
    )
    text = format_event(event)
    assert "xoxb-" not in text
    assert "Traceback" not in text


def test_all_six_event_kinds_render_a_non_empty_message() -> None:
    state_with_extras = _state(
        stage_history=[StageRecord(stage_name="A", tokens_used=1, cost_usd=1.0, completed_at="t1")],
        pending_issue=IssueRef(number=1, url="https://github.com/acme/widgets/issues/1"),
    )
    for kind in EventKind:
        error = "boom" if kind == EventKind.CRASHED else None
        text = format_event(
            LifecycleEvent(kind=kind, state=state_with_extras, budget_usd=1.0, error=error)
        )
        assert text
