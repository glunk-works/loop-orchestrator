# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is over.** Phases 1–6 are complete: one path (LangGraph engine + MCP tool
dispatch + declarative `GeneratorNode` personas / PM `CriticGate` + Ralph Coder), four flags
deleted, classic recoverable at the **`pre-phase6-classic`** tag. `LOOP_ENGINE_ISOLATION`
survives as genuine runtime config.

**Next unit: sprint `32_state_artifacts_strip` — the deferred `State.artifacts` strip
(decision FD3). Status: `planning`. No sprint plan exists yet; it needs one.**

## Just done (Opus/Architect, 2026-07-12)
Sprint `27_phase6_flip_block` is **complete and archived** (`ddd28a8`, PR #37). Its final
cursor is snapshotted at `.ai/archive/27_phase6_flip_block-next-steps.md`.

## Next
**Plan FD3 (Opus).** Read `docs/migration_roadmap.md`'s decisions log for FD3 before writing
the plan. The one thing to carry in:

> **FD3 is a behavior-changing refactor, NOT a deletion.** Task 5 was originally specced as a
> deletion on the premise that removing `run_loop` would make the engine the sole `artifacts`
> reader. That premise was **false** — the readers were always the **personas and gates**. Any
> plan that treats this as "delete a `State` field" will be wrong for the same reason.

It touches `State`, so it must keep `schema_version` accurate (bump + extend
`migrate_state_payload` for a breaking shape change) and keep `extra="forbid"` intact.

## Standing obligations (neither is a migration task; both are real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks that have **never been run**: §1
  (caching + USD budget smoke), §5 (`github_server` live launch), §6 (trigger surface live
  webhook), §7 (maintenance flow live clone→PR), §8 (bootstrap flow live create→push). They
  need a real Anthropic key, a real authenticated `gh`, or a daemon-bearing host that can bind
  a port. **A green `hatch run test` says nothing about any of them.** Sprint 27's Task 9
  pruned this file rather than deleting it precisely so this record survives — **do not
  "finish the job" by deleting it.** Its section numbers are intentionally non-contiguous
  (BL-3 cites §1; archived sprint plans cite §3/§6/§9).
- **FD3** — the `artifacts` strip (above).

## HITL gate
None open.

## Pointers
- `docs/migration_roadmap.md` — Phase 6 row (🟩 Done, V1–V3 results folded in), the
  NEXT ACTION line, and the decisions log (**FD3**).
- `sprints/27_phase6_flip_block/sprint_plan.md` — the closed sprint. Task 9's entry records
  why its premise was false; worth reading before planning FD3, which failed the same way.
- `docs/backlog.md` — **BL-8** (stop using process CWD as an isolation mechanism) and **BL-9**
  (retire the implicit-CWD destination from the issue path's remaining surfaces — item 1,
  `resume --from-issue` still guessing from CWD and only echoing the guess, is the one worth
  doing).
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.
- `.github/workflows/hitl-review.yml` — the gate: binds a review to an exact head SHA, exempts
  PRs with no `^src/` file.

## Live external state — needs cleanup (HUMAN ACTION)
- **`glunk-works/loop-engine-v3-scratch`** (private) is still live, holding issues **#1–#6**.
  Delete it in the GitHub UI, then remove it from the fine-grained PAT's repo list (the PAT has
  no `Administration` permission by design, so it cannot delete repos — that stays a human
  checkpoint on the one irreversible action; it also carries an unexpected `Contents: Write`
  worth trimming while you're there).

## Working tree
- `main` ← `feat/mcp-langgraph-migration` is the integration branch; sprint work lands via
  `sprint/NN-slug` PRs based on it. Sprint branches squash-merge, so only the tip ships.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is
  tracked**.
