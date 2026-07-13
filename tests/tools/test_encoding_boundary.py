"""Repo-wide static assertions (sprint 35) over every `read_text` /
`write_text` / `open()` call in `src/loop_engine`:

1. Every text-mode call must pin an explicit `encoding=` kwarg -- the C
   locale otherwise silently picks a platform-dependent encoding. Binary
   mode (`"b"` in the resolved mode, or unresolvable) is the only exemption.
2. Every write-capable call in `NEWLINE_PIN_SCAN_DIRS` (the file-write-owning
   modules, `state_io`/`scaffold`, plus `agent_state`'s one `.open()` call)
   must also pin `newline="\\n"` -- `encoding=` alone doesn't stop
   locale-translated newlines on write.

Mode resolution (which positional index holds the mode, and which `.open()`
receivers are in scope at all) is shared with `test_state_io_boundary.py`
via `tests/tools/_ast_open.py` (F37) -- see that module's docstring for why.
A mode argument that can't be resolved to a string literal stays in scope
for both checks rather than being treated as a safe read/binary call (F21):
it can't be proven otherwise.
"""

import ast
from pathlib import Path

from tests.tools._ast_open import is_write_capable, mode_node, open_call_is_method

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"
_TARGET_METHODS = {"read_text", "write_text"}
# Mirrors test_state_io_boundary.py::ALLOWED_DIRS -- the two sanctioned
# file-write-owning modules -- plus agent_state, whose store.py holds this
# PR's one method-form `.open()` call outside those two dirs (F31). It's a
# read today, so this guard finds nothing there, but a future write-mode
# `.open()` in agent_state is now covered structurally instead of relying on
# someone remembering to add it later.
NEWLINE_PIN_SCAN_DIRS = {
    SRC_DIR / "tools" / "state_io",
    SRC_DIR / "tools" / "scaffold",
    SRC_DIR / "tools" / "agent_state",
}


def _is_unencoded_text_open(node: ast.Call, *, is_method: bool) -> bool:
    node_ = mode_node(node, is_method=is_method)
    if isinstance(node_, ast.Constant) and isinstance(node_.value, str) and "b" in node_.value:
        return False  # binary mode takes no encoding kwarg
    # Text mode (explicit "r"/"w"/"a"/"x"/"r+"/... or the implicit default
    # "r"), or a mode we couldn't resolve statically: all in scope, since
    # none of those can be proven binary.
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
            continue
        is_method = open_call_is_method(node)
        if is_method is None:
            continue
        if _is_unencoded_text_open(node, is_method=is_method):
            found.append("open")
    return found


