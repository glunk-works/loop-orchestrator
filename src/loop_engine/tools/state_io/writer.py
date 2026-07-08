import re
from pathlib import Path, PurePosixPath

from loop_engine.core.state import State

_SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_ALLOWED_ARTIFACT_ROOTS = ("docs", "sprints", "src")


def _validate_safe_name(value: str, *, label: str) -> None:
    if not _SAFE_NAME_PATTERN.match(value):
        raise ValueError(
            f"Invalid {label}: {value!r} must match pattern {_SAFE_NAME_PATTERN.pattern!r}"
        )


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

    target_dir = Path("state") / run_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{stage_index:02d}_{stage_name}.json"
    target_path.write_text(state.model_dump_json())
    return target_path


def write_artifact(content: str, relative_path: str) -> Path:
    posix_path = validate_artifact_relative_path(relative_path)

    target_path = Path(*posix_path.parts)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)
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
    target_path.write_text(content)
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
        existing = target_path.read_text()
        if not full_content.startswith(existing):
            raise AppendOnlyViolationError(
                f"Refusing to write {AGENT_MEMORY_PATH}: the ledger is append-only "
                "and the new content does not preserve existing entries as a prefix."
            )
    target_path.write_text(full_content)
    return target_path
