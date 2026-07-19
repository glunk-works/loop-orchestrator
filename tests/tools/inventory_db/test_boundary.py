"""`psycopg` sole-importer boundary test (T2, P0-D9) -- the psycopg analog of
`tests/tools/test_keyring_boundary.py`. `tools/inventory_db/psycopg_impl.py`
is the only module in `src/` permitted to import `psycopg`; everything else
(including `factory.py`, which only imports the `PsycopgInventory` class)
must stay clear of it.
"""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "src" / "loop_orchestrator"
ALLOWED_MODULE = SRC_DIR / "tools" / "inventory_db" / "psycopg_impl.py"


def _imports_psycopg(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "psycopg" or alias.name.startswith("psycopg.") for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "psycopg" or node.module.startswith("psycopg."):
                return True
    return False


def test_psycopg_imported_only_by_psycopg_impl() -> None:
    for path in SRC_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        if _imports_psycopg(tree):
            assert path == ALLOWED_MODULE, (
                f"{path} imports psycopg but is not the sole permitted module"
            )
