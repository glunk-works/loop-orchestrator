# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 43 (BL-5 model routing). T1+T2 merged; T3 shipped → PR #154
awaiting fresh-session architect-review (Opus/architect). T4 (docs) is the last task.**
The second loop (`loops/bounty/`) is the active initiative; the dev loop (`loops/default`)
stays paused. `sprint_status: awaiting_architect_review`, assigned **Opus/architect**.

## Just done (this session, 2026-07-19)
- **T2 fresh-session Architect Review** — reviewed PR #152 (DEFAULT_MODEL de-dup):
  verified single canonical constant, no stale `shared.DEFAULT_MODEL` importer, no import
  cycle (pricing stays a pydantic-only leaf), value unchanged + still priced in RATES,
  both call sites pinned by tests. No blocking findings; posted via `gh pr review --comment`.
  Cleared the **BL-35 stale-red** trap (`gh run rerun` the old `pull_request` run). **Owner
  merged #152** (69c0205).
- **T3 — resolver `max_tokens` review + change.** Reviewed the resolver `max_tokens: 2048`
  in `architecture.yaml`/`pm.yaml`. Conclusion: **raise 2048 → 4096**. Deciding factor is
  the failure shape — `apply_resolution_response` parses the whole batch as one JSON blob,
  so a response that overflows the cap fails to parse and returns the **entire batch
  unresolved** (all questions escalate up, pass wasted); with **no cap on batch size**, a
  plausible heavy batch (~12–15 substantive resolutions) crosses ~1500–2000 output tokens.
  Raising the ceiling is zero-cost (billing is per emitted token) and matches PM's existing
  `EXTRACTION_MAX_TOKENS = 4096`. Shipped as **PR #154** (`sprint/43-t3-resolver-max-tokens`,
  commit `8dcbde8`); full local gate green (lint, format, 796 tests); both configs validated
  at 4096. No `/critic-gate` pass — the diff is config-value-only (no logic/import/surface),
  nothing for a critic to bite on (choice on the record).

## Next — post the fresh-session Architect Review on PR #154 (Opus/architect, NEW session)
Run `/code-review` on PR #154 (branch `sprint/43-t3-resolver-max-tokens`,
https://github.com/glunk-works/loop-orchestrator/pull/154) and post it via
`gh pr review --comment` (never `--approve`). The review body **must open with the verbatim
two-line header** from `.ai/context/workflow.md`: `**Opus/Architect HITL review (automated)**`
then `*Fresh-session review: this session did not author the diff.*` — paste verbatim, the
`architect-review` check matches by literal `contains()`. After a clean review **and** the
owner's merge of #154: **T4** (docs-only — `docs/backlog.md` BL-5 status, `docs/bounty_loop_architecture.md`
§8/§9 P0-D1/P0-D2, sprint 43 described **in-progress not done**; **do NOT touch `.ai/*`**).
After T4 merges, sprint 43 is complete → `/archive-sprint`.
**Next HITL Gate:** none open now; the sprint-completion Gate is the owner's merges of all
four sprint 43 PRs (T1/T2 merged; T3 #154 open; T4 not yet opened).

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **This review must run in a genuinely fresh session** — `/model opus` mid-session is not
  enough (doesn't clear context); the sequence is new window → `/model opus` → `/resume` →
  `/code-review` → post. The T3 diff was authored this session, so a fresh session that
  authored none of it must post the review.
- **BL-35 stale-red trap on every `src/` PR** — `architect-review` fires on both
  `pull_request` and `pull_request_review`, so a pre-review red can linger next to the
  post-review green; BLOCKED + rollup FAILURE ⇒ `gh run rerun` the OLD run.
- **PR title ≤72 bytes** — `wc -c` first. **Never commit to `main`, merge, or force-push.**
- Bounty invariants are non-negotiable (sprints 44/45): scope validation is structural
  code, never the LLM's job; active exploitation gates through the escalation ladder.

## Pointers
- [`sprints/43_bl5_model_routing/sprint_plan.md`](../sprints/43_bl5_model_routing/sprint_plan.md) — the active sprint (T4 remains after T3's review). **Read first.**
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§8 roadmap, §9 decisions).
- [`docs/backlog.md`](../docs/backlog.md) — BL-5 is this sprint; paused dev-loop items behind the pivot.
- PR #154 — https://github.com/glunk-works/loop-orchestrator/pull/154
