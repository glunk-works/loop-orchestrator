"""`build_inventory_from_env()` -- the runtime builder for `PsycopgInventory`
(P0-D4). Reads the DSN from `LOOP_ORCHESTRATOR_INVENTORY_DSN`, an **env var,
not keyring** -- a distinct credential class from the keyring-only Anthropic
key, same posture as `LOOP_ORCHESTRATOR_WEBHOOK_SECRET` and the Slack
tokens. Fails closed (raises) when the DSN is unset, and never logs it.
"""

from loop_orchestrator.tools.env_compat import getenv_compat
from loop_orchestrator.tools.inventory_db.psycopg_impl import PsycopgInventory

_DSN_ENV = "LOOP_ORCHESTRATOR_INVENTORY_DSN"  # noqa: S105 -- env var name, not a credential


def build_inventory_from_env() -> PsycopgInventory:
    """Fails closed (`RuntimeError`) when `LOOP_ORCHESTRATOR_INVENTORY_DSN`
    is unset, rather than returning a no-op/in-memory fallback -- a real DB
    connection is either configured or the caller must know it isn't."""
    dsn = getenv_compat(_DSN_ENV)
    if not dsn:
        raise RuntimeError(
            f"{_DSN_ENV} must be set; refusing to build a PsycopgInventory "
            "without a DSN (fail-closed)."
        )
    return PsycopgInventory(dsn)
