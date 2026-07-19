"""`InMemoryInventory` -- the hermetic fake `InventoryRepository` (P0-D4/
P0-D7). Dict-backed; mints `uuid4()` IDs; enforces the same natural-key
upsert semantics (P0-D8) and `validation_status` allowed set the real
psycopg3 impl (T2) enforces via UNIQUE constraints + a CHECK, so fake and
real stay behaviorally aligned without a live DB. This is the default test
double the hermetic suite runs against.

Row dicts (`targets`/`assets`/`endpoints`/`findings`) are public so tests can
inspect written state directly -- there is deliberately no read/query method
on the Protocol this sprint (P0-D7), and inspecting a fake's own state is not
that.
"""

from typing import Any
from uuid import uuid4

from pydantic import ValidationError

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


class InventoryError(Exception):
    """Raised on an inventory-integrity violation: an unknown FK-shaped
    reference or a row that fails a model constraint (e.g. an invalid
    `validation_status`)."""


class InMemoryInventory:
    def __init__(self) -> None:
        self.targets: dict[TargetId, Target] = {}
        self.assets: dict[AssetId, Asset] = {}
        self.endpoints: dict[EndpointId, Endpoint] = {}
        self.findings: dict[FindingId, Finding] = {}
        self._target_by_name: dict[str, TargetId] = {}
        self._asset_by_natural_key: dict[tuple[TargetId, str], AssetId] = {}
        self._endpoint_by_natural_key: dict[tuple[AssetId, str], EndpointId] = {}

    def bootstrap(self) -> None:
        pass

    def upsert_target(
        self,
        program_name: str,
        in_scope_regex: list[str] | None = None,
        out_of_scope_regex: list[str] | None = None,
        banned_actions: list[str] | None = None,
    ) -> TargetId:
        existing_id = self._target_by_name.get(program_name)
        target_id = existing_id if existing_id is not None else TargetId(uuid4())
        target = Target(
            id=target_id,
            program_name=program_name,
            in_scope_regex=in_scope_regex or [],
            out_of_scope_regex=out_of_scope_regex or [],
            banned_actions=banned_actions or [],
        )
        self.targets[target_id] = target
        self._target_by_name[program_name] = target_id
        return target_id

    def upsert_asset(
        self,
        target_id: TargetId,
        asset_identifier: str,
        asset_type: str | None = None,
        open_ports: list[int] | None = None,
        raw_scan_data: dict[str, Any] | None = None,
    ) -> AssetId:
        if target_id not in self.targets:
            raise InventoryError(f"unknown target_id {target_id!r}")
        key = (target_id, asset_identifier)
        existing_id = self._asset_by_natural_key.get(key)
        asset_id = existing_id if existing_id is not None else AssetId(uuid4())
        asset = Asset(
            id=asset_id,
            target_id=target_id,
            asset_identifier=asset_identifier,
            asset_type=asset_type,
            open_ports=open_ports or [],
            raw_scan_data=raw_scan_data,
        )
        self.assets[asset_id] = asset
        self._asset_by_natural_key[key] = asset_id
        return asset_id

    def upsert_endpoint(
        self,
        asset_id: AssetId,
        url_path: str,
        http_methods: list[str] | None = None,
        tech_stack: dict[str, Any] | None = None,
        requires_auth: bool | None = None,
    ) -> EndpointId:
        if asset_id not in self.assets:
            raise InventoryError(f"unknown asset_id {asset_id!r}")
        key = (asset_id, url_path)
        existing_id = self._endpoint_by_natural_key.get(key)
        endpoint_id = existing_id if existing_id is not None else EndpointId(uuid4())
        endpoint = Endpoint(
            id=endpoint_id,
            asset_id=asset_id,
            url_path=url_path,
            http_methods=http_methods or [],
            tech_stack=tech_stack,
            requires_auth=requires_auth,
        )
        self.endpoints[endpoint_id] = endpoint
        self._endpoint_by_natural_key[key] = endpoint_id
        return endpoint_id

    def insert_finding(
        self,
        endpoint_id: EndpointId,
        run_id: str,
        finding_type: str | None = None,
        severity: str | None = None,
        reproduction_steps: str | None = None,
        validation_status: ValidationStatus = "unverified",
    ) -> FindingId:
        if endpoint_id not in self.endpoints:
            raise InventoryError(f"unknown endpoint_id {endpoint_id!r}")
        try:
            finding = Finding(
                id=FindingId(uuid4()),
                endpoint_id=endpoint_id,
                run_id=run_id,
                finding_type=finding_type,
                severity=severity,
                reproduction_steps=reproduction_steps,
                validation_status=validation_status,
            )
        except ValidationError as exc:
            raise InventoryError(str(exc)) from exc
        self.findings[finding.id] = finding
        return finding.id
