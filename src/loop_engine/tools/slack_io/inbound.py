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
"""

import logging
import os
from typing import Any, Callable, Protocol

_logger = logging.getLogger(__name__)

_APP_TOKEN_ENV = "LOOP_ENGINE_SLACK_APP_TOKEN"  # noqa: S105 -- env var name, not a credential
_BOT_TOKEN_ENV = "LOOP_ENGINE_SLACK_BOT_TOKEN"  # noqa: S105 -- env var name, not a credential


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
    `LOOP_ENGINE_SLACK_APP_TOKEN` and `LOOP_ENGINE_SLACK_BOT_TOKEN` are set --
    an inbound trigger surface must never start half-configured (FD4, the
    deliberate inverse of the pass-1 notifier's inert-by-default posture).
    Never returns a no-op listener; never logs either token.
    """
    app_token = os.environ.get(_APP_TOKEN_ENV)
    bot_token = os.environ.get(_BOT_TOKEN_ENV)
    if not app_token or not bot_token:
        raise RuntimeError(
            f"{_APP_TOKEN_ENV} and {_BOT_TOKEN_ENV} must both be set; refusing "
            "to start the Slack inbound listener half-configured (fail-closed)."
        )

    from slack_sdk import WebClient
    from slack_sdk.socket_mode import SocketModeClient

    client = SocketModeClient(app_token=app_token, web_client=WebClient(token=bot_token))
    return SocketModeListener(client, on_request)
