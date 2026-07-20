# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 44 (`tools/inventory_db` + the §4 Postgres schema).
`sprint_status: awaiting_architect_review`, assigned Opus/architect.** Task 1 (hermetic
core) merged to `main` (PR [#159](https://github.com/glunk-works/loop-orchestrator/pull/159),
squash `6bfc173`). **Task 2 (the real psycopg3 driver) is coded, tested, and open as
[PR #162](https://github.com/glunk-works/loop-orchestrator/pull/162) against `main`,
awaiting the fresh-session `architect-review`.** T3 (docs) remains after T2 merges. The
second loop (`loops/bounty/`) is the active initiative; the dev loop (`loops/default`)
stays paused.

## Just done (2026-07-20) — sprint 44 Task 2 implementation (Sonnet/coder)
- **`PsycopgInventory`** (`src/loop_orchestrator/tools/inventory_db/psycopg_impl.py`) — the
  real sync psycopg3 impl, sole permitted `psycopg` importer. Every `cur.execute()` call
  (outside `bootstrap()`, which applies the static packaged `inventory.sql` DDL) passes a
  static string literal with `%s` placeholders — no caller data ever reaches query text.
  Upserts are select-then-insert-or-update (not `ON CONFLICT ... DO UPDATE`) so a `None`
  argument can be distinguished from an explicit value — `EXCLUDED` can't make that
  distinction, so the coalesce has to happen in Python.
- **`build_inventory_from_env()`** (`factory.py`) — reads `LOOP_ORCHESTRATOR_INVENTORY_DSN`,
  fails closed (raises) when unset, never logs the DSN.
- **Folded in all three T1 review notes**: (1) `test_validation_status_check_matches_model_literal`
  now regex-parses the CHECK constraint's value list out of `inventory.sql` instead of
  comparing against a second hardcoded constant; (2) all four `InMemoryInventory` write
  methods now wrap `ValidationError → InventoryError` consistently via a shared `_build()`
  helper; (3) upsert semantics fixed from full-replace to **coalesce** in both
  `InMemoryInventory` and `PsycopgInventory` — an omitted (`None`) argument now preserves
  the existing row's value instead of resetting it to an empty default. Verified in both
  the fake and against a live Postgres 16 container.
- **`psycopg[binary]==3.3.4` pinned**, `sbom.json` regenerated, `hatch run audit` clean.
- **New tests**: `test_boundary.py` (sole-importer AST guard), `test_sql_parameterization.py`
  (asserts every `execute()` call outside `bootstrap()` is a static literal),
  `test_psycopg_integration.py` (skips cleanly with no DSN; full write-chain round-trip when
  a DSN is set). Full local gate green: lint → format → 819 passed / 4 skipped.
- **Functionally verified against a live Postgres 16 Docker container** (not part of the
  hermetic gate, not re-run in CI): bootstrap idempotency, full write-chain round-trip,
  FK-violation → `InventoryError`, and the coalesce-upsert semantics preserving an omitted
  list field. Torn down after.
- **`/critic-gate` ran partially**: `security-critic` failed on the account's **monthly
  spend limit** before producing findings — not run, not substituted, an open gap.
  `guard-adversary`'s subagent also failed to launch (transient), so its check was done
  **manually** instead: planted an `import psycopg` in `factory.py` → `test_boundary.py`
  went RED as expected; planted an f-string-built SQL query in `psycopg_impl.py` →
  `test_sql_parameterization.py` went RED as expected. Both reverted cleanly, full
  inventory suite back to green.
- **Opened [PR #162](https://github.com/glunk-works/loop-orchestrator/pull/162)** against
  `main` from `sprint/44-inventory-db` (commit `e26362a`).

## Next — post the T2 Architect Review (Opus/architect, FRESH session required)
This crosses the review boundary — **new window/session, not just `/clear`** (CLAUDE.md;
BL-6): `/model opus` → `/resume` → `/code-review` (high) on PR #162 → post with the
verbatim `**Opus/Architect HITL review (automated)**` header + fresh-session attestation
(`gh pr review --comment`, never `--approve`). Watch the BL-35 stale-red trap. **Give the
parameterized-SQL invariant and DSN-handling extra scrutiny** — that's exactly the angle
`security-critic` would have covered and didn't get to run this pass. The human may also
run `security-critic` separately once the spend limit resets/is raised.

**Next HITL Gate:** none open. The next Gate is the sprint-44 **completion** Gate (the
owner's merges of the T2/T3 PRs). PR #162 needs the `architect-review` CI check green
before it's mergeable.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **`tools/inventory_db` is now an enforced module boundary** — `psycopg_impl.py` is the
  sole `psycopg` importer, pinned by `tests/tools/inventory_db/test_boundary.py`,
  manually guard-adversary-confirmed RED under a planted violation (BL-15).
- **Parameterized SQL only** — every `execute()` call outside `bootstrap()` is a static
  literal (`test_sql_parameterization.py` enforces this structurally), confirmed RED under
  a planted f-string violation. Keep it that way through sprint 45's untrusted
  scanner-output ingestion.
- **`security-critic` did not run on the T2 diff** — account spend limit. If a future
  session has budget, consider running it against PR #162 even after merge, as a
  retroactive check, rather than letting the gap go unaddressed silently.
- **`gen_random_uuid()` confirmed working with no `pgcrypto` extension** — PostgreSQL 13+
  core builtin (P0-D8), verified against a live PG16 container.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first. **Never commit
  to `main`, merge, or force-push.** **Full local gate (lint→format→test) before push**
  (memory: #141).

## Pointers
- [PR #159](https://github.com/glunk-works/loop-orchestrator/pull/159) — sprint-44 Task 1, **merged** (`6bfc173`).
- [PR #162](https://github.com/glunk-works/loop-orchestrator/pull/162) — sprint-44 Task 2, **open**, awaiting `architect-review`.
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§4 persistence + schema, §8 roadmap, §9 decisions log P0-D1..D10). **Read first.**
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the sprint-44 plan (T1 done, T2 PR #162, T3, P0-D7..D10, PR structure, security invariants).
- [`docs/backlog.md`](../docs/backlog.md) — paused dev-loop items behind the bounty pivot.
