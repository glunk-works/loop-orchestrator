"""Pure parser for the FD5 Slack trigger grammar: a `/agent-run` slash-command
payload -> a validated `SlackRunCommand`, or a typed `CommandRejection`
carrying a reason for the ephemeral reply -- never a raise. Mirrors
`trigger/parse.py`'s "locked grammar, never raise" posture, except every
non-matching input yields a typed rejection rather than `None`, so the daemon
(T4) always has a reason string to echo back to the user.

No I/O, no env read, no `slack_sdk` import, no token -- pure data in, pure
data out. `payload` is the raw Slack slash-command form fields (`command`,
`text`, `channel_id`, ...) *plus* the Socket Mode envelope's `envelope_id`
merged in by the caller (`request.payload | {"envelope_id": request.envelope_id}`)
-- `envelope_id` is a Socket Mode transport concern, not a slash-command form
field, so daemon.py (T4) owns that merge; this module only consumes the
result.
"""

import math

from pydantic import BaseModel, ConfigDict

_SLASH_COMMAND = "/agent-run"
_BUDGET_FLAG = "--budget"


class SlackRunCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    human_input: str
    budget_usd: float
    channel_id: str
    envelope_id: str


class CommandRejection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str


def _extract_budget(text: str) -> tuple[str | None, str]:
    """Pull the `--budget <value>` token pair out of `text`, returning
    `(value_or_none, remaining_text)`. `None` means the flag is absent; `""`
    means the flag is present but has no following value."""
    tokens = text.split()
    try:
        idx = tokens.index(_BUDGET_FLAG)
    except ValueError:
        return None, text
    if idx + 1 >= len(tokens):
        return "", " ".join(tokens[:idx])
    value = tokens[idx + 1]
    remaining = tokens[:idx] + tokens[idx + 2 :]
    return value, " ".join(remaining)


def parse_command(payload: dict) -> "SlackRunCommand | CommandRejection":
    """The locked FD5 grammar: `/agent-run --budget <n> <requirements text>`.
    Every rejection path (wrong command, missing/non-numeric/non-positive
    budget, empty requirements, missing channel/envelope id, or a malformed
    payload) yields a `CommandRejection` with a human-readable reason --
    never a raise, and never a defaulted budget (fail-closed on the money
    cap)."""
    try:
        if not isinstance(payload, dict):
            return CommandRejection(reason="malformed command payload")

        command = payload.get("command")
        if command != _SLASH_COMMAND:
            return CommandRejection(reason=f"unrecognized command: {command!r}")

        text = payload.get("text")
        if not isinstance(text, str):
            return CommandRejection(reason="malformed command payload: missing text")

        channel_id = payload.get("channel_id")
        if not isinstance(channel_id, str) or not channel_id:
            return CommandRejection(reason="malformed command payload: missing channel_id")

        envelope_id = payload.get("envelope_id")
        if not isinstance(envelope_id, str) or not envelope_id:
            return CommandRejection(reason="malformed command payload: missing envelope_id")

        if text.split().count(_BUDGET_FLAG) > 1:
            return CommandRejection(reason="multiple --budget flags; provide exactly one")

        budget_token, remaining_text = _extract_budget(text)
        if budget_token is None:
            return CommandRejection(
                reason="missing required --budget flag: "
                "usage `/agent-run --budget <n> <requirements>`"
            )
        if not budget_token:
            return CommandRejection(reason="--budget flag requires a numeric value")
        try:
            budget_usd = float(budget_token)
        except ValueError:
            return CommandRejection(reason=f"--budget value is not a number: {budget_token!r}")
        if not math.isfinite(budget_usd) or budget_usd <= 0:
            return CommandRejection(
                reason=f"--budget must be a finite number greater than zero: {budget_token!r}"
            )

        human_input = remaining_text.strip()
        if not human_input:
            return CommandRejection(reason="requirements text is empty")

        return SlackRunCommand(
            human_input=human_input,
            budget_usd=budget_usd,
            channel_id=channel_id,
            envelope_id=envelope_id,
        )
    except (KeyError, TypeError, ValueError):
        return CommandRejection(reason="malformed command payload")
