import sys
import types

import pytest

from loop_orchestrator.tools.slack_io import (
    SocketModeListener,
    build_listener_from_env,
    resolve_channel_id,
)
from loop_orchestrator.tools.slack_io.inbound import _APP_TOKEN_ENV, _BOT_TOKEN_ENV

_FAKE_APP_TOKEN = "xapp-fake-not-a-real-token"  # noqa: S105 -- fixture literal, not a real credential
_FAKE_BOT_TOKEN = "xoxb-fake-not-a-real-token"  # noqa: S105 -- fixture literal, not a real credential


class _FakeWebClient:
    def __init__(self, token: str, timeout: int = 5) -> None:
        self.token = token
        self.timeout = timeout


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
    assert client.web_client.timeout == 5
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


class _FakeConversationsWebClient:
    """Fake `WebClient` exposing only `conversations_list`, paginated over
    `pages` (a list of channel-list pages) -- installed per-test so
    `resolve_channel_id`'s name lookup can be exercised without a real
    connection."""

    pages: list[list[dict]] = [[]]

    def __init__(self, token: str, timeout: int = 5) -> None:
        self.token = token
        self.timeout = timeout

    def conversations_list(
        self, *, types: str, cursor: str | None = None, limit: int = 200
    ) -> dict:
        index = 0 if cursor is None else int(cursor)
        page = self.pages[index] if index < len(self.pages) else []
        next_cursor = str(index + 1) if index + 1 < len(self.pages) else ""
        return {"channels": page, "response_metadata": {"next_cursor": next_cursor}}


def _install_fake_conversations_client(monkeypatch, pages: list[list[dict]]) -> None:
    _FakeConversationsWebClient.pages = pages
    fake_module = types.ModuleType("slack_sdk")
    fake_module.WebClient = _FakeConversationsWebClient
    monkeypatch.setitem(sys.modules, "slack_sdk", fake_module)


def test_resolve_channel_id_returns_an_already_id_shaped_channel_unchanged(monkeypatch) -> None:
    # Any attempt to import slack_sdk raises -- proves the already-ID path
    # never makes an API call at all.
    monkeypatch.setitem(sys.modules, "slack_sdk", None)

    assert resolve_channel_id(bot_token=_FAKE_BOT_TOKEN, channel="C0123456789") == "C0123456789"


def test_resolve_channel_id_strips_a_leading_hash_before_checking_id_shape(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "slack_sdk", None)

    assert resolve_channel_id(bot_token=_FAKE_BOT_TOKEN, channel="#C0123456789") == "C0123456789"


def test_resolve_channel_id_looks_up_a_bare_name(monkeypatch) -> None:
    _install_fake_conversations_client(
        monkeypatch, pages=[[{"id": "C999", "name": "loop-orchestrator"}]]
    )

    assert resolve_channel_id(bot_token=_FAKE_BOT_TOKEN, channel="loop-orchestrator") == "C999"


def test_resolve_channel_id_strips_a_leading_hash_before_a_name_lookup(monkeypatch) -> None:
    _install_fake_conversations_client(
        monkeypatch, pages=[[{"id": "C999", "name": "loop-orchestrator"}]]
    )

    assert resolve_channel_id(bot_token=_FAKE_BOT_TOKEN, channel="#loop-orchestrator") == "C999"


def test_resolve_channel_id_paginates_across_multiple_pages(monkeypatch) -> None:
    _install_fake_conversations_client(
        monkeypatch,
        pages=[
            [{"id": "C1", "name": "general"}],
            [{"id": "C999", "name": "loop-orchestrator"}],
        ],
    )

    assert resolve_channel_id(bot_token=_FAKE_BOT_TOKEN, channel="loop-orchestrator") == "C999"


def test_resolve_channel_id_raises_when_name_not_found(monkeypatch) -> None:
    _install_fake_conversations_client(monkeypatch, pages=[[{"id": "C1", "name": "general"}]])

    with pytest.raises(RuntimeError):
        resolve_channel_id(bot_token=_FAKE_BOT_TOKEN, channel="nonexistent")


def test_resolve_channel_id_wraps_a_live_api_error_as_runtime_error(monkeypatch) -> None:
    # A network/auth/rate-limit failure from the real client (e.g.
    # slack_sdk's SlackApiError) must surface the same fail-closed way an
    # unresolvable name does, not as a raw traceback the CLI doesn't catch.
    class _RaisingWebClient:
        def __init__(self, token: str, timeout: int = 5) -> None:
            pass

        def conversations_list(self, *, types: str, cursor=None, limit=200):
            raise RuntimeError("simulated Slack API outage")

    fake_module = types.ModuleType("slack_sdk")
    fake_module.WebClient = _RaisingWebClient
    monkeypatch.setitem(sys.modules, "slack_sdk", fake_module)

    with pytest.raises(RuntimeError) as exc_info:
        resolve_channel_id(bot_token=_FAKE_BOT_TOKEN, channel="loop-orchestrator")

    assert _FAKE_BOT_TOKEN not in str(exc_info.value)
