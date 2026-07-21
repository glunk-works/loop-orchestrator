# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 46 T1 (skeleton + `State` 5→6 bump). The S46 T1
review-fix is pushed to PR #173 as `7cdf15b`. `sprint_status: awaiting_architect_review`,
assigned Opus/architect.**
[PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173) (branch
`sprint/46-bounty-loop-skeleton`, HEAD `7cdf15b`) is open against `main`. A prior Opus
session posted a fresh-session Architect Review on `46ddc9e` (changes requested,
docs+test honesty only, owner approved the fix list) — see
[PR #175](https://github.com/glunk-works/loop-orchestrator/pull/175) (still open,
unmerged) for that cursor sync. That review does **not** carry forward to the new commit
`7cdf15b` — a fresh review is needed before merge.

## Just done (2026-07-21, Sonnet/coder — unattended per pre-approval)
- Landed the S46 T1 review-fix on `sprint/46-bounty-loop-skeleton` (commit `7cdf15b`),
  exactly as scoped by the prior Architect Review's own change list — docs+test honesty
  only, **no `core/` churn**.
- `loops/bounty/loop.py`: corrected the docstring's false "`impact_reentry` is exercised
  from day one" claim and the inline comment describing re-entry as if it fires. Now
  states honestly that the map is planted ahead of core support, that `"scope"`/`"surface"`
  re-entry does not fire today, and names the three core edits S47/S48 owe
  (`Question.impact` Literal, `reentry_index()`'s `("architecture","plan")` tuple,
  `personas/resolution.py`'s `VALID_IMPACTS`). Added one honest sentence that the
  resolvers/escalation path is likewise not yet live.
- `tests/loops/test_bounty.py`: renamed `test_bounty_loop_blast_radius_reentry_targets` →
  `test_bounty_loop_blast_radius_reentry_targets_are_forward_declared` with a docstring
  making clear it's a shape assertion, not behavioral re-entry coverage.
- Verified via diff that `core/state.py`, `core/engine.py`, `personas/resolution.py` are
  untouched. Full local gate green: lint clean, format clean, 879 passed / 4 skipped.
- **No `/critic-gate` pass ran** on this diff — skipped deliberately, not silently: the
  change is docs/comment/test-rename only, fully pre-specified and pre-approved by the
  prior review's own fix list. Noted so the next session can request one before posting
  review if it disagrees with that call.

## Next — fresh-session Architect Review (Opus)
This is a **review-gate crossing — needs a genuinely new session**, not `/clear` in place:
1. New session → `/model opus` → `/resume`.
2. `/code-review` PR #173 at HEAD `7cdf15b` — verify the two fix changes actually close
   the prior HIGH finding (the docstring/comment now read honestly; the renamed test
   reads as shape-only, not behavioral).
3. If satisfied, post the Architect Review via `gh pr review --comment` with the verbatim
   frozen header + fresh-session attestation from `.ai/context/workflow.md` (**never
   `--approve`**).
4. If approved: T1 done pending the owner's merge (also merge the pending docs syncs,
   [#175](https://github.com/glunk-works/loop-orchestrator/pull/175) and this PR, in any
   order — both docs-only). **T2** (docs: CLAUDE.md boundary bullet +
   `docs/bounty_loop_architecture.md` §8/§9 P1-D1..D7) is next, Sonnet-suitable.

**HITL Gate: NONE OPEN.** The fix itself was pre-approved via the prior review's change
list. Next gate (if any) is only if the fresh Architect Review finds the fix incomplete.

## Gotchas worth remembering
- **The fix keeps the map and corrects the claim — it is NOT the core re-entry wiring.**
  `core/state.py`/`core/engine.py`/`personas/resolution.py` are still untouched by design
  (S47/S48; the exact churn P1-D3 avoids).
- **P1-D3's producer-swap seam holds.** The `impact_reentry` map is now honestly
  documented as inert-until-core, not claimed live — don't conflate the two when judging
  P1-D3.
- **Docs-sync PRs stack up unmerged** — [#175](https://github.com/glunk-works/loop-orchestrator/pull/175)
  (prior review sync) and this PR are both open against `main`; harmless (docs-only,
  `architect-review`-exempt) but merge them when convenient so `.ai/next-steps.md` on
  `main` stays current.
- **The sprint-44 live Postgres smoke is still OWED** (`DEFERRED_VERIFICATION.md` §10) —
  discharges in S47, not here.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes.** **Never commit to `main`, merge, or force-push.**

## Pointers
- [PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173) — S46 T1, branch `sprint/46-bounty-loop-skeleton`, HEAD `7cdf15b`.
- [`sprints/46_bounty_loop_skeleton/sprint_plan.md`](../sprints/46_bounty_loop_skeleton/sprint_plan.md) — active plan (T1 = this PR, T2 = docs).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — bounty loop reference-of-record; §9 P1-D1..D7 write-up owed (T2).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = OWED sprint-44 live Postgres smoke; discharge in S47.
