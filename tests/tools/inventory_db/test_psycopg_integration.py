"""Marked integration test for `PsycopgInventory` (T2, P0-D4). Skips
cleanly -- not errors -- when `LOOP_ORCHESTRATOR_INVENTORY_DSN` is unset, so
the default hermetic `hatch run test` suite never depends on a live
Postgres. When a DSN is provided (e.g. by the `live-verify` deferred-
verification posture), this bootstraps a real database and round-trips a
full upsert/insert chain through the real driver -- the discharge evidence
that the parameterized SQL in `psycopg_impl.py` actually works against
Postgres, not just against the in-memory fake.
"""

import os

import pytest

from loop_orchestrator.tools.inventory_db import InventoryError
from loop_orchestrator.tools.inventory_db.psycopg_impl import PsycopgInventory

_DSN_ENV = "LOOP_ORCHESTRATOR_INVENTORY_DSN"  # noqa: S105 -- env var name, not a credential

pytestmark = pytest.mark.skipif(
    not os.environ.get(_DSN_ENV),
    reason=f"{_DSN_ENV} not set -- skipping the live-Postgres integration test",
)


@pytest.fixture
def inventory() -> PsycopgInventory:
    inv = PsycopgInventory(os.environ[_DSN_ENV])
    inv.bootstrap()
    return inv


def test_bootstrap_is_idempotent(inventory: PsycopgInventory) -> None:
    # A second bootstrap() on an already-bootstrapped database is a no-op,
    # not an error -- every DDL statement is CREATE ... IF NOT EXISTS.
    inventory.bootstrap()


def test_full_write_chain_round_trips(inventory: PsycopgInventory) -> None:
    target_id = inventory.upsert_target("acme-bounty-integration", in_scope_regex=[r"^acme\.com$"])
    asset_id = inventory.upsert_asset(target_id, "10.0.0.1", asset_type="host")
    endpoint_id = inventory.upsert_endpoint(asset_id, "/login", http_methods=["GET"])
    finding_id = inventory.insert_finding(endpoint_id, run_id="run-1", finding_type="idor")

    assert target_id is not None
    assert asset_id is not None
    assert endpoint_id is not None
    assert finding_id is not None


def test_upsert_target_is_idempotent_by_program_name(inventory: PsycopgInventory) -> None:
    first = inventory.upsert_target("acme-bounty-idempotent")
    second = inventory.upsert_target("acme-bounty-idempotent")

    assert first == second


def test_upsert_asset_unknown_target_raises_inventory_error(
    inventory: PsycopgInventory,
) -> None:
    from uuid import uuid4

    from loop_orchestrator.tools.inventory_db.models import TargetId

    with pytest.raises(InventoryError):
        inventory.upsert_asset(TargetId(uuid4()), "10.0.0.1")
