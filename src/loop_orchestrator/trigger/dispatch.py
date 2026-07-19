"""The `RunDispatcher` seam: fire-and-forget scheduling of a loop-orchestrator run.

The webhook handler must ACK GitHub within seconds; a run takes minutes. The
seam is a `Protocol` so a durable-queue / process-isolated implementation can
swap in behind it later without touching `app.py`. 23 ships one
implementation, `InProcessDispatcher`, which runs the loop in-process on a
worker thread — best-effort, in-memory dedupe, single-process only.
"""

import asyncio
import logging
from typing import Protocol

from loop_orchestrator import runner
from loop_orchestrator.trigger.parse import RunRequest

logger = logging.getLogger(__name__)


class RunDispatcher(Protocol):
    async def dispatch(self, request: RunRequest) -> None:
        """Schedule `request`'s run and return; do not wait for it to finish."""
        ...


class InProcessDispatcher:
    def __init__(self) -> None:
        self._active: set[tuple[str, int]] = set()
        self._tasks: set[asyncio.Task] = set()
        # F3/F6: `_ORIGIN_CWD`/`_STATE_ROOT` are now per-context ContextVars,
        # so concurrent runs no longer read/clobber each other's values --
        # but `os.chdir` itself (inside `worktree_run`) is still
        # process-global. Two runs' worktree chdirs racing would still
        # corrupt each other's CWD (breaking snapshot paths and
        # `run_in_tree`'s fallback), so this lock makes that race
        # unreachable by serializing actual loop execution: `dispatch()`
        # still acks and dedupes immediately, but the loop itself starts
        # only once the previous one has finished. A real fix (BL-8) stops
        # using process CWD as an isolation mechanism at all; this is the
        # honest bottleneck in the meantime.
        self._run_lock = asyncio.Lock()

    async def dispatch(self, request: RunRequest) -> None:
        key = (request.repo_full_name, request.issue_number)
        if key in self._active:
            logger.info("dispatch skipped, already running for %s#%s", *key)
            return
        self._active.add(key)
        task = asyncio.create_task(self._run(request, key))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run(self, request: RunRequest, key: tuple[str, int]) -> None:
        try:
            async with self._run_lock:
                logger.info("run starting for %s#%s", *key)
                await asyncio.to_thread(
                    runner.run_new,
                    request.human_input,
                    budget_usd=request.budget_usd,
                    loop_name=request.loop_name,
                )
                logger.info("run finished for %s#%s", *key)
        except Exception:
            logger.exception("run failed for %s#%s", *key)
        finally:
            self._active.discard(key)
