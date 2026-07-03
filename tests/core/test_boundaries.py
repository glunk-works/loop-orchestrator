import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine" / "core"
ALLOWED_PERSONA_MODULE = "loop_engine.personas.base"


def _imported_module_names(tree: ast.Module) -> list[str]:
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_core_imports_no_concrete_persona_module() -> None:
    for path in CORE_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for module in _imported_module_names(tree):
            is_persona_import = module == "loop_engine.personas" or module.startswith(
                "loop_engine.personas."
            )
            if is_persona_import:
                assert module == ALLOWED_PERSONA_MODULE, (
                    f"{path} imports disallowed persona module: {module}"
                )
