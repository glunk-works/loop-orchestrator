"""Pure Slack mrkdwn formatter for lifecycle events. No I/O, no env read, no
token reference — deterministic given a `LifecycleEvent`.
"""

from loop_engine.core.notify import EventKind, LifecycleEvent

# Well under Slack's ~40k message limit — bounds any untrusted/unbounded text
# reaching the message body (human_input, and an unhandled exception's str())
# so it can never hit `msg_too_long` and get silently swallowed by the
# notifier's fail-open path. Applied before escaping, since mrkdwn escaping
# can expand a string up to ~5x (`&` -> `&amp;`).
_MAX_UNTRUSTED_TEXT_CHARS = 500


def _escape_mrkdwn(text: str) -> str:
    """Escape Slack mrkdwn control chars on untrusted interpolation. Order
    matters: `&` first, or the entities just inserted would be re-escaped."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "… (truncated)"


def _cost_line(event: LifecycleEvent) -> str:
    spent = sum(record.cost_usd for record in event.state.stage_history)
    if event.budget_usd is None:
        return f"Spent: ${spent:.2f}"
    return f"Spent: ${spent:.2f} of ${event.budget_usd:.2f}"


def _issue_line(event: LifecycleEvent) -> str:
    issue = event.state.pending_issue
    if issue is None:
        return "No escalation issue link available."
    return f"Escalation issue: <{issue.url}|#{issue.number}>"


def _slack_line(event: LifecycleEvent) -> str:
    slack_ref = event.state.pending_slack
    if slack_ref is None:
        return "No escalation thread available."
    return f"Escalation posted to <#{slack_ref.channel_id}> -- reply in that thread to resume."


def format_event(event: LifecycleEvent) -> str:
    run_id = event.state.run_id

    if event.kind == EventKind.STARTED:
        lines = [f":rocket: Run `{run_id}` started."]
        human_input = event.state.artifacts.get("human_input")
        if human_input:
            safe_input = _escape_mrkdwn(_truncate(human_input, _MAX_UNTRUSTED_TEXT_CHARS))
            lines.append(f"Input: {safe_input}")
        if event.budget_usd is not None:
            lines.append(f"Budget: ${event.budget_usd:.2f}")
        return "\n".join(lines)

    if event.kind == EventKind.COMPLETED:
        return f":white_check_mark: Run `{run_id}` completed.\n{_cost_line(event)}"

    if event.kind == EventKind.FAILED_STAGE:
        return f":x: Run `{run_id}` failed at a stage gate.\n{_cost_line(event)}"

    if event.kind == EventKind.BUDGET_EXCEEDED:
        return f":moneybag: Run `{run_id}` stopped: budget exceeded.\n{_cost_line(event)}"

    if event.kind == EventKind.AWAITING_ISSUE:
        return f":raising_hand: Run `{run_id}` is awaiting human input.\n{_issue_line(event)}"

    if event.kind == EventKind.AWAITING_SLACK:
        return f":raising_hand: Run `{run_id}` is awaiting human input.\n{_slack_line(event)}"

    if event.kind == EventKind.CRASHED:
        raw_error = event.error or "unknown error"
        error = _escape_mrkdwn(_truncate(raw_error, _MAX_UNTRUSTED_TEXT_CHARS))
        return f":boom: Run `{run_id}` crashed: {error}"

    raise ValueError(f"unhandled EventKind: {event.kind}")


def format_command_accepted(budget_usd: float) -> str:
    """The ephemeral reply to a valid `/agent-run` command."""
    return f"Run accepted (budget ${budget_usd:.2f})."


def format_command_rejected(reason: str) -> str:
    """The ephemeral reply to a `CommandRejection`. `reason` can echo back a
    user-supplied token (e.g. an unparsable `--budget` value), so it gets the
    same untrusted-interpolation treatment as `human_input`/`error` above."""
    safe_reason = _escape_mrkdwn(_truncate(reason, _MAX_UNTRUSTED_TEXT_CHARS))
    return f"Usage error: {safe_reason}"
