import sys
import types

import pytest

from loop_engine.tools.slack_io import SocketModeListener, build_listener_from_env
from loop_engine.tools.slack_io.inbound import _APP_TOKEN_ENV, _BOT_TOKEN_ENV

_FAKE_APP_TOKEN = "xapp-fake-not-a-real-token"  # noqa: S105 -- fixture literal, not a real credential
_FAKE_BOT_TOKEN = "xoxb-fake-not-a-real-token"  # noqa: S105 -- fixture literal, not a real credential


class _FakeWebClient:
    def __init__(self, token: str) -> None:
        self.token = token


class _FakeSocketModeClient:
    instances: list["_FakeSocketModeClient"] = []

    def __init__(self, app_token: str, web_client: _FakeWebClient) -> None:
        self.app_token = app_token
        self.web_client = web_client
        self.socket_mode_request_listeners: list = []
        self.acked: list[str] = []
        self.connected = False
        _FakeSocketModeClient.instances.append(self)

    def connect(self) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def send_socket_mode_response(self, response) -> None:
        self.acked.append(response.envelope_id)


class _FakeSocketModeResponse:
    def __init__(self, envelope_id: str) -> None:
        self.envelope_id = envelope_id


class _FakeRequest:
    def __init__(self, envelope_id: str, type: str, payload: dict) -> None:  # noqa: A002
        self.envelope_id = envelope_id
        self.type = type
        self.payload = payload


def _install_fake_slack_sdk(monkeypatch) -> None:
    slack_sdk_mod = types.ModuleType("slack_sdk")
    slack_sdk_mod.WebClient = _FakeWebClient
    socket_mode_mod = types.ModuleType("slack_sdk.socket_mode")
    socket_mode_mod.SocketModeClient = _FakeSocketModeClient
    socket_mode_response_mod = types.ModuleType("slack_sdk.socket_mode.response")
    socket_mode_response_mod.SocketModeResponse = _FakeSocketModeResponse

    monkeypatch.setitem(sys.modules, "slack_sdk", slack_sdk_mod)
    monkeypatch.setitem(sys.modules, "slack_sdk.socket_mode", socket_mode_mod)
    monkeypatch.setitem(sys.modules, "slack_sdk.socket_mode.response", socket_mode_response_mod)


@pytest.fixture(autouse=True)
def _reset_fake_client_instances():
    _FakeSocketModeClient.instances = []
    yield
    _FakeSocketModeClient.instances = []


def test_build_listener_from_env_raises_when_app_token_unset(monkeypatch) -> None:
    monkeypatch.delenv(_APP_TOKEN_ENV, raising=False)
    monkeypatch.setenv(_BOT_TOKEN_ENV, _FAKE_BOT_TOKEN)
    with pytest.raises(RuntimeError):
        build_listener_from_env(lambda req: None)


def test_build_listener_from_env_raises_when_bot_token_unset(monkeypatch) -> None:
    monkeypatch.setenv(_APP_TOKEN_ENV, _FAKE_APP_TOKEN)
    monkeypatch.delenv(_BOT_TOKEN_ENV, raising=False)
    with pytest.raises(RuntimeError):
        build_listener_from_env(lambda req: None)


def test_build_listener_from_env_raises_when_both_unset(monkeypatch) -> None:
    monkeypatch.delenv(_APP_TOKEN_ENV, raising=False)
    monkeypatch.delenv(_BOT_TOKEN_ENV, raising=False)
    with pytest.raises(RuntimeError):
        build_listener_from_env(lambda req: None)


def test_build_listener_from_env_raise_does_not_leak_the_set_token(monkeypatch) -> None:
    monkeypatch.setenv(_APP_TOKEN_ENV, _FAKE_APP_TOKEN)
    monkeypatch.delenv(_BOT_TOKEN_ENV, raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        build_listener_from_env(lambda req: None)
    assert _FAKE_APP_TOKEN not in str(exc_info.value)


def test_build_listener_from_env_constructs_a_listener_without_connecting(monkeypatch) -> None:
    monkeypatch.setenv(_APP_TOKEN_ENV, _FAKE_APP_TOKEN)
    monkeypatch.setenv(_BOT_TOKEN_ENV, _FAKE_BOT_TOKEN)
    _install_fake_slack_sdk(monkeypatch)

    listener = build_listener_from_env(lambda req: None)

    assert isinstance(listener, SocketModeListener)
    assert len(_FakeSocketModeClient.instances) == 1
    client = _FakeSocketModeClient.instances[0]
    assert client.app_token == _FAKE_APP_TOKEN
    assert client.web_client.token == _FAKE_BOT_TOKEN
    assert client.connected is False
    assert client.socket_mode_request_listeners  # the listener registered itself


def test_socket_mode_listener_acks_and_forwards_each_envelope(monkeypatch) -> None:
    _install_fake_slack_sdk(monkeypatch)
    client = _FakeSocketModeClient(
        app_token=_FAKE_APP_TOKEN, web_client=_FakeWebClient(_FAKE_BOT_TOKEN)
    )
    received: list = []

    listener = SocketModeListener(client, received.append)

    assert client.socket_mode_request_listeners == [listener._handle]

    request = _FakeRequest(
        envelope_id="env-1", type="slash_commands", payload={"command": "/agent-run"}
    )
    listener._handle(client, request)

    assert client.acked == ["env-1"]
    assert received == [request]


def test_socket_mode_listener_acks_exactly_once_per_envelope(monkeypatch) -> None:
    _install_fake_slack_sdk(monkeypatch)
    client = _FakeSocketModeClient(
        app_token=_FAKE_APP_TOKEN, web_client=_FakeWebClient(_FAKE_BOT_TOKEN)
    )
    listener = SocketModeListener(client, lambda req: None)

    request = _FakeRequest(envelope_id="env-2", type="slash_commands", payload={})
    listener._handle(client, request)

    assert client.acked == ["env-2"]


def test_socket_mode_listener_connect_and_close_delegate_to_client(monkeypatch) -> None:
    _install_fake_slack_sdk(monkeypatch)
    client = _FakeSocketModeClient(
        app_token=_FAKE_APP_TOKEN, web_client=_FakeWebClient(_FAKE_BOT_TOKEN)
    )
    listener = SocketModeListener(client, lambda req: None)

    listener.connect()
    assert client.connected is True

    listener.close()
    assert client.connected is False
