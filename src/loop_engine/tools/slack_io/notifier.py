"""Outbound Slack transport for the notifier seam (BL-2 pass 1 of 3): a thin
wrapper over `slack_sdk.WebClient.chat_postMessage`.

`slack_sdk` is imported function-scoped inside `SlackNotifier.emit`, not at
module scope, so `build_notifier_from_env()`'s no-op default (either env var
unset) never pulls it into the import graph — the same F7 posture as
`tools/issue_io/mcp_client.py`'s deferred `tools/mcp` import.
"""

import logging
import os

from loop_engine.core.notify import LifecycleEvent, NoOpNotifier, Notifier
from loop_engine.tools.slack_io.format import format_event

_logger = logging.getLogger(__name__)

_TOKEN_ENV = "LOOP_ENGINE_SLACK_BOT_TOKEN"  # noqa: S105 -- env var name, not a credential
_CHANNEL_ENV = "LOOP_ENGINE_SLACK_CHANNEL"


class SlackNotifier:
    """Posts a formatted lifecycle event to a single Slack channel.

    Internally fail-open: the `try/except` wraps both `format_event` and the
    post, so a formatter bug, a bad token, a network error, or a Slack
    outage is caught and swallowed rather than propagated — the run's
    correctness never depends on this call succeeding. The token is never
    logged or included in the swallowed-exception log line.
    """

    def __init__(self, token: str, channel: str) -> None:
        self._token = token
        self._channel = channel

    def emit(self, event: LifecycleEvent) -> None:
        try:
            from slack_sdk import WebClient

            text = format_event(event)
            WebClient(token=self._token, timeout=5).chat_postMessage(
                channel=self._channel, text=text
            )
        except Exception:
            _logger.warning("slack notify failed for event kind=%s", event.kind)


def build_notifier_from_env() -> Notifier:
    """The runtime default: a `NoOpNotifier` unless both
    `LOOP_ENGINE_SLACK_BOT_TOKEN` and `LOOP_ENGINE_SLACK_CHANNEL` are set."""
    token = os.environ.get(_TOKEN_ENV)
    channel = os.environ.get(_CHANNEL_ENV)
    if not token or not channel:
        return NoOpNotifier()
    return SlackNotifier(token=token, channel=channel)
