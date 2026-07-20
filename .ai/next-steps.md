# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 44 (`tools/inventory_db` + the §4 Postgres schema).
`sprint_status: implementing`, assigned Sonnet/coder.** Task 1 (hermetic core) merged
(`6bfc173`, PR [#159](https://github.com/glunk-works/loop-orchestrator/pull/159)) and Task 2
(the real psycopg3 driver) merged (`32c000a`, PR
[#162](https://github.com/glunk-works/loop-orchestrator/pull/162)). **Remaining:** the F1
fix (a live defect the T2 Architect Review caught, merged over) + T3 docs — one PR. The
second loop (`loops/bounty/`) is the active initiative; the dev loop (`loops/default`) stays
paused.

## Just done (2026-07-20) — T2 Architect Review + merge (Opus/architect)
- **Posted the fresh-session Architect Review on PR #162** (verbatim header + attestation,
  `gh pr review --comment`). During the review the `architect-review`/`secrets-scan` checks
  went red across #162 and #163 — traced to a **GitHub "Minor Service Outage"** (infra
  flake, not the review: my review is recorded with the exact header, and the run fired 3s
  after it). Held reruns until the outage cleared.
- **Outage cleared; owner merged both PRs** — #162 (T2 driver, `32c000a`) and #163 (docs
  sync, `d48cc83`). Local `main` synced; stale feature branches pruned.
- **Review findings (5):** **F1 (should-fix, now live on `main`)** — `PsycopgInventory`
  binds a bare `dict` for the two JSONB columns (`raw_scan_data`/`tech_stack`), but psycopg
  3.3.4 has **no `dict` dumper** (verified against the pinned wheel: `cannot adapt type
  'dict'`), so every non-None dict write raises `ProgrammingError`→`InventoryError`. The
  live V-run missed it because `test_full_write_chain_round_trips` leaves both dict fields
  `None`. F2 upsert TOCTOU race · F3 held conn never closed · F4 single conn not
  thread-safe · F5 SQL-param guard narrower than its docstring — **F2–F5 are Phase-1 notes,
  not this task.**
- **`security-critic` still has not run on the T2 diff** (spend limit) — a retroactive pass
  is worth doing once spend resets.

## Next — land the sprint-44 remainder (Sonnet/coder), then a FRESH Opus review
On a `sprint/44-inventory-remainder` branch cut from `main`:
1. **Fix F1** — wrap the `raw_scan_data`/`tech_stack` dict binds in
   `psycopg.types.json.Jsonb(...)` (leave `None` as `None` — `Jsonb(None)` writes JSON null,
   not SQL NULL) in BOTH the INSERT and UPDATE paths of `upsert_asset`/`upsert_endpoint`;
   extend `test_full_write_chain_round_trips` to pass a non-empty dict for both so the V-run
   actually exercises the JSONB path.
2. **T3 docs** — add the `tools/inventory_db` sole-psycopg-importer + parameterized-SQL
   boundary bullet to CLAUDE.md; advance §8 (T1+T2 merged) / §9 in
   `docs/bounty_loop_architecture.md`.
3. FULL local gate (lint → format → test) → ONE PR against `main`. It touches `src/`, so it
   needs a **fresh-session Opus `architect-review`** afterward (a later `/handoff`). Watch
   the BL-35 stale-red trap.

**Next HITL Gate:** none open. The next Gate is the sprint-44 **completion** Gate (the
owner's merge of the remainder PR).

## Gotchas worth remembering
- **F1 is unfixed on `main`** — see `memory/inventory-jsonb-dict-bug.md`. It breaks the
  first Phase-1 Recon scan-data write; fix it in this remainder, don't defer.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **`tools/inventory_db` is an enforced boundary** — `psycopg_impl.py` is the sole `psycopg`
  importer (`test_boundary.py`); every `execute()` outside `bootstrap()` is a static literal
  (`test_sql_parameterization.py`). Both manually guard-adversary-confirmed RED under a
  planted violation (BL-15).
- **`gen_random_uuid()` needs no `pgcrypto`** — PG13+ core builtin (P0-D8), live-verified.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first. **Never commit
  to `main`, merge, or force-push.** **Full local gate before push** (memory: #141).

## Pointers
- [PR #159](https://github.com/glunk-works/loop-orchestrator/pull/159) — sprint-44 T1, **merged** (`6bfc173`).
- [PR #162](https://github.com/glunk-works/loop-orchestrator/pull/162) — sprint-44 T2, **merged** (`32c000a`).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§4 persistence + schema, §8 roadmap, §9 decisions P0-D1..D10). **Read first.**
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the sprint-44 plan (T1/T2 merged, T3, P0-D7..D10, PR structure, security invariants).
- [`docs/backlog.md`](../docs/backlog.md) — paused dev-loop items behind the bounty pivot.
