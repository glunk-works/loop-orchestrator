# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 47 (recon data path): PLANNING, not yet started.**
`sprint_status: planning`, assigned Opus/architect. No `sprints/47_bounty_recon_data_path/`
directory exists yet — this session's job is the planning pass (one question at a time,
HITL micro-gates), producing `sprint_plan.md`, before any Sonnet/coder implementation.

## Just done (2026-07-21) — sprint 46 archived
Sprint 46 (bounty loop skeleton + `State` v5→v6 bump + Phase-1 decisions write-up) is
**complete and archived**:
- **T1** — [PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173): the
  skeleton (`loops/bounty/`, `personas/bounty/`, `BountyRunState`, schema v6). Fresh-session
  Architect Review APPROVE on the review-fixed HEAD `7cdf15b`; all 8 checks green (BL-35
  stale-red cleared via `gh run rerun`); merged.
- **T2** — [PR #177](https://github.com/glunk-works/loop-orchestrator/pull/177): CLAUDE.md's
  `loops/bounty/`/`personas/bounty/` boundary bullet + `docs/bounty_loop_architecture.md`
  §9's P1-D1..D7 write-up. Docs-only, `architect-review`-exempt; merged.
- **Fix** — [PR #178](https://github.com/glunk-works/loop-orchestrator/pull/178): flipped
  §8's roadmap row from "in progress" to complete, with the hermetic-vs-live distinction
  stated explicitly (no live surface yet; the sprint-44 live PG smoke stays deferred to
  S47). Merged — this was the last `/archive-sprint` precondition.
- Prior sprint's cursor snapshotted to `.ai/archive/46_bounty_loop_skeleton-next-steps.md`.

## Next — plan sprint 47 (Opus/architect)
Recon data path (P1-D1): `workflow_dispatch` seam on `bounty-infra` + a scope-validated
recon MCP tool + IDP parser → `inventory_db` (its first consumer). This is the sprint that
mounts `tools/scope_validator`/`tools/ingest` at a live boundary for the first time
(P0-D11) and discharges the OWED sprint-44 live Postgres smoke
(`sprints/DEFERRED_VERIFICATION.md` §10) via one authorized `live-verify` V-run (P1-D4).

**Three decisions are already pre-recorded** in `docs/bounty_loop_architecture.md` §9 —
confirm/refine them in the planning pass, don't re-derive from zero:
- **P1-D4** — S47 built fully hermetic (a `ReconDispatcher` protocol + `InMemoryInventory`
  fake); live `workflow_dispatch`→S3→real-Postgres discharges together in **one** authorized
  V-run (also clears §10).
- **P1-D5** — S3 fetch is a new pinned `boto3` **egress**, not a subprocess surface;
  `workflow_dispatch` rides `gh` as a **third** consumer of the already-sanctioned surface
  (not a sixth). `sbom`/`dependency-audit` deltas expected (like sprint 44's `psycopg`).
- **P1-D6** — scope enforcement mounts at **both** boundaries with distinct semantics:
  input `validate_target` **raises** `ScopeViolation` (caller-asserted target); output
  discovered-asset filtering **drops silently** (bulk recon naturally surfaces out-of-scope
  hosts — raising per host would halt a normal run).

Use `sprints/46_bounty_loop_skeleton/sprint_plan.md` as the structural template (Sprint
Goal, Out of scope, inherited-decisions context, sprint-specifics, Security Considerations,
Risks & Blockers). Write `sprints/47_bounty_recon_data_path/sprint_plan.md`, get owner
sign-off via HITL micro-gates, then hand off to Sonnet/coder for T1.

**HITL Gate: OPEN (implicitly) — this planning pass IS the gate.** The dialogue with the
owner, one question at a time, is the work; do not proceed to implementation or write code
in this session. `/resume` on this cursor always waits (never auto-starts) while
`sprint_status: planning`.

## Gotchas worth remembering
- **Don't re-litigate P1-D1..D7** — locked by the sprint-46 planning pass
  (2026-07-21, owner-confirmed via HITL micro-gates 1–7). P1-D4/D5/D6 above are the
  S47-scoped ones; this pass refines their *execution* detail, not whether they hold.
- **`impact_reentry={"scope":0,"surface":1}` is still inert.** Making it live needs three
  core edits (`Question.impact` Literal, `reentry_index()`'s tuple, `VALID_IMPACTS`) —
  S47/S48 own this, not the recon-data-path work itself unless the plan says otherwise.
- **The sprint-44 live Postgres smoke discharges in S47's V-run, not before.** Do not stamp
  `DEFERRED_VERIFICATION.md` §10 verified until that V-run actually runs.
- **This is the first `src/`-touching sprint since 46** — its T1 PR will need a fresh-session
  Architect Review (the CI gate). Plan for it, don't skip it.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes.** **Never commit to `main`, merge, or force-push.**

## Pointers
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — reference-of-record; §8 (roadmap), §9 (decisions log, P1-D1..D7).
- [`sprints/46_bounty_loop_skeleton/sprint_plan.md`](../sprints/46_bounty_loop_skeleton/sprint_plan.md) — structural template for the S47 plan.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = OWED sprint-44 live Postgres smoke; discharge in S47's V-run.
- `.ai/archive/46_bounty_loop_skeleton-next-steps.md` — sprint 46's final cursor (archived).
