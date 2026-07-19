"""Hermetic unit tests for InMemoryInventory (T1 -- no driver, no psycopg).

Covers: natural-key upsert idempotency (P0-D8), find-after-write via the
returned ID, findings as an append-only insert, an invalid
`validation_status` being rejected, and the FK-shaped relationships holding
in the fake's model.
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from loop_orchestrator.tools.inventory_db import InMemoryInventory, InventoryError, Target
from loop_orchestrator.tools.inventory_db.models import AssetId, EndpointId, TargetId


@pytest.fixture
def inventory() -> InMemoryInventory:
    inv = InMemoryInventory()
    inv.bootstrap()
    return inv


def test_upsert_target_idempotent(inventory: InMemoryInventory) -> None:
    first = inventory.upsert_target("acme-bounty", in_scope_regex=[r"^acme\.com$"])
    second = inventory.upsert_target(
        "acme-bounty", in_scope_regex=[r"^acme\.com$", r"^api\.acme\.com$"]
    )

    assert first == second
    assert len(inventory.targets) == 1
    assert inventory.targets[first].in_scope_regex == [r"^acme\.com$", r"^api\.acme\.com$"]


def test_upsert_asset_idempotent_and_keyed_by_target(inventory: InMemoryInventory) -> None:
    target_id = inventory.upsert_target("acme-bounty")
    first = inventory.upsert_asset(target_id, "10.0.0.1", asset_type="host")
    second = inventory.upsert_asset(target_id, "10.0.0.1", asset_type="host", open_ports=[80, 443])

    assert first == second
    assert len(inventory.assets) == 1
    assert inventory.assets[first].open_ports == [80, 443]


def test_upsert_asset_unknown_target_raises(inventory: InMemoryInventory) -> None:
    with pytest.raises(InventoryError):
        inventory.upsert_asset(TargetId(uuid4()), "10.0.0.1")


def test_upsert_endpoint_idempotent_and_keyed_by_asset(inventory: InMemoryInventory) -> None:
    target_id = inventory.upsert_target("acme-bounty")
    asset_id = inventory.upsert_asset(target_id, "10.0.0.1")
    first = inventory.upsert_endpoint(asset_id, "/login", http_methods=["GET"])
    second = inventory.upsert_endpoint(asset_id, "/login", http_methods=["GET", "POST"])

    assert first == second
    assert len(inventory.endpoints) == 1
    assert inventory.endpoints[first].http_methods == ["GET", "POST"]


def test_upsert_endpoint_unknown_asset_raises(inventory: InMemoryInventory) -> None:
    with pytest.raises(InventoryError):
        inventory.upsert_endpoint(AssetId(uuid4()), "/login")


def test_insert_finding_appends_distinct_rows(inventory: InMemoryInventory) -> None:
    target_id = inventory.upsert_target("acme-bounty")
    asset_id = inventory.upsert_asset(target_id, "10.0.0.1")
    endpoint_id = inventory.upsert_endpoint(asset_id, "/login")

    first = inventory.insert_finding(endpoint_id, run_id="run-1", finding_type="idor")
    second = inventory.insert_finding(endpoint_id, run_id="run-2", finding_type="idor")

    assert first != second
    assert len(inventory.findings) == 2
    assert inventory.findings[first].run_id == "run-1"
    assert inventory.findings[second].run_id == "run-2"


def test_insert_finding_unknown_endpoint_raises(inventory: InMemoryInventory) -> None:
    with pytest.raises(InventoryError):
        inventory.insert_finding(EndpointId(uuid4()), run_id="run-1")


def test_insert_finding_default_validation_status_is_unverified(
    inventory: InMemoryInventory,
) -> None:
    target_id = inventory.upsert_target("acme-bounty")
    asset_id = inventory.upsert_asset(target_id, "10.0.0.1")
    endpoint_id = inventory.upsert_endpoint(asset_id, "/login")

    finding_id = inventory.insert_finding(endpoint_id, run_id="run-1")

    assert inventory.findings[finding_id].validation_status == "unverified"


def test_insert_finding_rejects_invalid_validation_status(inventory: InMemoryInventory) -> None:
    target_id = inventory.upsert_target("acme-bounty")
    asset_id = inventory.upsert_asset(target_id, "10.0.0.1")
    endpoint_id = inventory.upsert_endpoint(asset_id, "/login")

    with pytest.raises(InventoryError):
        inventory.insert_finding(endpoint_id, run_id="run-1", validation_status="bogus")


def test_target_model_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        Target(id=TargetId(uuid4()), program_name="acme", extra_field="nope")
