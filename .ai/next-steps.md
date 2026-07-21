# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 46. T1 (skeleton + `State` 5→6 bump) is MERGED to `main`
([PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173), squash commit
`91167be`). Next is T2 (docs). `sprint_status: implementing`, assigned Sonnet/coder.**
The fresh-session Architect Review was posted on HEAD `7cdf15b` with an **APPROVE**
verdict and all eight required checks went green; the owner merged T1 immediately after.
Sprint 46 is **not** complete — T2 remains — so this is a handoff to T2, not an archive.

## Just done (2026-07-21, Opus/architect — re-review session)
- Re-reviewed PR #173 at the review-fixed HEAD `7cdf15b` (the earlier `46ddc9e` review did
  not carry forward). Verified the HIGH finding is closed at all three layers directly:
  `Question.impact` (`core/state.py:47`) has no `scope`/`surface` member; `reentry_index()`
  (`core/engine.py:199-202`) iterates only `("architecture","plan")` and falls through to
  `stage_index`; `VALID_IMPACTS` (`personas/resolution.py:12`) filters both out — the map
  is triple-inert exactly as the corrected docstring now states.
- Posted the fresh-session Architect Review via `gh pr review --comment` (verbatim frozen
  header + attestation). Verdict **APPROVE**; one sub-threshold note (SurfaceMap's
  `state.bounty` narrowing) left for S48, not this PR.
- Cleared the **BL-35 stale-red trap**: posting the review left the old
  `pull_request`-triggered `architect-review` FAILURE on the same SHA (`BLOCKED` + rollup
  FAILURE). `gh run rerun` on the OLD run cleared it → `mergeState: CLEAN`.
- Owner merged **#173** (T1), plus cursor-syncs **#174** and **#175**. This PR (**#176**)
  was left conflicting on `next-steps.md` by #175's merge; resolved by merging `main` in
  and refreshing the cursor to this post-merge state.

## Next — T2 docs (Sonnet/coder)
Bounded, docs-only, `architect-review`-exempt work on a fresh `sprint/46-...docs` branch
cut from the now-updated `main`:
1. **CLAUDE.md** — add the enforced-boundary bullet for `loops/bounty/` + `personas/bounty/`
   (the walking skeleton: stub personas behind the `ArtifactProducer` seam, `State` v6
   `bounty` namespace, the inert-until-core `impact_reentry` map).
2. **`docs/bounty_loop_architecture.md`** — write up §8/§9 decisions **P1-D1..D7** (still
   owed; the reference-of-record currently lacks them).
3. Run the full green gate, push, open a docs-only PR based on `main`.
Then `/handoff`. After T2 merges, sprint 46 is complete → `/archive-sprint`.

**HITL Gate: NONE OPEN.** T1 shipped. No gate is expected on T2 (docs-only, exempt);
the next real gate is whenever a `src/`-touching sprint (S47) next opens a PR.

## Gotchas worth remembering
- **T1 kept the `impact_reentry` map and corrected the claim — it is NOT the core re-entry
  wiring.** Making it live is three core edits (`Question.impact` Literal,
  `reentry_index()`'s tuple, `VALID_IMPACTS`), deferred to S47/S48 by P1-D3. Don't
  conflate "map planted" with "re-entry live"; resolvers/escalation for this loop are also
  not yet live.
- **P1-D3's producer-swap seam (`ArtifactProducer`) holds.** S47/S48 swap only the injected
  producer; the persona shells, loop wiring, and gates do not churn.
- **The sprint-44 live Postgres smoke is still OWED** (`DEFERRED_VERIFICATION.md` §10) —
  discharges in S47, not here.
- **Docs-sync PRs stack and collide on `next-steps.md`** — #174/#175/#176 all rewrote the
  same sections; #176 conflicted the moment #175 merged. Merge cursor-syncs promptly, or
  resolve by merging `main` in and refreshing (never force-push).
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes.** **Never commit to `main`, merge, or force-push.**

## Pointers
- [PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173) — S46 T1 (MERGED, `91167be`): `State` v6 + `loops/bounty/` + `personas/bounty/`.
- [`sprints/46_bounty_loop_skeleton/sprint_plan.md`](../sprints/46_bounty_loop_skeleton/sprint_plan.md) — active plan (T1 done, T2 = docs).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — bounty loop reference-of-record; §8/§9 P1-D1..D7 write-up owed (T2).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = OWED sprint-44 live Postgres smoke; discharge in S47.
