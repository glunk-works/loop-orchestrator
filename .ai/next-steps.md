# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 44 (`tools/inventory_db` + the §4 Postgres schema).
`sprint_status: implementing`, assigned Sonnet/coder.** The planning pass is done — the
plan is written; the next step is implementing Task 1. Sprint 43 (BL-5 model routing) is
complete and archived. The second loop (`loops/bounty/`) is the active initiative; the dev
loop (`loops/default`) stays paused.

## Just done (2026-07-19) — sprint 44 planning pass (Opus/architect)
- **Wrote `sprints/44_inventory_db/sprint_plan.md`** through four HITL micro-gates. Sprint 44
  stands up `tools/inventory_db` — the sole Postgres-connection / sole `psycopg` importer
  (the DB analog of the keyring single-importer) — plus the §4 schema. **Write surface only**
  this sprint.
- **Four new locked decisions** (P0-D7..D10, to be recorded in `docs/bounty_loop_architecture.md`
  §9 by T3):
  - **P0-D7** — scope = schema + writes only; read/query/join surface deferred to Phase 1's
    Recon consumer (no in-repo consumer until then — P0-D2).
  - **P0-D8** — UUID PKs (`gen_random_uuid()`); natural keys `program_name` /
    `(target_id, asset_identifier)` / `(asset_id, url_path)`; `findings` append-only insert +
    `run_id` plain-text soft-ref (no FK — snapshots live in JSON).
  - **P0-D9** — hard-pinned `psycopg[binary]` in the flat deps list; module-level import in
    the real impl only; regen `sbom` + pass `dependency-audit`.
  - **P0-D10** — `validation_status` = `TEXT` + `CHECK` (not native ENUM — keeps DDL cleanly
    idempotent per P0-D5); `TEXT[]`/`INT[]` arrays + `JSONB` per §4.
- Inherited & honored: **P0-D4** (hermetic fake default + skip-when-no-DSN psycopg3
  integration test + env-var DSN), **P0-D5** (idempotent `.sql`, no Alembic), **P0-D2** (no
  `schema_version` bump).

## Next — implement Task 1 (Sonnet/coder)
On a fresh **`sprint/44-inventory-db`** branch cut from `main`, implement **T1: the hermetic
core (driver-free)** — the `tools/inventory_db` package: `inventory.sql` (§4 + P0-D8/D10),
the Pydantic domain models (`extra="forbid"`) + ID newtypes, the write-only
`InventoryRepository` Protocol, the `InMemoryInventory` fake, and the full hermetic unit
suite. **No `psycopg` import, no dep change in T1** (that is T2). Follow the sprint plan
exactly. Then `/critic-gate` (architect indicated) → `/handoff` → fresh Opus
`architect-review` session.

**Next HITL Gate:** none open. The planning micro-gates are closed; the next Gate is the
sprint-44 **completion** Gate (the owner's merges of the T1/T2/T3 PRs). Each `src/`-touching
PR (T1, T2) also needs a fresh-session `architect-review` (a CI gate).

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **`tools/inventory_db` is a new enforced module boundary** — the sole `psycopg` importer;
  pin it with an AST test modeled on `tests/tools/test_keyring_boundary.py`, landed in the
  **same PR (T2)** as the psycopg import it guards, and have guard-adversary confirm it goes
  RED under a planted violation (BL-15).
- **Parameterized SQL only** — the SQL-sink analog of fixed-argv/`shell=False`; build it now,
  before sprint 45's untrusted scanner-output ingestion flows through these write methods.
- **The integration test must SKIP (not ERROR) with no DSN set** — verify `hatch run test -k
  inventory` shows it skipped in a no-DSN run before pushing.
- **T2 adds `psycopg[binary]`** ⇒ regen `sbom.json` (`hatch run sbom`) + clean `hatch run
  audit`, both CI gates. Confirm the `.sql` is packaged in the wheel build config.
- **Any `src/`-touching PR needs a fresh-session `architect-review`** — `/handoff` → new
  session → `/model opus` → `/resume` → `/code-review` → post the verbatim-header review.
  Watch the **BL-35 stale-red** trap (BLOCKED + rollup FAILURE ⇒ `gh run rerun` the OLD run).
- **PR title ≤72 bytes** — `wc -c` first. **Never commit to `main`, merge, or force-push.**
  **Full local gate (lint→format→test) before push** (memory: #141).

## Pointers
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§4 persistence + schema, §8 roadmap, §9 decisions log P0-D1..D10). **Read first.**
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the sprint-44 plan (T1/T2/T3, P0-D7..D10, PR structure, security invariants).
- [`docs/backlog.md`](../docs/backlog.md) — paused dev-loop items behind the bounty pivot.
