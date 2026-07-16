import sys
import types

import pytest

from loop_engine.core.notify import EventKind, LifecycleEvent, NoOpNotifier
from loop_engine.core.state import CURRENT_SCHEMA_VERSION, RunStatus, State
from loop_engine.tools.slack_io import SlackNotifier, build_notifier_from_env
from loop_engine.tools.slack_io.notifier import _CHANNEL_ENV, _TOKEN_ENV

_FAKE_TOKEN = "xoxb-fake-not-a-real-token"  # noqa: S105 -- fixture literal, not a real credential


def _state() -> State:
    return State(
        schema_version=CURRENT_SCHEMA_VERSION,
        run_id="run-1",
        status=RunStatus.RUNNING,
        stage_history=[],
        artifacts={},
    )


def _install_fake_slack_sdk(monkeypatch, client_cls) -> None:
    fake_module = types.ModuleType("slack_sdk")
    fake_module.WebClient = client_cls
    monkeypatch.setitem(sys.modules, "slack_sdk", fake_module)


def test_build_notifier_from_env_defaults_to_noop_when_both_unset(monkeypatch) -> None:
    monkeypatch.delenv(_TOKEN_ENV, raising=False)
    monkeypatch.delenv(_CHANNEL_ENV, raising=False)
    assert isinstance(build_notifier_from_env(), NoOpNotifier)


def test_build_notifier_from_env_noop_when_only_token_set(monkeypatch) -> None:
    monkeypatch.setenv(_TOKEN_ENV, _FAKE_TOKEN)
    monkeypatch.delenv(_CHANNEL_ENV, raising=False)
    assert isinstance(build_notifier_from_env(), NoOpNotifier)


def test_build_notifier_from_env_noop_when_only_channel_set(monkeypatch) -> None:
    monkeypatch.delenv(_TOKEN_ENV, raising=False)
    monkeypatch.setenv(_CHANNEL_ENV, "C123")
    assert isinstance(build_notifier_from_env(), NoOpNotifier)


def test_build_notifier_from_env_returns_slack_notifier_when_both_set(monkeypatch) -> None:
    monkeypatch.setenv(_TOKEN_ENV, _FAKE_TOKEN)
    monkeypatch.setenv(_CHANNEL_ENV, "C123")
    assert isinstance(build_notifier_from_env(), SlackNotifier)


def test_noop_default_never_imports_slack_sdk_and_makes_no_call(monkeypatch) -> None:
    monkeypatch.delenv(_TOKEN_ENV, raising=False)
    monkeypatch.delenv(_CHANNEL_ENV, raising=False)
    # Any attempt to import slack_sdk raises ImportError -- proves the no-op
    # path never touches it, whether or not a prior test already imported
    # the real package into sys.modules.
    monkeypatch.setitem(sys.modules, "slack_sdk", None)

    notifier = build_notifier_from_env()
    notifier.emit(LifecycleEvent(kind=EventKind.STARTED, state=_state(), budget_usd=5.0))


def test_slack_notifier_posts_formatted_text_to_configured_channel(monkeypatch) -> None:
    calls: list[tuple] = []

    class _Client:
        def __init__(self, token: str, timeout: int) -> None:
            calls.append(("init", token, timeout))

        def chat_postMessage(self, **kwargs) -> None:
            calls.append(("post", kwargs))

    _install_fake_slack_sdk(monkeypatch, _Client)

    notifier = SlackNotifier(token=_FAKE_TOKEN, channel="C123")
    notifier.emit(LifecycleEvent(kind=EventKind.COMPLETED, state=_state(), budget_usd=5.0))

    assert calls[0] == ("init", _FAKE_TOKEN, 5)
    kind, kwargs = calls[1]
    assert kind == "post"
    assert kwargs["channel"] == "C123"
    assert "completed" in kwargs["text"].lower()


def test_slack_notifier_swallows_a_raising_client(monkeypatch, caplog) -> None:
    class _RaisingClient:
        def __init__(self, token: str, timeout: int) -> None:
            pass

        def chat_postMessage(self, **kwargs) -> None:
            raise RuntimeError("simulated Slack outage")

    _install_fake_slack_sdk(monkeypatch, _RaisingClient)

    notifier = SlackNotifier(token=_FAKE_TOKEN, channel="C123")
    with caplog.at_level("WARNING"):
        notifier.emit(LifecycleEvent(kind=EventKind.COMPLETED, state=_state(), budget_usd=5.0))

    assert _FAKE_TOKEN not in caplog.text


def test_slack_notifier_swallows_a_formatter_bug(monkeypatch) -> None:
    class _Client:
        def __init__(self, token: str, timeout: int) -> None:
            pass

        def chat_postMessage(self, **kwargs) -> None:
            pytest.fail("must not be reached when format_event raises")

    _install_fake_slack_sdk(monkeypatch, _Client)
    monkeypatch.setattr(
        "loop_engine.tools.slack_io.notifier.format_event",
        lambda event: (_ for _ in ()).throw(RuntimeError("formatter bug")),
    )

    notifier = SlackNotifier(token=_FAKE_TOKEN, channel="C123")
    notifier.emit(LifecycleEvent(kind=EventKind.CRASHED, state=_state(), error="boom"))
