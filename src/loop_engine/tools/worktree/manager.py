"""Per-run git worktree isolation (Phase 3a).

Each run executes against its own `git worktree` on a per-run branch
(`loop/<run_id>`). `worktree_run` is the single integration seam: it chdir's
the process into the worktree so the model-facing artifact tree (`src/`,
`docs/`, `sprints/`, `.agent/`) and the tool sandbox (which key off
`Path.cwd()`) are confined to it — while State snapshots stay in the
orchestrator's main checkout, because `worktree_run` pins `state_io`'s state
root to the original CWD before the chdir.

This is a **sanctioned subprocess surface** (`git worktree`), alongside
`issue_io`'s `gh` and `coder_tools`'s `pytest`: fixed argv, `shell=False`, and
the `run_id` is validated before it reaches git. No file-write calls
(`open`/`write_text`/`write_bytes`) live here — that boundary stays with
`state_io`.

Selected by `LOOP_ENGINE_ISOLATION=worktree` (default off): when unset,
`worktree_run` is a no-op passthrough and behavior is byte-identical to the
pre-isolation engine.

Retention is deliberate: worktrees are **retained** after a run (a paused run
resumes into its worktree; a completed run is a PR source; a failed run is
inspectable). Removal is explicit — `cleanup()` / the CLI `prune-worktrees`
command.
"""

import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from loop_engine.tools.isolation import worktree_needed
from loop_engine.tools.state_io.writer import set_state_root, validate_run_id

_WORKTREE_ROOT_ENV_VAR = "LOOP_ENGINE_WORKTREE_ROOT"
_DEFAULT_WORKTREE_DIRNAME = ".worktrees"

_GIT_TIMEOUT_S = 60


class WorktreeError(Exception):
    """A git worktree operation failed, or a resume targeted a worktree that no
    longer exists."""


def use_worktree_isolation() -> bool:
    """Whether the selected isolation mode needs a per-run git worktree
    (`worktree`/`container`/`sandbox`). Delegates to `tools.isolation` so the
    flag has a single reader; the container/sandbox modes still run inside a
    worktree (the sandbox mounts it)."""
    return worktree_needed()


def worktree_root() -> Path:
    """Base directory holding per-run worktrees. `LOOP_ENGINE_WORKTREE_ROOT`
    overrides the default `.worktrees/` under the current checkout. Resolved
    against the CWD at call time, so it must be read before any chdir."""
    override = os.environ.get(_WORKTREE_ROOT_ENV_VAR, "").strip()
    base = Path(override) if override else Path.cwd() / _DEFAULT_WORKTREE_DIRNAME
    return base.resolve()


def worktree_path(run_id: str) -> Path:
    """Absolute path of the worktree for `run_id`."""
    return worktree_root() / validate_run_id(run_id)


def branch_name(run_id: str) -> str:
    """Per-run branch a worktree is checked out on."""
    return f"loop/{validate_run_id(run_id)}"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command with a fixed argv and no shell."""
    return subprocess.run(  # noqa: S603 — fixed argv (git + literal subcommands), no shell; the only variable args are a path derived from a validated run_id
        ["git", *args],  # noqa: S607 — resolved via PATH intentionally, matching issue_io's `gh` (git's location varies by platform)
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_S,
        check=False,
    )


def _registered_worktrees() -> set[Path]:
    result = _git("worktree", "list", "--porcelain")
    paths: set[Path] = set()
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            paths.add(Path(line[len("worktree ") :]).resolve())
    return paths


def _is_registered(path: Path) -> bool:
    return path.resolve() in _registered_worktrees()


def _branch_exists(branch: str) -> bool:
    return _git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0


def create(run_id: str) -> Path:
    """Create (or reuse) the worktree for `run_id` and return its path.

    Idempotent: an already-registered worktree at the target path is returned
    as-is, so a re-run or resume reuses the same tree and branch.
    """
    path = worktree_path(run_id)
    if _is_registered(path):
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    branch = branch_name(run_id)
    # Reuse the branch if it survives from an earlier run whose worktree was
    # removed; otherwise cut a fresh one from HEAD.
    if _branch_exists(branch):
        result = _git("worktree", "add", str(path), branch)
    else:
        result = _git("worktree", "add", str(path), "-b", branch, "HEAD")
    if result.returncode != 0:
        raise WorktreeError(f"git worktree add failed for run {run_id!r}: {result.stderr.strip()}")
    return path


def cleanup(run_id: str) -> None:
    """Remove the worktree and its branch for `run_id` (best-effort)."""
    path = worktree_path(run_id)
    if _is_registered(path):
        _git("worktree", "remove", "--force", str(path))
    _git("worktree", "prune")
    _git("branch", "-D", branch_name(run_id))


def prune_all() -> list[str]:
    """Remove every worktree under the worktree root; returns the run_ids
    removed. Also prunes stale admin entries for hand-deleted worktrees."""
    root = worktree_root()
    removed: list[str] = []
    for path in sorted(_registered_worktrees()):
        if path.parent.resolve() == root:
            _git("worktree", "remove", "--force", str(path))
            _git("branch", "-D", f"loop/{path.name}")
            removed.append(path.name)
    _git("worktree", "prune")
    return removed


@contextmanager
def worktree_run(run_id: str, *, reuse: bool = False) -> Iterator[Path | None]:
    """Run the enclosed block inside `run_id`'s worktree.

    When isolation is off, this is a no-op passthrough (yields None, no chdir).
    When on, it pins snapshots to the current (main-checkout) CWD, chdir's into
    the worktree, and restores both on exit — even on exception.

    `reuse=True` (resume) requires the worktree to already exist and errors if
    it was pruned; `reuse=False` (fresh run) creates it.
    """
    if not use_worktree_isolation():
        if reuse and _is_registered(worktree_path(run_id)):
            # R10: the converse of the missing-worktree error below. A run
            # paused under a worktree-isolated mode left a real worktree on
            # disk; resuming it under `none` would otherwise silently
            # passthrough against the *current* cwd instead of that tree.
            # Honest failure beats a silent wrong-tree resume.
            raise WorktreeError(
                f"cannot resume run {run_id!r} under isolation mode 'none': its "
                f"worktree {worktree_path(run_id)} still exists, meaning it was "
                "paused under a worktree-isolated LOOP_ENGINE_ISOLATION mode. "
                "Resume under that same mode instead."
            )
        yield None
        return

    origin = Path.cwd()
    if reuse:
        path = worktree_path(run_id)
        if not _is_registered(path):
            raise WorktreeError(
                f"cannot resume run {run_id!r}: its worktree {path} does not exist "
                "(it may have been pruned; the artifact tree cannot be reconstructed)."
            )
    else:
        path = create(run_id)

    set_state_root(origin)
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(origin)
        set_state_root(None)
