"""Repo-wide static assertion (sprint 35, F12): every `read_text`/`write_text`
call in `src/loop_engine` must pin an explicit `encoding=` kwarg. F8/F9 fixed
ten call sites across five files but shipped regression tests for only two
(`tools/scaffold/writer.py`, `artifact_store.py`) — this closes the class
structurally instead of file-by-file, so a future unencoded call fails here
instead of needing its own bespoke locale test."""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"
_TARGET_METHODS = {"read_text", "write_text"}


def _unencoded_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr in _TARGET_METHODS):
            continue
        if not any(kw.arg == "encoding" for kw in node.keywords):
            found.append(func.attr)
    return found


def test_every_read_text_and_write_text_call_pins_an_encoding() -> None:
    offenders = {}
    for path in SRC_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        calls = _unencoded_calls(tree)
        if calls:
            offenders[path] = calls
    assert not offenders, f"unencoded read_text/write_text call(s): {offenders}"


def test_detector_actually_flags_an_unencoded_call() -> None:
    # Spot-check the checker itself: proves the guard above would fail (not
    # vacuously pass) if an unencoded call were ever reintroduced.
    assert _unencoded_calls(ast.parse("Path('x').read_text()")) == ["read_text"]
    assert _unencoded_calls(ast.parse("Path('x').write_text('y')")) == ["write_text"]
    assert _unencoded_calls(ast.parse("Path('x').read_text(encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("do_something_harmless()")) == []
