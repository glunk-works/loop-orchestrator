import asyncio
import sys
import types
from types import SimpleNamespace

import pytest

from loop_engine.slack_control.command import SlackRunCommand
from loop_engine.slack_control.daemon import (
    _APP_TOKEN_ENV,
    _BOT_TOKEN_ENV,
    _CHANNEL_ENV,
    SlackDaemon,
    build_daemon_from_env,
)

_CHANNEL_ID = "C0123456789"


class _FakeListener:
    def __init__(self, on_request) -> None:
        self.on_request = on_request
        self.connected = False

    def connect(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False


class _FakeDispatcher:
    def __init__(self) -> None:
        self.received: list[SlackRunCommand] = []

    async def dispatch(self, command: SlackRunCommand) -> None:
        self.received.append(command)


def _request(
    envelope_id: str = "env-1",
    channel_id: str = _CHANNEL_ID,
    user_id: str = "U1",
    text: str = "--budget 5.00 fix it",
    command: str = "/agent-run",
    request_type: str = "slash_commands",
) -> SimpleNamespace:
    return SimpleNamespace(
        envelope_id=envelope_id,
        type=request_type,
        payload={
            "command": command,
            "text": text,
            "channel_id": channel_id,
            "user_id": user_id,
        },
    )


def _daemon(dispatcher: _FakeDispatcher | None = None) -> SlackDaemon:
    return SlackDaemon(
        channel_id=_CHANNEL_ID,
        bot_token="xoxb-fake-not-a-real-token",  # noqa: S106
        dispatcher=dispatcher or _FakeDispatcher(),
        build_listener=_FakeListener,
    )


def _patch_reply(monkeypatch) -> list[dict]:
    replies: list[dict] = []
    monkeypatch.setattr(
        "loop_engine.slack_control.daemon.send_ephemeral_reply",
        lambda **kwargs: replies.append(kwargs),
    )
    return replies


def test_foreign_channel_is_dropped_silently(monkeypatch) -> None:
    replies = _patch_reply(monkeypatch)
    dispatcher = _FakeDispatcher()
    daemon = _daemon(dispatcher)

    daemon._handle_request(_request(channel_id="C-some-other-channel"))

    assert dispatcher.received == []
    assert replies == []


def test_non_slash_command_event_type_is_ignored(monkeypatch) -> None:
    replies = _patch_reply(monkeypatch)
    dispatcher = _FakeDispatcher()
    daemon = _daemon(dispatcher)

    daemon._handle_request(_request(request_type="events_api"))

    assert dispatcher.received == []
    assert replies == []


def test_matching_valid_command_dispatches_and_replies_accepted(monkeypatch) -> None:
    replies = _patch_reply(monkeypatch)
    dispatcher = _FakeDispatcher()
    daemon = _daemon(dispatcher)

    async def main() -> None:
        daemon._loop = asyncio.get_running_loop()
        daemon._handle_request(_request(text="--budget 5.00 fix it", user_id="U1"))
        await asyncio.sleep(0.2)

    asyncio.run(main())

    assert len(dispatcher.received) == 1
    assert dispatcher.received[0].human_input == "fix it"
    assert dispatcher.received[0].budget_usd == 5.00
    assert len(replies) == 1
    assert replies[0]["channel_id"] == _CHANNEL_ID
    assert replies[0]["user_id"] == "U1"
    assert "accepted" in replies[0]["text"].lower()


def test_matching_invalid_command_replies_usage_error_and_does_not_dispatch(monkeypatch) -> None:
    replies = _patch_reply(monkeypatch)
    dispatcher = _FakeDispatcher()
    daemon = _daemon(dispatcher)

    daemon._handle_request(_request(text="fix it"))  # missing --budget

    assert dispatcher.received == []
    assert len(replies) == 1
    assert "usage error" in replies[0]["text"].lower()


def test_missing_channel_id_or_user_id_skips_the_reply_without_raising(monkeypatch) -> None:
    replies = _patch_reply(monkeypatch)
    dispatcher = _FakeDispatcher()
    daemon = _daemon(dispatcher)

    request = _request(text="fix it")
    request.payload = {**request.payload, "user_id": None}
    daemon._handle_request(request)

    assert replies == []


def test_valid_command_with_no_running_loop_is_dropped_without_a_misleading_reply(
    monkeypatch,
) -> None:
    # Regression: previously an "accepted" reply was sent even when _loop was
    # None and nothing was actually dispatched (architect finding, PR #119
    # critic-gate pass) -- never tell the user a run was accepted unless it
    # was actually scheduled.
    replies = _patch_reply(monkeypatch)
    dispatcher = _FakeDispatcher()
    daemon = _daemon(dispatcher)
    assert daemon._loop is None

    daemon._handle_request(_request())

    assert dispatcher.received == []
    assert replies == []


def test_shutting_down_event_loop_drops_the_command_without_raising(monkeypatch) -> None:
    # Regression: architect's shutdown-race finding -- run_coroutine_threadsafe
    # can raise RuntimeError if the loop is tearing down; _handle_request must
    # never propagate that out of a callback invoked from the Slack SDK's own
    # thread.
    replies = _patch_reply(monkeypatch)
    dispatcher = _FakeDispatcher()
    daemon = _daemon(dispatcher)

    async def main() -> None:
        daemon._loop = asyncio.get_running_loop()

    asyncio.run(main())  # the loop returned by asyncio.run is now closed

    daemon._handle_request(_request())  # must not raise

    assert dispatcher.received == []
    assert replies == []


@pytest.mark.parametrize(
    "missing_env",
    [_APP_TOKEN_ENV, _BOT_TOKEN_ENV, _CHANNEL_ENV],
)
def test_build_daemon_from_env_raises_when_one_var_is_missing(monkeypatch, missing_env) -> None:
    env_values = {
        _APP_TOKEN_ENV: "xapp-fake-not-a-real-token",
        _BOT_TOKEN_ENV: "xoxb-fake-not-a-real-token",
        _CHANNEL_ENV: _CHANNEL_ID,
    }
    for name, value in env_values.items():
        if name == missing_env:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError) as exc_info:
        build_daemon_from_env()

    assert missing_env in str(exc_info.value)


