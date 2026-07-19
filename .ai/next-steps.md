# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 43 (BL-5 model routing). T2 implemented → PR #152 awaiting
fresh-session architect-review (Opus/architect).**
The second loop (`loops/bounty/`) is the active initiative; the dev loop (`loops/default`)
stays paused. `sprint_status: awaiting_architect_review`, assigned **Opus/architect**.

## Just done (Sonnet/coder implementation session, 2026-07-19)
- **Implemented Task 2** — collapsed the two duplicate `DEFAULT_MODEL = "claude-sonnet-5"`
  literals (`personas/coder_iac/shared.py`, `personas/pm/persona.py`) into one canonical
  constant in [`tools/llm/pricing.py`](../src/loop_orchestrator/tools/llm/pricing.py). `ralph.py`
  now imports it directly from `pricing` (not re-exported through `shared.py`); `pm/persona.py`
  imports it the same way. Value unchanged (`claude-sonnet-5`); no `model` parameter added
  to either call site (per-persona override stays deferred).
- **Added 3 regression tests** pinning the constant's value and proving both call sites
  resolve to it: `test_default_model_is_claude_sonnet_5`, `test_run_increment_calls_the_shared_canonical_default_model`,
  `test_fold_answers_calls_the_shared_canonical_default_model`.
- **Full local gate green** — lint, format, 796 tests passed.
- **Ran `/critic-gate`** — `architect` (proposed and confirmed by the human) reviewed the
  diff: no blocking findings, one low-severity test-purity observation (accepted, no fix
  needed — the load-bearing invariant is genuinely proven by a separate constant-value test).
- **Opened PR #152** (`sprint/43-t2-dedup-default-model` → `main`, commit `9c98827`) — still
  needs the fresh-session `architect-review` CI gate before it's mergeable.

## Next — post the fresh-session Architect Review on PR #152 (Opus/architect, NEW session)
Run `/code-review` on PR #152 (branch `sprint/43-t2-dedup-default-model`,
https://github.com/glunk-works/loop-orchestrator/pull/152) and post it via
`gh pr review --comment` (never `--approve`). The review body **must open with the verbatim
two-line header** from `.ai/context/workflow.md`: `**Opus/Architect HITL review (automated)**`
then `*Fresh-session review: this session did not author the diff.*` — paste verbatim, the
`architect-review` check matches by literal `contains()`. After a clean review: **Task 3**
(review the resolver `max_tokens: 2048` in `architecture.yaml`/`pm.yaml`, adjust only if a
concrete truncation risk is found), then **Task 4** (docs-only).
**Next HITL Gate:** none open now; the sprint-completion Gate is the owner's merges of all
four sprint 43 PRs.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **This review must run in a genuinely fresh session** — `/model opus` mid-session is not
  enough (doesn't clear context); the sequence is `/handoff` → **new session** →
  `/model opus` → `/resume` → `/code-review` → post.
- **BL-35 stale-red trap on every `src/` PR** — `architect-review` fires on both
  `pull_request` and `pull_request_review`, so a pre-review red can linger next to the
  post-review green; BLOCKED + rollup FAILURE ⇒ `gh run rerun` the OLD run.
- **PR title ≤72 bytes** — `wc -c` first. **Never commit to `main`, merge, or force-push.**
- Bounty invariants are non-negotiable (sprints 44/45): scope validation is structural
  code, never the LLM's job; active exploitation gates through the escalation ladder.

## Pointers
- [`sprints/43_bl5_model_routing/sprint_plan.md`](../sprints/43_bl5_model_routing/sprint_plan.md) — the active sprint (T3/T4 remain after T2's review). **Read first.**
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§8 roadmap, §9 decisions).
- [`docs/backlog.md`](../docs/backlog.md) — BL-5 is this sprint; paused dev-loop items behind the pivot.
- PR #152 — https://github.com/glunk-works/loop-orchestrator/pull/152
