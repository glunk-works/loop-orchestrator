"""Ephemeral-reply transport for the inbound trigger surface (BL-2 pass 2,
T4): a thin wrapper over `slack_sdk.WebClient.chat_postEphemeral`, used by
`slack_control/daemon.py` to answer a `/agent-run` invocation (accepted or
rejected) visibly only to the invoking user, not the whole channel.

`slack_sdk` is imported function-scoped inside `send_ephemeral_reply`, the
same F7 posture as `notifier.py`'s `SlackNotifier.emit`, so `tools/slack_io`
stays the sole `slack_sdk` importer. Fail-open, mirroring the notifier: a
reply failure must never crash the daemon or undo the accept/reject decision
already made -- it is caught and logged, never propagated. The bot token is
never logged.
"""

import logging

logger = logging.getLogger(__name__)


def send_ephemeral_reply(*, bot_token: str, channel_id: str, user_id: str, text: str) -> None:
    try:
        from slack_sdk import WebClient

        WebClient(token=bot_token, timeout=5).chat_postEphemeral(
            channel=channel_id, user=user_id, text=text
        )
    except Exception:
        logger.warning("slack ephemeral reply failed for channel=%s user=%s", channel_id, user_id)
