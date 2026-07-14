"""Local-git working-tree writes in a cloned tree (Phase 5 piece 3).

The flow-forced local-git write surface deferred from Sprint 22b:
`flows/maintenance` needs to `checkout -b`, `add`, `commit`, and `push`
inside a repo cloned by `tools/repo_io.clone_repo`. This is a **fourth
sanctioned subprocess surface** (mirroring `tools/worktree/manager.py::_git`'s
posture exactly: fixed argv, `shell=False`, a hard timeout, `check=False`
with an explicit raise) — kept in its own module rather than bolted onto
`tools/repo_io` (which shells `gh`, the remote GitHub API) or
`tools/worktree` (strictly the orchestrator's own per-run isolation, keyed
off `run_id`; a maintenance clone is a foreign tree). `git push` here rides
`gh`'s own credential helper in the cloned tree — no `keyring` import, no
new credential path.

Every verb validates its `tree` argument by reusing
`tools/repo_io/github.py::_validate_clone_dest` (relative, no `..`, no
symlink escape out of the run tree) before it reaches git.
"""

import subprocess
from pathlib import Path

from loop_engine.tools.repo_io.github import _validate_clone_dest

_GIT_TIMEOUT_S = 60


class GitIOError(Exception):
    """A local git operation failed."""


def _git(tree: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command against `tree` with a fixed argv and no shell."""
    return subprocess.run(  # noqa: S603 — fixed argv (git + literal subcommands), no shell; tree is validated before this call reaches git
        ["git", "-C", str(tree), *args],  # noqa: S607 — resolved via PATH intentionally, matching worktree's `git`
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_S,
        check=False,
    )


def _run(tree: str, *args: str) -> subprocess.CompletedProcess[str]:
    validated = _validate_clone_dest(tree)
    result = _git(validated, *args)
    if result.returncode != 0:
        raise GitIOError(f"git {' '.join(args)} failed in {tree!r}: {result.stderr.strip()}")
    return result


def has_changes(tree: str) -> bool:
    """True if the working tree at `tree` has any staged or unstaged change.

    Read-only (`git status --porcelain`) — lets a caller distinguish a run
    that produced a diff worth shipping from a no-op run, so `commit_all`
    (which fails on an empty index) is never reached with nothing to commit.
    """
    return bool(_run(tree, "status", "--porcelain").stdout.strip())


def checkout_branch(tree: str, branch: str) -> None:
    """Create and switch to `branch` in the working tree at `tree`."""
    _run(tree, "checkout", "-b", branch)


def commit_all(tree: str, message: str) -> None:
    """Stage and commit every change in the working tree at `tree`."""
    _run(tree, "add", "-A")
    _run(tree, "commit", "-m", message)


def push_branch(tree: str, branch: str, *, remote: str = "origin") -> None:
    """Push `branch` to `remote` from the working tree at `tree`."""
    _run(tree, "push", remote, branch)
