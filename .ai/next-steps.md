# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1 (Recon + Surface-Mapping), sprint 46 (skeleton + `State` 5→6 bump).
`sprint_status: implementing`, assigned Sonnet/coder.** The Phase-1 planning pass is
**done and owner-approved**: Phase 1 decomposes into **3 sprints** (P1-D1) — **46** (this
one: bounty loop skeleton + the schema bump) → 47 (recon data path) → 48 (Surface-Mapping).
The S46 `sprint_plan.md` is written, critically reviewed, and its ambiguities folded in. The
next unit is **implementing S46 T1** (the `src/` PR).

## Just done (2026-07-21) — Phase 1 planning pass (Opus/architect)
- **Decomposed Phase 1 into 3 sprints** and wrote the first plan,
  [`sprints/46_bounty_loop_skeleton/sprint_plan.md`](../sprints/46_bounty_loop_skeleton/sprint_plan.md),
  via 7 owner-confirmed HITL micro-gates → **P1-D1..D7** (recorded in the plan; to land in
  `docs/bounty_loop_architecture.md` §9 in S46 T2).
- **Locked decisions:** nested `bounty: BountyRunState | None` for the 5→6 bump (P1-D2);
  walking-skeleton both stages behind an injected-producer seam (P1-D3); S47 hermetic + one
  V-run discharging the owed §10 PG smoke (P1-D4); `boto3` egress + `gh` `workflow_dispatch`,
  5 subprocess surfaces stay 5 (P1-D5); scope_validator at both boundaries — input raises,
  discovered-asset output filters (P1-D6); S46 library-only, no CLI selector (P1-D7).
- **Critic review of the plan** (this session): found + folded in 9 coder-facing ambiguities
  — gate `parse_json` shapes locked (`asset_inventory`="list", `surface_map`="object"), the
  `ArtifactProducer` seam signature (`__call__(bounty) -> str`), stub-body pass-first-try
  constraints, the `run_graph_loop` test harness pointer, `BountyRunState` mutable-not-frozen,
  and more. Owner approved.

## Next — implement S46 T1 (Sonnet/coder)
Build **S46 Task 1** (one `src/` PR) exactly per the plan:
- `core/state.py`: `BountyRunState` (`extra="forbid"`, **mutable**; `target_id: str`) +
  `bounty: BountyRunState | None = None`, bump `CURRENT_SCHEMA_VERSION` 5→6, extend
  `migrate_state_payload` (`version in (1,2,3,4,5)` → 6).
- `loops/bounty/loop.py`: `build_bounty_loop()` + `BOUNTY_LOOP`, two stages with
  `ArtifactGate("asset_inventory", parse_json="list")` / `("surface_map", parse_json="object")`,
  `resolvers=[recon]` on Mapping, `impact_reentry={"scope":0,"surface":1}`.
- `personas/bounty/`: `ArtifactProducer` protocol + 2 fixture stubs in `producers.py`;
  `ReconPersona`/`SurfaceMapPersona` shells (own the None-raise + `model_copy` write).
- Full hermetic suite (migrate round-trip, loop structure + re-entry, `run_graph_loop`
  end-to-end **COMPLETED**, boundary asserts). No new dep, no `.sql`, no new subprocess surface.
- **First `State`-touching PR of the bounty initiative ⇒ fresh-session `architect-review`.**
  Run `/critic-gate` (architect + security-critic indicated) before `/handoff`.
- Then **T2** (docs, exempt): CLAUDE.md boundary bullet + schema-v6 note; roadmap §8 status +
  §9 P1-D1..D7.

**HITL Gate: NONE OPEN.** Phase-1 planning Gate passed (plan approved 2026-07-21). Next gate:
the S46 T1 fresh-session `architect-review` on its PR.

## Gotchas worth remembering
- **First `State` change of the whole bounty initiative** — schema bump + migrate branch +
  `extra="forbid"` intact ⇒ fresh-session `architect-review` on the T1 PR (`/handoff` → new
  session → `/resume` → `/code-review` → post the verbatim header). Watch the **BL-35
  stale-red** trap (BLOCKED + rollup FAILURE ⇒ `gh run rerun` the OLD run).
- **The stub artifact bodies must pass their gate on the first attempt** — valid JSON of the
  gate `parse_json` type (`[]` / `{}`); a REVISE re-runs the identical stub → exhaustion
  escalation → the "green" run silently pauses. See the plan's stub-body constraints.
- **The injected-producer seam is the load-bearing bet (P1-D3)** — S47 must land the real
  recon body by swapping *one* `ArtifactProducer`, changing neither loop wiring nor persona
  shell. If S47 has to touch either, the skeleton failed.
- **`BountyRunState` is mutable, NOT frozen** (unlike `ScopeRules`) — later stages add
  `asset_ids`/`finding_ids` via `model_copy`.
- **The sprint-44 live Postgres smoke is still OWED** (`DEFERRED_VERIFICATION.md` §10) —
  discharges in **S47** (first `inventory_db` consumer + real PG), not S46. Don't stamp it.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first. **Never commit
  to `main`, merge, or force-push.** **Full local gate (lint→format→test) before push.**

## Pointers
- [`sprints/46_bounty_loop_skeleton/sprint_plan.md`](../sprints/46_bounty_loop_skeleton/sprint_plan.md) — the active plan (T1 = the `src/` PR, T2 = docs).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — bounty loop reference-of-record (§3 stages, §4 persistence, §5 scope, §7 compute topology, §8 roadmap [Phase 0 complete], §9 decisions [P1-D1..D7 land in S46 T2], §10 ingestion seam).
- [`sprints/45_scope_validator_ingestion/sprint_plan.md`](../sprints/45_scope_validator_ingestion/sprint_plan.md) / [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — precedent plans + the Phase-0 primitives S47 consumes.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = the OWED sprint-44 live Postgres smoke; discharge in S47.
