"""The S47-D5/D11 untrusted-input ingest pipeline (T2): parse -> normalize
the identifier -> scope-filter (drop+count) -> sanitize the free-text
survivors -> `inventory_db` upsert. This is where P1-D6's **output** scope
boundary lives -- the input half (`validate_target`-raise on the seed)
lives in `tools/recon/models.py` (T1).

Records are grouped by their own (normalized) `host` before any upsert, so
an off-host discovery -- e.g. an httpx redirect landing on a host distinct
from the seed -- is scope-checked and persisted as **its own** asset
(S47-D11), never silently folded into the seed's. Scope is decided on the
*normalized* identifier and that same normalized form is what gets stored
(anti-evasion: an invisible-character/homoglyph host must not slip past the
regex by looking different pre-normalization than post-).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scope_core import DEFAULT_MAX_LEN, ScopeRules, is_in_scope, normalize, sanitize

from loop_orchestrator.tools.inventory_db.models import AssetId, TargetId
from loop_orchestrator.tools.inventory_db.repository import InventoryRepository
from loop_orchestrator.tools.recon.parse import ReconRecord, parse_jsonl


@dataclass
class IngestStats:
    """Per-batch drop counters -- surfaced as a run signal (S47-D5), never
    silently swallowed."""

    malformed_records: int = 0
    out_of_scope_hosts: int = 0


def _sanitize_or_none(value: str | None) -> str | None:
    if not value:
        return None
    return sanitize(value, max_len=DEFAULT_MAX_LEN)


def _sanitized_tech(records: list[ReconRecord]) -> list[str]:
    seen: set[str] = set()
    for record in records:
        for item in record.tech:
            cleaned = _sanitize_or_none(item)
            if cleaned:
                seen.add(cleaned)
    return sorted(seen)


def _sanitized_http_methods(record: ReconRecord) -> list[str] | None:
    # http_methods is scanner-observed text like every other free-text
    # field on the record -- attacker-influenceable, so it gets the same
    # sanitize pass as title/webserver/tech/matched_at before it reaches
    # inventory_db (and, downstream, a triage LLM). An empty/all-stripped
    # list is "not provided" (None), matching upsert_endpoint's coalesce
    # semantics -- never an empty-list overwrite of a prior value.
    cleaned = [m for item in record.http_methods if (m := _sanitize_or_none(item))]
    return cleaned or None


def _raw_scan_data(records: list[ReconRecord], tech: list[str]) -> dict[str, Any] | None:
    titles = sorted({t for r in records if (t := _sanitize_or_none(r.title))})
    webservers = sorted({w for r in records if (w := _sanitize_or_none(r.webserver))})
    matched_at = sorted({m for r in records if (m := _sanitize_or_none(r.matched_at))})

    data: dict[str, Any] = {}
    if titles:
        data["titles"] = titles
    if webservers:
        data["webservers"] = webservers
    if tech:
        data["tech"] = tech
    if matched_at:
        data["matched_at"] = matched_at
    return data or None


def ingest_batch(
    *,
    rules: ScopeRules,
    target_id: TargetId,
    payload: bytes,
    inventory: InventoryRepository,
) -> tuple[list[AssetId], IngestStats]:
    """Run the full T2 pipeline over one recon JSONL payload, upserting only
    in-scope, sanitized assets/endpoints. Returns the upserted `AssetId`s
    (S47-D4 -- the artifact carries these as UUID strings) plus per-batch
    drop counters.
    """
    records, malformed_count = parse_jsonl(payload)
    stats = IngestStats(malformed_records=malformed_count)

    by_identifier: dict[str, list[ReconRecord]] = {}
    for record in records:
        identifier = normalize(record.host)
        by_identifier.setdefault(identifier, []).append(record)

    asset_ids: list[AssetId] = []
    for identifier, host_records in by_identifier.items():
        if not is_in_scope(rules, identifier):
            stats.out_of_scope_hosts += 1
            continue

        ports = sorted({r.port for r in host_records if r.port is not None})
        tech = _sanitized_tech(host_records)
        asset_id = inventory.upsert_asset(
            target_id,
            identifier,
            open_ports=ports,
            raw_scan_data=_raw_scan_data(host_records, tech),
        )
        asset_ids.append(asset_id)

        for record in host_records:
            if record.path is None:
                continue
            sanitized_path = _sanitize_or_none(record.path)
            if not sanitized_path:
                # The path was entirely stripped by `sanitize` (e.g. pure
                # invisible-format content) -- never fall back to the raw,
                # unsanitized value; just drop this one endpoint.
                continue
            inventory.upsert_endpoint(
                asset_id,
                sanitized_path,
                http_methods=_sanitized_http_methods(record),
                tech_stack={"tech": tech} if tech else None,
            )

    return asset_ids, stats
