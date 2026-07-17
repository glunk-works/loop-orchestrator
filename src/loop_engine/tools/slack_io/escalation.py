"""Slack transport for the escalation ladder's human terminus (BL-2 pass 3,
T3): the outbound half of the round-trip whose inbound half (thread-reply
correlation + resume) lands in `slack_control/daemon.py` (T5).

`slack_escalation_filer` is an `EscalationFiler`-shaped callable (see
`core/engine.py`'s `EscalationFiler` protocol) that posts the paused run's
open questions to `LOOP_ENGINE_SLACK_CHANNEL` and returns a `SlackRef`
correlating the posted message's thread to the pause -- the Slack-transport
counterpart to `tools/issue_io`'s `default_issue_filer`. `render_question_message`
mirrors `issue_io.render_question_issue`'s numbered `[origin_stage] text`
format; `parse_thread_answers` mirrors `issue_io.parse_issue_answers`'s
numbered-line convention for the reply side.

`slack_sdk` is imported function-scoped in both `slack_escalation_filer` and
`send_thread_message` -- the same F7 posture as `notifier.py`/`reply.py` --
so `tools/slack_io` stays the sole `slack_sdk` importer. Unlike the notifier
and `send_ephemeral_reply` (both fail-open: a notification is best-effort),
`slack_escalation_filer` FAILS CLOSED -- it is the actual pause mechanism,
so a posting failure must surface to the engine rather than leave a run
paused with no way for a human to find the questions.
"""

import logging
import os
import re

from loop_engine.core.state import Question, SlackRef, State
from loop_engine.tools.slack_io.format import _MAX_UNTRUSTED_TEXT_CHARS, _escape_mrkdwn, _truncate

_ANSWER_LINE_RE = re.compile(r"^\s*(\d+)\s*[:.)]\s*(.+?)\s*$")

logger = logging.getLogger(__name__)

_TOKEN_ENV = "LOOP_ENGINE_SLACK_BOT_TOKEN"  # noqa: S105 -- env var name, not a credential
_CHANNEL_ENV = "LOOP_ENGINE_SLACK_CHANNEL"


class SlackEscalationConfigError(Exception):
    """`slack_escalation_filer` could not find a configured bot token/channel
    to post to. Raised instead of silently no-op'ing -- an unconfigured Slack
    transport must never swallow a pause the way a best-effort notification
    can."""


def render_question_message(state: State, questions: list[Question]) -> str:
    """Pure: the Slack mrkdwn message body for a paused run's questions.

    Mirrors `issue_io.render_question_issue`'s numbered `[origin_stage] text`
    format. Question text is model/human-authored (finding #7, a repeat of
    the pass-2 T3 critic finding), so it is mrkdwn-escaped and length-capped
    before interpolation, reusing the pass-1 `format.py` helpers so all three
    untrusted-text sinks in this package (lifecycle events, escalation
    questions) share one escaping/truncation policy.
    """
    lines = [
        f"loop-engine run `{state.run_id}` is paused: {len(questions)} question(s) "
        "need a human answer.",
        "",
    ]
    for number, question in enumerate(questions, start=1):
        origin = _escape_mrkdwn(question.origin_stage)
        text = _escape_mrkdwn(_truncate(question.text, _MAX_UNTRUSTED_TEXT_CHARS))
        lines.append(f"{number}. *[{origin}]* {text}")
    lines += [
        "",
        "Reply *in this thread*, one line per question number:",
        "`1: your answer`",
        "`2: your answer`",
        "(A single plain reply works if there's only one question.)",
    ]
    return "\n".join(lines)


def slack_escalation_filer(state: State, questions: list[Question], snapshot_hint: str) -> SlackRef:
    """The Slack-transport `EscalationFiler`: posts `render_question_message`
    un-threaded to the configured channel (this post *creates* the thread
    subsequent answers/outcomes reply into) and returns a `SlackRef` built
    from the API response's own `channel`/`ts` -- not the raw configured
    channel value -- so the correlation key matches the channel ID Socket
    Mode delivers in inbound events even when `LOOP_ENGINE_SLACK_CHANNEL` is
    configured as a human-readable name. `snapshot_hint` is accepted (the
    shared `EscalationFiler` signature) but unused here -- unlike the GitHub
    issue body, the Slack message does not carry the snapshot path.

    Raises `SlackEscalationConfigError` if the bot token/channel are not
    configured, and propagates any `slack_sdk` posting error -- fail-closed,
    since a swallowed failure here would leave the run paused with no
    discoverable escalation.
    """
    token = os.environ.get(_TOKEN_ENV)
    channel = os.environ.get(_CHANNEL_ENV)
    if not token or not channel:
        raise SlackEscalationConfigError(
            f"{_TOKEN_ENV} and {_CHANNEL_ENV} must both be set to file a Slack escalation."
        )

    from slack_sdk import WebClient

    text = render_question_message(state, questions)
    response = WebClient(token=token, timeout=5).chat_postMessage(channel=channel, text=text)
    return SlackRef(channel_id=response["channel"], message_ts=response["ts"])


def send_thread_message(*, bot_token: str, channel_id: str, thread_ts: str, text: str) -> None:
    """Post `text` into an existing thread (finding #5) -- used by T5's
    `dispatch_resume` to post a run's outcome back where the human answered.
    Fail-open like `notifier.emit`/`send_ephemeral_reply`: a failure here
    must never crash the daemon or undo a resume already under way. The bot
    token is never logged."""
    try:
        from slack_sdk import WebClient

        WebClient(token=bot_token, timeout=5).chat_postMessage(
            channel=channel_id, thread_ts=thread_ts, text=text
        )
    except Exception:
        logger.warning(
            "slack thread message failed for channel=%s thread_ts=%s", channel_id, thread_ts
        )


def parse_thread_answers(text: str, unresolved_count: int) -> dict[int, str]:
    """Pure: `{question number: answer}` from a single thread-reply message
    body (finding #6). No I/O.

    Reuses the issue path's numbered-line convention (`^\\s*(\\d+)\\s*[:.)]\\s*(.+)$`),
    scanning every line; numbers outside `1..unresolved_count` are ignored. A
    reply with no numbered lines maps to `{1: <whole body>}` **only** when
    `unresolved_count == 1` -- ambiguous prose against multiple open
    questions is not silently pinned to question 1.
    """
    answers: dict[int, str] = {}
    for line in text.splitlines():
        match = _ANSWER_LINE_RE.match(line)
        if not match:
            continue
        try:
            number = int(match.group(1))
        except ValueError:
            # An absurdly long digit run trips Python's integer-string-
            # conversion limit (sys.get_int_max_str_digits) -- an adversarial
            # thread reply must not crash this parser, so treat it as an
            # unparseable (non-matching) line rather than propagating.
            continue
        if 1 <= number <= unresolved_count:
            answers[number] = match.group(2)

    if answers:
        return answers

    stripped = text.strip()
    if stripped and unresolved_count == 1:
        return {1: stripped}
    return {}
