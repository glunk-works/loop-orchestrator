"""P0-D12 no-runtime-edge assertion -- `tools/scope_validator` must import
nothing from any other `loop_orchestrator.tools.*` package at runtime (in
particular no `inventory_db`; the `Target` reference is `TYPE_CHECKING`-only).
The standalone-leaf analog of `tests/tools/inventory_db/test_boundary.py`'s
sole-importer check.

Hardened per a guard-adversary (BL-32) pass: a bare `Import`/`ImportFrom`
walk under-detects a genuine runtime edge in three ways this file now closes
-- a relative import (`from ..inventory_db import models`) resolves to only
its bare tail on the AST node, a locally-shadowed `TYPE_CHECKING = True` was
exempted by surface name alone, and `importlib.import_module(...)` /
`__import__(...)` calls were invisible to an Import/ImportFrom-only walk.
"""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "src" / "loop_orchestrator"
SCOPE_VALIDATOR_DIR = SRC_DIR / "tools" / "scope_validator"
ALLOWED_RUNTIME_PREFIX = "loop_orchestrator.tools.scope_validator"
FORBIDDEN_PREFIX = "loop_orchestrator.tools"


def _containing_package(path: Path) -> str:
    relative = path.relative_to(SRC_DIR.parent)
    return ".".join(relative.parts[:-1])


def _resolve_import_from_targets(file_package: str, node: ast.ImportFrom) -> list[str]:
    if node.level == 0:
        if node.module:
            return [node.module]
        return [alias.name for alias in node.names]
    # Relative import: level 1 means "this file's own package", each extra
    # level walks one package further up before appending `node.module`
    # (or, for `from .. import x`, each alias name directly).
    parts = file_package.split(".") if file_package else []
    up = node.level - 1
    if up:
        parts = parts[: len(parts) - up]
    base = ".".join(parts)
    if node.module:
        return [f"{base}.{node.module}" if base else node.module]
    return [f"{base}.{alias.name}" if base else alias.name for alias in node.names]


def _typing_type_checking_is_trustworthy(tree: ast.Module) -> bool:
    imported_from_typing = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "typing":
            if any(alias.name == "TYPE_CHECKING" and alias.asname is None for alias in node.names):
                imported_from_typing = True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TYPE_CHECKING":
                    return False
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "TYPE_CHECKING":
                return False
    return imported_from_typing


def _is_type_checking_guard(node: ast.If, type_checking_is_trustworthy: bool) -> bool:
    if not type_checking_is_trustworthy:
        return False
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return bool(isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")


def _is_forbidden(module: str) -> bool:
    return module.startswith(FORBIDDEN_PREFIX) and not module.startswith(ALLOWED_RUNTIME_PREFIX)


def _dynamic_import_targets(tree: ast.Module) -> list[str]:
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_import_module = (
            isinstance(func, ast.Attribute)
            and func.attr == "import_module"
            and isinstance(func.value, ast.Name)
            and func.value.id == "importlib"
        )
        is_dunder_import = isinstance(func, ast.Name) and func.id == "__import__"
        if not (is_import_module or is_dunder_import):
            continue
        if (
            node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            found.append(node.args[0].value)
    return found


def _runtime_imports_of_other_tools(tree: ast.Module, file_package: str = "") -> list[str]:
    found: list[str] = []
    type_checking_is_trustworthy = _typing_type_checking_is_trustworthy(tree)

    class _Visitor(ast.NodeVisitor):
        def visit_If(self, node: ast.If) -> None:
            if _is_type_checking_guard(node, type_checking_is_trustworthy):
                # Only the `if TYPE_CHECKING:` body is exempt -- the
                # else-branch (if any) still runs at import time.
                for stmt in node.orelse:
                    self.visit(stmt)
                return
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                if _is_forbidden(alias.name):
                    found.append(alias.name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            for target in _resolve_import_from_targets(file_package, node):
                if _is_forbidden(target):
                    found.append(target)

    _Visitor().visit(tree)
    for target in _dynamic_import_targets(tree):
        if _is_forbidden(target):
            found.append(target)
    return found


def test_scope_validator_has_no_runtime_edge_onto_other_tools() -> None:
    for path in SCOPE_VALIDATOR_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        found = _runtime_imports_of_other_tools(tree, _containing_package(path))
        assert not found, f"{path} has a runtime import edge onto: {found}"


def test_detector_flags_a_planted_runtime_import_outside_type_checking() -> None:
    planted = ast.parse("from loop_orchestrator.tools.inventory_db.models import Target\n")
    assert _runtime_imports_of_other_tools(planted) == [
        "loop_orchestrator.tools.inventory_db.models"
    ]


def test_detector_does_not_flag_a_type_checking_only_import() -> None:
    guarded = ast.parse(
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from loop_orchestrator.tools.inventory_db.models import Target\n"
    )
    assert _runtime_imports_of_other_tools(guarded) == []


def test_detector_does_not_flag_an_import_from_within_scope_validator_itself() -> None:
    internal = ast.parse("from loop_orchestrator.tools.scope_validator.rules import ScopeRules\n")
    assert _runtime_imports_of_other_tools(internal) == []


def test_detector_resolves_a_relative_import_to_its_absolute_target() -> None:
    # BL-32 finding: a relative import records only its bare tail
    # (`inventory_db.models`) on the AST node -- the walker must resolve it
    # against the importing file's own package to see the real edge.
    relative = ast.parse("from ..inventory_db.models import Target\n")
    assert _runtime_imports_of_other_tools(
        relative, file_package="loop_orchestrator.tools.scope_validator"
    ) == ["loop_orchestrator.tools.inventory_db.models"]


def test_detector_ignores_a_shadowed_type_checking_name() -> None:
    # BL-32 finding: exempting any `if <Name "TYPE_CHECKING">:` by surface
    # name alone lets a locally-rebound `TYPE_CHECKING = True` smuggle a
    # real runtime import past the guard.
    shadowed = ast.parse(
        "TYPE_CHECKING = True\n"
        "if TYPE_CHECKING:\n"
        "    from loop_orchestrator.tools.inventory_db.models import Target\n"
    )
    assert _runtime_imports_of_other_tools(shadowed) == [
        "loop_orchestrator.tools.inventory_db.models"
    ]


def test_detector_flags_a_dynamic_import_of_a_forbidden_module() -> None:
    # BL-32 finding: `importlib.import_module(...)` / `__import__(...)` are
    # `ast.Call` nodes, invisible to a pure Import/ImportFrom walk.
    via_importlib = ast.parse(
        'import importlib\nimportlib.import_module("loop_orchestrator.tools.inventory_db")\n'
    )
    assert _runtime_imports_of_other_tools(via_importlib) == [
        "loop_orchestrator.tools.inventory_db"
    ]
    via_dunder = ast.parse('__import__("loop_orchestrator.tools.inventory_db")\n')
    assert _runtime_imports_of_other_tools(via_dunder) == ["loop_orchestrator.tools.inventory_db"]
