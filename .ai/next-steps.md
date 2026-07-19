# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 44 (`tools/inventory_db` + the §4 Postgres schema).
`sprint_status: planning`, assigned Opus/architect.** Sprint 43 (BL-5 model routing) is
complete and archived. The second loop (`loops/bounty/`) is the active initiative; the dev
loop (`loops/default`) stays paused.

The sprint-44 plan does **not exist yet** — the next action is the planning pass, then
writing `sprints/44_inventory_db/sprint_plan.md`.

## Just done (2026-07-19)
- **Sprint 43 (BL-5 model routing) — COMPLETE and archived.** All four PRs merged:
  T1 pricing RATES += Opus 4.8 / Haiku 4.5 (#149), T2 one canonical `DEFAULT_MODEL`
  in `tools/llm/pricing.py` (#152), T3 resolver `max_tokens` 2048→4096 (#154), T4 docs
  (#156, `main` @ `720e8aa`). Sprint-43 cursor snapshotted to
  `.ai/archive/43_bl5_model_routing-next-steps.md`.

## Next — plan sprint 44 (Opus/architect)
Run the planning pass for **`tools/inventory_db` + the §4 Postgres schema** (the
`targets`/`assets`/`endpoints`/`findings` tables + run linkage), the sole
Postgres-connection-owning module. One question at a time, HITL micro-gates, then write
`sprints/44_inventory_db/sprint_plan.md`.

**Pre-locked decisions — do NOT re-litigate** (recorded in
`sprints/43_bl5_model_routing/sprint_plan.md`, ratified 2026-07-19):
- **P0-D4** — Postgres tested **hermetically** against a fake/in-memory impl (**no Docker
  in CI**). The real **psycopg3 (sync)** + DDL path is a marked integration test that
  **skips when no DSN is set**, discharged via the `live-verify`/deferred-verification
  posture. DSN via env var `LOOP_ORCHESTRATOR_INVENTORY_DSN`, **not keyring**.
- **P0-D5** — the §4 schema ships as an idempotent versioned `.sql` applied via
  `CREATE ... IF NOT EXISTS` in `inventory_db`'s bootstrap — **no Alembic** until the first
  schema *evolution*.
- **P0-D2** — `schema_version` 5→6 stays deferred to **Phase 1** (ships with the first
  bounty `State` field, not with pure infra).

**Next HITL Gate:** none open now; the sprint-44 plan's micro-gates open during the
planning dialogue.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **`tools/inventory_db` will be a new enforced module boundary** — the *only* module that
  opens a Postgres connection, mirroring how `tools/llm/client.py` is the sole `keyring`
  importer. Plan its static-test boundary alongside the schema.
- **Any `src/`-touching PR needs a fresh-session `architect-review`** — `/handoff` → new
  session → `/model opus` → `/resume` → `/code-review` → post the verbatim-header review.
  Watch the **BL-35 stale-red** trap (BLOCKED + rollup FAILURE ⇒ `gh run rerun` the OLD run).
- **PR title ≤72 bytes** — `wc -c` first. **Never commit to `main`, merge, or force-push.**
- Bounty invariants are non-negotiable (sprint 45): scope validation is structural code,
  never the LLM's job; active exploitation gates through the escalation ladder.

## Pointers
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§8 roadmap incl. the P0-D1 three-sprint decomposition, §9 decisions log P0-D1..D6). **Read first.**
- `sprints/44_inventory_db/sprint_plan.md` — **to be written** by the sprint-44 planning pass.
- [`sprints/43_bl5_model_routing/sprint_plan.md`](../sprints/43_bl5_model_routing/sprint_plan.md) — the prior sprint; carries the recorded P0-D4/P0-D5/P0-D6 decisions for sprints 44/45.
- [`docs/backlog.md`](../docs/backlog.md) — paused dev-loop items behind the bounty pivot.
