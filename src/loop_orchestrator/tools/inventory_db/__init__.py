"""Cross-run asset/finding inventory (bounty loop, §4) -- the module that
owns the sole Postgres connection. T1 shipped the hermetic core: the schema
DDL (`inventory.sql`), the domain models, the write-only
`InventoryRepository` Protocol, and the `InMemoryInventory` fake. T2 adds
the real driver: `PsycopgInventory` (the sole `psycopg` importer, pinned by
`tests/tools/inventory_db/test_boundary.py`) and `build_inventory_from_env()`.
"""

from loop_orchestrator.tools.inventory_db.factory import build_inventory_from_env
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
from loop_orchestrator.tools.inventory_db.psycopg_impl import PsycopgInventory
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
    "PsycopgInventory",
    "Target",
    "TargetId",
    "ValidationStatus",
    "build_inventory_from_env",
]
