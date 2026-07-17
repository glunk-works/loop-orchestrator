import sys
import types

import pytest

from loop_engine.core.state import CURRENT_SCHEMA_VERSION, Question, RunStatus, State
from loop_engine.tools.slack_io import (
    SlackEscalationConfigError,
    parse_thread_answers,
    render_question_message,
    send_thread_message,
    slack_escalation_filer,
)
from loop_engine.tools.slack_io.escalation import _CHANNEL_ENV, _TOKEN_ENV

_FAKE_TOKEN = "xoxb-fake-not-a-real-token"  # noqa: S105 -- fixture literal, not a real credential


def _state() -> State:
    return State(
        schema_version=CURRENT_SCHEMA_VERSION,
        run_id="run-1",
        status=RunStatus.RUNNING,
        stage_history=[],
        artifacts={},
    )


def _question(id_: str, origin_stage: str, text: str) -> Question:
    return Question(id=id_, origin_stage=origin_stage, text=text)


def _install_fake_slack_sdk(monkeypatch, client_cls) -> None:
    fake_module = types.ModuleType("slack_sdk")
    fake_module.WebClient = client_cls
    monkeypatch.setitem(sys.modules, "slack_sdk", fake_module)


# -- render_question_message -------------------------------------------------


def test_render_question_message_numbers_and_labels_questions() -> None:
    questions = [
        _question("q1", "RalphCoderPersona", "Which retry policy?"),
        _question("q2", "ArchitectPersona", "Is the schema bump additive?"),
    ]
    text = render_question_message(_state(), questions)

    assert "1. *[RalphCoderPersona]* Which retry policy?" in text
    assert "2. *[ArchitectPersona]* Is the schema bump additive?" in text
    assert "run `run-1`" in text
    assert "2 question(s)" in text
    assert "reply" in text.lower()


def test_render_question_message_escapes_mrkdwn_control_chars() -> None:
    questions = [_question("q1", "Coder", "Use <script>alert(1)</script> & retry?")]
    text = render_question_message(_state(), questions)

    assert "<script>" not in text
    assert "&lt;script&gt;" in text
    assert "&amp;" in text


def test_render_question_message_truncates_long_question_text() -> None:
    questions = [_question("q1", "Coder", "x" * 1000)]
    text = render_question_message(_state(), questions)

    assert "(truncated)" in text
    assert "x" * 1000 not in text


# -- slack_escalation_filer ---------------------------------------------------


def test_slack_escalation_filer_posts_and_returns_slack_ref(monkeypatch) -> None:
    calls: list[tuple] = []

    class _Client:
        def __init__(self, token: str, timeout: int) -> None:
            calls.append(("init", token, timeout))

        def chat_postMessage(self, **kwargs) -> dict:
            calls.append(("post", kwargs))
            return {"ok": True, "channel": "C999", "ts": "1700000000.000100"}

    _install_fake_slack_sdk(monkeypatch, _Client)
    monkeypatch.setenv(_TOKEN_ENV, _FAKE_TOKEN)
    monkeypatch.setenv(_CHANNEL_ENV, "#escalations")

    questions = [_question("q1", "Coder", "Which retry policy?")]
    ref = slack_escalation_filer(_state(), questions, "state/run-1/00_awaiting_issue.json")

    assert calls[0] == ("init", _FAKE_TOKEN, 5)
    kind, kwargs = calls[1]
    assert kind == "post"
    assert kwargs["channel"] == "#escalations"
    assert "Which retry policy?" in kwargs["text"]
    assert "thread_ts" not in kwargs  # the filing post creates the thread, un-threaded

    # The ref is built from the API response, not the configured channel --
    # this is what keeps correlation working when an operator configures a
    # human-readable channel name instead of an id.
    assert ref.channel_id == "C999"
    assert ref.message_ts == "1700000000.000100"


def test_slack_escalation_filer_raises_when_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv(_TOKEN_ENV, raising=False)
    monkeypatch.delenv(_CHANNEL_ENV, raising=False)

    with pytest.raises(SlackEscalationConfigError):
        slack_escalation_filer(_state(), [_question("q1", "Coder", "text")], "hint")


