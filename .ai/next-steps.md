# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 45 (scope validator §5 + ingestion-sanitization seam §10).
`sprint_status: planning`, assigned Opus/architect.** Sprint 44 (`tools/inventory_db` +
the §4 Postgres schema) is **complete and archived** — all three PRs merged (T1
[#159](https://github.com/glunk-works/loop-orchestrator/pull/159), T2
[#162](https://github.com/glunk-works/loop-orchestrator/pull/162), remainder F1 + T3
[#165](https://github.com/glunk-works/loop-orchestrator/pull/165)) at `main` `29df5dd`.
Sprint 45 is Phase 0's **final** sprint; after it, Phase 1 (Recon) begins. The second loop
(`loops/bounty/`) is the active initiative; the dev loop (`loops/default`) stays paused.

## Just done (2026-07-20) — sprint-44 closed out
- **Posted the fresh-session Opus Architect Review on PR #165** (F1 JSONB fix + T3 docs) —
  APPROVE, no new findings; verified the `Jsonb(...)` wrap covers both JSONB columns in all
  four INSERT/UPDATE sites, the coalesce×wrap cases, and the regression test. Cleared the
  **BL-35 stale-red** (`gh run rerun` the old `pull_request` `architect-review` run); all 8
  required checks green, merge state CLEAN.
- **Owner merged PR #165** → sprint-44 **completion Gate passed**.
- **`/archive-sprint`**: snapshotted the sprint-44 cursor to `.ai/archive/`, flipped
  `bounty_loop_architecture.md` §8 to *sprint 44 complete — hermetically verified; live
  Postgres smoke deferred*, and **added `DEFERRED_VERIFICATION.md` §10** (the OWED live
  psycopg3 round-trip — never run against a real PG, per the owner). Advanced the cursor to
  sprint 45.

## Next — plan sprint 45 (Opus/architect)
There is **no `sprints/45_scope_validator_ingestion/sprint_plan.md` yet** — the planning
pass writes it (one question at a time, HITL Gates). Scope, from
`bounty_loop_architecture.md`:
1. **Scope validator (§5)** — a structural in/out-of-scope + banned-action check reading
   sprint-44's `targets` rules-of-engagement (`in_scope_regex`/`out_of_scope_regex`/
   `banned_actions`). The concrete fix for `bounty-infra#7` (no structural scope check).
2. **Ingestion-sanitization seam (§10; P0-D6)** — sanitize scanner/target-derived output
   before it reaches the triage LLM. The concrete fix for `bounty-infra#13` (target-derived
   fields fed straight into the model).
Both built once here and shared into the bounty loop.

**Next HITL Gate:** none open. The next Gate is the sprint-45 **planning** Gate (HITL
approval of the plan before any implementation).

## Gotchas worth remembering
- **`schema_version` 5→6 stays DEFERRED to Phase 1** (P0-D2) — sprint 45 is still pure
  non-`State` infra unless the planning pass surfaces a `State` field.
- **`DEFERRED_VERIFICATION.md` §10 is owed** — the sprint-44 live Postgres round-trip
  (real driver: bootstrap DDL + F1 JSONB round-trip + coalesce). Discharge in Phase 1 when
  the first inventory consumer + a real PG exist. Don't let it drift.
- **F2–F5 remain open Phase-1 notes** (upsert TOCTOU race, held conn never closed, single
  conn not thread-safe, SQL-param guard narrower than its docstring) — `bounty_loop_architecture.md`
  §9, not sprint 45's scope.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first. **Never commit
  to `main`, merge, or force-push.** **Full local gate before push** (memory: #141).
- **`src/`-touching PRs need a FRESH-session architect-review** — watch the BL-35 stale-red
  trap (`architect-review` fires on both `pull_request` and `pull_request_review`; BLOCKED +
  rollup FAILURE ⇒ `gh run rerun` the OLD run).

## Pointers
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§5 scope validator, §10 ingestion seam, §8 roadmap, §9 decisions P0-D1..D10). **Read first for sprint-45 planning.**
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the just-completed sprint's plan (all tasks merged) — the template/precedent for the sprint-45 plan.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = the owed sprint-44 live Postgres smoke.
- [`docs/backlog.md`](../docs/backlog.md) — paused dev-loop items behind the bounty pivot.
- [PR #165](https://github.com/glunk-works/loop-orchestrator/pull/165) — sprint-44 remainder (F1 + T3 docs), **merged** (`29df5dd`).
