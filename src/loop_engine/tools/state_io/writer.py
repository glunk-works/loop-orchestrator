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


def _validate_artifact_relative_path(relative_path: str) -> PurePosixPath:
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
    posix_path = _validate_artifact_relative_path(relative_path)

    target_path = Path(*posix_path.parts)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)
    return target_path