def test_slack_escalation_filer_propagates_a_raising_client(monkeypatch) -> None:
    class _RaisingClient:
        def __init__(self, token: str, timeout: int) -> None:
            pass

        def chat_postMessage(self, **kwargs) -> dict:
            raise RuntimeError("simulated Slack outage")

    _install_fake_slack_sdk(monkeypatch, _RaisingClient)
    monkeypatch.setenv(_TOKEN_ENV, _FAKE_TOKEN)
    monkeypatch.setenv(_CHANNEL_ENV, "C123")

    with pytest.raises(RuntimeError, match="simulated Slack outage"):
        slack_escalation_filer(_state(), [_question("q1", "Coder", "text")], "hint")


# -- send_thread_message ------------------------------------------------------


def test_send_thread_message_posts_to_the_given_thread(monkeypatch) -> None:
    calls: list[tuple] = []

    class _Client:
        def __init__(self, token: str, timeout: int) -> None:
            calls.append(("init", token, timeout))

        def chat_postMessage(self, **kwargs) -> None:
            calls.append(("post", kwargs))

    _install_fake_slack_sdk(monkeypatch, _Client)

    send_thread_message(
        bot_token=_FAKE_TOKEN,
        channel_id="C123",
        thread_ts="1700000000.000100",
        text="Run completed.",
    )

    assert calls[0] == ("init", _FAKE_TOKEN, 5)
    kind, kwargs = calls[1]
    assert kind == "post"
    assert kwargs == {
        "channel": "C123",
        "thread_ts": "1700000000.000100",
        "text": "Run completed.",
    }


def test_send_thread_message_swallows_a_raising_client(monkeypatch, caplog) -> None:
    class _RaisingClient:
        def __init__(self, token: str, timeout: int) -> None:
            pass

        def chat_postMessage(self, **kwargs) -> None:
            raise RuntimeError("simulated Slack outage")

    _install_fake_slack_sdk(monkeypatch, _RaisingClient)

    with caplog.at_level("WARNING"):
        send_thread_message(
            bot_token=_FAKE_TOKEN, channel_id="C123", thread_ts="1700000000.000100", text="text"
        )

    assert _FAKE_TOKEN not in caplog.text


# -- parse_thread_answers -----------------------------------------------------


def test_parse_thread_answers_numbered_multiline() -> None:
    text = "1: retry three times\n2: yes, additive"
    assert parse_thread_answers(text, unresolved_count=2) == {
        1: "retry three times",
        2: "yes, additive",
    }


def test_parse_thread_answers_bare_body_with_one_unresolved_question() -> None:
    assert parse_thread_answers("just retry three times", unresolved_count=1) == {
        1: "just retry three times"
    }


def test_parse_thread_answers_bare_body_with_multiple_unresolved_questions() -> None:
    assert parse_thread_answers("just retry three times", unresolved_count=2) == {}


def test_parse_thread_answers_ignores_out_of_range_numbers() -> None:
    text = "1: retry three times\n5: unrelated"
    assert parse_thread_answers(text, unresolved_count=2) == {1: "retry three times"}


def test_parse_thread_answers_empty_or_garbage_with_multiple_open_questions() -> None:
    assert parse_thread_answers("", unresolved_count=2) == {}
    assert parse_thread_answers("   \n  ", unresolved_count=2) == {}


def test_parse_thread_answers_accepts_dot_and_paren_separators() -> None:
    text = "1. retry three times\n2) yes"
    assert parse_thread_answers(text, unresolved_count=2) == {1: "retry three times", 2: "yes"}


def test_parse_thread_answers_does_not_raise_on_an_oversized_digit_run() -> None:
    # A digit run past Python's integer-string-conversion limit (~4300 digits,
    # sys.get_int_max_str_digits) must be treated as an unparseable line, not
    # raise -- the parser's contract is pure/total over adversarial input.
    huge_number = "1" * 5000
    text = f"{huge_number}: whatever\n1: real answer"
    assert parse_thread_answers(text, unresolved_count=1) == {1: "real answer"}
