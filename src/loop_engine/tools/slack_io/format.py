"""Pure Slack mrkdwn formatter for lifecycle events. No I/O, no env read, no
token reference — deterministic given a `LifecycleEvent`.
"""

from loop_engine.core.notify import EventKind, LifecycleEvent


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


def format_event(event: LifecycleEvent) -> str:
    run_id = event.state.run_id

    if event.kind == EventKind.STARTED:
        lines = [f":rocket: Run `{run_id}` started."]
        human_input = event.state.artifacts.get("human_input")
        if human_input:
            lines.append(f"Input: {human_input}")
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

    if event.kind == EventKind.CRASHED:
        error = event.error or "unknown error"
        return f":boom: Run `{run_id}` crashed: {error}"

    raise ValueError(f"unhandled EventKind: {event.kind}")
