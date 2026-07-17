"""The `SlackRunDispatcher` seam: fire-and-forget scheduling of a
loop-engine run from a parsed Slack `/agent-run` command.

A direct mirror of `trigger/dispatch.py`'s `InProcessDispatcher` (FD6):
Socket Mode redelivers an unacked envelope, so dedupe is keyed on
`envelope_id` rather than trigger's `(repo, issue)` pair. `slack_control/`
deliberately does not share code with parked `trigger/` -- keeping the two
inbound paths independent matches FD1's "supersede, not unify," and avoids
coupling live code to a parked module. `worktree_run`'s `os.chdir` is still
process-global (BL-8), so actual loop execution stays serialized by a single
`_run_lock`, exactly as the trigger dispatcher does.
"""

import asyncio
import logging

from loop_engine import runner
from loop_engine.slack_control.command import SlackRunCommand

logger = logging.getLogger(__name__)


class SlackRunDispatcher:
    def __init__(self) -> None:
        self._active: set[str] = set()
        self._tasks: set[asyncio.Task] = set()
        self._run_lock = asyncio.Lock()

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
