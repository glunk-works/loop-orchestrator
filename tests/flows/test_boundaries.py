"""`flows/` boundary posture (Phase 5 piece 3), mirroring
`tests/trigger/test_boundaries.py`: no module under `flows/` imports
`keyring`, performs a direct file write, or introduces a subprocess surface
of its own. The deliberate difference from `trigger/`: `flows/` *does* reach
a new subprocess surface, `tools/git_io` -- but only by calling it, never by
shelling out itself. `tests/tools/test_subprocess_surfaces.py` asserts
`git_io` is the only module that actually shells out."""

import ast
from pathlib import Path

FLOWS_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_orchestrator" / "flows"

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


def _imports_keyring(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "keyring" or alias.name.startswith("keyring.") for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "keyring" or node.module.startswith("keyring."):
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


def _flows_modules() -> list[Path]:
    return sorted(FLOWS_DIR.rglob("*.py"))


def test_flows_package_imports_no_keyring() -> None:
    for path in _flows_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        assert not _imports_keyring(tree), f"{path} imports keyring"


def test_flows_package_writes_no_files_directly() -> None:
    for path in _flows_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_write_calls(tree)
        assert not calls, f"{path} calls disallowed file-write function(s): {calls}"


def test_flows_package_adds_no_subprocess_surface_of_its_own() -> None:
    for path in _flows_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        surfaces = _subprocess_surfaces(tree)
        assert not surfaces, f"{path} introduces a subprocess surface: {surfaces}"


def test_flows_modules_provably_enumerate_bootstrap() -> None:
    # Sharpens the auto-discovery above: proves `_flows_modules()` actually
    # walks into the newer `flows/bootstrap` package (Phase 5 piece 4), not
    # just the pre-existing `flows/maintenance` one.
    bootstrap_dir = FLOWS_DIR / "bootstrap"
    discovered = _flows_modules()
    assert any(bootstrap_dir in path.parents for path in discovered)
    assert bootstrap_dir / "flow.py" in discovered
