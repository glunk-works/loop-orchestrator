# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `implementing`.**
T1 merged ([PR #127](https://github.com/glunk-works/loop-engine/pull/127) → `55d6d9d`).
T2 merged ([PR #128](https://github.com/glunk-works/loop-engine/pull/128) → squash `cbc82ac`).
**T3 merged ([PR #131](https://github.com/glunk-works/loop-engine/pull/131) → squash `954572a`) — Architect-Reviewed clean, all 8 checks green.**
**T4 is next: Coder, Sonnet.**

## Just done (Opus/Architect review session, 2026-07-17)
- Posted the fresh-session **Architect Review** on PR #131 (verbatim header + attestation),
  verdict **clean, no blockers**; independently re-ran the affected surface (23 tests) + full
  `hatch run lint` (clean), and traced the `EscalationFiler` wire-contract, the
  `SlackRef`-from-API-response correlation, the env-var constants (agree with T2's selector),
  and the fail-closed/fail-open split against their callers.
- Carried **three low, non-blocking** review notes into `.ai/state.json` (`t3_review_notes`):
  no aggregate message-length cap in `render_question_message`; `_ANSWER_LINE_RE` duplicates
  `issue_io/github.py:23`; the oversized-digit `int()` guard is absent from the parallel
  `issue_io.parse_issue_answers` (same crash still live on the issue path — BL candidate).
- **No BL-35 stale-red** this time — both `architect-review` runs on the SHA resolved SUCCESS.
  Human merged. Synced `main`, pruned the merged branch.

## Next — Task 4: shared `runner.resume_run` seam + `state_io` correlation scan (Coder, **Sonnet**)
Cut a fresh branch off `main`. Two pieces:
- Extract `runner.resume_run(state, resolved_answers, *, budget_usd, loop_name)` from
  `cli.resume`; **re-entry must key on the EXPLICIT applied-answer question-id set the apply
  step returns, NOT a `resolved_by` string match** (finding #4 — `resolved_by` becomes
  provenance-only). Refactor `cli.resume` to read/verify the issue (unchanged) then call the
  seam — exactly **one** resume-execution path. Issue path byte-for-byte unchanged (regression test).
- Add read-only `tools/state_io.find_paused_snapshot_by_slack_thread(message_ts) -> Path | None`:
  plain `state/*/*.json` glob over the **main-checkout** `state/` (finding #1 — NOT worktrees),
  raw-JSON/defensive read tolerant of v4/non-Slack snapshots (finding #9), returns the
  `AWAITING_SLACK` snapshot whose `pending_slack.message_ts` matches, else `None`.

Then green gate → `/critic-gate` → `/ship` (touches `src/` ⇒ `architect-review` applies).
**HITL Gate: NONE OPEN** — a fresh **Sonnet** session may auto-start (`implementing` + gate
NONE OPEN + model matches + clean cursor). An Opus session flags the model mismatch and waits.

## Note for Task 4 (carry-forward from T2/T3, confirmed in T3)
Resume from the actual `awaiting_slack`-named snapshot on disk, **not** from the `snapshot_hint`
string `_pause_for_escalation` hands the filer (always built from `AWAITING_ISSUE` — confirmed
`slack_escalation_filer` accepts-and-ignores it). A Slack pause also leaves a contradictory
`..._awaiting_issue.json` placeholder beside the real `..._awaiting_slack.json`; the T4 scan must
dedupe on the `awaiting_slack` snapshot. Finding #3 (channel from `payload['event']['channel']`)
is **T5**, not T4.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **`/resume` auto-starts here only on Sonnet** — `sprint_status` is `implementing` + gate `NONE OPEN`, so a
  fresh **Sonnet** session starts T4 unattended; a fresh **Opus** session flags the model mismatch and waits.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_failed_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.** (Rebase a stale pushed branch by merging `main` INTO it.)
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1/T2/T3 done+merged; **T4 next**.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).
