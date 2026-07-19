"""Inbound Slack transport for the trigger surface (BL-2 pass 2 of 3): a thin
wrapper over `slack_sdk.socket_mode.SocketModeClient` that opens the app's
outbound WebSocket under the app-level + bot tokens and acks every envelope
within Slack's ~3s window.

`slack_sdk` is imported function-scoped, mirroring `notifier.py`'s F7
posture, so `tools/slack_io` stays the sole `slack_sdk` importer for both
directions (outbound in pass 1, inbound here). Unlike the notifier -- inert
by default when unconfigured -- `build_listener_from_env()` FAILS CLOSED
(FD4): an inbound trigger surface must never start half-configured, so it
raises rather than returning a no-op listener. Reconnect/backoff is
delegated entirely to `SocketModeClient` -- this module does not hand-roll
it.

`resolve_channel_id()` (T4) is the FD3 channel-name-to-ID resolver: Socket
Mode event payloads carry a channel ID only, so `slack_control/daemon.py`'s
channel-scope guard needs an ID to compare against even when the operator
configured `LOOP_ORCHESTRATOR_SLACK_CHANNEL` as a bare name (the same name-or-ID
ambiguity `notifier.py` already tolerates for outbound posting).
"""

import re
from typing import Any, Callable, Protocol

from loop_orchestrator.tools.env_compat import getenv_compat

_APP_TOKEN_ENV = "LOOP_ORCHESTRATOR_SLACK_APP_TOKEN"  # noqa: S105 -- env var name, not a credential
_BOT_TOKEN_ENV = "LOOP_ORCHESTRATOR_SLACK_BOT_TOKEN"  # noqa: S105 -- env var name, not a credential

# Slack channel IDs are uppercase-alnum, starting with C (public), G (private/
# MPIM), or D (DM) -- distinct in shape from a human-chosen channel name.
_CHANNEL_ID_RE = re.compile(r"^[CGD][A-Z0-9]{8,}$")


class SocketModeRequestLike(Protocol):
    """Structural shape of `slack_sdk.socket_mode.request.SocketModeRequest`
    this module relies on -- kept local so nothing here needs a module-scope
    `slack_sdk` import."""

    envelope_id: str
    type: str
    payload: dict[str, Any]


class SocketModeClientLike(Protocol):
    """Structural shape of `slack_sdk.socket_mode.SocketModeClient` this
    module relies on -- lets tests inject a fake client with no live
    connection."""

    socket_mode_request_listeners: list

    def connect(self) -> None: ...

    def close(self) -> None: ...

    def send_socket_mode_response(self, response: Any) -> None: ...


RequestHandler = Callable[[SocketModeRequestLike], None]


class SocketModeListener:
    """Wraps a `SocketModeClient`-shaped object: registers a single request
    listener that acks every envelope before forwarding it to `on_request`.
    Connection lifecycle (`connect`/`close`) is delegated to the wrapped
    client; reconnect/backoff is `SocketModeClient`'s own responsibility.
    """

    def __init__(self, client: SocketModeClientLike, on_request: RequestHandler) -> None:
        self._client = client
        self._on_request = on_request
        client.socket_mode_request_listeners.append(self._handle)

    def _handle(self, client: SocketModeClientLike, request: SocketModeRequestLike) -> None:
        from slack_sdk.socket_mode.response import SocketModeResponse

        client.send_socket_mode_response(SocketModeResponse(envelope_id=request.envelope_id))
        self._on_request(request)

    def connect(self) -> None:
        self._client.connect()

    def close(self) -> None:
        self._client.close()


def build_listener_from_env(on_request: RequestHandler) -> SocketModeListener:
    """The runtime builder: FAILS CLOSED (raises `RuntimeError`) unless both
    `LOOP_ORCHESTRATOR_SLACK_APP_TOKEN` and `LOOP_ORCHESTRATOR_SLACK_BOT_TOKEN` are set --
    an inbound trigger surface must never start half-configured (FD4, the
    deliberate inverse of the pass-1 notifier's inert-by-default posture).
    Never returns a no-op listener; never logs either token.
    """
    app_token = getenv_compat(_APP_TOKEN_ENV)
    bot_token = getenv_compat(_BOT_TOKEN_ENV)
    if not app_token or not bot_token:
        raise RuntimeError(
            f"{_APP_TOKEN_ENV} and {_BOT_TOKEN_ENV} must both be set; refusing "
            "to start the Slack inbound listener half-configured (fail-closed)."
        )

    from slack_sdk import WebClient
    from slack_sdk.socket_mode import SocketModeClient

    client = SocketModeClient(app_token=app_token, web_client=WebClient(token=bot_token, timeout=5))
    return SocketModeListener(client, on_request)


def resolve_channel_id(*, bot_token: str, channel: str) -> str:
    """Resolve `channel` (a bare name, a `#name`, or an already-ID `Cxxxxxxxx`
    form) to its channel ID, once, at daemon startup (FD3): inbound Socket
    Mode event payloads carry the ID only, so the channel-scope guard must
    compare against an ID even when the operator configured a human-readable
    name -- a naive string compare against a configured name would silently
    match nothing. Raises `RuntimeError` if a name cannot be resolved; the
    daemon must fail closed rather than start with a guard that matches no
    channel. Never logs the bot token.
    """
    name = channel[1:] if channel.startswith("#") else channel
    if _CHANNEL_ID_RE.match(name):
        return name

    from slack_sdk import WebClient

    client = WebClient(token=bot_token, timeout=5)
    try:
        cursor = None
        while True:
            response = client.conversations_list(
                types="public_channel,private_channel", cursor=cursor, limit=200
            )
            for candidate in response.get("channels", []):
                if candidate.get("name") == name:
                    return candidate["id"]
            cursor = response.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                break
    except Exception as exc:
        # A live auth/network/rate-limit failure (e.g. slack_sdk's
        # SlackApiError) must surface the same way an unresolvable name
        # does -- a clean fail-closed RuntimeError, not a raw traceback from
        # an exception type the CLI doesn't know to catch. Never includes
        # the bot token.
        raise RuntimeError(
            f"failed to resolve Slack channel {channel!r} to an id "
            f"({type(exc).__name__}); refusing to start the Slack daemon "
            "with an unresolved channel guard (fail-closed)."
        ) from exc

    raise RuntimeError(
        f"could not resolve Slack channel {channel!r} to an id; refusing to "
        "start the Slack daemon with an unresolved channel guard (fail-closed)."
    )
