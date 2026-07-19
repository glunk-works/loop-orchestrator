import pytest
from pydantic import ValidationError

from loop_orchestrator.slack_control.command import CommandRejection, SlackRunCommand, parse_command


def _payload(
    command: str = "/agent-run",
    text: str = "--budget 5.00 fix the flaky test",
    channel_id: str = "C123456",
    envelope_id: str = "env-1",
) -> dict:
    return {
        "command": command,
        "text": text,
        "channel_id": channel_id,
        "envelope_id": envelope_id,
    }


def test_valid_command_parses_to_slack_run_command() -> None:
    result = parse_command(_payload())

    assert isinstance(result, SlackRunCommand)
    assert result.human_input == "fix the flaky test"
    assert result.budget_usd == 5.00
    assert result.channel_id == "C123456"
    assert result.envelope_id == "env-1"


def test_budget_flag_may_appear_after_the_requirements_text() -> None:
    result = parse_command(_payload(text="fix the flaky test --budget 5.00"))

    assert isinstance(result, SlackRunCommand)
    assert result.human_input == "fix the flaky test"
    assert result.budget_usd == 5.00


def test_missing_budget_flag_is_rejected() -> None:
    result = parse_command(_payload(text="fix the flaky test"))

    assert isinstance(result, CommandRejection)
    assert "--budget" in result.reason


def test_budget_flag_with_no_value_is_rejected() -> None:
    result = parse_command(_payload(text="--budget"))

    assert isinstance(result, CommandRejection)
    assert "--budget" in result.reason


@pytest.mark.parametrize("bad_value", ["abc", "0", "-5", "-5.00"])
def test_non_positive_or_non_numeric_budget_is_rejected(bad_value) -> None:
    result = parse_command(_payload(text=f"--budget {bad_value} fix the flaky test"))

    assert isinstance(result, CommandRejection)


@pytest.mark.parametrize("non_finite_value", ["inf", "-inf", "Infinity", "nan", "1e999"])
def test_non_finite_budget_is_rejected(non_finite_value) -> None:
    """`float()` parses inf/nan/overflowing literals, and `inf <= 0` /
    `nan <= 0` are both False -- without an explicit finiteness check an
    attacker could smuggle an unbounded budget straight past the fail-closed
    money-cap guard (security-critic + architect finding, Sprint 40 T2)."""
    result = parse_command(_payload(text=f"--budget {non_finite_value} fix the flaky test"))

    assert isinstance(result, CommandRejection)


def test_duplicate_budget_flag_is_rejected() -> None:
    result = parse_command(_payload(text="--budget 5.00 --budget 10.00 fix the flaky test"))

    assert isinstance(result, CommandRejection)
    assert "--budget" in result.reason


def test_empty_requirements_text_is_rejected() -> None:
    result = parse_command(_payload(text="--budget 5.00"))

    assert isinstance(result, CommandRejection)
    assert "requirements" in result.reason


def test_wrong_command_is_rejected() -> None:
    result = parse_command(_payload(command="/other-command"))

    assert isinstance(result, CommandRejection)
    assert "unrecognized command" in result.reason


@pytest.mark.parametrize(
    "payload",
    [
        {},
        None,
        {"command": "/agent-run"},
        {"command": "/agent-run", "text": "--budget 5.00 fix it"},
        {"command": "/agent-run", "text": "--budget 5.00 fix it", "channel_id": "C1"},
        {"command": "/agent-run", "text": 42, "channel_id": "C1", "envelope_id": "env-1"},
        {
            "command": "/agent-run",
            "text": "--budget 5.00 fix it",
            "channel_id": "",
            "envelope_id": "env-1",
        },
        "not a dict",
    ],
)
def test_malformed_payload_never_raises(payload) -> None:
    result = parse_command(payload)

    assert isinstance(result, CommandRejection)


def test_slack_run_command_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        SlackRunCommand(
            human_input="hi",
            budget_usd=5.0,
            channel_id="C1",
            envelope_id="env-1",
            extra_field="nope",
        )


def test_command_rejection_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        CommandRejection(reason="nope", extra_field="nope")
