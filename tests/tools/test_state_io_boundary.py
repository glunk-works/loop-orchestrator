import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"
# The two sanctioned file-write-owning modules (Phase 5 sprint 25 added
# `tools/scaffold` as the second, mirroring how sprint 24 added `tools/git_io`
# as the fourth sanctioned subprocess surface): `state_io` owns run
# state/artifact persistence; `scaffold` writes a bootstrapped repo skeleton
# into a validated foreign clone tree. Every other module must still raise.
ALLOWED_DIRS = {SRC_DIR / "tools" / "state_io", SRC_DIR / "tools" / "scaffold"}
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
        if any(allowed in path.parents for allowed in ALLOWED_DIRS):
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        calls = _direct_write_calls(tree)
        assert not calls, f"{path} calls disallowed file-write function(s): {calls}"


def test_detector_actually_flags_a_direct_write_outside_the_allowed_dirs() -> None:
    # Spot-check the checker itself: a synthetic module calling `open()` or
    # `.write_text()` is caught, proving `test_only_state_io_writes_files`
    # would fail (not vacuously pass) if a non-allow-listed module ever
    # added a direct file write.
    assert _direct_write_calls(ast.parse("open('x', 'w')")) == ["open"]
    assert _direct_write_calls(ast.parse("Path('x').write_text('y')")) == ["write_text"]
    assert _direct_write_calls(ast.parse("Path('x').write_bytes(b'y')")) == ["write_bytes"]
    assert _direct_write_calls(ast.parse("do_something_harmless()")) == []
