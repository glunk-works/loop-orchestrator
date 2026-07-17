"""Daemon wiring for the Slack inbound trigger surface: T1 transport -> FD3
channel-scope guard -> T2 `parse_command` -> T3 `SlackRunDispatcher.dispatch`
+ an ephemeral reply (BL-2 pass 2, T4) -- and (BL-2 pass 3, T5) a second
Socket Mode event type, `events_api` thread replies, correlated to a paused
run by an on-demand `tools/state_io` scan and resumed via
`SlackRunDispatcher.dispatch_resume`.

Fails closed at construction (FD4): `build_daemon_from_env()` raises before
opening any socket if `LOOP_ENGINE_SLACK_APP_TOKEN`, `LOOP_ENGINE_SLACK_BOT_TOKEN`,
or `LOOP_ENGINE_SLACK_CHANNEL` is unset -- an inbound trigger surface must
never start half-configured. It also resolves the channel name/ID (FD3)
before returning, so the running daemon's guard is never comparing against
an unresolved name.

Imports no `slack_sdk` and no `keyring`; all Slack I/O goes through
`tools/slack_io` (the T1 inbound transport, channel resolution, and
ephemeral/threaded replies). It now also reads the run-state tree, but only
via `tools/state_io` -- no raw file I/O of its own. Tokens are never logged.
"""

import asyncio
import logging
import os
import signal
from typing import Any, Callable

from loop_engine.core.engine import unresolved_questions
from loop_engine.runner import DEFAULT_BUDGET_USD
from loop_engine.slack_control.command import CommandRejection, SlackRunCommand, parse_command
from loop_engine.slack_control.dispatch import SlackRunDispatcher
from loop_engine.tools.slack_io import (
    RequestHandler,
    build_listener_from_env,
    format_command_accepted,
    format_command_rejected,
    parse_thread_answers,
    resolve_channel_id,
    send_ephemeral_reply,
    send_thread_message,
)
from loop_engine.tools.slack_io.inbound import SocketModeRequestLike
from loop_engine.tools.state_io.reader import find_paused_snapshot_by_slack_thread, load_state

logger = logging.getLogger(__name__)

_APP_TOKEN_ENV = "LOOP_ENGINE_SLACK_APP_TOKEN"  # noqa: S105 -- env var name, not a credential
_BOT_TOKEN_ENV = "LOOP_ENGINE_SLACK_BOT_TOKEN"  # noqa: S105 -- env var name, not a credential
_CHANNEL_ENV = "LOOP_ENGINE_SLACK_CHANNEL"
_IGNORED_MESSAGE_SUBTYPES = {"bot_message", "message_changed", "message_deleted"}


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
        if request.type == "events_api":
            self._handle_message_event(request)
            return
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
            if self._loop is None:
                # Unreachable in production -- the listener only connects
                # inside serve_forever, after _loop is assigned -- but a
                # direct/test caller could still hit this. Never tell the
                # user "accepted" for a command that was not actually
                # dispatched.
                logger.warning("dropping accepted command: daemon has no running event loop")
                return
            coro = self._dispatcher.dispatch(result)
            try:
                asyncio.run_coroutine_threadsafe(coro, self._loop)
            except RuntimeError:
                # The event loop is shutting down (serve_forever's teardown
                # race) -- log and drop rather than raise out of a callback
                # invoked from the Slack SDK's own thread. Close the coroutine
                # explicitly: run_coroutine_threadsafe never got to schedule
                # it, so leaving it unawaited would warn/leak.
                coro.close()
                logger.warning(
                    "dropping command for envelope %s: event loop is shutting down",
                    result.envelope_id,
                )
                return
            self._reply(channel_id, user_id, format_command_accepted(result.budget_usd))
        elif isinstance(result, CommandRejection):
            self._reply(channel_id, user_id, format_command_rejected(result.reason))

    def _handle_message_event(self, request: SocketModeRequestLike) -> None:
        """The T5 inbound half: a Slack `message` event (Events API over
        Socket Mode) that might be a human's reply to an escalation thread.
        Never raises -- the pass-2 `slash_commands` path above is unaffected;
        these are two disjoint request types the T1 listener forwards as-is.
        """
        payload = request.payload
        event = payload.get("event") if isinstance(payload, dict) else None
        if not isinstance(event, dict):
            return

        # Finding #3: an events_api payload's channel/thread/user/text/
        # subtype/bot_id all live under payload["event"], NOT at payload's
        # top level the way the slash-command shape puts channel_id -- a
        # different field path from the guard above.
        channel_id = event.get("channel")
        if channel_id != self._channel_id:
            # FD3 channel-scope guard, applied to message events too.
            return

        if event.get("bot_id") or event.get("subtype") in _IGNORED_MESSAGE_SUBTYPES:
            # Never parse our own escalation post, outcome post, or an edit/
            # delete of one, as a human answer (no self-trigger loop).
            return

        thread_ts = event.get("thread_ts")
        if not isinstance(thread_ts, str) or not thread_ts:
            return  # not a thread reply -- an ordinary channel message

        text = event.get("text")
        if not isinstance(text, str):
            return

        snapshot_path = find_paused_snapshot_by_slack_thread(thread_ts)
        if snapshot_path is None:
            # No paused run correlates to this thread (already resumed, a
            # foreign thread, or plain conversation) -- drop silently.
            return

        state = load_state(snapshot_path)
        unresolved_count = len(unresolved_questions(state))
        answers = parse_thread_answers(text, unresolved_count)
        if not answers:
            send_thread_message(
                bot_token=self._bot_token,
                channel_id=channel_id,
                thread_ts=thread_ts,
                text="Couldn't parse an answer -- reply with one numbered line per "
                "question, e.g. `1: your answer`.",
            )
            return

        if self._loop is None:
            # Same unreachable-in-production guard as the slash-command path
            # above: never resume for a daemon with no running event loop.
            logger.warning("dropping resume: daemon has no running event loop")
            return
        coro = self._dispatcher.dispatch_resume(
            snapshot_path=snapshot_path,
            resolved_answers=answers,
            budget_usd=DEFAULT_BUDGET_USD,
            envelope_id=request.envelope_id,
            thread_ts=thread_ts,
            channel_id=channel_id,
        )
        try:
            asyncio.run_coroutine_threadsafe(coro, self._loop)
        except RuntimeError:
            # The event loop is shutting down (serve_forever's teardown
            # race) -- log and drop rather than raise out of a callback
            # invoked from the Slack SDK's own thread. Close the coroutine
            # explicitly: run_coroutine_threadsafe never got to schedule it,
            # so leaving it unawaited would warn/leak.
            coro.close()
            logger.warning(
                "dropping resume for envelope %s: event loop is shutting down",
                request.envelope_id,
            )

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
    return SlackDaemon(
        channel_id=channel_id,
        bot_token=bot_token,
        dispatcher=SlackRunDispatcher(bot_token=bot_token),
    )


def run_daemon() -> None:
    """Entry point for `loop-engine slack-listen`: build from env (fails
    closed before any socket opens) and block until interrupted."""
    daemon = build_daemon_from_env()
    asyncio.run(daemon.serve_forever())
