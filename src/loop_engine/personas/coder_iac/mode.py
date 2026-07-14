"""The Ralph loop's iteration bound.

Until Phase 6 this module was also the single reader of `LOOP_ENGINE_CODER`,
selecting between the classic per-sprint Coder and the Ralph loop. That flag and
the classic Coder are deleted — Ralph is the only Coder — so all that remains is
its self-loop bound, which is genuine runtime config rather than migration
scaffolding.
"""

import os

RALPH_MAX_ITERS_ENV_VAR = "LOOP_ENGINE_RALPH_MAX_ITERS"

# The Ralph self-loop bound: the Coder stage's `max_revisions`. Generous headroom
# over a realistic task count; the USD budget and the no-progress escalation
# terminate a stuck run well before this.
_DEFAULT_MAX_ITERS = 30


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
