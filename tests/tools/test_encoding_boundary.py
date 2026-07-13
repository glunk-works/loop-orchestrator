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
named in `test_state_io_boundary.py::ALLOWED_DIRS` (`state_io`, `scaffold`).

F25 (PR #57 follow-up review): `_unencoded_calls`'s open() branch was an
`elif isinstance(func, ast.Name) and func.id == "open"`, reachable only for
the bare-name builtin form. A method-form call like `target_path.open(...)`
is an `ast.Attribute` whose `attr` ("open") isn't in `_TARGET_METHODS`
either, so it matched neither branch and was invisible to the guard --
including `state_io/writer.py`'s own F22 fix, `target_path.open(encoding=
"utf-8", newline="")`. Now matched explicitly, with `_open_mode` told which
form it's looking at: builtin `open(file, mode, ...)` carries `mode` at
positional index 1, but method `path.open(mode, ...)` carries it at index 0
(no implicit `self` in the AST args) -- reusing the builtin's index for the
method form would misresolve a method-form mode.

F26 (PR #57 follow-up review): the newline-pin guard (F19) only ever scanned
`.write_text()` calls, so an `open()`-based write missing `newline="\n"`
would reproduce F18 undetected. Not reachable today -- the one `.open()` call
in `src/loop_engine` is a read (F22/F24) and correctly does NOT pin
`newline="\n"` (it pins `newline=""` instead, for a byte-exact read) -- but
the same shape as F19's rationale, so a future write-mode `open()` call is
covered structurally now instead of needing its own bespoke test.

F30 (second PR #57 follow-up review): `_open_mode(is_method=True)` assumed
every `ast.Attribute` named `open` was `Path.open` and read positional index
0 as the mode. `gzip.open('blob.gz', 'wt')` resolved mode to `'blob.gz'`,
which contains a `b`, so it was judged binary and a genuinely unencoded text
write was exempted; `codecs.open(...)` was conversely flagged for a
`newline=` kwarg it doesn't accept, and `webbrowser.open(url)`, which
touches no file, was flagged as an unencoded text open. `_is_path_open` now
gates on the receiver: a known non-filesystem-opener module name (`gzip`,
`codecs`, `webbrowser`, etc.) is excluded rather than misresolved as
method-form `Path.open`.

F31 (second PR #57 follow-up review): `WRITE_OWNING_DIRS` excluded
`tools/agent_state/`, the one module this PR gave an `.open()` handle to;
combined with F29 (`test_state_io_boundary.py`), a future write-mode
`path.open('w')` there was invisible to both structural guards. Added here
too for defense in depth, even though F29 alone would now catch a write
there first.

F34 (second PR #57 follow-up review): `_is_write_capable_mode` took the
already-collapsed `str | None` from `_open_mode`, which maps both "no mode
argument at all" (a read) and "a mode argument that couldn't be resolved to
a literal" (F21: must stay in scope) to the same `None` -- inverting F21's
conservatism and letting a dynamic `open(p, mode_var, encoding="utf-8")`
escape the newline pin. It now takes the call node directly and checks for
a mode node's *presence* before checking its resolved value."""

import ast
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "loop_engine"
_TARGET_METHODS = {"read_text", "write_text"}
# Mirrors test_state_io_boundary.py::ALLOWED_DIRS -- the two sanctioned
# file-write-owning modules -- plus agent_state (F31), whose store.py holds
# this PR's one method-form `.open()` call outside those two dirs. Scanning
# it here costs nothing today (its call is a read, so `_unpinned_newline_
# write_text_calls` finds nothing) and closes the gap the review named: a
# future write-mode `.open()` there would otherwise be invisible to this
# guard even after F29 makes it visible to the write-boundary one.
WRITE_OWNING_DIRS = {
    SRC_DIR / "tools" / "state_io",
    SRC_DIR / "tools" / "scaffold",
    SRC_DIR / "tools" / "agent_state",
}
# Module-level callables that happen to be attribute-accessed as `.open` but
# are NOT Path.open -- their signatures differ (mode position, accepted
# kwargs), so conflating them with method-form Path.open misresolves the
# mode (F30): gzip.open('blob.gz', 'wt') would read index 0 ('blob.gz', the
# filename) as the mode, judge it binary (contains 'b'), and wrongly exempt
# a real unencoded text write. These aren't Path.open and aren't in scope
# for this guard; excluded rather than mishandled.
_NON_PATH_OPEN_RECEIVERS = {
    "gzip",
    "bz2",
    "lzma",
    "io",
    "codecs",
    "shelve",
    "tarfile",
    "zipfile",
    "dbm",
    "webbrowser",
    "os",
}


