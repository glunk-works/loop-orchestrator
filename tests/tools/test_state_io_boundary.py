import ast
from pathlib import Path

from tests.tools._ast_open import is_write_capable, open_call_is_method

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"
# The two sanctioned file-write-owning modules (Phase 5 sprint 25 added
# `tools/scaffold` as the second, mirroring how sprint 24 added `tools/git_io`
# as the fourth sanctioned subprocess surface): `state_io` owns run
# state/artifact persistence; `scaffold` writes a bootstrapped repo skeleton
# into a validated foreign clone tree. Every other module must still raise.
ALLOWED_DIRS = {SRC_DIR / "tools" / "state_io", SRC_DIR / "tools" / "scaffold"}
DISALLOWED_WRITE_CALLS = {"write_text", "write_bytes"}


def _direct_write_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_method = open_call_is_method(node)
        if is_method is not None:
            # F35: every open()-shaped call -- bare `open()`, method-form
            # `.open()`, or a shared-module-recognized receiver like
            # `gzip.open()` -- is resolved through the same receiver-aware
            # mode logic used by test_encoding_boundary.py, instead of
            # blindly reading index 0 as the mode for any `.open` attribute
            # access (F30's defect, previously unfixed here).
            if is_write_capable(node, is_method=is_method):
                found.append("open")
        elif isinstance(func, ast.Name) and func.id in DISALLOWED_WRITE_CALLS:
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
    # F35: a non-Path `.open()` receiver was previously read as method-form,
    # misreading its filename argument as the mode -- whether it was flagged
    # depended on the letters in the filename. gzip's mode sits at index 1
    # like the builtin's; a write-capable mode there must be flagged
    # regardless of the filename, and a read-mode one must not be.
    assert _direct_write_calls(ast.parse("gzip.open('out.gz', 'wt')")) == ["open"]
    assert _direct_write_calls(ast.parse("gzip.open('archive.gz', 'rt')")) == []
    # ...while a receiver with no comparable mode concept at all is out of
    # scope for this guard, not misresolved as a write -- the mirror-image
    # false positive the review found (`webbrowser.open(url)` touches no
    # file but was flagged before the receiver gate existed here).
    assert _direct_write_calls(ast.parse("webbrowser.open(url)")) == []
    assert _direct_write_calls(ast.parse("os.open(path, os.O_WRONLY)")) == []
