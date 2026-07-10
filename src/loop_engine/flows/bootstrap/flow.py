"""The bootstrap flow: create -> clone -> scaffold -> commit -> push `main`
-> create `develop`.

The second top-level orchestrator-level flow (sibling of
`flows/maintenance`, Phase 5 piece 4): the factory verb that brings a new,
conventions-conformant repo into *existence*. Unlike `flows/maintenance` it
runs **no inner loop** (`run_in_tree`), has **no green gate**, and opens
**no PR** — a brand-new repo has no commits and nothing to review into.
`create_repository` -> `clone_repo` (empty tree) -> `checkout_branch(main)`
(names the unborn default branch deterministically) -> `scaffold.
write_skeleton` (the templates + injected conventions `CLAUDE.md`) ->
`commit_all` -> `push_branch(main)` -> `create_branch(develop, base=main)`.
Ordering is load-bearing: `create_branch` reads the base ref's SHA over the
API, so it must come *after* `main` is pushed remotely.

Collaborators (`repo_io`, `git_io`, `scaffold`) are injectable, mirroring
`flows/maintenance`, so tests fake every external effect: no real create,
clone, or push runs in CI. See `tests/flows/bootstrap/test_flow.py` /
`tests/flows/bootstrap/test_integration.py`.
"""

import logging
from enum import Enum

from pydantic import BaseModel, ConfigDict

from loop_engine.tools import git_io as _git_io_module
from loop_engine.tools import repo_io as _repo_io_module
from loop_engine.tools import scaffold as _scaffold_module
from loop_engine.tools.repo_io import RepoRef
from loop_engine.tools.scaffold.writer import _sanitize_pkg_name

logger = logging.getLogger(__name__)


class BootstrapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    org: str = "glunk-works"
    kind: str = "python"
    private: bool = True
    default_branch: str = "main"
    integration_branch: str = "develop"
    clone_dest: str | None = None

    @property
    def dest(self) -> str:
        """Where the new repo is cloned to, relative to the run tree.
        Defaults to the repo's own name when `clone_dest` isn't given."""
        return self.clone_dest or self.name

    @property
    def pkg_name(self) -> str:
        """The Python package directory name derived from `name`, sanitized
        to a safe identifier (reuses `tools/scaffold`'s own sanitizer — the
        same validator `write_skeleton` applies again on every write, so a
        crafted `name` can never inject a path segment or non-identifier)."""
        return _sanitize_pkg_name(self.name)


class BootstrapStatus(str, Enum):
    CREATED = "created"


class BootstrapResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: BootstrapStatus
    repo: RepoRef
    default_branch: str
    integration_branch: str


def run_bootstrap(
    request: BootstrapRequest,
    *,
    repo_io=_repo_io_module,
    git_io=_git_io_module,
    scaffold=_scaffold_module,
) -> BootstrapResult:
    """Chain create -> clone -> scaffold -> commit -> push `main` -> create
    `develop` for `request`. No inner loop, no green gate, no PR."""
    logger.info("creating repository %s/%s", request.org, request.name)
    repo = repo_io.create_repository(request.name, org=request.org, private=request.private)

    logger.info("cloning %s to %s", repo.slug, request.dest)
    tree = repo_io.clone_repo(repo.slug, request.dest)

    logger.info("checking out branch %s", request.default_branch)
    git_io.checkout_branch(tree, request.default_branch)

    logger.info("writing %s skeleton into %s", request.kind, tree)
    scaffold.write_skeleton(
        tree, kind=request.kind, pkg_name=request.pkg_name, repo_name=request.name
    )

    logger.info("committing initial scaffold")
    git_io.commit_all(tree, f"Initial scaffold: conventions + {request.kind} skeleton")

    logger.info("pushing %s", request.default_branch)
    git_io.push_branch(tree, request.default_branch)

    owner, repo_name = repo.slug.split("/", 1)
    logger.info("creating integration branch %s", request.integration_branch)
    repo_io.create_branch(owner, repo_name, request.integration_branch, base=request.default_branch)

    return BootstrapResult(
        status=BootstrapStatus.CREATED,
        repo=repo,
        default_branch=request.default_branch,
        integration_branch=request.integration_branch,
    )
