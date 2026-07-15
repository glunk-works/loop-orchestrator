"""The bootstrap flow: create -> clone -> scaffold -> commit -> push `main`
-> create `develop` -> protect (`main` + `develop`).

The second top-level orchestrator-level flow (sibling of
`flows/maintenance`, Phase 5 piece 4): the factory verb that brings a new,
conventions-conformant repo into *existence*. Unlike `flows/maintenance` it
runs **no inner loop** (`run_in_tree`), has **no green gate**, and opens
**no PR** — a brand-new repo has no commits and nothing to review into.
`create_repository` -> `clone_repo` (empty tree) -> `checkout_branch(main)`
(names the unborn default branch deterministically) -> `scaffold.
write_skeleton` (the templates + injected conventions `CLAUDE.md`) ->
`commit_all` -> `push_branch(main)` -> `create_branch(develop, base=main)`
-> `create_ruleset(main, develop)` (sprint 36, BL-21). Ordering is
load-bearing twice over: `create_branch` reads the base ref's SHA over the
API, so it must come *after* `main` is pushed remotely; `create_ruleset`
runs **last** because a `pull_request` rule on `main` would reject the
scaffold's own initial direct push if installed any earlier (FD7,
sprint 36 plan).

BL-21: a repository ruleset is only installable on a **public** repo under
the org's Free plan (private repos need GitHub Team) — so `BootstrapRequest.
private` defaults to `False`: protection is the invariant `run_bootstrap`
guarantees for its own default request shape, not a claim about
`repo_io.create_repository`/the MCP `github_server.create_repository` verb
in general -- both of those keep their own, separate `private=True` default
(S8, sprint 36 review), unaffected by this flow. Privacy on a bootstrap
request is an opt-in that knowingly forfeits it. When `request.private=True`,
`create_ruleset` is not attempted at all — attempting a call already known
to 403 and swallowing the failure into a log line is exactly BL-16's shape
(a check reporting success on a property it never verified), so this flow
refuses to pretend: it skips the call outright and reports
`ruleset_installed=False` on the result, never a silent `CREATED`.

A *live* `create_ruleset` call can still fail (R2, sprint 36 review) even on a
public repo -- by then `main` is already pushed to a real, existing remote
repo, so the failure is caught and reported as `RULESET_FAILED` with the
`RepoRef` intact, rather than propagating and leaving the caller with a
dangling repo it has no slug to tear down (FD11).

Collaborators (`repo_io`, `git_io`, `scaffold`) are injectable, mirroring
`flows/maintenance`, so tests fake every external effect: no real create,
clone, or push runs in CI. See `tests/flows/bootstrap/test_flow.py` /
`tests/flows/bootstrap/test_integration.py`.
"""

import logging
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from loop_engine.tools import git_io as _git_io_module
from loop_engine.tools import repo_io as _repo_io_module
from loop_engine.tools import scaffold as _scaffold_module
from loop_engine.tools.repo_io import RepoRef, RulesetInstallError
from loop_engine.tools.scaffold.writer import _sanitize_pkg_name

logger = logging.getLogger(__name__)


class BootstrapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    org: str = "glunk-works"
    kind: str = "python"
    private: bool = Field(
        default=False,
        description=(
            "Defaults to False: repository rulesets (BL-21's protection fix) "
            "are only installable on a PUBLIC repo under the org's Free plan "
            "-- a private repo needs GitHub Team, the same 403 that blocked "
            "the org-level fix (FD3, sprint 36). Set True only as an "
            "explicit, deliberate opt-in that KNOWINGLY FORFEITS branch "
            "protection: run_bootstrap will not even attempt create_ruleset "
            "in that case, and the returned BootstrapResult.ruleset_installed "
            "will be False."
        ),
    )
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
    RULESET_FAILED = "ruleset_failed"
    """`create_ruleset` was attempted (repo is public) and raised
    `repo_io.RulesetInstallError` (S5, sprint 36 review) -- `create_ruleset`
    itself raises this only when the underlying `gh` call failed to complete
    (a wrapped `subprocess.SubprocessError`: `CalledProcessError`/
    `TimeoutExpired`), meaning the POST was genuinely rejected or never
    completed, so the repo is genuinely NOT protected. This flow catches only
    `RulesetInstallError`, not a bare `Exception` -- `flows/` imports no
    `subprocess` of its own (`tests/flows/test_boundaries.py`), so
    `create_ruleset` wraps the transport failure into this typed exception,
    mirroring `RepoNotResolvableError`'s precedent. A successful POST that
    returns an unparseable body is a *different* failure mode (the ruleset
    likely WAS created) and is not wrapped -- it propagates unwrapped rather
    than being mislabeled RULESET_FAILED, which would tell an operator the
    repo is safe to tear down when it may already be protected. The repo
    exists and `main` is already pushed, so the
    `RepoRef` is still returned -- a caller doing FD11 teardown needs the
    slug, not an exception with no result. Distinct from a `private=True`
    request (which reports `CREATED` with `ruleset_installed=False` because
    the call was never attempted at all -- see `BootstrapRequest.private`)."""


class BootstrapResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: BootstrapStatus
    repo: RepoRef
    default_branch: str
    integration_branch: str
    ruleset_installed: bool
    """Whether `create_ruleset` actually ran. `True` only when the repo was
    created public and the ruleset call was made; `False` for a `private=True`
    request, where it is never attempted (see `BootstrapRequest.private`).
    Always inspect this rather than inferring protection from `status`
    alone -- `status` is `CREATED` either way (BL-16: a status that reports
    success must not double as a claim about a property it didn't check)."""
    ruleset_id: int | None = None
    """The ruleset `id` returned by a successful `create_ruleset` call (S4,
    sprint 36 review) -- carried explicitly rather than inferred from "no
    exception was raised". `None` for a `private=True` request (never
    attempted) and for the `RULESET_FAILED` path (the call did not
    succeed)."""
    ruleset_error: str | None = None
    """`str(exc)` of the `RulesetInstallError` that produced `RULESET_FAILED`
    (S6, sprint 36 review) -- the 403-vs-422 distinction is the primary
    diagnostic signal for an operator (permission/plan problem vs. a
    rejected request body), and `RULESET_FAILED` alone carries neither.
    `None` on every other path."""


def run_bootstrap(
    request: BootstrapRequest,
    *,
    repo_io=_repo_io_module,
    git_io=_git_io_module,
    scaffold=_scaffold_module,
) -> BootstrapResult:
    """Chain create -> clone -> scaffold -> commit -> push `main` -> create
    `develop` -> protect for `request`. No inner loop, no green gate, no PR."""
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

    ruleset_id: int | None = None
    if request.private:
        logger.warning(
            "skipping ruleset installation on %s/%s: private=True forfeits "
            "branch protection -- repository rulesets require GitHub Team on "
            "private repos under the org's Free plan (BL-21/FD3)",
            owner,
            repo_name,
        )
        ruleset_installed = False
    else:
        logger.info(
            "installing branch-protection ruleset on %s/%s (%s, %s)",
            owner,
            repo_name,
            request.default_branch,
            request.integration_branch,
        )
        try:
            ruleset_id = repo_io.create_ruleset(
                owner, repo_name, branches=[request.default_branch, request.integration_branch]
            )
        except RulesetInstallError as exc:
            # S5, sprint 36 review: `create_ruleset` raises this typed error
            # only when the underlying `gh` call itself failed to complete
            # (a wrapped subprocess.SubprocessError -- CalledProcessError/
            # TimeoutExpired), meaning the ruleset genuinely was not created.
            # A successful POST that returns an unparseable body
            # (json.JSONDecodeError/KeyError out of `create_ruleset`) is NOT
            # wrapped in this type -- it means the call likely SUCCEEDED, so
            # it propagates here rather than being mislabeled RULESET_FAILED,
            # which would tell an operator the repo is unprotected and safe
            # to tear down. `flows/` imports no `subprocess` of its own
            # (`tests/flows/test_boundaries.py`) -- this typed exception is
            # how that transport failure crosses the boundary.
            logger.exception(
                "create_ruleset failed on %s/%s -- the repo exists and %s is already "
                "pushed, but is NOT protected; returning the RepoRef so the caller can "
                "decide whether to tear it down (FD11)",
                owner,
                repo_name,
                request.default_branch,
            )
            return BootstrapResult(
                status=BootstrapStatus.RULESET_FAILED,
                repo=repo,
                default_branch=request.default_branch,
                integration_branch=request.integration_branch,
                ruleset_installed=False,
                ruleset_id=None,
                ruleset_error=str(exc),
            )
        ruleset_installed = True

    return BootstrapResult(
        status=BootstrapStatus.CREATED,
        repo=repo,
        default_branch=request.default_branch,
        integration_branch=request.integration_branch,
        ruleset_installed=ruleset_installed,
        ruleset_id=ruleset_id,
        ruleset_error=None,
    )
