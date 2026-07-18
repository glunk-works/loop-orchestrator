"""The `SlackRunDispatcher` seam: fire-and-forget scheduling of a
loop-orchestrator run from a parsed Slack `/agent-run` command, and (T5) of a
resume from a correlated thread reply.

A direct mirror of `trigger/dispatch.py`'s `InProcessDispatcher` (FD6):
Socket Mode redelivers an unacked envelope, so dedupe is keyed on
`envelope_id` rather than trigger's `(repo, issue)` pair. `slack_control/`
deliberately does not share code with parked `trigger/` -- keeping the two
inbound paths independent matches FD1's "supersede, not unify," and avoids
coupling live code to a parked module. `worktree_run`'s `os.chdir` is still
process-global (BL-8), so actual loop execution stays serialized by a single
`_run_lock`, exactly as the trigger dispatcher does -- a start (`dispatch`)
and a resume (`dispatch_resume`) share that one lock, so the two can never
race the chdir.
"""

import asyncio
import logging
from pathlib import Path

from loop_orchestrator import runner
from loop_orchestrator.core.state import State
from loop_orchestrator.slack_control.command import SlackRunCommand
from loop_orchestrator.tools.slack_io import send_thread_message
from loop_orchestrator.tools.state_io.reader import load_state

logger = logging.getLogger(__name__)

_OUTCOME_MESSAGES = {
    "completed": "Run completed.",
    "failed_stage": "Run failed.",
    "budget_exceeded": "Run stopped: budget exceeded.",
}


def _format_outcome(state: State) -> str:
    """The T5 outcome-message mapping (finding #11). A re-pause
    (`AWAITING_SLACK` again) is not a fresh escalation post here -- the
    escalation filer already started a *new* thread for the new questions
    (correlation is per-pause), so this just points at it rather than
    re-posting the questions into the just-answered thread."""
    if state.status.value == "awaiting_slack":
        return "More questions came up -- see the new thread for this run."
    return _OUTCOME_MESSAGES.get(state.status.value, f"Run finished: {state.status.value}.")


class SlackRunDispatcher:
    def __init__(self, *, bot_token: str | None = None) -> None:
        self._active: set[str] = set()
        # Distinct from `_active` (keyed on `envelope_id`, which only
        # collapses Socket Mode *redelivery* of the same envelope): the
        # paused snapshot a resume reads from is never flipped out of
        # `awaiting_slack` until the resume itself finishes (architect/
        # security-critic finding on T5), so two *distinct* thread replies
        # -- different envelope_ids -- landing before the first resume
        # completes would otherwise both scan-match and both dispatch. This
        # set closes that window at the one point both replies share: the
        # correlated thread.
        self._active_threads: set[str] = set()
        self._tasks: set[asyncio.Task] = set()
        self._run_lock = asyncio.Lock()
        self._bot_token = bot_token

    async def dispatch(self, command: SlackRunCommand) -> None:
        """Schedule `command`'s run and return; do not wait for it to
        finish. A repeated `envelope_id` for a still-active run is a no-op
        (Socket Mode redelivery dedupe)."""
        if command.envelope_id in self._active:
            logger.info("dispatch skipped, already running for envelope %s", command.envelope_id)
            return
        self._active.add(command.envelope_id)
        task = asyncio.create_task(self._run(command))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run(self, command: SlackRunCommand) -> None:
        try:
            async with self._run_lock:
                logger.info("run starting for envelope %s", command.envelope_id)
                await asyncio.to_thread(
                    runner.run_new,
                    command.human_input,
                    budget_usd=command.budget_usd,
                    loop_name="default",
                )
                logger.info("run finished for envelope %s", command.envelope_id)
        except Exception:
            logger.exception("run failed for envelope %s", command.envelope_id)
        finally:
            self._active.discard(command.envelope_id)

    async def dispatch_resume(
        self,
        *,
        snapshot_path: Path,
        resolved_answers: dict[int, str],
        budget_usd: float,
        envelope_id: str,
        thread_ts: str,
        channel_id: str,
    ) -> None:
        """Schedule a paused run's resume (a correlated thread reply) and
        return; do not wait for it to finish. Same `envelope_id` dedupe and
        `_run_lock` serialization as `dispatch` -- a start and a resume must
        not race the process-global `os.chdir` (BL-8). Also dedupes on
        `thread_ts`: the paused snapshot stays `awaiting_slack` on disk until
        the resume actually finishes, so a second, *distinct* reply to the
        same thread arriving before then would otherwise scan-match and
        dispatch again. A raising resume is logged and swallowed: a bad
        answer must not kill the daemon."""
        if envelope_id in self._active or thread_ts in self._active_threads:
            logger.info(
                "dispatch_resume skipped, already running for envelope %s (thread %s)",
                envelope_id,
                thread_ts,
            )
            return
        self._active.add(envelope_id)
        self._active_threads.add(thread_ts)
        task = asyncio.create_task(
            self._run_resume(
                snapshot_path=snapshot_path,
                resolved_answers=resolved_answers,
                budget_usd=budget_usd,
                envelope_id=envelope_id,
                thread_ts=thread_ts,
                channel_id=channel_id,
            )
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def _resume_sync(
        self,
        snapshot_path: Path,
        resolved_answers: dict[int, str],
        budget_usd: float,
        thread_ts: str,
    ) -> State:
        state = load_state(snapshot_path)
        return runner.resume_run(
            state,
            resolved_answers,
            resolved_by=f"human:slack:{thread_ts}",
            budget_usd=budget_usd,
        )

    async def _run_resume(
        self,
        *,
        snapshot_path: Path,
        resolved_answers: dict[int, str],
        budget_usd: float,
        envelope_id: str,
        thread_ts: str,
        channel_id: str,
    ) -> None:
        try:
            async with self._run_lock:
                logger.info("resume starting for envelope %s", envelope_id)
                final_state = await asyncio.to_thread(
                    self._resume_sync, snapshot_path, resolved_answers, budget_usd, thread_ts
                )
                logger.info("resume finished for envelope %s", envelope_id)
            if self._bot_token is not None:
                send_thread_message(
                    bot_token=self._bot_token,
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    text=_format_outcome(final_state),
                )
        except Exception:
            logger.exception("resume failed for envelope %s", envelope_id)
        finally:
            self._active.discard(envelope_id)
            self._active_threads.discard(thread_ts)
