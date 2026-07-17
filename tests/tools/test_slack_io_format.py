from loop_engine.core.notify import EventKind, LifecycleEvent
from loop_engine.core.state import (
    CURRENT_SCHEMA_VERSION,
    IssueRef,
    RunStatus,
    SlackRef,
    StageRecord,
    State,
)
from loop_engine.tools.slack_io.format import (
    format_command_accepted,
    format_command_rejected,
    format_event,
)


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


def test_awaiting_slack_includes_pending_slack_channel() -> None:
    state = _state(pending_slack=SlackRef(channel_id="C123", message_ts="1700000000.000100"))
    event = LifecycleEvent(kind=EventKind.AWAITING_SLACK, state=state, budget_usd=1.0)
    text = format_event(event)
    assert "C123" in text


def test_awaiting_slack_degrades_gracefully_when_pending_slack_is_none() -> None:
    event = LifecycleEvent(kind=EventKind.AWAITING_SLACK, state=_state(pending_slack=None))
    text = format_event(event)
    assert "run-1" in text


def test_crashed_includes_run_id_and_error_only() -> None:
    event = LifecycleEvent(kind=EventKind.CRASHED, state=_state(), error="ValueError: boom")
    text = format_event(event)
    assert "run-1" in text
    assert "ValueError: boom" in text


def test_crashed_message_includes_only_run_id_and_error_not_other_state_fields() -> None:
    # Was vacuous: feeding an already-clean error string can never fail,
    # regardless of what format_event does. The real, checkable invariant is
    # that CRASHED ignores everything else on `event.state` -- a crashed
    # event's state is the pre-invoke primed snapshot, so leaking its
    # artifacts/stage_history/pending_issue would surface stale or sensitive
    # data (e.g. human_input) under a message that looks like a bare error.
    state = _state(
        artifacts={"human_input": "sensitive plan detail"},
        stage_history=[StageRecord(stage_name="A", tokens_used=1, cost_usd=1.0, completed_at="t1")],
        pending_issue=IssueRef(number=99, url="https://github.com/acme/widgets/issues/99"),
    )
    event = LifecycleEvent(kind=EventKind.CRASHED, state=state, error="RuntimeError: engine bug")
    text = format_event(event)
    assert "sensitive plan detail" not in text
    assert "99" not in text
    assert "1.00" not in text


def test_crashed_error_is_escaped_for_mrkdwn() -> None:
    event = LifecycleEvent(
        kind=EventKind.CRASHED, state=_state(), error="RuntimeError: <a href=x&y>boom</a>"
    )
    text = format_event(event)
    assert "<a href=x&y>" not in text
    assert "&lt;a href=x&amp;y&gt;boom&lt;/a&gt;" in text


def test_crashed_error_is_truncated_before_escaping() -> None:
    # An unhandled exception's str() is unbounded -- without truncation, mrkdwn
    # escaping's ~5x expansion (`&` -> `&amp;`) could push it over Slack's
    # msg_too_long threshold, letting the crash alert itself get silently
    # swallowed by the notifier's fail-open path (the exact failure mode
    # truncation exists to prevent).
    event = LifecycleEvent(kind=EventKind.CRASHED, state=_state(), error="x" * 1000)
    text = format_event(event)
    assert "x" * 501 not in text
    assert "(truncated)" in text


def test_started_human_input_is_escaped_for_mrkdwn() -> None:
    state = _state(artifacts={"human_input": "<!channel> ship it & <a|link>"})
    event = LifecycleEvent(kind=EventKind.STARTED, state=state, budget_usd=1.0)
    text = format_event(event)
    assert "<!channel>" not in text
    assert "&lt;!channel&gt; ship it &amp; &lt;a|link&gt;" in text


def test_started_human_input_is_truncated_before_escaping() -> None:
    state = _state(artifacts={"human_input": "x" * 1000})
    event = LifecycleEvent(kind=EventKind.STARTED, state=state, budget_usd=1.0)
    text = format_event(event)
    assert "x" * 501 not in text
    assert "(truncated)" in text


def test_format_command_accepted_includes_the_budget() -> None:
    text = format_command_accepted(5.0)
    assert "5.00" in text
    assert "accepted" in text.lower()


def test_format_command_rejected_includes_the_reason() -> None:
    text = format_command_rejected("missing required --budget flag")
    assert "missing required --budget flag" in text
    assert "usage error" in text.lower()


def test_format_command_rejected_escapes_and_truncates_the_reason() -> None:
    # The rejection reason can echo back a user-supplied token (e.g. a
    # malformed --budget value), so it gets the same untrusted-interpolation
    # treatment as human_input/error in format_event above.
    text = format_command_rejected("<!channel> bad value & <a|link>" + "x" * 1000)
    assert "<!channel>" not in text
    assert "&lt;!channel&gt;" in text
    assert "(truncated)" in text


def test_all_seven_event_kinds_render_a_non_empty_message() -> None:
    state_with_extras = _state(
        stage_history=[StageRecord(stage_name="A", tokens_used=1, cost_usd=1.0, completed_at="t1")],
        pending_issue=IssueRef(number=1, url="https://github.com/acme/widgets/issues/1"),
        pending_slack=SlackRef(channel_id="C123", message_ts="1700000000.000100"),
    )
    for kind in EventKind:
        error = "boom" if kind == EventKind.CRASHED else None
        text = format_event(
            LifecycleEvent(kind=kind, state=state_with_extras, budget_usd=1.0, error=error)
        )
        assert text
