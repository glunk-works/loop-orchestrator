"""Shared AST helpers for the write-boundary (`test_state_io_boundary.py`) and
encoding (`test_encoding_boundary.py`) structural guards.

F37: both guards need to resolve an `open()`-shaped call's mode argument and
receiver. That logic was hand-duplicated three times (two copies of
mode-node resolution, two of the write-capability check), with the F30
receiver gate present in only one of the two files -- which is exactly how
F35/F36 diverged from each other. Extracted here so a fix lands once, in one
place, for both guards.
"""

import ast

# .open() receivers that accept a string mode at positional index 1 with
# encoding semantics -- the same call shape as the builtin open() -- but
# are not Path.open, so their mode is not at index 0 (F36): gzip, bz2, lzma,
# codecs, io.
_INDEX1_MODE_RECEIVERS = {"gzip", "bz2", "lzma", "codecs", "io"}

# .open() receivers with no comparable string-mode/encoding concept at all
# (a different signature entirely: numeric flags, single-char db modes, or
# no file argument at all) -- out of scope for both guards, not misresolved
# as a Path.open (F30/F35/F36): os, shelve, dbm, webbrowser, tarfile, zipfile.
_NO_MODE_CONCEPT_RECEIVERS = {"os", "shelve", "dbm", "webbrowser", "tarfile", "zipfile"}


def open_call_is_method(node: ast.Call) -> bool | None:
    """Classify a Call node's mode-argument position.

    Returns True for a method-form Path.open()-shaped call (mode at index
    0); False for a builtin-open()-shaped call -- either the bare `open()`
    builtin itself, or an `_INDEX1_MODE_RECEIVERS` receiver that shares its
    call shape (mode at index 1); or None if the call isn't an open() at
    all, or is an `_NO_MODE_CONCEPT_RECEIVERS` receiver with no comparable
    mode concept and so is out of scope for both guards.
    """
    func = node.func
    if isinstance(func, ast.Name):
        return False if func.id == "open" else None
    if isinstance(func, ast.Attribute) and func.attr == "open":
        receiver = func.value
        if isinstance(receiver, ast.Name):
            if receiver.id in _NO_MODE_CONCEPT_RECEIVERS:
                return None
            if receiver.id in _INDEX1_MODE_RECEIVERS:
                return False
        return True
    return None


def mode_node(node: ast.Call, *, is_method: bool) -> ast.expr | None:
    """The AST node holding an open()-shaped call's mode argument, if any.

    Builtin open(file, mode, ...) and `_INDEX1_MODE_RECEIVERS` opens carry
    mode at positional index 1; method-form path.open(mode, ...) has no
    implicit `self` in the AST args, so mode sits at index 0 there instead
    (F25).
    """
    mode_index = 0 if is_method else 1
    if len(node.args) > mode_index:
        return node.args[mode_index]
    for kw in node.keywords:
        if kw.arg == "mode":
            return kw.value
    return None


def is_write_capable(node: ast.Call, *, is_method: bool) -> bool:
    """Whether an open()-shaped call's mode is write-capable.

    No mode argument at all is a genuine read (the implicit "r" default)
    and is not write-capable. A mode resolved to a string literal is
    write-capable iff it contains a w/a/x/+ char. A mode argument that's
    present but can't be resolved to a literal can't be proven read-only,
    so it stays in scope (F21/F34's conservatism).
    """
    node_ = mode_node(node, is_method=is_method)
    if node_ is None:
        return False
    if isinstance(node_, ast.Constant) and isinstance(node_.value, str):
        return any(c in node_.value for c in "wax+")
    return True
