# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 43 (BL-5 model routing). T1 MERGED → T2 next (Sonnet/coder).**
The second loop (`loops/bounty/`) is the active initiative; the dev loop (`loops/default`)
stays paused. `sprint_status: implementing`, assigned **Sonnet/coder**.

## Just done (Opus/architect review session, 2026-07-19)
- **Posted the fresh-session architect-review on PR #149** (T1: `RATES += claude-opus-4-8`
  + `claude-haiku-4-5` with cost tests). Verified rates against the authoritative
  `claude-api` reference (Opus 4.8 $5/$25, Haiku 4.5 $1/$5; cache-write ×1.25, cache-read
  ×0.1) and hand-checked every test assertion — `/code-review` (high) found nothing.
- **Cleared the BL-35 stale-red trap** — `architect-review` had a stale `fail` from the
  `pull_request` trigger alongside the fresh `pass` from `pull_request_review`;
  `gh run rerun` on the old run turned it green. All 8 required checks passed.
- **PR #149 MERGED** by the owner (`ee9b2eb` on `main`) — the approval for T1. The
  docs-sync PR #150 (`98ef99b`) also merged; both sprint-43 branches pruned; `main` synced.

## Next — implement Task 2: de-dup the DEFAULT_MODEL constant (Sonnet/coder, fresh branch)
Two identical `DEFAULT_MODEL = "claude-sonnet-5"` literals exist —
[`personas/coder_iac/shared.py:24`](../src/loop_orchestrator/personas/coder_iac/shared.py#L24)
(used in `ralph.py`'s module-level `_run_increment`) and
[`personas/pm/persona.py:27`](../src/loop_orchestrator/personas/pm/persona.py#L27)
(used in the module-level `fold_answers`). Define **one** canonical constant and have both
import it; recommended home is a constant in `tools/llm` (no new import edge, `core/` graph
and keyring boundary untouched — confirm the import is clean and state the home in the PR).
**De-duplication ONLY** — do NOT add a `model` parameter to `_run_increment`/`fold_answers`
(per-persona override deferred). **Value stays `claude-sonnet-5`** — byte-for-byte unchanged.
This touches `src/` ⇒ FULL local gate → `/critic-gate` (architect) → fresh-session
`architect-review` CI gate on the PR. See
[`sprints/43_bl5_model_routing/sprint_plan.md`](../sprints/43_bl5_model_routing/sprint_plan.md) Task 2.
**Next HITL Gate:** none open now; the sprint-completion Gate is the owner's merges of all
four sprint 43 PRs. After T2: T3 (resolver `max_tokens` review), T4 (docs).

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **Cut T2 from fresh `main`** (now at `ee9b2eb`) — don't stack on a stale base. **PR title
  ≤72 bytes** — `wc -c` first. **Never commit to `main`, merge, or force-push.**
- **BL-35 stale-red trap on every `src/` PR** — `architect-review` fires on both
  `pull_request` and `pull_request_review`, so a pre-review red can linger next to the
  post-review green; BLOCKED + rollup FAILURE ⇒ `gh run rerun` the OLD run.
- **Before pushing code, run the FULL local gate** (lint → format → test) or `/ship`.
- Bounty invariants are non-negotiable (sprints 44/45): scope validation is structural
  code, never the LLM's job; active exploitation gates through the escalation ladder.

## Pointers
- [`sprints/43_bl5_model_routing/sprint_plan.md`](../sprints/43_bl5_model_routing/sprint_plan.md) — the active sprint (T2/T3/T4 remain). **Read first.**
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§8 roadmap, §9 decisions).
- [`docs/backlog.md`](../docs/backlog.md) — BL-5 is this sprint; paused dev-loop items behind the pivot.
