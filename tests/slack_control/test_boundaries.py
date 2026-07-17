"""Boundary posture for `slack_control/` (Sprint 40, T5), mirroring
`tests/trigger/test_boundaries.py`: a new top-level orchestrator-level
caller that imports no `keyring`, writes no files directly, adds no
subprocess surface, and -- distinct from `trigger/` -- imports no
`slack_sdk` either (all Slack I/O goes through `tools/slack_io`)."""

import ast
from pathlib import Path

SLACK_CONTROL_DIR = (
    Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine" / "slack_control"
)

_DISALLOWED_WRITE_CALLS = {"open", "write_text", "write_bytes"}
_DISALLOWED_SUBPROCESS_MODULES = {"subprocess"}
_DISALLOWED_OS_CALLS = {
    "system",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "execv",
    "execve",
    "execvp",
    "execvpe",
}


def _imports_named_module(tree: ast.Module, name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == name or alias.name.startswith(f"{name}.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == name or node.module.startswith(f"{name}."):
                return True
    return False


def _direct_write_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in _DISALLOWED_WRITE_CALLS:
            found.append(func.id)
        elif isinstance(func, ast.Attribute) and func.attr in {"write_text", "write_bytes"}:
            found.append(func.attr)
    return found


def _subprocess_surfaces(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                alias.name for alias in node.names if alias.name in _DISALLOWED_SUBPROCESS_MODULES
            )
        elif isinstance(node, ast.ImportFrom) and node.module in _DISALLOWED_SUBPROCESS_MODULES:
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "Popen":
                found.append("Popen")
            elif isinstance(func, ast.Attribute) and func.attr in _DISALLOWED_OS_CALLS:
                found.append(f"os.{func.attr}")
            elif isinstance(func, ast.Name) and func.id == "Popen":
                found.append("Popen")
    return found


def _slack_control_modules() -> list[Path]:
    return sorted(SLACK_CONTROL_DIR.rglob("*.py"))


def test_slack_control_package_imports_no_keyring() -> None:
    for path in _slack_control_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        assert not _imports_named_module(tree, "keyring"), f"{path} imports keyring"


def test_slack_control_package_imports_no_slack_sdk() -> None:
    # Distinct from trigger/'s boundary posture: slack_control/ is the
    # orchestrator-level caller -- all Slack I/O goes through tools/slack_io,
    # never a direct slack_sdk import here.
    for path in _slack_control_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        assert not _imports_named_module(tree, "slack_sdk"), f"{path} imports slack_sdk"


def test_slack_control_package_writes_no_files_directly() -> None:
    for path in _slack_control_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_write_calls(tree)
        assert not calls, f"{path} calls disallowed file-write function(s): {calls}"


def test_slack_control_package_adds_no_subprocess_surface() -> None:
    for path in _slack_control_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        surfaces = _subprocess_surfaces(tree)
        assert not surfaces, f"{path} introduces a subprocess surface: {surfaces}"


def test_boundary_suite_covers_daemon_module() -> None:
    assert (SLACK_CONTROL_DIR / "daemon.py") in _slack_control_modules(), (
        "daemon.py (T4) is missing from the slack_control boundary sweep -- "
        "the keyring/slack_sdk/write/subprocess assertions above would "
        "silently stop covering it"
    )
