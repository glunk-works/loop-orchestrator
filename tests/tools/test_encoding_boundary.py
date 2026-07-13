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
had, so it is flagged here too.

F20 (this round): the locale hazard is identical for a text-mode *read* --
`open(path)` / `open(path, "r")` without `encoding=` is just as
locale-dependent as an unencoded write. The mode-char split that used to
exempt reads is gone; any resolvable text mode (or an unresolvable one --
F21) is in scope unless it is binary.

F21 (this round): the old `_open_mode` treated `"r+"` (write-capable, no
`w`/`a`/`x` char) and any non-literal/dynamic mode argument as an
unconditional read, silently exempting both. Since F20 now requires
`encoding=` for text-mode reads too, that distinction no longer matters for
detection purposes -- only `"b"` (binary, which takes no `encoding` kwarg at
all) is exempt; every other resolvable-or-not mode must pin `encoding=`.

F19 (this round): the guard above only ever checked `encoding=`, so a
`write_text` call could pin `encoding="utf-8"` and still default to
locale-translated newlines on write -- exactly the gap F18 slipped through
(`tools/scaffold/writer.py:77`). `test_write_owning_modules_pin_newline_on_write_text`
closes that structurally, scoped to the sanctioned file-write-owning modules
named in `test_state_io_boundary.py::ALLOWED_DIRS` (`state_io`, `scaffold`)."""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"
_TARGET_METHODS = {"read_text", "write_text"}
# Mirrors test_state_io_boundary.py::ALLOWED_DIRS -- the two sanctioned
# file-write-owning modules.
WRITE_OWNING_DIRS = {SRC_DIR / "tools" / "state_io", SRC_DIR / "tools" / "scaffold"}


def _open_mode(node: ast.Call) -> str | None:
    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
        value = node.args[1].value
        return value if isinstance(value, str) else None
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            value = kw.value.value
            return value if isinstance(value, str) else None
    return None


def _is_unencoded_text_open(node: ast.Call) -> bool:
    mode = _open_mode(node)
    if mode is not None and "b" in mode:
        return False  # binary mode takes no encoding kwarg
    # Text mode (explicit "r"/"w"/"a"/"x"/"r+"/... or the implicit default
    # "r"), or a mode we couldn't resolve statically (F21): all in scope,
    # since none of those can be proven binary.
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
            if _is_unencoded_text_open(node):
                found.append("open")
    return found


def _unpinned_newline_write_text_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "write_text"):
            continue
        newline_kwarg = next((kw for kw in node.keywords if kw.arg == "newline"), None)
        pinned = (
            newline_kwarg is not None
            and isinstance(newline_kwarg.value, ast.Constant)
            and newline_kwarg.value.value == "\n"
        )
        if not pinned:
            found.append("write_text")
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
    # open(): flagged for any unencoded text-mode call, read or write (F20);
    # binary mode and an explicit encoding are the only ways out.
    assert _unencoded_calls(ast.parse("open('x', 'w')")) == ["open"]
    assert _unencoded_calls(ast.parse("open('x', mode='a')")) == ["open"]
    assert _unencoded_calls(ast.parse("open('x', 'w', encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("open('x', 'wb')")) == []
    assert _unencoded_calls(ast.parse("open('x')")) == ["open"]
    assert _unencoded_calls(ast.parse("open('x', 'r')")) == ["open"]
    assert _unencoded_calls(ast.parse("open('x', encoding='utf-8')")) == []
    # "r+" is write-capable but has no w/a/x char (F21) -- still flagged.
    assert _unencoded_calls(ast.parse("open('x', 'r+')")) == ["open"]
    # A non-literal/dynamic mode can't be proven binary, so it stays in scope
    # rather than being silently treated as a read (F21).
    assert _unencoded_calls(ast.parse("open('x', some_mode_var)")) == ["open"]


def test_write_owning_modules_pin_newline_on_write_text() -> None:
    offenders = {}
    scanned = 0
    for allowed_dir in WRITE_OWNING_DIRS:
        for path in allowed_dir.rglob("*.py"):
            scanned += 1
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            calls = _unpinned_newline_write_text_calls(tree)
            if calls:
                offenders[path] = calls
    # F5-shaped guard: without this, a misresolved WRITE_OWNING_DIRS makes the
    # scan yield nothing and the assertion below passes vacuously.
    assert scanned > 0, f"no .py files found under {WRITE_OWNING_DIRS} -- guard scanned nothing"
    assert not offenders, f"write_text call(s) missing newline='\\n': {offenders}"


def test_newline_detector_actually_flags_a_missing_pin() -> None:
    # Spot-check the checker itself (same shape as F5/F12's precedent above).
    assert _unpinned_newline_write_text_calls(
        ast.parse("Path('x').write_text('y', encoding='utf-8')")
    ) == ["write_text"]
    assert (
        _unpinned_newline_write_text_calls(
            ast.parse("Path('x').write_text('y', encoding='utf-8', newline='\\n')")
        )
        == []
    )
    assert _unpinned_newline_write_text_calls(
        ast.parse("Path('x').write_text('y', encoding='utf-8', newline='')")
    ) == ["write_text"]
    assert _unpinned_newline_write_text_calls(
        ast.parse("Path('x').write_text('y', encoding='utf-8', newline=None)")
    ) == ["write_text"]
    assert _unpinned_newline_write_text_calls(ast.parse("do_something_harmless()")) == []
