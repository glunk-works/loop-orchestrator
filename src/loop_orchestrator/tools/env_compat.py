"""Env-var reads with a ``LOOP_ENGINE_*`` → ``LOOP_ORCHESTRATOR_*`` fallback.

The project's runtime env-var prefix was renamed ``LOOP_ENGINE_`` →
``LOOP_ORCHESTRATOR_`` alongside the ``loop-engine`` → ``loop-orchestrator``
package rename (sprint 42). Live deployments — the factory container host and
the Slack daemon — still set the **old** names in their environment, so a hard
cut would break a running system rather than fail a test.

``getenv_compat`` reads the new name and, only if it is unset, falls back to the
legacy ``LOOP_ENGINE_``-prefixed equivalent (warning once per var). Drop the
fallback a release later once every deployment sets the new names.

Pure stdlib (``os`` + ``warnings``): imports no project module, writes no file,
shells nothing — safe to import from any boundary-guarded package (core/,
trigger/, slack_control/, flows/, tools/).
"""

from __future__ import annotations

import os
import warnings

_NEW_PREFIX = "LOOP_ORCHESTRATOR_"
_OLD_PREFIX = "LOOP_ENGINE_"

# One deprecation warning per legacy var, not one per read.
_warned: set[str] = set()


def getenv_compat(name: str, default: str | None = None) -> str | None:
    """``os.environ.get(name, default)`` with a legacy-prefix fallback.

    ``name`` is expected to be a ``LOOP_ORCHESTRATOR_*`` var. If it is unset but
    its legacy ``LOOP_ENGINE_*`` equivalent is set, the legacy value is returned
    and a :class:`DeprecationWarning` is emitted once for that var. Behaviour is
    otherwise identical to :func:`os.environ.get` (returns ``default`` — which
    defaults to ``None`` — when neither is set).
    """
    value = os.environ.get(name)
    if value is not None:
        return value
    if name.startswith(_NEW_PREFIX):
        legacy = _OLD_PREFIX + name[len(_NEW_PREFIX) :]
        legacy_value = os.environ.get(legacy)
        if legacy_value is not None:
            if legacy not in _warned:
                _warned.add(legacy)
                warnings.warn(
                    f"{legacy} is deprecated; set {name} instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            return legacy_value
    return default
