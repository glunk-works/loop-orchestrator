"""`PsycopgInventory` -- the real, sync psycopg3 `InventoryRepository` (T2,
P0-D4/P0-D9). This is the **sole** module permitted to import `psycopg`,
pinned by `tests/tools/inventory_db/test_boundary.py` (the psycopg analog of
`tests/tools/test_keyring_boundary.py`).

Every value-bearing query is a static string with `%s` placeholders bound by
psycopg -- the SQL-sink analog of fixed-argv/`shell=False` on the five
sanctioned subprocess surfaces (CLAUDE.md). No SQL is ever built by
f-string/`%`-format/`.format()`/string concatenation on caller data; this
module contains no such construction at all, which is what makes that a
mechanically checkable invariant (`test_boundary.py` asserts it holds).

Upsert semantics mirror `InMemoryInventory` exactly (coalesce, not
full-replace, per the T2 architect-review note): each upsert selects the
existing row (if any) first, then a `None` argument falls back to the prior
row's value while an explicit value (including `[]`) overwrites it. This is
the select-then-insert-or-update shape rather than a single `ON CONFLICT ...
DO UPDATE` because `EXCLUDED` can't distinguish "caller omitted this field"
from "caller explicitly set it to NULL" -- the coalesce has to happen in
Python, on both implementations, identically.
"""

from importlib import resources
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from loop_orchestrator.tools.inventory_db.memory import InventoryError
from loop_orchestrator.tools.inventory_db.models import (
    AssetId,
    EndpointId,
    FindingId,
    TargetId,
    ValidationStatus,
)


