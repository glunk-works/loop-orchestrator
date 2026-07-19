# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 43 (BL-5 model routing). T1 landed → awaiting architect-review.**
The second loop (`loops/bounty/`) is the active initiative; the dev loop (`loops/default`)
stays paused. `sprint_status: awaiting_architect_review`, assigned **Opus/architect**.

## Just done (Sonnet/coder session, 2026-07-19)
- **Synced local `main`** — a drift check found `origin/main` one commit ahead (PR #148,
  the sprint-43 plan-approval docs PR, had merged but wasn't fetched yet); fast-forwarded
  and pruned the now-dead branch plus one other stale squash-merged branch.
- **Cut `sprint/43-bl5-model-routing` from `main`.**
- **Implemented Task 1** — added `claude-opus-4-8` ($5/$25, cache-write $6.25, cache-read
  $0.50 per MTok) and `claude-haiku-4-5` ($1/$5, cache-write $1.25, cache-read $0.10 per
  MTok) to `tools/llm/pricing.RATES`, with cost-asserting tests in
  `tests/tools/test_pricing.py` mirroring the existing `claude-sonnet-5` cases (commit
  `1add391`). Full local gate green (lint → format → 793 tests passed).
- **Ran `/critic-gate`** — owner selected `architect` only (diff is a pure data-table +
  test addition, no boundary/taint surface). Verdict: clean, no findings.
- **Opened PR #149** (`sprint/43-bl5-model-routing` → `main`), pricing/tests only.

## Next — post the architect-review on PR #149 (Opus/architect, fresh session)
This is the separate, human-triggered, fresh-session `architect-review` CI gate — not a
repeat of the `/critic-gate` pass above (that already ran and was clean; this reviewer
did not author the diff). `/code-review` the PR, then post with the **verbatim** two-line
header + attestation block from `.ai/context/workflow.md` against the PR's current head
commit. Never `--approve`; the owner's merge is the approval.
**After the review lands:** the sprint is **not** done — T2 (de-dup the two `DEFAULT_MODEL`
constants), T3 (resolver `max_tokens` review), and T4 (docs) remain. A follow-up
`/handoff` should hand T2 back to **Sonnet/coder**, on a fresh branch cut from `main`
once PR #149 is merged (don't stack T2 on the unreviewed `sprint/43-bl5-model-routing`
branch).
**Next HITL Gate:** none open now; the sprint-completion Gate is the owner's merges of
all four sprint 43 PRs.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **The review boundary needs a genuinely new session** — `/clear` resets context but
  does not make the reviewer a separate invocation; the fresh-session attestation is an
  integrity property, not just context hygiene.
- **Before pushing code, run the FULL local gate** (lint → format → test) or `/ship`. **PR
  title ≤72 bytes** — `wc -c` first. **Never commit to `main`, merge, or force-push.**
- Bounty invariants are non-negotiable (sprints 44/45): scope validation is structural
  code, never the LLM's job; active exploitation gates through the escalation ladder.

## Pointers
- [PR #149](https://github.com/glunk-works/loop-orchestrator/pull/149) — T1, awaiting architect-review. **Read first.**
- [`sprints/43_bl5_model_routing/sprint_plan.md`](../sprints/43_bl5_model_routing/sprint_plan.md) — the active sprint (T2/T3/T4 remain).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§8 roadmap, §9 decisions).
- [`docs/backlog.md`](../docs/backlog.md) — BL-5 is this sprint; paused dev-loop items behind the pivot.
