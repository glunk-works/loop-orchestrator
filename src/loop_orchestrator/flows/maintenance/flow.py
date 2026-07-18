"""The maintenance flow: clone -> branch -> run -> green gate -> push -> PR.

The first caller to chain `tools/repo_io`'s factory verbs into an
end-to-end run over a target repo. It clones the target, cuts a local
feature branch, runs the default loop with cwd inside the clone (via
`runner.run_in_tree`, so the target's own `CLAUDE.md` / `.agent/STATE.md`
are absorbed by the existing readers) and — **only on a green gate** —
commits, pushes, and opens a PR against `base` (default `develop`). A red
gate short-circuits before any git write: no commit, no push, no PR.
Auto-merge stays impossible — `open_pr` is the terminal GitHub call.

Collaborators (`run_step`, `repo_io`, `git_io`, `run_tests`) are injectable
so tests fake every external effect: no real clone, loop, or push runs in
CI. See `tests/flows/maintenance/test_flow.py` /
`tests/flows/maintenance/test_integration.py`.
"""

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from loop_orchestrator import runner as _runner_module
from loop_orchestrator.core.state import RunStatus, State
from loop_orchestrator.runner import DEFAULT_BUDGET_USD
from loop_orchestrator.tools import git_io as _git_io_module
from loop_orchestrator.tools import repo_io as _repo_io_module
from loop_orchestrator.tools.coder_tools.run_tests import run_pytest
from loop_orchestrator.tools.repo_io import PullRef

logger = logging.getLogger(__name__)

# The Global Conventions (`.ai/context/conventions.md`) personas inject into
# managed repos mandate a `src/` layout, so this is the path the green gate
# runs against inside the clone (same convention `core/coder_gate.py` relies
# on for the in-loop evidence gate).
_TARGET_TEST_PATH = "src"


class MaintenanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo_full_name: str
    human_input: str
    branch: str
    budget_usd: float = DEFAULT_BUDGET_USD
    loop_name: str = "default"
    base: str = "develop"
    clone_dest: str | None = None

    @property
    def dest(self) -> str:
        """Where the target repo is cloned to, relative to the run tree.
        Defaults to the repo's own name when `clone_dest` isn't given."""
        return self.clone_dest or self.repo_full_name.rsplit("/", 1)[-1]

    @property
    def owner_repo(self) -> tuple[str, str]:
        owner, _, repo = self.repo_full_name.rpartition("/")
        return owner, repo


class MaintenanceStatus(str, Enum):
    OPENED_PR = "opened_pr"
    GATE_FAILED = "gate_failed"
    RUN_INCOMPLETE = "run_incomplete"
    NO_CHANGES = "no_changes"


class MaintenanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MaintenanceStatus
    pull: PullRef | None = None


class RunStep(Protocol):
    def __call__(
        self, human_input: str, tree_path: str, *, budget_usd: float, loop_name: str
    ) -> State: ...


def _default_run_tests(tree: str) -> tuple[int, str]:
    """Run the existing sanctioned `coder_tools.run_tests` pytest surface
    against the clone: chdir into `tree` so its own `src/` resolves under
    the artifact-root validator, then restore cwd."""
    origin = Path.cwd()
    os.chdir(tree)
    try:
        return run_pytest(_TARGET_TEST_PATH)
    finally:
        os.chdir(origin)


def run_maintenance(
    request: MaintenanceRequest,
    *,
    run_step: RunStep = _runner_module.run_in_tree,
    repo_io=_repo_io_module,
    git_io=_git_io_module,
    run_tests=_default_run_tests,
) -> MaintenanceResult:
    """Chain clone -> branch -> run -> green gate -> push -> PR for `request`."""
    dest = request.dest
    logger.info("cloning %s to %s", request.repo_full_name, dest)
    tree = repo_io.clone_repo(request.repo_full_name, dest)

    logger.info("checking out branch %s", request.branch)
    git_io.checkout_branch(tree, request.branch)

    logger.info("running loop_name=%s in tree", request.loop_name)
    final_state = run_step(
        request.human_input,
        tree,
        budget_usd=request.budget_usd,
        loop_name=request.loop_name,
    )

    # The green gate is a *quality* gate, not a *completion* gate: a run that
    # ended FAILED_STAGE / BUDGET_EXCEEDED / AWAITING_ISSUE left a partial (or
    # human-paused) tree whose pytest may still pass. Shipping that would turn
    # a "needs a human" pause into a merge-ready PR, so require COMPLETED first.
    if final_state.status != RunStatus.COMPLETED:
        logger.info("inner run did not complete (status=%s), no commit/push/PR", final_state.status)
        return MaintenanceResult(status=MaintenanceStatus.RUN_INCOMPLETE)

    # A completed run that changed nothing is a clean no-op — don't run the
    # gate or reach `commit_all` (which fails on an empty index) with an empty
    # diff; there is nothing to ship.
    if not git_io.has_changes(tree):
        logger.info("inner run produced no changes, no commit/push/PR")
        return MaintenanceResult(status=MaintenanceStatus.NO_CHANGES)

    logger.info("running green gate")
    exit_code, _output = run_tests(tree)
    if exit_code != 0:
        logger.info("green gate failed (exit_code=%s), no commit/push/PR", exit_code)
        return MaintenanceResult(status=MaintenanceStatus.GATE_FAILED)

    logger.info("green gate passed, committing and pushing %s", request.branch)
    git_io.commit_all(tree, f"Automated maintenance: {request.branch}")
    git_io.push_branch(tree, request.branch)

    owner, repo_name = request.owner_repo
    pull = repo_io.open_pr(
        owner,
        repo_name,
        head=request.branch,
        base=request.base,
        title=f"Automated maintenance: {request.branch}",
        body=request.human_input,
    )
    logger.info("opened PR %s", pull.url)
    return MaintenanceResult(status=MaintenanceStatus.OPENED_PR, pull=pull)
