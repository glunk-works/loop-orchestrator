"""`InventoryRepository` -- the write-only Protocol over the bounty loop's
cross-run inventory (§4, P0-D7). Read/query/dedup/join methods are deferred
to Phase 1's Recon consumer; this sprint ships schema + writes only.

Upserts key on the §4 natural keys (P0-D8) -- a second call with the same
natural key updates the existing row rather than duplicating it.
`insert_finding` is a plain append: each finding is a distinct observation.
"""

from typing import Any, Protocol

from loop_orchestrator.tools.inventory_db.models import (
    AssetId,
    EndpointId,
    FindingId,
    TargetId,
    ValidationStatus,
)


class InventoryRepository(Protocol):
    def bootstrap(self) -> None: ...

    def upsert_target(
        self,
        program_name: str,
        in_scope_regex: list[str] | None = None,
        out_of_scope_regex: list[str] | None = None,
        banned_actions: list[str] | None = None,
    ) -> TargetId: ...

    def upsert_asset(
        self,
        target_id: TargetId,
        asset_identifier: str,
        asset_type: str | None = None,
        open_ports: list[int] | None = None,
        raw_scan_data: dict[str, Any] | None = None,
    ) -> AssetId: ...

    def upsert_endpoint(
        self,
        asset_id: AssetId,
        url_path: str,
        http_methods: list[str] | None = None,
        tech_stack: dict[str, Any] | None = None,
        requires_auth: bool | None = None,
    ) -> EndpointId: ...

    def insert_finding(
        self,
        endpoint_id: EndpointId,
        run_id: str,
        finding_type: str | None = None,
        severity: str | None = None,
        reproduction_steps: str | None = None,
        validation_status: ValidationStatus = "unverified",
    ) -> FindingId: ...
