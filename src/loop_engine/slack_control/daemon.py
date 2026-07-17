"""Daemon wiring for the Slack inbound trigger surface (BL-2 pass 2, T4):
T1 transport -> FD3 channel-scope guard -> T2 `parse_command` -> T3
`SlackRunDispatcher.dispatch` + an ephemeral reply.

Fails closed at construction (FD4): `build_daemon_from_env()` raises before
opening any socket if `LOOP_ENGINE_SLACK_APP_TOKEN`, `LOOP_ENGINE_SLACK_BOT_TOKEN`,
or `LOOP_ENGINE_SLACK_CHANNEL` is unset -- an inbound trigger surface must
never start half-configured. It also resolves the channel name/ID (FD3)
before returning, so the running daemon's guard is never comparing against
an unresolved name.

Imports no `slack_sdk` and no `keyring`; all Slack I/O goes through
`tools/slack_io` (the T1 inbound transport, channel resolution, and
ephemeral replies). Tokens are never logged.
"""

import asyncio
import logging
import os
import signal
from typing import Any, Callable

from loop_engine.slack_control.command import CommandRejection, SlackRunCommand, parse_command
from loop_engine.slack_control.dispatch import SlackRunDispatcher
from loop_engine.tools.slack_io import (
    RequestHandler,
    build_listener_from_env,
    format_command_accepted,
    format_command_rejected,
    resolve_channel_id,
    send_ephemeral_reply,
)
from loop_engine.tools.slack_io.inbound import SocketModeRequestLike

logger = logging.getLogger(__name__)

_APP_TOKEN_ENV = "LOOP_ENGINE_SLACK_APP_TOKEN"  # noqa: S105 -- env var name, not a credential
_BOT_TOKEN_ENV = "LOOP_ENGINE_SLACK_BOT_TOKEN"  # noqa: S105 -- env var name, not a credential
_CHANNEL_ENV = "LOOP_ENGINE_SLACK_CHANNEL"


class SlackDaemon:
    """Wires the T1 listener to the T2/T3 parse+dispatch seam under the FD3
    channel-scope guard, and answers every `/agent-run` invocation with an
    ephemeral reply (accepted or a usage error)."""

    def __init__(
        self,
        *,
        channel_id: str,
        bot_token: str,
        dispatcher: SlackRunDispatcher,
        build_listener: Callable[[RequestHandler], Any] = build_listener_from_env,
    ) -> None:
        self._channel_id = channel_id
        self._bot_token = bot_token
        self._dispatcher = dispatcher
        self._loop: asyncio.AbstractEventLoop | None = None
        # Built last: `build_listener` (real or fake) receives the bound
        # `_handle_request` method, so every other attribute must already
        # be set before this line runs.
        self._listener = build_listener(self._handle_request)

    def _reply(self, channel_id: str | None, user_id: str | None, text: str) -> None:
        if not channel_id or not user_id:
            logger.warning("cannot send ephemeral reply: missing channel_id or user_id")
            return
        send_ephemeral_reply(
            bot_token=self._bot_token, channel_id=channel_id, user_id=user_id, text=text
        )

    def _handle_request(self, request: SocketModeRequestLike) -> None:
        """Called by the T1 listener *after* it has already acked the
        envelope. Never raises -- an unparsable/foreign event is dropped or
        answered, never allowed to kill the listener's callback."""
        if request.type != "slash_commands":
            return
        payload = request.payload
        channel_id = payload.get("channel_id") if isinstance(payload, dict) else None
        if channel_id != self._channel_id:
            # FD3: the outer boundary (app+bot tokens, our workspace only)
            # already narrows delivery; this inner guard narrows further to
            # the one operating channel. A foreign channel is dropped
            # silently -- no dispatch, no reply.
            return

        user_id = payload.get("user_id") if isinstance(payload, dict) else None
        merged = {**payload, "envelope_id": request.envelope_id}
        result = parse_command(merged)

        if isinstance(result, SlackRunCommand):
            if self._loop is not None:
                asyncio.run_coroutine_threadsafe(self._dispatcher.dispatch(result), self._loop)
            else:
                logger.warning("dropping accepted command: daemon has no running event loop")
            self._reply(channel_id, user_id, format_command_accepted(result.budget_usd))
        elif isinstance(result, CommandRejection):
            self._reply(channel_id, user_id, format_command_rejected(result.reason))

    async def serve_forever(self) -> None:
        """Open the socket and block until interrupted (SIGINT/SIGTERM),
        then close it. Socket Mode's reconnect/backoff is `SocketModeClient`'s
        own responsibility (delegated via the T1 listener)."""
        self._loop = asyncio.get_running_loop()
        stop = asyncio.Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                self._loop.add_signal_handler(sig, stop.set)
            except NotImplementedError:
                pass  # non-Unix: Ctrl-C still raises KeyboardInterrupt below
        self._listener.connect()
        try:
            await stop.wait()
        finally:
            self._listener.close()


def build_daemon_from_env() -> SlackDaemon:
    """Fails closed (raises `RuntimeError`) unless `LOOP_ENGINE_SLACK_APP_TOKEN`,
    `LOOP_ENGINE_SLACK_BOT_TOKEN`, and `LOOP_ENGINE_SLACK_CHANNEL` are all
    set, and resolves the channel to an ID (FD3) -- all before any socket
    opens."""
    app_token = os.environ.get(_APP_TOKEN_ENV)
    bot_token = os.environ.get(_BOT_TOKEN_ENV)
    channel = os.environ.get(_CHANNEL_ENV)
    missing = [
        name
        for name, value in (
            (_APP_TOKEN_ENV, app_token),
            (_BOT_TOKEN_ENV, bot_token),
            (_CHANNEL_ENV, channel),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"{', '.join(missing)} must be set; refusing to start the Slack "
            "daemon half-configured (fail-closed)."
        )

    channel_id = resolve_channel_id(bot_token=bot_token, channel=channel)
    return SlackDaemon(channel_id=channel_id, bot_token=bot_token, dispatcher=SlackRunDispatcher())


def run_daemon() -> None:
    """Entry point for `loop-engine slack-listen`: build from env (fails
    closed before any socket opens) and block until interrupted."""
    daemon = build_daemon_from_env()
    asyncio.run(daemon.serve_forever())
