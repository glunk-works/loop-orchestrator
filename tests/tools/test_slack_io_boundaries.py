"""Boundary posture for `tools/slack_io` (Sprint 39/BL-2 pass 1, extended
Sprint 40/BL-2 pass 2 for the inbound transport), mirroring
`tests/trigger/test_boundaries.py`: it is a `tools/*` module that imports no
`keyring`, writes no files directly, and adds no subprocess surface — the
five sanctioned subprocess surfaces (`tests/tools/test_subprocess_surfaces.py`)
are unaffected. It also asserts the FD2/FD4 import-graph shape: the pure
contract in `core/notify.py` never imports `slack_sdk`, and no module in the
package imports `slack_sdk` at module scope (it must stay function-scoped,
inside `SlackNotifier.emit` for the outbound path and inside
`inbound.build_listener_from_env`/`SocketModeListener._handle` for the
inbound path added in pass 2). `_slack_io_modules()` globs every `.py` file
under the package directory, so `inbound.py` is covered by the existing
assertions automatically — `test_boundary_suite_covers_inbound_module`
below just pins that `inbound.py` is actually present in that enumeration,
so a future rename/move can't silently drop it out of coverage.
"""

import ast
from pathlib import Path

SLACK_IO_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "loop_orchestrator"
    / "tools"
    / "slack_io"
)
NOTIFY_MODULE = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "loop_orchestrator"
    / "core"
    / "notify.py"
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


def _module_scope_imports_named_module(tree: ast.Module, name: str) -> bool:
    """Like `_imports_named_module`, but only looks at imports at the top
    level of the module — an import nested inside a function body (the
    required posture for `slack_sdk` in `SlackNotifier.emit`) does not
    count."""
    for node in tree.body:
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


def _slack_io_modules() -> list[Path]:
    return sorted(SLACK_IO_DIR.rglob("*.py"))


def test_slack_io_package_imports_no_keyring() -> None:
    for path in _slack_io_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        assert not _imports_named_module(tree, "keyring"), f"{path} imports keyring"


def test_slack_io_package_writes_no_files_directly() -> None:
    for path in _slack_io_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_write_calls(tree)
        assert not calls, f"{path} calls disallowed file-write function(s): {calls}"


def test_slack_io_package_adds_no_subprocess_surface() -> None:
    for path in _slack_io_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        surfaces = _subprocess_surfaces(tree)
        assert not surfaces, f"{path} introduces a subprocess surface: {surfaces}"


def test_core_notify_imports_no_slack_sdk() -> None:
    tree = ast.parse(NOTIFY_MODULE.read_text(), filename=str(NOTIFY_MODULE))
    assert not _imports_named_module(tree, "slack_sdk"), "core/notify.py imports slack_sdk"
    assert not _imports_named_module(tree, "loop_orchestrator.tools.slack_io"), (
        "core/notify.py imports tools/slack_io -- it must stay a leaf"
    )


def test_slack_io_package_never_imports_slack_sdk_at_module_scope() -> None:
    for path in _slack_io_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        assert not _module_scope_imports_named_module(tree, "slack_sdk"), (
            f"{path} imports slack_sdk at module scope -- it must be function-scoped "
            "inside SlackNotifier.emit so the no-op default never pulls it in"
        )


def test_boundary_suite_covers_inbound_module() -> None:
    assert (SLACK_IO_DIR / "inbound.py") in _slack_io_modules(), (
        "inbound.py is missing from the slack_io boundary sweep -- the "
        "keyring/write/subprocess/module-scope-import assertions above "
        "would silently stop covering it"
    )


def test_boundary_suite_covers_reply_module() -> None:
    assert (SLACK_IO_DIR / "reply.py") in _slack_io_modules(), (
        "reply.py (T4, ephemeral replies) is missing from the slack_io "
        "boundary sweep -- the keyring/write/subprocess/module-scope-import "
        "assertions above would silently stop covering it"
    )


def test_boundary_suite_covers_escalation_module() -> None:
    assert (SLACK_IO_DIR / "escalation.py") in _slack_io_modules(), (
        "escalation.py (T3, the Slack escalation filer/renderer/parser) is "
        "missing from the slack_io boundary sweep -- the "
        "keyring/write/subprocess/module-scope-import assertions above "
        "would silently stop covering it"
    )