def _unpinned_newline_write_text_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "write_text":
            label = "write_text"
        else:
            is_method = open_call_is_method(node)
            if is_method is None:
                continue
            # open()-based writes go through the same newline= translation
            # on write as write_text; only a confirmed write-capable mode
            # -- or one that can't be resolved and so can't be proven safe
            # -- is in scope. A genuine read (no mode arg at all) doesn't
            # need newline="\n" pinned, and forcing it there would misflag
            # reads.
            if not is_write_capable(node, is_method=is_method):
                continue
            label = "open"
        newline_kwarg = next((kw for kw in node.keywords if kw.arg == "newline"), None)
        pinned = (
            newline_kwarg is not None
            and isinstance(newline_kwarg.value, ast.Constant)
            and newline_kwarg.value.value == "\n"
        )
        if not pinned:
            found.append(label)
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
    # Method form (F25): mode sits at index 0, not builtin open()'s index 1 --
    # a naive reuse of the builtin's index would misresolve 'wb' here as
    # unresolvable and wrongly flag it.
    assert _unencoded_calls(ast.parse("Path('x').open('w')")) == ["open"]
    assert _unencoded_calls(ast.parse("Path('x').open('w', encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("Path('x').open('wb')")) == []
    assert _unencoded_calls(ast.parse("Path('x').open(encoding='utf-8')")) == []
    # The exact shape of state_io/writer.py's own F22/F24 read call.
    assert _unencoded_calls(ast.parse("target_path.open(encoding='utf-8', newline='')")) == []
    # F36: gzip/bz2/lzma/codecs/io all accept `encoding=` and carry mode at
    # index 1, same as the builtin -- they're routed through that path, not
    # excluded outright, so an unencoded call through them is still caught
    # instead of silently escaping the guard entirely.
    assert _unencoded_calls(ast.parse("gzip.open('blob.gz', 'wt')")) == ["open"]
    assert _unencoded_calls(ast.parse("gzip.open('blob.gz', 'wt', encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("codecs.open('backup.txt', 'w')")) == ["open"]
    assert _unencoded_calls(ast.parse("codecs.open('backup.txt', 'w', encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("io.open('x', 'w')")) == ["open"]
    assert _unencoded_calls(ast.parse("io.open('x', 'w', encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("io.open('x', 'wb')")) == []
    # ...while a receiver with no comparable mode/encoding concept at all
    # (webbrowser.open(url) touches no file) is out of scope entirely, not
    # misresolved as an unencoded text open.
    assert _unencoded_calls(ast.parse("webbrowser.open(url)")) == []
    assert _unencoded_calls(ast.parse("os.open(path, os.O_WRONLY)")) == []


def test_write_owning_modules_pin_newline_on_write_text() -> None:
    # Covers write_text() calls and write-mode open() calls (F26) in the same
    # sweep -- both go through the same newline= translation on write.
    offenders = {}
    scanned = 0
    for allowed_dir in NEWLINE_PIN_SCAN_DIRS:
        for path in allowed_dir.rglob("*.py"):
            scanned += 1
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            calls = _unpinned_newline_write_text_calls(tree)
            if calls:
                offenders[path] = calls
    # F5-shaped guard: without this, a misresolved NEWLINE_PIN_SCAN_DIRS makes the
    # scan yield nothing and the assertion below passes vacuously.
    assert scanned > 0, f"no .py files found under {NEWLINE_PIN_SCAN_DIRS} -- guard scanned nothing"
    assert not offenders, f"write_text/open() call(s) missing newline='\\n': {offenders}"


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
    # open()-based writes (F26): write-capable mode missing the pin is flagged...
    assert _unpinned_newline_write_text_calls(
        ast.parse("Path('x').open('w', encoding='utf-8')")
    ) == ["open"]
    assert _unpinned_newline_write_text_calls(ast.parse("open('x', 'a', encoding='utf-8')")) == [
        "open"
    ]
    assert (
        _unpinned_newline_write_text_calls(
            ast.parse("Path('x').open('w', encoding='utf-8', newline='\\n')")
        )
        == []
    )
    # ...but a read -- including this module's own F22/F24 shape, which pins
    # newline="" (byte-exact), not "\n" -- is out of scope, not misflagged.
    assert (
        _unpinned_newline_write_text_calls(
            ast.parse("target_path.open(encoding='utf-8', newline='')")
        )
        == []
    )
    assert _unpinned_newline_write_text_calls(ast.parse("Path('x').open('r')")) == []
    assert _unpinned_newline_write_text_calls(ast.parse("Path('x').open()")) == []
    # F34: a dynamic/unresolvable mode can't be proven read-only, so it stays
    # in scope -- before the fix, this collapsed to the same "None" answer as
    # a genuine no-mode-arg read and silently escaped the newline pin.
    assert _unpinned_newline_write_text_calls(
        ast.parse("open('x', mode_var, encoding='utf-8')")
    ) == ["open"]
    assert _unpinned_newline_write_text_calls(
        ast.parse("Path('x').open(mode_var, encoding='utf-8')")
    ) == ["open"]
    # F36: gzip is routed through the same write-capable check as the
    # builtin now (mode at index 1), not excluded outright.
    assert _unpinned_newline_write_text_calls(
        ast.parse("gzip.open('x.gz', 'wt', encoding='utf-8')")
    ) == ["open"]
    assert (
        _unpinned_newline_write_text_calls(
            ast.parse("gzip.open('x.gz', 'wt', encoding='utf-8', newline='\\n')")
        )
        == []
    )
    # A receiver with no comparable mode concept is out of scope entirely.
    assert _unpinned_newline_write_text_calls(ast.parse("webbrowser.open(url)")) == []
