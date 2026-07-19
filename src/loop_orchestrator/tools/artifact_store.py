"""Disk-backed artifact publication.

`State.artifacts` (inline text) is the single source of truth for artifact
bodies — it is also the prompt-cache prefix, so it is never routed through
disk on the read side. This module handles the one thing that still needs a
disk write: publishing those bodies into the working tree so they ship as
documentation in the managed repo's PR (`flows/maintenance` commits the whole
tree).

- `publish_artifacts(state)` writes every inline body to disk, skipping the
  write when the on-disk content already matches (see its docstring for the
  read-compare detail).
- `has_artifact` checks the inline body directly.

All writes are delegated to `tools/state_io` so the single-writer boundary
holds.
"""

from pathlib import Path

from loop_orchestrator.core.state import State, default_artifact_path
from loop_orchestrator.tools.state_io.writer import write_artifact


def publish_artifacts(state: State) -> None:
    """Write every inline artifact body to disk under `docs/artifacts/<run_id>/`.

    A pure side effect — mutates no state. Reads back the on-disk content as
    bytes to compare against the inline body's UTF-8 encoding and skips the
    write when they already match; the read still happens for every artifact
    that already exists on disk (`path.exists()` short-circuits it on first
    publish), so this avoids a redundant write, not I/O altogether. Comparing
    bytes rather than `read_text()` means a corrupt, non-UTF-8 on-disk
    artifact can never raise `UnicodeDecodeError` here — it just compares
    unequal and gets overwritten, which was going to happen anyway.
    """
    for key, body in state.artifacts.items():
        path = Path(default_artifact_path(state.run_id, key))
        if path.exists() and path.read_bytes() == body.encode("utf-8"):
            continue
        write_artifact(body, str(path))


def has_artifact(state: State, key: str) -> bool:
    """Whether a non-empty artifact body is available for `key`."""
    return bool(state.artifacts.get(key, "").strip())
