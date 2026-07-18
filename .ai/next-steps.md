# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Between sprints — BL-2 is COMPLETE, no next sprint committed.** The migration is long done and
post-migration work is backlog-driven. The next unit is the **owner's pick** from the backlog; until
one is selected there is no sprint plan and no work to auto-start. `sprint_status: planning`,
assigned **Opus/architect**.

## Just done (Opus/architect session, 2026-07-18)
- **Sprint 41 (BL-2 pass 3, Slack escalation round-trip) shipped and archived.** Posted the
  fresh-session Architect Review on **T5** ([#136](https://github.com/glunk-works/loop-orchestrator/pull/136),
  APPROVE) and cleared its BL-35 stale-red. Implemented **T6** (docs-only,
  [#138](https://github.com/glunk-works/loop-orchestrator/pull/138) → squash `36fe931`): marked **BL-2
  COMPLETE**, advanced the roadmap, added exit code 5 (`AWAITING_SLACK`) + the round-trip to CLAUDE.md /
  README / modules.md / threat model.
- **Flagged that BL-2 is complete-but-not-live.** The whole Slack *inbound* surface (pass 2 command +
  pass 3 round-trip) is hermetically verified (780 tests, fakes) but has **never** run against a real
  Socket Mode session. Tightened the docs to say so, filed **BL-37**, and wrote the operator runbook
  [`docs/slack_escalation_live_smoke.md`](../docs/slack_escalation_live_smoke.md).
- Archived sprint 41's cursor to `.ai/archive/41_bl2_slack_escalation-next-steps.md`.
- **Landed a workflow-friction thread** (owner-requested review of the day's sessions):
  [#140](https://github.com/glunk-works/loop-orchestrator/pull/140) — `/pr-checks` now auto-clears the
  BL-35 stale-red, a **verification-ledger** in `/archive-sprint`+`/handoff` blocks "complete"
  overclaiming "live", `/handoff` emits a paste-ready next-session command block, a backlog **Index**,
  and a new **`/retro`** skill; [#141](https://github.com/glunk-works/loop-orchestrator/pull/141) —
  **resolved BL-34** (CI docs-only fail-safe) and made docs-only PRs skip `dependency-audit`+`sbom`.
- Ran `/retro`: routed one finding to memory ([[feedback-local-green-gate]] — run the full local
  gate, not just pytest, before pushing; #141 format-check red was the trigger).

## Next — owner picks the next backlog item, then plan it (Opus)
No sprint is committed. The owner chooses from `docs/migration_roadmap.md`'s NEXT ACTION list:
- **Product (owner-requested):** BL-1 (in-loop code review of the Coder), BL-3 (prompt-caching review —
  needs a real key + spend), BL-4 (Ralph loop watcher), BL-5 (per-persona model routing; `claude-opus-4-8`
  `RATES` entry is its hard prerequisite).
- **Decisions:** BL-24 (retire `trigger/` + `LOOP_ORCHESTRATOR_WEBHOOK_SECRET` as moot vs. keep + verify §6),
  BL-35 (which stale-red `architect-review` fix, if any).
- **Hardening / deferred verification:** BL-32/BL-33 (adversarial guard audit + one shared hardened
  boundary-guard helper), BL-36 (sprint-41 low-priority review cleanups), **BL-37** (the live Slack smoke).

Once selected: run the planning pass (Opus, one question at a time, HITL Gates) → write the sprint plan.
**`/resume` must WAIT here** — `planning` + no plan + unselected unit — never auto-start.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`.** Slack supersedes it in practice but proves nothing about its
  HMAC path. **Still open.**
- **BL-35 — which stale-red fix, if any.** File-don't-fix stands; manual `gh run rerun` is the workaround.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **BL-2 is "complete + hermetically verified," NOT "proven live"** — see BL-37 / the runbook before
  claiming the Slack round-trip works end-to-end.
- **Stale-red `architect-review` (BL-35):** every `src/` PR gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_failed_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
  (`/pr-checks` now detects this and offers the rerun automatically.)
- **Before pushing code, run the FULL local gate** (lint → format → test), not just `hatch run test` —
  or use `/ship`, which bakes it in. #141's `format-check` went red on a quoting nit from a tests-only run.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`
  (already baked into `/ship` + `/handoff`).
- **Never commit to `main`, never merge, never force-push.** (Rebase a stale pushed branch by merging `main` INTO it.)
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2 COMPLETE**; the open items list above.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (the candidate list).
- [`docs/slack_escalation_live_smoke.md`](../docs/slack_escalation_live_smoke.md) — the BL-37 live-smoke runbook.
- `.ai/archive/41_bl2_slack_escalation-next-steps.md` — the retired sprint-41 cursor.
