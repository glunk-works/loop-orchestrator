# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `implementing`.**
T1 merged ([PR #127](https://github.com/glunk-works/loop-engine/pull/127) → `55d6d9d`).
T2 merged ([PR #128](https://github.com/glunk-works/loop-engine/pull/128) → squash `cbc82ac`).
**T3 is open as [PR #131](https://github.com/glunk-works/loop-engine/pull/131) → `bda41a2`, awaiting the Architect Review.**

## Just done (Sonnet/Coder session, 2026-07-17)
- Implemented **Task 3**: `tools/slack_io/escalation.py` — `slack_escalation_filer` (fail-closed
  `EscalationFiler`, builds `SlackRef` from the API response's `channel`/`ts`, not the raw
  configured value), pure `render_question_message` (mrkdwn-escaped + length-capped, finding #7),
  `send_thread_message` (fail-open threaded post, finding #5, for T5), pure count-aware
  `parse_thread_answers` (finding #6). All exported from `tools/slack_io/__init__.py`.
- Extended `tests/tools/test_slack_io_boundaries.py` (escalation.py pinned into the boundary
  sweep) and added `tests/tools/test_slack_io_escalation.py`. Green gate: lint/format clean,
  740 tests passing.
- Ran **`/critic-gate`** (`architect` + `security-critic`, both confirmed by the human):
  `architect` — clean, no correctness findings, confirmed wire-compatibility with T2's already-landed
  `build_escalation_filer_from_env()` selector. `security-critic` — one LOW finding, **fixed**: an
  adversarial >4300-digit reply line could raise `ValueError` in `parse_thread_answers`'s `int()` call
  (Python's integer-string-conversion limit), breaking the parser's pure/total contract; now caught and
  treated as a non-match, with a regression test. Re-gated green (740 passed) after the fix.
- **Shipped:** committed on `sprint/41-bl2-t3-slack-filer` (cut off `main`, HEAD `b8ed616`), pushed,
  opened [PR #131](https://github.com/glunk-works/loop-engine/pull/131) against `main`.

## Next — post the Architect Review (Opus, fresh session)
`/handoff` (this session, done) → new **Opus** session → `/resume` → `/code-review` → post the
Architect Review on **PR #131** with the verbatim header + attestation
(`.ai/context/workflow.md`). The `architect-review` check is currently **red** on this PR pending
that review (it touches `src/`). Watch for the **BL-35 stale-red trap** (see Gotchas below).

**HITL Gate: OPEN** — PR #131 is pushed and awaiting the fresh-session Architect Review. A fresh
Sonnet session must **wait**, not auto-start T4, until this gate clears.

## Note for Task 4 (carry-forward from T2, confirmed in T3)
The filer/daemon must resume from the actual `awaiting_slack`-named snapshot on disk, **not** from the
`snapshot_hint` string `_pause_for_escalation` hands the filer (always built from `AWAITING_ISSUE`) —
confirmed in T3 that `slack_escalation_filer` correctly accepts-and-ignores this hint. A Slack pause also
leaves a contradictory `..._awaiting_issue.json` placeholder beside the real `..._awaiting_slack.json`;
the T4 `state/*/*.json` scan (findings #1/#9) must dedupe on the `awaiting_slack` snapshot. Findings
#1/#4/#9 (T4), #3 (T5) are **not** T3 — they weren't touched this session.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **`/resume` waits here** — `hitl_gate` is `OPEN` (PR #131 awaiting Architect Review), so a fresh
  session of either model states the pick-up point and waits rather than auto-starting.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_failed_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.** (Rebase a stale pushed branch by merging `main` INTO it.)
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1/T2 done+merged; **T3 open as PR #131**.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).
