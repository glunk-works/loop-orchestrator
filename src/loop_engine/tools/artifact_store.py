"""Disk-backed artifact publication.

`State.artifacts` (inline text) is the single source of truth for artifact
bodies — it is also the prompt-cache prefix, so it is never routed through
disk on the read side. This module handles the one thing that still needs a
disk write: publishing those bodies into the working tree so they ship as
documentation in the managed repo's PR (`flows/maintenance` commits the whole
tree).

- `publish_artifacts(state)` writes every inline body to disk, reading back
  the on-disk content for comparison and skipping the write when it already
  matches — a read-compare, not a no-op: it still does a `read_text()` per
  artifact per stage, it only avoids the redundant write.
- `has_artifact` checks the inline body directly.

All writes are delegated to `tools/state_io` so the single-writer boundary
holds.
"""

from pathlib import Path

from loop_engine.core.state import State, default_artifact_path
from loop_engine.tools.state_io.writer import write_artifact


def publish_artifacts(state: State) -> None:
    """Write every inline artifact body to disk under `docs/artifacts/<run_id>/`.

    A pure side effect — mutates no state. Reads back the on-disk content to
    compare against the inline body and skips the write when they already
    match; the read still happens for every artifact on every stage, so this
    avoids a redundant write, not I/O altogether.
    """
    for key, body in state.artifacts.items():
        path = Path(default_artifact_path(state.run_id, key))
        if path.exists() and path.read_text(encoding="utf-8") == body:
            continue
        write_artifact(body, str(path))


def has_artifact(state: State, key: str) -> bool:
    """Whether a non-empty artifact body is available for `key`."""
    return bool(state.artifacts.get(key, "").strip())