def test_build_daemon_from_env_raises_before_touching_slack_sdk_when_all_unset(monkeypatch) -> None:
    monkeypatch.delenv(_APP_TOKEN_ENV, raising=False)
    monkeypatch.delenv(_BOT_TOKEN_ENV, raising=False)
    monkeypatch.delenv(_CHANNEL_ENV, raising=False)
    # Any attempt to import slack_sdk raises -- proves the fail-closed check
    # runs before any socket/API call is attempted.
    monkeypatch.setitem(sys.modules, "slack_sdk", None)

    with pytest.raises(RuntimeError) as exc_info:
        build_daemon_from_env()

    for name in (_APP_TOKEN_ENV, _BOT_TOKEN_ENV, _CHANNEL_ENV):
        assert name in str(exc_info.value)


class _FakeWebClient:
    def __init__(self, token: str, timeout: int = 5) -> None:
        pass


class _FakeSocketModeClient:
    def __init__(self, app_token: str, web_client) -> None:
        self.socket_mode_request_listeners: list = []

    def connect(self) -> None:
        pass

    def close(self) -> None:
        pass

    def send_socket_mode_response(self, response) -> None:
        pass


def test_build_daemon_from_env_constructs_with_the_resolved_channel_id(monkeypatch) -> None:
    monkeypatch.setenv(_APP_TOKEN_ENV, "xapp-fake-not-a-real-token")
    monkeypatch.setenv(_BOT_TOKEN_ENV, "xoxb-fake-not-a-real-token")
    monkeypatch.setenv(_CHANNEL_ENV, _CHANNEL_ID)

    fake_module = types.ModuleType("slack_sdk")
    fake_module.WebClient = _FakeWebClient
    socket_mode_mod = types.ModuleType("slack_sdk.socket_mode")
    socket_mode_mod.SocketModeClient = _FakeSocketModeClient
    monkeypatch.setitem(sys.modules, "slack_sdk", fake_module)
    monkeypatch.setitem(sys.modules, "slack_sdk.socket_mode", socket_mode_mod)

    daemon = build_daemon_from_env()

    assert isinstance(daemon, SlackDaemon)
    assert daemon._channel_id == _CHANNEL_ID
