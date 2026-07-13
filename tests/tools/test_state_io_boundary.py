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


def _open_mode_node(node: ast.Call, *, is_method: bool) -> ast.expr | None:
    # Builtin open(file, mode, ...) carries mode at positional index 1;
    # method form path.open(mode, ...) has no implicit `self` in the AST
    # args, so mode sits at index 0 there instead (mirrors
    # test_encoding_boundary.py's _open_mode, F25's finding).
    mode_index = 0 if is_method else 1
    if len(node.args) > mode_index:
        return node.args[mode_index]
    for kw in node.keywords:
        if kw.arg == "mode":
            return kw.value
    return None


def _is_write_capable_open(node: ast.Call, *, is_method: bool) -> bool:
    # F29: a genuine read (no mode arg at all -- the implicit "r" default,
    # e.g. agent_state/store.py's `path.open(encoding="utf-8", newline="")`)
    # is not a write-boundary violation and must not be flagged. A mode arg
    # that can't be resolved statically stays in scope, same conservatism as
    # F21/F34 in test_encoding_boundary.py -- it can't be proven read-only.
    mode_node = _open_mode_node(node, is_method=is_method)
    if mode_node is None:
        return False
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return any(c in mode_node.value for c in "wax+")
    return True


def _direct_write_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "open":
            if _is_write_capable_open(node, is_method=False):
                found.append(func.id)
        elif isinstance(func, ast.Name) and func.id in DISALLOWED_WRITE_CALLS:
            found.append(func.id)
        elif isinstance(func, ast.Attribute) and func.attr in {"write_text", "write_bytes"}:
            found.append(func.attr)
        elif isinstance(func, ast.Attribute) and func.attr == "open":
            # F29: method-form `.open()` was previously invisible here --
            # matched neither the ast.Name branch above nor the
            # write_text/write_bytes attribute set.
            if _is_write_capable_open(node, is_method=True):
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
    # F29: method-form `.open()` in write-capable mode is now caught outside
    # the allowed dirs -- this is the exact shape the review found invisible.
    assert _direct_write_calls(ast.parse("Path('x').open('w')")) == ["open"]
    assert _direct_write_calls(ast.parse("target_path.open('a')")) == ["open"]
    # ...but a genuine read, including agent_state/store.py's own shape, is
    # correctly NOT a boundary violation and stays unflagged.
    assert _direct_write_calls(ast.parse("target_path.open(encoding='utf-8', newline='')")) == []
    assert _direct_write_calls(ast.parse("Path('x').open('r')")) == []
    assert _direct_write_calls(ast.parse("Path('x').open()")) == []
    # An unresolvable mode can't be proven read-only, so it stays in scope.
    assert _direct_write_calls(ast.parse("Path('x').open(mode_var)")) == ["open"]
    assert _direct_write_calls(ast.parse("open('x', mode_var)")) == ["open"]
    # A bare-name read is likewise no longer over-flagged (matches the
    # method-form treatment now, closing the inconsistency the review named).
    assert _direct_write_calls(ast.parse("open('x', 'r')")) == []
    assert _direct_write_calls(ast.parse("open('x')")) == []
