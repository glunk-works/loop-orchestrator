import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"
ALLOWED_DIR = SRC_DIR / "tools" / "state_io"
DISALLOWED_WRITE_CALLS = {"open", "write_text", "write_bytes"}


def _direct_write_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in DISALLOWED_WRITE_CALLS:
            found.append(func.id)
        elif isinstance(func, ast.Attribute) and func.attr in {"write_text", "write_bytes"}:
            found.append(func.attr)
    return found


def test_only_state_io_writes_files() -> None:
    for path in SRC_DIR.rglob("*.py"):
        if ALLOWED_DIR in path.parents:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_write_calls(tree)
        assert not calls, f"{path} calls disallowed file-write function(s): {calls}"
