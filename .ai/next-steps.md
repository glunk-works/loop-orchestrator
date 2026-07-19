# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 44 (`tools/inventory_db` + the §4 Postgres schema).
`sprint_status: implementing`, assigned Sonnet/coder for Task 2.** Task 1 (the hermetic
core, driver-free) is **merged to `main`** (PR
[#159](https://github.com/glunk-works/loop-orchestrator/pull/159), squash `6bfc173`) with
the fresh-session `architect-review` posted and green. T2 (the real psycopg3 driver) and
T3 (docs) remain. Sprint 43 (BL-5 model routing) is complete and archived. The second loop
(`loops/bounty/`) is the active initiative; the dev loop (`loops/default`) stays paused.

## Just done (2026-07-19) — sprint 44 Task 1 Architect Review (Opus/architect, fresh session)
- **`/code-review` (high) on PR #159 @ `d9967da`** — the hermetic core (`inventory.sql`,
  the Pydantic models + `NewType` IDs, the write-only `InventoryRepository` Protocol, the
  `InMemoryInventory` fake, two hermetic test modules). Verdict: merge-ready, no blocking
  findings; schema columns align 1:1 with the models, DDL is interpolation-free, boundary
  correctly empty of psycopg this sprint.
- **Posted the Architect Review** with the verbatim header + attestation (`gh pr review
  --comment`, never `--approve` — gh authenticates as `Seuss27`, the PR author). Three
  low-to-medium notes, all carried into T2 (see next): (1) the `CHECK`↔`Literal` drift
  guard `test_validation_status_check_matches_model_literal` never reads the SQL — it pins
  the model `Literal` to a hardcoded constant, so a CHECK-only value add ships silently;
  (2) inconsistent `ValidationError→InventoryError` wrapping between `insert_finding` and
  the upserts; (3) partial upsert clobbers prior list fields via `x or []`. Forward note:
  `gen_random_uuid()` needs `pgcrypto` on Postgres <13.
- **BL-35 stale-red trap watched and cleared on its own** — `architect-review` fires on
  both `pull_request` and `pull_request_review`; the newer review-triggered run superseded
  the old pre-review red, both settled SUCCESS, rollup `CLEAN`. No `gh run rerun` needed.
- **Owner merged T1** (squash `6bfc173`); `main` synced.

## Next — implement Task 2 (Sonnet/coder), auto-startable
On a **fresh `sprint/44-inventory-db` branch cut from the current `main` (`6bfc173`)**:
`PsycopgInventory` (parameterized SQL only) + `bootstrap()` running `inventory.sql` +
`build_inventory_from_env()` (env-var DSN, **fail-closed**, no keyring) + pin
`psycopg[binary]` + regen `sbom.json` + clean `pip-audit` + the **sole-importer AST
boundary test** (modeled on `tests/tools/test_keyring_boundary.py`, landed in the **same
T2 PR** as the import it guards) + the **skip-when-no-DSN** integration test (must SKIP not
ERROR — verify `hatch run test -k inventory` shows it skipped). **Fold in the three review
notes above.** Run the FULL local gate before push; open the T2 PR against `main`; then
`/critic-gate` on the T2 diff (**guard-adversary now applies** — confirm the boundary test
goes RED under a planted psycopg import, BL-15) before the T2 architect-review handoff.

**Next HITL Gate:** none open. The planning micro-gates are closed; the next Gate is the
sprint-44 **completion** Gate (the owner's merges of the T2/T3 PRs). Each `src/`-touching
PR still needs its own fresh-session `architect-review` CI gate before it's mergeable.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **`tools/inventory_db` becomes an enforced module boundary in T2** — the sole `psycopg`
  importer; pin it with an AST test modeled on `tests/tools/test_keyring_boundary.py`,
  landed in the **same PR (T2)** as the import it guards, guard-adversary-confirmed RED
  under a planted violation (BL-15).
- **Parameterized SQL only** — the SQL-sink analog of fixed-argv/`shell=False`; T1's DDL
  has zero interpolation (security-critic-confirmed) — keep it that way through T2, before
  sprint 45's untrusted scanner-output ingestion flows through these write methods.
- **The integration test must SKIP (not ERROR) with no DSN set** (T2) — verify `hatch run
  test -k inventory` shows it skipped in a no-DSN run before pushing.
- **T2 adds `psycopg[binary]`** ⇒ regen `sbom.json` (`hatch run sbom`) + clean `hatch run
  audit`, both CI gates.
- **`gen_random_uuid()` needs Postgres 13+** (core) or `CREATE EXTENSION IF NOT EXISTS
  pgcrypto` before `bootstrap()` runs the DDL — decide in T2.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first; the
  Conventional-Commits regex also rejects an upper-case subject start (bit T1 on the first
  `gh pr create`). **Never commit to `main`, merge, or force-push.** **Full local gate
  (lint→format→test) before push** (memory: #141).

## Pointers
- [PR #159](https://github.com/glunk-works/loop-orchestrator/pull/159) — sprint-44 Task 1, **merged** (`6bfc173`).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§4 persistence + schema, §8 roadmap, §9 decisions log P0-D1..D10). **Read first.**
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the sprint-44 plan (T1 done, T2/T3, P0-D7..D10, PR structure, security invariants).
- [`docs/backlog.md`](../docs/backlog.md) — paused dev-loop items behind the bounty pivot.
