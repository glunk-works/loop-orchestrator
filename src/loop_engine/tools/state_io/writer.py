import contextvars
import re
from pathlib import Path, PurePosixPath

from loop_engine.core.state import State

_SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_ALLOWED_ARTIFACT_ROOTS = ("docs", "sprints", "src")

# Where `state/<run_id>/` snapshots are anchored. Defaults to the process CWD,
# so behavior is unchanged when execution isolation is off. Under worktree
# isolation (Phase 3a) the run chdir's into its worktree, but snapshots must
# stay in the orchestrator's main checkout — `worktree_run` pins this to the
# original CWD before the chdir. Only snapshots honor it; model-facing artifacts
# (`write_artifact`) deliberately follow the CWD into the worktree.
#
# A `ContextVar`, not a plain module global (F3): `asyncio.to_thread` copies
# the current context per worker thread, so a `set()` in one concurrent run
# (the trigger surface dispatches several) never leaks into another's reads,
# and `reset(token)` restores the prior value on exit rather than clobbering
# to `None` — re-entrant, unlike the plain-global version this replaced.
_STATE_ROOT: contextvars.ContextVar[Path | None] = contextvars.ContextVar(
    "_STATE_ROOT", default=None
)


def set_state_root(root: Path | None) -> contextvars.Token:
    """Pin (or, with None, reset to CWD) the anchor for state snapshots.

    Returns the `Token` from the underlying `ContextVar.set()`; a caller that
    wants proper re-entrant restoration should pass it to `reset_state_root`
    in a `finally` rather than calling `set_state_root(None)`, which merely
    pins the anchor back to "unset" instead of restoring whatever it was
    before this call.
    """
    return _STATE_ROOT.set(root)


def reset_state_root(token: contextvars.Token) -> None:
    """Restore the anchor `set_state_root` held before the matching `set()`."""
    _STATE_ROOT.reset(token)


def state_root() -> Path:
    """The directory `state/` is written under: the pinned root when set (an
    absolute main-checkout path, under worktree isolation), else `Path(".")`
    (the CWD, keeping the snapshot path relative as before)."""
    root = _STATE_ROOT.get()
    return root if root is not None else Path(".")


def _validate_safe_name(value: str, *, label: str) -> None:
    if not _SAFE_NAME_PATTERN.match(value):
        raise ValueError(
            f"Invalid {label}: {value!r} must match pattern {_SAFE_NAME_PATTERN.pattern!r}"
        )


def validate_run_id(run_id: str) -> str:
    """Public run_id guard (same rule the snapshot writer applies), so callers
    that derive filesystem paths from a run_id — e.g. the worktree manager —
    reuse the exact validation instead of duplicating the pattern."""
    _validate_safe_name(run_id, label="run_id")
    return run_id


def validate_artifact_relative_path(relative_path: str) -> PurePosixPath:
    """Validate a model-supplied artifact path: relative, under an allowed
    root, no traversal. Public so read-side tools (tools/coder_tools) reuse
    the exact write-side rules instead of duplicating them."""
    normalized = relative_path.replace("\\", "/")
    if not normalized or normalized.startswith("/"):
        raise ValueError(f"Invalid artifact path: {relative_path!r} must be a relative path")

    posix_path = PurePosixPath(normalized)
    parts = posix_path.parts
    if not parts or parts[0] not in _ALLOWED_ARTIFACT_ROOTS or ".." in parts:
        raise ValueError(
            f"Invalid artifact path: {relative_path!r} must stay under one of "
            f"{_ALLOWED_ARTIFACT_ROOTS} with no '..' segments"
        )
    return posix_path


def write_state_snapshot(state: State, run_id: str, stage_index: int, stage_name: str) -> Path:
    _validate_safe_name(run_id, label="run_id")
    _validate_safe_name(stage_name, label="stage_name")

    target_dir = state_root() / "state" / run_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{stage_index:02d}_{stage_name}.json"
    target_path.write_text(state.model_dump_json(), encoding="utf-8", newline="\n")
    return target_path


def write_artifact(content: str, relative_path: str) -> Path:
    posix_path = validate_artifact_relative_path(relative_path)

    target_path = Path(*posix_path.parts)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8", newline="\n")
    return target_path


# The `.agent/` semantic-state layer. These paths are engine-controlled
# constants, not model-supplied, and are deliberately kept OUT of
# `_ALLOWED_ARTIFACT_ROOTS` so model-emitted `write_artifact` edits can never
# target the scratchpad or the decisions ledger.
AGENT_DIR = ".agent"
AGENT_SCRATCHPAD_PATH = f"{AGENT_DIR}/STATE.md"
AGENT_MEMORY_PATH = f"{AGENT_DIR}/MEMORY.md"


class AppendOnlyViolationError(Exception):
    """A write to the append-only MEMORY.md ledger would drop or rewrite
    existing content instead of appending to it."""


def _agent_target(relative_path: str) -> Path:
    # Hardened even though callers pass constants: relative, under .agent/,
    # no traversal — the same discipline validate_artifact_relative_path
    # applies to model paths.
    normalized = relative_path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if not parts or parts[0] != AGENT_DIR or ".." in parts or normalized.startswith("/"):
        raise ValueError(
            f"Invalid agent-state path: {relative_path!r} must stay under '{AGENT_DIR}/'"
        )
    return Path(*parts)


def write_agent_scratchpad(content: str) -> Path:
    """Overwrite the mutable `.agent/STATE.md` scratchpad."""
    target_path = _agent_target(AGENT_SCRATCHPAD_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8", newline="\n")
    return target_path


def append_agent_memory(full_content: str) -> Path:
    """Persist the `.agent/MEMORY.md` ledger, enforcing append-only semantics.

    Callers render the complete file (existing + new entry); this rejects any
    write that does not preserve the current content as a prefix, so a finalized
    decision can never be silently edited or dropped.
    """
    target_path = _agent_target(AGENT_MEMORY_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        # newline="" (no universal-newline translation): the write below is
        # byte-exact (newline="\n"), so the prefix check must see the file's
        # actual on-disk content, not a CRLF->LF-translated view of it (F22)
        # -- otherwise a whole-file CRLF rewrite could pass as a no-op prefix.
        # Path.read_text() has no newline= param (only write_text gained one,
        # in 3.10), so this goes through Path.open() instead.
        with target_path.open(encoding="utf-8", newline="") as fh:
            existing = fh.read()
        if not full_content.startswith(existing):
            raise AppendOnlyViolationError(
                f"Refusing to write {AGENT_MEMORY_PATH}: the ledger is append-only "
                "and the new content does not preserve existing entries as a prefix."
            )
    target_path.write_text(full_content, encoding="utf-8", newline="\n")
    return target_path
