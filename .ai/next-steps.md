# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `planning`.**
No sprint plan exists yet; **writing it is the next action.** Planning = **Opus/Architect**.

## Just done
- **Sprint 40 (BL-2 pass 2, Slack inbound trigger) is COMPLETE and archived** — merged across
  #117 (T2+T3), #119 (T4+T5), #120 (T6 docs). Final commit `95c5a71`. Prior cursor snapshotted to
  `.ai/archive/40_bl2_slack_inbound-next-steps.md`.
- `loop-engine slack-listen` is live: `/agent-run --budget <n> <requirements>` in
  `LOOP_ENGINE_SLACK_CHANNEL` starts a real run.

## Next — plan sprint 41 (Opus)
Write `sprints/41_bl2_slack_escalation/sprint_plan.md`: route a paused run's questions to Slack and
fold the reply back, as an alternative to the GitHub-issue round-trip. **The last BL-2 pass.**
Use `sprints/40_bl2_slack_inbound/sprint_plan.md` as the shape precedent (locked FDs, per-task
acceptance criteria, PR structure, which tasks touch `src/`).

**Prior art to reason from — both directions already exist:**
- **Pass 1 (outbound):** `tools/slack_io`'s notifier + the `core/notify` `Notifier` seam; fail-open.
- **Pass 2 (inbound):** `slack_control/`'s Socket Mode daemon; FD3 channel guard (resolved IDs, not
  names), fail-closed construction, `envelope_id` dedupe.
- **The round-trip precedent:** the GitHub-issue path — `tools/issue_io`, `resume --from-issue`,
  `State.pending_issue`, and PM's `fold_answers` (which already folds answers in and classifies
  blast radius). Pass 3 needs both directions **plus a correlation mechanism** tying a reply back to
  a specific paused run/question; that correlation is the interesting design question.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify.** Slack superseded `trigger/` as the live inbound path but shares
  **no code** with it, so `trigger/`'s HMAC path stays unverified. The risk shifted from "unverified
  auth on a live surface" to "**dead code carrying an inbound credential**"
  (`LOOP_ENGINE_WEBHOOK_SECRET`). Decide: retire `trigger/` + the secret and close
  `DEFERRED_VERIFICATION.md` §6 as moot, or keep it and pay for the verification. **Still open.**
- **`hitl-review.yml`'s stale-red check-run** (below) — worth filing? **Not filed.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Stale-red `architect-review` (structural, found 2026-07-17 on #119).** `hitl-review.yml` fires on
  **both** `pull_request` and `pull_request_review`, so every `src/`-touching PR ends up with **two
  `architect-review` check-runs on the same SHA** — the first failed (no review existed yet), the
  second passed. The rollup aggregates to **FAILURE** and does **not** self-supersede: the PR sits
  `BLOCKED` with every check green. Fix: **`gh run rerun <old_run_id>`** (truthful — the review
  genuinely exists at that SHA). **Discriminator:** `BLOCKED` + rollup **SUCCESS** = ordinary lag,
  wait; `BLOCKED` + rollup **FAILURE** = stale red, rerun. Docs-only PRs are unaffected.
- **Squash trap:** both sprint-40 branches are dead and pruned. Cut sprint 41's branch fresh off
  updated `main`.
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the
  host pinentry and retry.
- **`/critic-gate` proposes, never auto-spawns** — confirm the subagents before spawning.

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; passes 1–2 LANDED), **BL-24** (retire-or-verify), **BL-33** (guard-hardening), **BL-34** (CI `test` docs-only fail-safe defeated by `bash -e`).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3).
- [`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md) — the immediate precedent for plan shape.
- `sprints/41_bl2_slack_escalation/sprint_plan.md` — **to be written.**
