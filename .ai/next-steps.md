# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PR) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 46 T1 (skeleton + `State` 5→6 bump) is IMPLEMENTED.
`sprint_status: awaiting_architect_review`, assigned Opus/architect.**
[PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173) is open against
`main` (branch `sprint/46-bounty-loop-skeleton`), `/critic-gate` has run, and its
findings are posted as a PR comment. The next unit is the **fresh-session Architect
Review** — it must explicitly rule on one HIGH finding the critic pass surfaced (below),
not just wave the happy-path acceptance criteria through.

## Just done (2026-07-21, Sonnet/coder)
- Implemented S46 T1 per the plan: `BountyRunState` + `bounty: BountyRunState | None`
  on `State`, `CURRENT_SCHEMA_VERSION` 5→6 + the matching `migrate_state_payload`
  branch (`core/state.py`); `build_bounty_loop()` + `BOUNTY_LOOP` wiring Recon →
  Surface-Mapping (`loops/bounty/loop.py`); the `ArtifactProducer` seam + two stub
  personas (`personas/bounty/`). Full hermetic suite added/extended; also fixed a
  pre-existing hardcoded `schema_version == 5` assertion in
  `tests/tools/test_state_io_reader.py` this bump would otherwise have broken silently.
- Full local gate green throughout: `hatch run lint && format && test-parallel` —
  879 passed, 4 skipped, no lint/format deltas.
- Pushed and opened **PR #173** (commits `2999196`, `46ddc9e`).
- Ran `/critic-gate`: spawned `architect` + `security-critic` (owner-confirmed) against
  the diff.
  - **security-critic: clean.** No reachable trust-boundary issue; two forward-looking
    notes for S47/S48 (SurfaceMapPersona's missing `bounty is None` guard vs. Recon's;
    the producer→`artifacts` seam validates only JSON shape, not content).
  - **architect: one HIGH finding, verified directly against the code.**
    `loops/bounty/loop.py`'s `impact_reentry={"scope": 0, "surface": 1}` **cannot fire**
    — `core/engine.py::reentry_index()` is hardwired to
    `for impact in ("architecture", "plan")`; `Question.impact` (`core/state.py`) is
    `Literal["task","plan","architecture"] | None` (a Question can never even *hold*
    `"scope"`/`"surface"`); `personas/resolution.py`'s `VALID_IMPACTS` matches the same
    3-value set. Making this real needs `core/state.py` + `core/engine.py` +
    `personas/resolution.py` changes in S47/S48 — the exact core churn P1-D3 states the
    skeleton avoids. **Also flagged, lower severity:** the bounty loop's
    escalation/resume path is inert (`ReconPersona` has no `resolve_questions` override
    or `fold_answers`) — not reachable today (the loop isn't in `runner.NAMED_LOOPS`
    yet, per P1-D7), but a forward gap.
  - Fixed the one mechanical NIT (a mutability test that would've passed even on a
    frozen model) — commit `46ddc9e`. **Owner explicitly deferred the HIGH finding's
    fix-vs-document call to the Architect Review** rather than expanding this PR into
    `core/` mid-implementation.
  - Findings posted in full on the PR:
    https://github.com/glunk-works/loop-orchestrator/pull/173#issuecomment-5029833958

## Next — post the fresh-session Architect Review (Opus/architect)
`/code-review` the PR #173 diff, then post with the **verbatim** two-line header +
attestation (`**Opus/Architect HITL review (automated)**` /
`*Fresh-session review: this session did not author the diff.*`) via
`gh pr review --comment` (never `--approve`). The review must **explicitly address the
impact_reentry HIGH finding** — decide whether to request a `core/` fix before merge, or
approve with an explicit, documented note that scope/surface re-entry is deferred to
S47/S48 (and what will need to change there). Don't just re-derive the finding from
scratch — the critic-gate comment already has file:line detail; spend the review's
judgment on the fix-vs-defer call, not re-discovery.

If the review requests changes: that's a Sonnet/coder task, new session,
`/handoff` → `/model sonnet` → `/resume`. If it approves: T1 is done pending the human's
merge; **T2** (docs: `CLAUDE.md` boundary bullet + `docs/bounty_loop_architecture.md`
§8/§9 — P1-D1..D7 write-up, still owed) is next, and is itself Sonnet-suitable
(mechanical, `architect-review`-exempt).

**HITL Gate: NONE OPEN.** S46 T1 implementation + `/critic-gate` complete. Next gate: the
S46 T1 fresh-session `architect-review` on PR #173.

## Gotchas worth remembering
- **The impact_reentry HIGH finding is the review's main job** — don't let a
  fresh-session review just confirm the green suite and the schema-migrate correctness
  (both of which are genuinely solid) without also ruling on the dead re-entry
  vocabulary. The happy-path S46 acceptance criteria doesn't exercise re-entry at all,
  so it can't catch this on its own.
- **P1-D3's seam bet (the producer swap) DOES hold** — don't conflate it with the
  re-entry map, which does not. They're separate claims in the same sprint.
- **The sprint-44 live Postgres smoke is still OWED** (`DEFERRED_VERIFICATION.md` §10) —
  discharges in S47, not here.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes.** **Never commit to `main`, merge, or force-push.**

## Pointers
- [PR #173](https://github.com/glunk-works/loop-orchestrator/pull/173) — S46 T1, branch `sprint/46-bounty-loop-skeleton`, HEAD `46ddc9e`.
- [critic-gate findings](https://github.com/glunk-works/loop-orchestrator/pull/173#issuecomment-5029833958) — full architect + security-critic detail.
- [`sprints/46_bounty_loop_skeleton/sprint_plan.md`](../sprints/46_bounty_loop_skeleton/sprint_plan.md) — the active plan (T1 = this PR, T2 = docs, next after merge).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — bounty loop reference-of-record; §9 P1-D1..D7 write-up still owed (T2).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = the OWED sprint-44 live Postgres smoke; discharge in S47.
