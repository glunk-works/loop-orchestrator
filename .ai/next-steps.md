# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 43 (BL-5 model routing). Plan APPROVED → implementing.**
The second loop (`loops/bounty/`) is the active initiative; the dev loop (`loops/default`)
stays paused. Phase 0 was decomposed this pass into **three sprints** (43 routing · 44
`tools/inventory_db`+schema · 45 scope validator + ingestion seam). `sprint_status:
implementing`, assigned **Sonnet/coder**. Owner approved the Phase 0 sprint-plan HITL Gate
2026-07-19.

## Just done (Opus/architect planning session, 2026-07-19)
- **Ran the Phase 0 planning pass** (one-question-at-a-time, HITL micro-gates). Locked six
  decisions **P0-D1…D6** — all recorded in the sprint 43 plan's Context + the roadmap:
  three-sprint split (D1); `schema_version` bump **deferred to Phase 1** (D2, YAGNI — no
  bounty `State` field yet); sprint 43 = "enabler + one seam" (D3); sprint 44 Postgres =
  hermetic + deferred live-verify, psycopg3 sync, env-var DSN (D4); idempotent `.sql` DDL,
  no Alembic yet (D5); sprint 45 `tools/scope` pure validator + structured-extraction
  ingestion seam (D6).
- **Authored + self-critiqued `sprints/43_bl5_model_routing/sprint_plan.md`** — grounded
  every task in real file:line anchors; tightened T2 to a **de-duplication only** (no
  speculative override plumbing — consistent with D2) and carved `.ai/` ownership out of
  T4 (that's `/handoff`'s file), after an owner-requested critic pass.
- Verified the true Phase-0 blocker: `pricing.RATES` has only `claude-sonnet-5`, so Opus/
  Haiku raise `UnknownModelError` and disable the budget cap. Sourced exact list pricing
  (Opus 4.8 $5/$25, Haiku 4.5 $1/$5; cache-write ×1.25, cache-read ×0.1) from the
  `claude-api` reference.

## Next — implement sprint 43 (Sonnet/coder)
Read [`sprints/43_bl5_model_routing/sprint_plan.md`](../sprints/43_bl5_model_routing/sprint_plan.md).
Cut `sprint/43-bl5-model-routing` from `main`; land tasks as separate PRs based on `main`:
1. **T1** — `RATES += claude-opus-4-8 + claude-haiku-4-5` with **cost-asserting** tests in
   `tests/tools/test_pricing.py` (copy the `claude-sonnet-5` cases). The real unblock;
   lands first, own PR.
2. **T2** — de-dup the two `DEFAULT_MODEL` literals into one shared constant (recommended
   home: `tools/llm`); **no** `model` param added; value stays `claude-sonnet-5`. Own PR.
3. **T3** — review resolver `max_tokens: 2048` (raise only if a resolution could exceed
   ~1500 output tokens).
4. **T4** — docs (backlog BL-5, roadmap §8/§9); **not** `.ai/*`.
Each `src/`-touching PR needs a **fresh-session `architect-review`** (`/handoff` → new
session → `/resume` → `/code-review` → post the verbatim header). Run `/critic-gate` after
the green gate, before that handoff.
**Next HITL Gate:** none open now; the sprint-completion Gate is the owner's merges of the
sprint 43 PRs.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **Planning→coding is not a review boundary** — `/clear` → `/model sonnet` → `/resume`
  in place is fine for the coder. The *review* handoff (later) needs a genuinely new session.
- The prior "pivot cursor" commit `d21badb` was **never merged** (no PR); this handoff's
  docs PR supersedes it — don't resurrect that branch.
- **Before pushing code, run the FULL local gate** (lint → format → test) or `/ship`. **PR
  title ≤72 bytes** — `wc -c` first. **Never commit to `main`, merge, or force-push.**
- Bounty invariants are non-negotiable (sprints 44/45): scope validation is structural
  code, never the LLM's job; active exploitation gates through the escalation ladder.

## Pointers
- [`sprints/43_bl5_model_routing/sprint_plan.md`](../sprints/43_bl5_model_routing/sprint_plan.md) — the active sprint. **Read first.**
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§8 roadmap, §9 decisions).
- [`docs/backlog.md`](../docs/backlog.md) — BL-5 is this sprint; paused dev-loop items behind the pivot.
