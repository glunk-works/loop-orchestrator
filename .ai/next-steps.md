# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 40 — BL-2 pass 2 (Slack inbound trigger) — T1–T6 all done.**
T6 is on **[PR #120](https://github.com/glunk-works/loop-engine/pull/120)** (docs-only,
`architect-review`-exempt). **`/archive-sprint` once #120 merges** — that closes the sprint.

## Just done (Architect/Opus session)
- Posted the fresh-session **Architect HITL review on PR #119** (T4+T5) — LGTM, no changes
  requested, `--comment` only. **#119 merged** (`54c2a65`).
- **Found and cleared a stale-red CI trap on #119.** All eight checks passed, yet the PR stayed
  `BLOCKED` — *not* the usual GitHub lag. `hitl-review.yml` fires on **both** `pull_request` and
  `pull_request_review`, so every `src/` PR gets **two `architect-review` check-runs on the same
  SHA**: the first fails correctly (no review exists yet), the second passes once the review lands.
  `statusCheckRollup` aggregated to **FAILURE** and did **not** self-supersede. Fixed with
  `gh run rerun` on the **old** run (truthful — the review genuinely exists at that SHA) →
  rollup SUCCESS → CLEAN. **This is structural and will recur on every `src/` PR** — flagged to
  the owner as likely `hitl-review.yml` backlog material; **not filed** (owner's call).
  - Discriminator worth keeping: `BLOCKED` + rollup **SUCCESS** = lag, wait. `BLOCKED` + rollup
    **FAILURE** = stale red, `gh run rerun` the old run.
- Implemented **T6** (docs close-out) and opened **PR #120**: README operator setup (app token,
  Socket Mode, `/agent-run` registration, Infisical provenance, `slack-listen`, fail-closed,
  required-budget grammar); `CLAUDE.md` + `modules.md` boundary updates (`slack_control/` as a new
  orchestrator-level caller; `tools/slack_io` now bidirectional, still sole `slack_sdk` importer);
  the inbound-trigger **threat model**; `docs/backlog.md` BL-2 pass 2 LANDED + the BL-24 supersede
  note; roadmap Sprint 40 row + NEXT ACTION → pass 3.
- Green gate: lint clean, format clean, full suite **709 passed**.

## Next
1. **`/archive-sprint` after #120 merges.** Sprint 40 is then complete (BL-2 pass 2 shipped).
2. **Then: plan BL-2 pass 3** (escalation round-trip — route a paused run's questions to Slack and
   fold the reply back). Last BL-2 pass; both notify (pass 1) and command (pass 2) are live to
   build on. Planning = **Opus**.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify.** Slack superseded `trigger/` as the live inbound path, but shares
  **no code** with it, so `trigger/`'s HMAC path stays unverified. The risk shifted from
  "unverified auth on a live surface" to "**dead code carrying an inbound credential**"
  (`LOOP_ENGINE_WEBHOOK_SECRET`). Decide: retire `trigger/` + the secret and close §6 as moot, or
  keep it and pay for the verification. Recorded in the BL-24 supersede note; **still open**.
- **`hitl-review.yml`'s stale-red check-run** (above) — worth filing?

## Accepted-with-reason on #119 (don't re-litigate without cause)
- A redelivered Socket Mode envelope can still produce a **duplicate "accepted" ephemeral reply**
  even though the dispatcher correctly dedupes the run. UX-only; fixing it means changing
  `dispatch.py`'s already-merged T3 return contract. Both the critic-gate and the HITL review
  concurred with leaving it.
- `dispatch.py`'s dedupe is **active-only** ("no concurrent double-run," not exactly-once) —
  effectively unreachable here, since real runs vastly exceed Slack's ~3s redelivery window.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Squash trap:** `sprint/40-bl2-slack-daemon-cli` (#119) is dead and pruned. The live branch is
  `sprint/40-bl2-slack-docs` (#120) — once it merges it too goes dead; cut the next sprint's
  branch fresh off updated `main`.
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer
  the host pinentry and retry.
- **`/critic-gate` proposes, never auto-spawns** — confirm the subagents before spawning.

## Pointers
- [PR #120](https://github.com/glunk-works/loop-engine/pull/120) — T6 docs close-out, awaiting merge.
- [`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md) — the approved plan (all tasks done).
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 open), **BL-24** (retire-or-verify decision), **BL-33** (guard-hardening), **BL-34** (CI `test` docs-only fail-safe defeated by `bash -e`).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3).
