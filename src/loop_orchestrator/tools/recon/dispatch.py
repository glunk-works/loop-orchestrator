"""`ReconDispatcher` -- the seam between `tools/recon`'s input boundary and
`bounty-infra`'s ProjectDiscovery recon workflow (S47-D3). `GhReconDispatcher`
is the real implementation: a *third* `gh` subprocess consumer (alongside
`tools/issue_io` and `tools/repo_io`'s `gh` calls) -- not a sixth surface
(`tests/tools/test_subprocess_surfaces.py`).

`gh workflow_dispatch` returns no run id, so the S47-D8 contract mints a
correlation token (the caller's `ReconRequest.correlation_token`), passes it
as a workflow input, and polls `gh run list` for the run whose title echoes
the token back -- a `bounty-infra` API contract tracked as `bounty-infra#18`
(a V-run precondition; untested here beyond this module's own hermetic `gh`
argv/polling logic). The completed run's recon output lands at the
deterministic S3 key `recon/<token>.jsonl`, fetched by `tools/s3_io` once
`await_completion` returns.

The S47-D9 bounded poll fails closed: `ReconTimeout` after `max_wait_seconds`
with no completed run carrying the token; `ReconDispatchFailedError`
immediately if that run finishes with a non-success conclusion (no reason to
keep polling a run that has already failed).
"""

import json
import subprocess
import time
from typing import Any, NewType, Protocol

from pydantic import BaseModel, ConfigDict

from loop_orchestrator.tools.recon.models import ReconRequest

S3Key = NewType("S3Key", str)

_GH_TIMEOUT_S = 60
_POLL_INTERVAL_S = 10.0
_MAX_WAIT_S = 900.0

_DEFAULT_WORKFLOW = "recon.yml"


class ReconTimeout(Exception):
    """No `gh` run carrying the dispatch's correlation token completed
    within `max_wait_seconds` (S47-D9's fail-closed bound)."""


class ReconDispatchFailedError(Exception):
    """The `gh` run carrying the dispatch's correlation token finished with
    a non-success conclusion."""


class DispatchHandle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    correlation_token: str


class ReconDispatcher(Protocol):
    def dispatch(self, request: ReconRequest) -> DispatchHandle: ...

    def await_completion(self, handle: DispatchHandle) -> S3Key: ...


def _run_gh(args: list[str]) -> str:
    result = subprocess.run(  # noqa: S603 -- fixed executable, no shell; args carry only the already scope-cleared seed/token plus the caller-configured repo/workflow name
        ["gh", *args],  # noqa: S607 -- resolved via PATH intentionally, matching issue_io/repo_io's gh
        capture_output=True,
        text=True,
        check=True,
        timeout=_GH_TIMEOUT_S,
    )
    return result.stdout


def _find_run_for_token(runs: list[dict[str, Any]], token: str) -> dict[str, Any] | None:
    for run in runs:
        if token in run.get("displayTitle", ""):
            return run
    return None


class GhReconDispatcher:
    """The real `ReconDispatcher`: shells `gh workflow run` to dispatch,
    then bounded-polls `gh run list` for the run whose title echoes the
    correlation token back."""

    def __init__(
        self,
        *,
        repo: str,
        workflow: str = _DEFAULT_WORKFLOW,
        poll_interval_seconds: float = _POLL_INTERVAL_S,
        max_wait_seconds: float = _MAX_WAIT_S,
    ) -> None:
        self._repo = repo
        self._workflow = workflow
        self._poll_interval_seconds = poll_interval_seconds
        self._max_wait_seconds = max_wait_seconds

    def dispatch(self, request: ReconRequest) -> DispatchHandle:
        _run_gh(
            [
                "workflow",
                "run",
                self._workflow,
                "--repo",
                self._repo,
                "-f",
                f"seed={request.seed}",
                "-f",
                f"token={request.correlation_token}",
            ]
        )
        return DispatchHandle(correlation_token=request.correlation_token)

    def await_completion(self, handle: DispatchHandle) -> S3Key:
        """Blocks until the run carrying `handle`'s token completes, fails,
        or the bounded poll times out. Deliberately fail-closed on a
        transient `gh run list` error too: `_run_gh`'s `check=True` lets a
        `CalledProcessError` from any single poll propagate out of the loop
        rather than being swallowed and retried -- one flaky API call ends
        the wait rather than risking an unbounded silent retry."""
        deadline = time.monotonic() + self._max_wait_seconds
        while True:
            match = _find_run_for_token(self._list_runs(), handle.correlation_token)
            if match is not None and match.get("status") == "completed":
                if match.get("conclusion") == "success":
                    return S3Key(f"recon/{handle.correlation_token}.jsonl")
                raise ReconDispatchFailedError(
                    f"recon run for token {handle.correlation_token!r} concluded "
                    f"{match.get('conclusion')!r}"
                )
            if time.monotonic() >= deadline:
                raise ReconTimeout(
                    f"no {self._workflow} run carrying token "
                    f"{handle.correlation_token!r} completed within "
                    f"{self._max_wait_seconds}s"
                )
            time.sleep(self._poll_interval_seconds)

    def _list_runs(self) -> list[dict[str, Any]]:
        output = _run_gh(
            [
                "run",
                "list",
                "--repo",
                self._repo,
                "--workflow",
                self._workflow,
                "--json",
                "displayTitle,status,conclusion",
            ]
        )
        return json.loads(output)


class FakeReconDispatcher:
    """Hermetic fake: `dispatch`/`await_completion` return canned values
    with no subprocess call -- unblocks every T1-T3 test ahead of
    `bounty-infra#18` (the real dispatch contract)."""

    def __init__(self, *, s3_key: str | None = None) -> None:
        self._s3_key = s3_key

    def dispatch(self, request: ReconRequest) -> DispatchHandle:
        return DispatchHandle(correlation_token=request.correlation_token)

    def await_completion(self, handle: DispatchHandle) -> S3Key:
        return S3Key(self._s3_key or f"recon/{handle.correlation_token}.jsonl")