def _is_path_open(node: ast.Call) -> bool:
    func = node.func
    if not (isinstance(func, ast.Attribute) and func.attr == "open"):
        return False
    receiver = func.value
    return not (isinstance(receiver, ast.Name) and receiver.id in _NON_PATH_OPEN_RECEIVERS)


def _open_mode(node: ast.Call, *, is_method: bool) -> str | None:
    # Builtin open(file, mode, ...) carries mode at positional index 1; method
    # form path.open(mode, ...) has no implicit `self` in the AST args, so
    # mode sits at index 0 there instead (F25).
    mode_index = 0 if is_method else 1
    if len(node.args) > mode_index and isinstance(node.args[mode_index], ast.Constant):
        value = node.args[mode_index].value
        return value if isinstance(value, str) else None
    for kw in node.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            value = kw.value.value
            return value if isinstance(value, str) else None
    return None


def _is_unencoded_text_open(node: ast.Call, *, is_method: bool) -> bool:
    mode = _open_mode(node, is_method=is_method)
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
        elif _is_path_open(node):
            if _is_unencoded_text_open(node, is_method=True):
                found.append("open")
        elif isinstance(func, ast.Name) and func.id == "open":
            if _is_unencoded_text_open(node, is_method=False):
                found.append("open")
    return found


def _mode_node(node: ast.Call, *, is_method: bool) -> ast.expr | None:
    mode_index = 0 if is_method else 1
    if len(node.args) > mode_index:
        return node.args[mode_index]
    for kw in node.keywords:
        if kw.arg == "mode":
            return kw.value
    return None


def _is_write_capable_mode(node: ast.Call, *, is_method: bool) -> bool:
    # F34: distinguishes "no mode argument at all" (a legitimate default
    # read -- e.g. state_io/writer.py's own `target_path.open(encoding=
    # "utf-8", newline="")` call, which has no positional or keyword mode)
    # from "a mode argument present but not resolvable to a string literal"
    # (F21's conservatism: since it can't be proven read-only or binary, it
    # stays in scope). The prior version collapsed both cases to the same
    # `mode is None` answer via `_open_mode`, which let a dynamic
    # `open(p, mode_var, encoding="utf-8")` escape the newline pin entirely.
    mode_node = _mode_node(node, is_method=is_method)
    if mode_node is None:
        return False
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return any(c in mode_node.value for c in "wax+")
    return True


def _unpinned_newline_write_text_calls(tree: ast.Module) -> list[str]:
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_write_text = isinstance(func, ast.Attribute) and func.attr == "write_text"
        is_method_open = _is_path_open(node)
        is_builtin_open = isinstance(func, ast.Name) and func.id == "open"
        if is_write_text:
            label = "write_text"
        elif is_method_open or is_builtin_open:
            # open()-based writes go through the same newline= translation on
            # write as write_text (F26); only a confirmed write-capable mode
            # -- or one that can't be resolved and so can't be proven safe
            # (F34) -- is in scope. A genuine read (no mode arg at all)
            # doesn't need newline="\n" pinned, and forcing it there would
            # misflag reads.
            if not _is_write_capable_mode(node, is_method=is_method_open):
                continue
            label = "open"
        else:
            continue
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
    # F30: module-level `.open()` on a known non-Path receiver isn't
    # Path.open and is out of scope, not misresolved. Before the fix,
    # gzip.open('blob.gz', 'wt') read index 0 ('blob.gz') as the mode, saw a
    # 'b', and wrongly exempted this real unencoded text write.
    assert _unencoded_calls(ast.parse("gzip.open('blob.gz', 'wt')")) == []
    assert _unencoded_calls(ast.parse("codecs.open('backup.txt', 'w', encoding='utf-8')")) == []
    assert _unencoded_calls(ast.parse("webbrowser.open(url)")) == []
    assert _unencoded_calls(ast.parse("io.open('x', 'w')")) == []


def test_write_owning_modules_pin_newline_on_write_text() -> None:
    # Covers write_text() calls and write-mode open() calls (F26) in the same
    # sweep -- both go through the same newline= translation on write.
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
    # F30: a non-Path `.open()` on a known non-filesystem-opener receiver is
    # out of scope for this guard entirely.
    assert _unpinned_newline_write_text_calls(ast.parse("webbrowser.open(url)")) == []
