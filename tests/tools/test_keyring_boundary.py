import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_orchestrator"
ALLOWED_MODULE = SRC_DIR / "tools" / "llm" / "client.py"


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


def test_keyring_imported_only_by_llm_client() -> None:
    for path in SRC_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        if _imports_keyring(tree):
            assert path == ALLOWED_MODULE, (
                f"{path} imports keyring but is not the sole permitted module"
            )
