# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `implementing`.**
T1 merged ([#127](https://github.com/glunk-works/loop-engine/pull/127)) ·
T2 merged ([#128](https://github.com/glunk-works/loop-engine/pull/128)) ·
T3 merged ([#131](https://github.com/glunk-works/loop-engine/pull/131)) ·
**T4 merged ([#133](https://github.com/glunk-works/loop-engine/pull/133) → squash `ac4923b`).**
**T5 is next** (Coder, **Sonnet**). T6 (docs) remains.

## Just done (Architect/Opus review session, 2026-07-17)
- Posted the **T4 Architect Review** on PR #133 (fresh Opus session, did not author the
  diff) — verdict **APPROVE**, 3 non-blocking notes. `gh pr review --comment`, verbatim
  header + attestation. PR **merged** as squash `ac4923b`; pruned the T4 branch.
- The refactor is sound: finding #4 (re-entry on the explicit resolved-id set, not a
  `resolved_by` match) and the critic-gate fix (`LoopHasNoFoldAnswersPersonaError` narrowing)
  are both correctly implemented; issue-path behavior is equivalent.
- **One T5-facing note to fold in (review finding #1, medium):** `reader.find_paused_snapshot_by_slack_thread`
  can re-match an **already-resumed thread** (the paused `NN_awaiting_slack.json` is never
  rewritten), so a second reply would double-resume. Close it in T5 — detail + fix options in
  `.ai/state.json`'s `t5_reader_contract_note`.

## Next — implement T5 (Coder, **Sonnet**, fresh session)
`.ai/state.json` `sprint_status` is `implementing` with `hitl_gate: NONE OPEN`, so a fresh
**Sonnet** `/resume` **auto-starts** T5. In short: `slack_control/dispatch.py` gains
`dispatch_resume(...)` calling `runner.resume_run` on the worker thread under the pass-2
`_run_lock`; `slack_control/daemon.py`'s `_handle_request` branches on `request.type` to
handle `events_api` message events via the FD3 channel guard →
`state_io.reader.find_paused_snapshot_by_slack_thread(thread_ts)` → `parse_thread_answers` →
`dispatch_resume`. **Finding #3:** an `events_api` payload reads channel from
`payload['event']['channel']` (NOT `payload['channel_id']`). **Finding #11:** map outcome
messages per terminal status, treating AWAITING_SLACK-again as a re-pause (don't re-post
questions). Fold in review finding #1 above. Green gate + `/critic-gate` before `/handoff`
to the T5 Architect Review. **This is a Sonnet task — if you're on Opus, that's fine for
mechanical work, but the review of T5 must be a fresh Opus session.**

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**
- **Two low T4-review notes** (cli.resume lost early `--loop` validation; `_resolve_loop`/`NAMED_LOOPS`
  duplicated across `cli.py`/`runner.py`) and **three low T3-review notes** — candidates for
  `docs/backlog.md` if T5/T6 don't pick them up.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Auto-start applies for T5** — `sprint_status` is `implementing`, gate `NONE OPEN`; a clean fresh **Sonnet** `/resume` starts it unattended.
- **Stale-red `architect-review` (BL-35):** every `src/` PR gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_failed_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.** (Rebase a stale pushed branch by merging `main` INTO it.)
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1–T4 done+merged; **T5 next, then T6**.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).
