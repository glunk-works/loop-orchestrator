"""`InMemoryInventory` -- the hermetic fake `InventoryRepository` (P0-D4/
P0-D7). Dict-backed; mints `uuid4()` IDs; enforces the same natural-key
upsert semantics (P0-D8) and `validation_status` allowed set the real
psycopg3 impl (T2) enforces via UNIQUE constraints + a CHECK, so fake and
real stay behaviorally aligned without a live DB. This is the default test
double the hermetic suite runs against.

Upsert semantics are **coalesce, not full-replace** (T2 architect-review
note): a `None` argument means "not provided" and preserves the existing
row's value; an explicit value (including `[]`) overwrites it. `T2`'s
`PsycopgInventory` mirrors this exactly via a select-then-insert-or-update
so a partial upsert never silently wipes a previously-set field.

Row dicts (`targets`/`assets`/`endpoints`/`findings`) are public so tests can
inspect written state directly -- there is deliberately no read/query method
on the Protocol this sprint (P0-D7), and inspecting a fake's own state is not
that.
"""

from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

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


_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _build(model_cls: type[_ModelT], **kwargs: Any) -> _ModelT:
    """Construct a domain model, wrapping any `ValidationError` in
    `InventoryError` -- every row constructor uses this so the error type a
    caller catches doesn't depend on which write method raised it (T2
    architect-review note: `insert_finding` did this but the upserts didn't)."""
    try:
        return model_cls(**kwargs)
    except ValidationError as exc:
        raise InventoryError(str(exc)) from exc


def _pick(new: Any, prior: BaseModel | None, field: str, default: Any) -> Any:
    """Coalesce a partial-upsert argument: an explicit `new` value always
    wins; otherwise fall back to the prior row's field (update path) or
    `default` (fresh-insert path). `new is None` is the "not provided"
    sentinel, so an explicit `[]` still overwrites -- only omitting the
    argument preserves the existing value."""
    if new is not None:
        return new
    if prior is not None:
        return getattr(prior, field)
    return default


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
        prior = self.targets.get(existing_id) if existing_id is not None else None
        target_id = existing_id if existing_id is not None else TargetId(uuid4())
        target = _build(
            Target,
            id=target_id,
            program_name=program_name,
            in_scope_regex=_pick(in_scope_regex, prior, "in_scope_regex", []),
            out_of_scope_regex=_pick(out_of_scope_regex, prior, "out_of_scope_regex", []),
            banned_actions=_pick(banned_actions, prior, "banned_actions", []),
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
        prior = self.assets.get(existing_id) if existing_id is not None else None
        asset_id = existing_id if existing_id is not None else AssetId(uuid4())
        asset = _build(
            Asset,
            id=asset_id,
            target_id=target_id,
            asset_identifier=asset_identifier,
            asset_type=_pick(asset_type, prior, "asset_type", None),
            open_ports=_pick(open_ports, prior, "open_ports", []),
            raw_scan_data=_pick(raw_scan_data, prior, "raw_scan_data", None),
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
        prior = self.endpoints.get(existing_id) if existing_id is not None else None
        endpoint_id = existing_id if existing_id is not None else EndpointId(uuid4())
        endpoint = _build(
            Endpoint,
            id=endpoint_id,
            asset_id=asset_id,
            url_path=url_path,
            http_methods=_pick(http_methods, prior, "http_methods", []),
            tech_stack=_pick(tech_stack, prior, "tech_stack", None),
            requires_auth=_pick(requires_auth, prior, "requires_auth", None),
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
        finding = _build(
            Finding,
            id=FindingId(uuid4()),
            endpoint_id=endpoint_id,
            run_id=run_id,
            finding_type=finding_type,
            severity=severity,
            reproduction_steps=reproduction_steps,
            validation_status=validation_status,
        )
        self.findings[finding.id] = finding
        return finding.id
