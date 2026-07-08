"""Disk-backed artifact storage.

During the LangGraph migration, artifact bodies move out of `State.artifacts`
(inline text) and onto disk, with `State.artifact_refs` holding a path + digest
pointer for each. This module is the mediator:

- `mirror_to_disk(state)` writes any body not yet on disk (or whose content
  changed) and refreshes its ref. The engine calls this at snapshot time, so
  personas keep populating `state.artifacts` unchanged and externalization
  happens centrally.
- `get_artifact` / `has_artifact` read through the ref (falling back to the
  inline body during the dual-field phase), so new (LangGraph) readers never
  touch `state.artifacts` directly.

All writes are delegated to `tools/state_io` so the single-writer boundary
holds; reads go straight to the filesystem.
"""

from pathlib import Path

from loop_engine.core.state import ArtifactRef, State, artifact_digest, default_artifact_path
from loop_engine.tools.state_io.writer import write_artifact


def mirror_to_disk(state: State) -> State:
    """Write every inline artifact body to disk and (re)point its ref.

    Idempotent: a body whose ref already matches its digest is skipped, so
    re-mirroring an unchanged state does no I/O.
    """
    refs = dict(state.artifact_refs)
    changed = False
    for key, body in state.artifacts.items():
        digest = artifact_digest(body)
        existing = refs.get(key)
        if existing is not None and existing.digest == digest:
            continue
        path = default_artifact_path(state.run_id, key)
        write_artifact(body, path)
        refs[key] = ArtifactRef(path=path, digest=digest, size_bytes=len(body.encode("utf-8")))
        changed = True
    if not changed:
        return state
    return state.model_copy(update={"artifact_refs": refs})


def get_artifact(state: State, key: str, default: str = "") -> str:
    """Read an artifact body via its disk ref, falling back to the inline body
    (dual-field phase) and then to `default`."""
    ref = state.artifact_refs.get(key)
    if ref is not None:
        path = Path(ref.path)
        if path.exists():
            return path.read_text()
    if key in state.artifacts:
        return state.artifacts[key]
    return default


def has_artifact(state: State, key: str) -> bool:
    """Whether a non-empty artifact body is available for `key`."""
    return bool(get_artifact(state, key).strip())
