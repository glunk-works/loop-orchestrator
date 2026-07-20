# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 44 (`tools/inventory_db` + the §4 Postgres schema).
`sprint_status: awaiting_architect_review`, assigned Opus/architect.** Task 1 (hermetic
core) merged (`6bfc173`, PR [#159](https://github.com/glunk-works/loop-orchestrator/pull/159))
and Task 2 (the real psycopg3 driver) merged (`32c000a`, PR
[#162](https://github.com/glunk-works/loop-orchestrator/pull/162)). **The remainder (F1 fix
+ T3 docs) is coded, gated, and open as
[PR #165](https://github.com/glunk-works/loop-orchestrator/pull/165)** against `main`,
awaiting the fresh-session Opus `architect-review`. The second loop (`loops/bounty/`) is
the active initiative; the dev loop (`loops/default`) stays paused.

## Just done (2026-07-20) — sprint-44 remainder implementation (Sonnet/coder)
- **Fixed F1** — `PsycopgInventory.upsert_asset`/`upsert_endpoint`
  (`src/loop_orchestrator/tools/inventory_db/psycopg_impl.py`) now wrap the
  `raw_scan_data`/`tech_stack` dict binds in `psycopg.types.json.Jsonb(...)` in both the
  INSERT and UPDATE (coalesce) paths; a bare `None` stays `None` (never `Jsonb(None)`,
  which would write JSON `null` instead of SQL `NULL`).
- **Extended `test_full_write_chain_round_trips`** to pass non-empty
  `raw_scan_data`/`tech_stack` dicts and read both JSONB columns back directly to assert
  the round-trip — this test previously left both fields `None`, which is why F1 shipped
  unnoticed.
- **T3 docs** — added the `tools/inventory_db` sole-psycopg-importer + parameterized-SQL
  boundary bullet to `CLAUDE.md`; advanced §8 (roadmap status) / §9 (decisions log, new F1
  bullet) in `docs/bounty_loop_architecture.md`.
- **Full local gate green**: lint → format → 819 passed / 4 skipped (the live-Postgres
  integration suite skips cleanly without a DSN, by design).
- **Ran `/critic-gate`** on the diff before handoff (security-critic + architect, both
  read-only, in parallel): **security-critic found nothing reachable** — the `Jsonb(...)`
  fix keeps all caller data on the bound-parameter side of the SQL sink, no unwrapped-rebind
  path. **architect found one low-severity docs-wording issue** — the new CLAUDE.md bullet
  claimed *every* `cur.execute()` call is a static literal, missing the documented
  `bootstrap()` exception — fixed in commit `688b628`. Neither critic pass is a substitute
  for the CI `architect-review` gate; that review still needs a genuinely fresh session.
- **Opened [PR #165](https://github.com/glunk-works/loop-orchestrator/pull/165)** against
  `main` (branch `sprint/44-inventory-remainder`, head `688b628`).

## Next — fresh-session Opus Architect Review on PR #165
In a **new session** (not just `/model` + `/clear` — the fresh-session attestation is an
integrity property, not context hygiene):
1. `/model opus` → `/resume` → `/code-review` the diff (PR #165 / `sprint/44-inventory-remainder`
   vs `main`).
2. Post the review with `gh pr review --comment` (**never `--approve`**) against PR #165's
   current head commit. The body **must open with the verbatim two-line header +
   attestation block** from `.ai/context/workflow.md` — paste it, don't paraphrase, or the
   `architect-review` check won't go green.
3. If clean, the PR is ready for the owner's merge (the sprint-44 **completion** Gate). If
   the review finds something, route it back to a Sonnet/coder session per the usual
   resolver ladder.

**Next HITL Gate:** none open. The next Gate is the sprint-44 **completion** Gate (the
owner's merge of PR #165, which needs the `architect-review` CI check green first).

## Gotchas worth remembering
- **F1 is fixed in PR #165, not yet on `main`** — see `memory/inventory-jsonb-dict-bug.md`
  (updated). `main` still carries the live defect until #165 merges.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **`tools/inventory_db` is an enforced boundary** — `psycopg_impl.py` is the sole `psycopg`
  importer (`test_boundary.py`); every value-bearing `execute()` outside `bootstrap()` is a
  static literal (`test_sql_parameterization.py`). Both manually guard-adversary-confirmed
  RED under a planted violation (BL-15).
- **`gen_random_uuid()` needs no `pgcrypto`** — PG13+ core builtin (P0-D8), live-verified.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first. **Never commit
  to `main`, merge, or force-push.** **Full local gate before push** (memory: #141).
- **F2–F5 remain open Phase-1 notes** (upsert TOCTOU race, held conn never closed, single
  conn not thread-safe, SQL-param guard narrower than its docstring) — not this sprint's
  scope.

## Pointers
- [PR #159](https://github.com/glunk-works/loop-orchestrator/pull/159) — sprint-44 T1, **merged** (`6bfc173`).
- [PR #162](https://github.com/glunk-works/loop-orchestrator/pull/162) — sprint-44 T2, **merged** (`32c000a`).
- [PR #165](https://github.com/glunk-works/loop-orchestrator/pull/165) — sprint-44 remainder (F1 fix + T3 docs), **open**, awaiting architect-review.
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§4 persistence + schema, §8 roadmap, §9 decisions P0-D1..D10). **Read first.**
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the sprint-44 plan (T1/T2 merged, T3 in PR #165, P0-D7..D10, PR structure, security invariants).
- [`docs/backlog.md`](../docs/backlog.md) — paused dev-loop items behind the bounty pivot.
