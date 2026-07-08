"""Coder execution-mode flag — the single reader of `LOOP_ENGINE_CODER`.

Mirrors `graph_engine.use_langgraph_engine()` / `mcp.use_mcp_tools()`: a
lightweight, stdlib-only selector so `loops/default/loop.py` can pick the Ralph
wiring without an import cycle. Default (`classic`) keeps the per-sprint Coder
byte-identical; `ralph` selects the one-task-per-invocation Ralph loop.
"""

import os
from typing import Literal

CODER_ENV_VAR = "LOOP_ENGINE_CODER"
RALPH_MAX_ITERS_ENV_VAR = "LOOP_ENGINE_RALPH_MAX_ITERS"

_CLASSIC = "classic"
_RALPH = "ralph"
_ALLOWED = (_CLASSIC, _RALPH)

# The Ralph self-loop bound: the Coder stage's `max_revisions` under ralph mode.
# Generous headroom over a realistic task count; the USD budget and the
# no-progress escalation terminate a stuck run well before this.
_DEFAULT_MAX_ITERS = 30


def coder_mode() -> Literal["classic", "ralph"]:
    """The selected Coder mode; unset/empty ⇒ `classic`. Unknown ⇒ ValueError."""
    raw = os.environ.get(CODER_ENV_VAR, "").strip().lower()
    if not raw:
        return _CLASSIC
    if raw not in _ALLOWED:
        raise ValueError(
            f"{CODER_ENV_VAR}={raw!r} is not a valid Coder mode; expected one of {_ALLOWED}"
        )
    return raw  # type: ignore[return-value]


def use_ralph_coder() -> bool:
    """Whether the Ralph-loop Coder is selected via the environment flag."""
    return coder_mode() == _RALPH


def ralph_max_iterations() -> int:
    """The Ralph iteration cap; must be a positive integer if set."""
    raw = os.environ.get(RALPH_MAX_ITERS_ENV_VAR, "").strip()
    if not raw:
        return _DEFAULT_MAX_ITERS
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{RALPH_MAX_ITERS_ENV_VAR}={raw!r} is not an integer") from exc
    if value <= 0:
        raise ValueError(f"{RALPH_MAX_ITERS_ENV_VAR} must be positive, got {value}")
    return value
