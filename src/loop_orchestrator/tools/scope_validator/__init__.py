"""The structural scope validator (bounty loop, §5) -- Phase 0's fail-closed
in/out-of-scope + banned-action check over sprint-44's `targets`
rules-of-engagement. A pure leaf: no live consumer yet (Phase 1 mounts this
at the scanning tools' Pydantic boundary), no runtime edge onto
`tools/inventory_db` (P0-D12), no `keyring`/`psycopg`/`subprocess`, no file
writes.
"""

from loop_orchestrator.tools.scope_validator.rules import ScopeRules
from loop_orchestrator.tools.scope_validator.validate import (
    ScopeViolation,
    is_action_banned,
    validate_target,
)

__all__ = [
    "ScopeRules",
    "ScopeViolation",
    "is_action_banned",
    "validate_target",
]
