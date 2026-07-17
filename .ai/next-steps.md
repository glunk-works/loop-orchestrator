# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `awaiting_architect_review`.**
T1 merged ([#127](https://github.com/glunk-works/loop-engine/pull/127)) ·
T2 merged ([#128](https://github.com/glunk-works/loop-engine/pull/128)) ·
T3 merged ([#131](https://github.com/glunk-works/loop-engine/pull/131)) ·
T4 merged ([#133](https://github.com/glunk-works/loop-engine/pull/133) → squash `ac4923b`) ·
**T5 done, [PR #136](https://github.com/glunk-works/loop-engine/pull/136) open, awaiting the fresh-session Architect Review.** T6 (docs) remains.

## Just done (Coder/Sonnet session, 2026-07-17)
- Implemented **T5**: `slack_control/dispatch.py` gained `dispatch_resume` (mirrors
  `dispatch`'s envelope dedupe + shared `_run_lock`, posts a terminal-status-mapped
  outcome via `send_thread_message`); `slack_control/daemon.py`'s `_handle_request` now
  branches on `request.type` and handles `events_api` message events (FD3 channel guard
  on `payload["event"]["channel"]` → `find_paused_snapshot_by_slack_thread` →
  `parse_thread_answers` → `dispatch_resume`, or a numbering hint if unparseable).
- Ran `/critic-gate` (human-confirmed: `security-critic` + `architect` + `guard-adversary`,
  all three in parallel) on the diff. **Both `security-critic` and `architect` independently
  found the same real bug**: the first-pass fix for T4-review finding #1 (a stale
  `awaiting_slack` snapshot re-matching after a resume) picked "latest snapshot per run
  dir" by **filename**, but `stage_index` is the loop stage position, not a monotonic write
  counter — blast-radius re-entry (`reentry_index`) can re-enter at an *earlier* stage than
  a prior pause, so a later pause can write a numerically *lower*-prefixed file. Re-fixed
  using **mtime** instead of filename, with a regression test reproducing the exact
  backward-reentry shape. `architect` also caught a related distinct-envelope-same-thread
  double-dispatch window, closed with a new `_active_threads` dedupe set on
  `SlackRunDispatcher`. `guard-adversary` found pre-existing blind spots in the *shared*
  guard tests (not exploited by this PR) — noted for a future hardening pass, not fixed
  here (out of scope for T5).
- Pushed as **PR #136** (branch `sprint/41-bl2-t5-slack-resume`, head `b978764`). Green
  gate (`lint` + `format --check` + `test`, 780 passed) is clean. Full critic-gate summary
  posted as a PR comment.

## Next — post the Architect Review on PR #136 (Opus, **fresh session**)
`sprint_status` is deliberately `awaiting_architect_review` (not `implementing`), so a
fresh `/resume` will **state the pick-up point and wait**, not auto-start — this review
needs judgment, not a rubber stamp. Read the diff cold and verify in particular: the mtime
fix actually resolves the backward-reentry bug; the `_active_threads` dedupe actually closes
the double-dispatch window; the `events_api` payload-shape handling in `daemon.py` is
correct. Post via `gh pr review --comment` (**never `--approve`**) with the verbatim
two-line header + attestation from `.ai/context/workflow.md`, against PR #136's current
head commit. **After merge, T6 (docs-only, marks BL-2 complete) is the last task in this
sprint.**

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**
- Candidates for `docs/backlog.md` if T6 doesn't pick them up: two low T4-review notes
  (`cli.resume` lost early `--loop` validation; `_resolve_loop`/`NAMED_LOOPS` duplicated
  across `cli.py`/`runner.py`), three low T3-review notes, and the new guard-adversary
  hardening item (shared boundary-guard blind spots on `.open()`-as-attribute,
  `os.popen`/`os.posix_spawn`, `importlib.import_module`).

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **This review is NOT auto-started** — `sprint_status` isn't `implementing`, so `/resume`
  waits. That's intentional for a review requiring judgment.
- **Stale-red `architect-review` (BL-35):** every `src/` PR gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_failed_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.** (Rebase a stale pushed branch by merging `main` INTO it.)
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1–T5 done; **T5 review next, then T6**.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).
- [PR #136](https://github.com/glunk-works/loop-engine/pull/136) — T5's diff + full critic-gate findings/fixes in the comment thread.
