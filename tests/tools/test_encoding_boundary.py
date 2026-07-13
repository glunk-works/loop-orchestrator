"""Repo-wide static assertion (sprint 35, F12): every `read_text`/`write_text`
call in `src/loop_engine` must pin an explicit `encoding=` kwarg. F8/F9 fixed
ten call sites across five files but shipped regression tests for only two
(`tools/scaffold/writer.py`, `artifact_store.py`) — this closes the class
structurally instead of file-by-file, so a future unencoded call fails here
instead of needing its own bespoke locale test.

F3 (sprint 35 PR #57 review): `open()` is the third sanctioned write primitive
(`test_state_io_boundary.py`'s `DISALLOWED_WRITE_CALLS` names all three) and is
legal precisely inside `state_io`/`scaffold` -- i.e. legal in exactly the two
modules this PR touches. A bare `open(path, "w")` in text mode defaults to the
locale's preferred encoding, the same C-locale hazard `read_text`/`write_text`
had, so it is flagged here too."""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"
_TARGET_METHODS = {"read_text", "write_text"}
_WRITE_MODE_CHARS = {"w", "a", "x"}


def _open_mode(node: ast.Call) -> str | None:
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        value = node.args[1].value
        return value if isinstance(value, str) else None
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            value = kw.value.value
            return value if isinstance(value, str) else None
    return None


def _is_unencoded_text_write_open(node: ast.Call) -> bool:
    mode = _open_mode(node)
    if mode is None:
        return False  # default mode is "r": a read, out of scope here
    if "b" in mode or not any(char in mode for char in _WRITE_MODE_CHARS):
        return False  # binary mode takes no encoding kwarg; plain reads are out of scope
    return not any(kw.arg == "encoding" for kw in node.keywords)


def _unencoded_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in _TARGET_METHODS:
            if not any(kw.arg == "encoding" for kw in node.keywords):
                found.append(func.attr)
        elif isinstance(func, ast.Name) and func.id == "open":
            if _is_unencoded_text_write_open(node):
                found.append("open")
    return found


def test_every_read_text_and_write_text_call_pins_an_encoding() -> None:
    offenders = {}
    scanned = 0
    for path in SRC_DIR.rglob("*.py"):
        scanned += 1
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        calls = _unencoded_calls(tree)
        if calls:
            offenders[path] = calls
    # F5: without this, a misresolved SRC_DIR makes rglob yield nothing,
    # offenders stays empty, and the assertion below passes vacuously.
    assert scanned > 0, f"no .py files found under {SRC_DIR} -- guard scanned nothing"
    assert not offenders, f"unencoded read_text/write_text/open call(s): {offenders}"


def test_detector_actually_flags_an_unencoded_call() -> None:
    # Spot-check the checker itself: proves the guard above would fail (not
    # vacuously pass) if an unencoded call were ever reintroduced.
    assert _unencoded_calls(ast.parse("Path('x').read_text()")) == ["read_text"]
    assert _unencoded_calls(ast.parse("Path('x').write_text('y')")) == ["write_text"]
    assert _unencoded_calls(ast.parse("Path('x').read_text(encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("do_something_harmless()")) == []
    # open(): flagged only for an unencoded text-mode write; binary mode and
    # plain reads are out of scope, and an explicit encoding clears it.
    assert _unencoded_calls(ast.parse("open('x', 'w')")) == ["open"]
    assert _unencoded_calls(ast.parse("open('x', mode='a')")) == ["open"]
    assert _unencoded_calls(ast.parse("open('x', 'w', encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("open('x', 'wb')")) == []
    assert _unencoded_calls(ast.parse("open('x')")) == []
