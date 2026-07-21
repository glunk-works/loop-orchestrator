# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PR) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 46 T1 (skeleton + `State` 5→6 bump). The fresh-session
Architect Review is POSTED on PR #173 with a CHANGES-REQUESTED verdict (owner-approved
the change list). `sprint_status: implementing`, assigned Sonnet/coder.**
[PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173) (branch
`sprint/46-bounty-loop-skeleton`, HEAD `46ddc9e`) is open against `main`. One small,
**non-core** fix is required before merge; the core re-entry wiring stays deferred to
S47/S48 (that deferral was explicitly affirmed, not the blocker).

## Just done (2026-07-21, Opus/architect — review session)
- Posted the fresh-session Architect Review on PR #173 via `gh pr review --comment`
  (verbatim frozen header + attestation; matches the gate filter on HEAD `46ddc9e`).
- **Verdict: changes requested — docs+test honesty only, no `core/` churn.** Verified the
  HIGH finding directly at all three layers (`core/engine.py::reentry_index` iterates only
  `("architecture","plan")`; `Question.impact` can't hold `scope`/`surface`;
  `VALID_IMPACTS` filters them). The blocker is the *false claim*, not the inert map:
  loop.py's docstring says `impact_reentry` is "exercised from day one" (it is not), the
  inline comment describes re-entry that can't fire, and
  `test_bounty_loop_blast_radius_reentry_targets` is a tautological shape check named as
  behavioral coverage (sprint-27 / BL-32 "green for the wrong reason").
- Affirmed as solid (do not touch): schema v5→v6 migration, `BountyRunState`, the
  fail-closed `bounty is None` guard, the `ArtifactProducer` producer-swap seam.
- Gate note: `architect-review` shows a stale-red run + a newer green run on `46ddc9e`;
  `mergeStateStatus: BLOCKED`. Left un-cleared **on purpose** — a follow-up commit is
  required anyway, so this SHA is moot and must not read as merge-ready.

## Next — land the fix (Sonnet/coder)
Bounded, mechanical, `architect-review`-exempt work is NOT what this is (it touches a test
+ src docstrings), so it re-arms the gate. On `sprint/46-bounty-loop-skeleton`:
1. **Keep** `impact_reentry={"scope":0,"surface":1}` (honors P1-D3). Correct loop.py's
   docstring + inline comment to state honestly that the map is planted ahead of core
   support, that scope/surface re-entry does **not** fire today, and name the three core
   edits S47/S48 must make (`Question.impact` Literal, `reentry_index()`'s tuple,
   `VALID_IMPACTS`). One honest sentence that resolvers/escalation are likewise not yet
   live closes the same trap (lower-severity note).
2. De-mislead `test_bounty_loop_blast_radius_reentry_targets` — rename to signal it is a
   forward-declaration *shape* assertion, or add an explicit inert-until-core comment.
3. Run the full green gate (`hatch run lint && format && test-parallel`), push.
Then `/handoff` → new session → Opus re-review of the NEW HEAD (the fresh-session gate
re-fails until re-posted). If approved: T1 done pending merge; **T2** (docs: CLAUDE.md
boundary bullet + `docs/bounty_loop_architecture.md` §8/§9 P1-D1..D7) is next, Sonnet-suitable.

**HITL Gate: NONE OPEN.** Architect Review ruled; owner approved the change list. Next
gate: the S46 T1 fresh-session `architect-review` re-post on the new HEAD after the fix.

## Gotchas worth remembering
- **The fix keeps the map and corrects the claim — it is NOT the core re-entry wiring.**
  Do not expand this into `core/state.py`/`core/engine.py`/`resolution.py` (that is
  S47/S48; the exact churn P1-D3 avoids).
- **P1-D3's producer-swap seam holds; the re-entry map does not.** Separate claims — don't
  conflate. The schema migration and the `bounty is None` guard are genuinely correct.
- **The sprint-44 live Postgres smoke is still OWED** (`DEFERRED_VERIFICATION.md` §10) —
  discharges in S47, not here.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes.** **Never commit to `main`, merge, or force-push.**

## Pointers
- [PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173) — S46 T1, branch `sprint/46-bounty-loop-skeleton`, HEAD `46ddc9e`.
- [Architect Review](https://github.com/glunk-works/loop-orchestrator/pull/173) — this session's changes-requested review (fix list above).
- [critic-gate findings](https://github.com/glunk-works/loop-orchestrator/pull/173#issuecomment-5029833958) — prior architect + security-critic detail.
- [`sprints/46_bounty_loop_skeleton/sprint_plan.md`](../sprints/46_bounty_loop_skeleton/sprint_plan.md) — active plan (T1 = this PR, T2 = docs).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — bounty loop reference-of-record; §9 P1-D1..D7 write-up owed (T2).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = OWED sprint-44 live Postgres smoke; discharge in S47.
