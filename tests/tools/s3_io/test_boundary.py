"""`boto3` sole-importer boundary test (T1, S47-D3) -- the boto3 analog of
`tests/tools/inventory_db/test_boundary.py`. `tools/s3_io/fetcher.py` is the
only module in `src/` permitted to import `boto3`; everything else
(including `tools/recon`, which only imports the `S3Fetcher` protocol/fakes)
must stay clear of it.
"""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "src" / "loop_orchestrator"
ALLOWED_MODULE = SRC_DIR / "tools" / "s3_io" / "fetcher.py"


def _imports_boto3(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "boto3" or alias.name.startswith("boto3.") for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "boto3" or node.module.startswith("boto3."):
                return True
    return False


def test_boto3_imported_only_by_s3_io_fetcher() -> None:
    for path in SRC_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        if _imports_boto3(tree):
            assert path == ALLOWED_MODULE, (
                f"{path} imports boto3 but is not the sole permitted module"
            )
