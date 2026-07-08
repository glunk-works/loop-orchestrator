"""Execution-isolation mode selection (Phase 3).

The single reader of `LOOP_ENGINE_ISOLATION`, shared by `tools/worktree` (which
needs a per-run worktree for the `worktree`/`container`/`sandbox` modes) and
`tools/mcp` (which sandboxes the coder-tools server launch for
`container`/`sandbox`). Keeping the enum in one place stops the two callers from
disagreeing on the allowed values.

`IsolationUnavailableError` also lives here so that `core/` (the Coder gate) can
signal "cannot honor this mode" without importing `tools/mcp` — this module
imports no other `loop_engine` module, so it is safe to import from anywhere.

The load-bearing rule for the sandbox modes: selecting `container`/`sandbox` must
never silently degrade to running untrusted code in-process. Callers that cannot
honor the mode raise `IsolationUnavailableError` instead of falling back.
"""

import os
from typing import Literal

_ISOLATION_ENV_VAR = "LOOP_ENGINE_ISOLATION"

IsolationMode = Literal["none", "worktree", "container", "sandbox"]
SandboxRuntimeMode = Literal["container", "sandbox"]

_ALLOWED: tuple[IsolationMode, ...] = ("none", "worktree", "container", "sandbox")
_WORKTREE_MODES = frozenset({"worktree", "container", "sandbox"})
_SANDBOX_MODES = frozenset({"container", "sandbox"})


class IsolationUnavailableError(Exception):
    """An isolation mode was selected but cannot be honored — no runtime is
    available, or honoring it would require running untrusted code in-process.
    Raised instead of silently degrading to in-process execution."""


def isolation_mode() -> IsolationMode:
    """The selected isolation mode. An unknown value raises `ValueError` (this
    is the negative-input boundary for the flag); unset/empty means `none`."""
    raw = os.environ.get(_ISOLATION_ENV_VAR, "").strip().lower()
    if raw == "":
        return "none"
    if raw not in _ALLOWED:
        raise ValueError(f"invalid {_ISOLATION_ENV_VAR}={raw!r}; expected one of {_ALLOWED}")
    return raw  # type: ignore[return-value]  # membership-checked against _ALLOWED above


def worktree_needed() -> bool:
    """Whether the selected mode needs a per-run worktree — to run in
    (`worktree`) or to mount into a sandbox (`container`/`sandbox`)."""
    return isolation_mode() in _WORKTREE_MODES


def sandbox_runtime_mode() -> SandboxRuntimeMode | None:
    """The sandboxed-tool-execution mode (`container`/`sandbox`), or `None` when
    tools run unsandboxed (`none`/`worktree`)."""
    mode = isolation_mode()
    return mode if mode in _SANDBOX_MODES else None  # type: ignore[return-value]
