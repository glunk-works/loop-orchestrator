"""Cross-run asset/finding inventory (bounty loop, §4) -- the module that
will own the sole Postgres connection (T2 lands `PsycopgInventory`). This
sprint (T1) ships the hermetic core only: the schema DDL (`inventory.sql`),
the domain models, the write-only `InventoryRepository` Protocol, and the
`InMemoryInventory` fake. No `psycopg` import, no dependency change.
"""

from loop_orchestrator.tools.inventory_db.memory import InMemoryInventory, InventoryError
from loop_orchestrator.tools.inventory_db.models import (
    Asset,
    AssetId,
    Endpoint,
    EndpointId,
    Finding,
    FindingId,
    Target,
    TargetId,
    ValidationStatus,
)
from loop_orchestrator.tools.inventory_db.repository import InventoryRepository

__all__ = [
    "Asset",
    "AssetId",
    "Endpoint",
    "EndpointId",
    "Finding",
    "FindingId",
    "InMemoryInventory",
    "InventoryError",
    "InventoryRepository",
    "Target",
    "TargetId",
    "ValidationStatus",
]
