"""Domain models for the bounty loop's cross-run asset/finding inventory
(§4). Pydantic, `extra="forbid"` -- a typed row is a fixed shape, not an
open bag, matching `State`'s discipline (`core/state.py`).

`TargetId`/`AssetId`/`EndpointId`/`FindingId` are thin `NewType`s over `UUID`
so the §4 by-ID boundary discipline (`State` references inventory rows by ID,
never embeds them) is expressed in the type system.
"""

from typing import Any, Literal, NewType
from uuid import UUID

from pydantic import BaseModel, ConfigDict

TargetId = NewType("TargetId", UUID)
AssetId = NewType("AssetId", UUID)
EndpointId = NewType("EndpointId", UUID)
FindingId = NewType("FindingId", UUID)

ValidationStatus = Literal["unverified", "ai_verified", "human_verified"]


class Target(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: TargetId
    program_name: str
    in_scope_regex: list[str] = []
    out_of_scope_regex: list[str] = []
    banned_actions: list[str] = []


class Asset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: AssetId
    target_id: TargetId
    asset_identifier: str
    asset_type: str | None = None
    open_ports: list[int] = []
    raw_scan_data: dict[str, Any] | None = None


class Endpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: EndpointId
    asset_id: AssetId
    url_path: str
    http_methods: list[str] = []
    tech_stack: dict[str, Any] | None = None
    requires_auth: bool | None = None


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: FindingId
    endpoint_id: EndpointId
    run_id: str
    finding_type: str | None = None
    severity: str | None = None
    reproduction_steps: str | None = None
    validation_status: ValidationStatus = "unverified"