class PsycopgInventory:
    """The real `InventoryRepository`: one held sync psycopg connection,
    one transaction per write call (no pooling -- YAGNI, P0-D4: there is no
    consumer yet to size a pool for)."""

    def __init__(self, dsn: str) -> None:
        self._conn = psycopg.connect(dsn)

    def bootstrap(self) -> None:
        """Applies the versioned `inventory.sql` DDL (P0-D5). Every
        statement is `CREATE ... IF NOT EXISTS`, so this is safe to call on
        every startup, including against an already-bootstrapped database.
        Assumes PostgreSQL 13+, where `gen_random_uuid()` is a core builtin
        (P0-D8) -- no `pgcrypto` extension is created or required."""
        sql = (
            resources.files("loop_orchestrator.tools.inventory_db")
            .joinpath("inventory.sql")
            .read_text(encoding="utf-8")
        )
        try:
            with self._conn.cursor() as cur:
                cur.execute(sql)
            self._conn.commit()
        except psycopg.Error as exc:
            self._conn.rollback()
            raise InventoryError(f"bootstrap failed: {exc}") from exc

    def upsert_target(
        self,
        program_name: str,
        in_scope_regex: list[str] | None = None,
        out_of_scope_regex: list[str] | None = None,
        banned_actions: list[str] | None = None,
    ) -> TargetId:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT id, in_scope_regex, out_of_scope_regex, banned_actions "
                    "FROM targets WHERE program_name = %s",
                    (program_name,),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "INSERT INTO targets "
                        "(program_name, in_scope_regex, out_of_scope_regex, banned_actions) "
                        "VALUES (%s, %s, %s, %s) RETURNING id",
                        (
                            program_name,
                            in_scope_regex or [],
                            out_of_scope_regex or [],
                            banned_actions or [],
                        ),
                    )
                    target_id = cur.fetchone()[0]
                else:
                    existing_id, existing_in, existing_out, existing_banned = row
                    cur.execute(
                        "UPDATE targets SET in_scope_regex = %s, out_of_scope_regex = %s, "
                        "banned_actions = %s WHERE id = %s",
                        (
                            in_scope_regex if in_scope_regex is not None else existing_in,
                            out_of_scope_regex if out_of_scope_regex is not None else existing_out,
                            banned_actions if banned_actions is not None else existing_banned,
                            existing_id,
                        ),
                    )
                    target_id = existing_id
            self._conn.commit()
        except psycopg.Error as exc:
            self._conn.rollback()
            raise InventoryError(str(exc)) from exc
        return TargetId(target_id)

    def upsert_asset(
        self,
        target_id: TargetId,
        asset_identifier: str,
        asset_type: str | None = None,
        open_ports: list[int] | None = None,
        raw_scan_data: dict[str, Any] | None = None,
    ) -> AssetId:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT id, asset_type, open_ports, raw_scan_data FROM assets "
                    "WHERE target_id = %s AND asset_identifier = %s",
                    (target_id, asset_identifier),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "INSERT INTO assets "
                        "(target_id, asset_identifier, asset_type, open_ports, raw_scan_data) "
                        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                        (
                            target_id,
                            asset_identifier,
                            asset_type,
                            open_ports or [],
                            Jsonb(raw_scan_data) if raw_scan_data is not None else None,
                        ),
                    )
                    asset_id = cur.fetchone()[0]
                else:
                    existing_id, existing_type, existing_ports, existing_scan = row
                    coalesced_scan = raw_scan_data if raw_scan_data is not None else existing_scan
                    cur.execute(
                        "UPDATE assets SET asset_type = %s, open_ports = %s, "
                        "raw_scan_data = %s WHERE id = %s",
                        (
                            asset_type if asset_type is not None else existing_type,
                            open_ports if open_ports is not None else existing_ports,
                            Jsonb(coalesced_scan) if coalesced_scan is not None else None,
                            existing_id,
                        ),
                    )
                    asset_id = existing_id
            self._conn.commit()
        except psycopg.Error as exc:
            self._conn.rollback()
            raise InventoryError(str(exc)) from exc
        return AssetId(asset_id)

    def upsert_endpoint(
        self,
        asset_id: AssetId,
        url_path: str,
        http_methods: list[str] | None = None,
        tech_stack: dict[str, Any] | None = None,
        requires_auth: bool | None = None,
    ) -> EndpointId:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT id, http_methods, tech_stack, requires_auth FROM endpoints "
                    "WHERE asset_id = %s AND url_path = %s",
                    (asset_id, url_path),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "INSERT INTO endpoints "
                        "(asset_id, url_path, http_methods, tech_stack, requires_auth) "
                        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                        (
                            asset_id,
                            url_path,
                            http_methods or [],
                            Jsonb(tech_stack) if tech_stack is not None else None,
                            requires_auth,
                        ),
                    )
                    endpoint_id = cur.fetchone()[0]
                else:
                    existing_id, existing_methods, existing_stack, existing_auth = row
                    coalesced_stack = tech_stack if tech_stack is not None else existing_stack
                    cur.execute(
                        "UPDATE endpoints SET http_methods = %s, tech_stack = %s, "
                        "requires_auth = %s WHERE id = %s",
                        (
                            http_methods if http_methods is not None else existing_methods,
                            Jsonb(coalesced_stack) if coalesced_stack is not None else None,
                            requires_auth if requires_auth is not None else existing_auth,
                            existing_id,
                        ),
                    )
                    endpoint_id = existing_id
            self._conn.commit()
        except psycopg.Error as exc:
            self._conn.rollback()
            raise InventoryError(str(exc)) from exc
        return EndpointId(endpoint_id)

    def insert_finding(
        self,
        endpoint_id: EndpointId,
        run_id: str,
        finding_type: str | None = None,
        severity: str | None = None,
        reproduction_steps: str | None = None,
        validation_status: ValidationStatus = "unverified",
    ) -> FindingId:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO findings "
                    "(endpoint_id, run_id, finding_type, severity, reproduction_steps, "
                    "validation_status) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (
                        endpoint_id,
                        run_id,
                        finding_type,
                        severity,
                        reproduction_steps,
                        validation_status,
                    ),
                )
                finding_id = cur.fetchone()[0]
            self._conn.commit()
        except psycopg.Error as exc:
            self._conn.rollback()
            raise InventoryError(str(exc)) from exc
        return FindingId(finding_id)
