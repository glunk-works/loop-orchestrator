# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `implementing`.**
T1 merged ([PR #127](https://github.com/glunk-works/loop-engine/pull/127) → `55d6d9d`).
T2 merged ([PR #128](https://github.com/glunk-works/loop-engine/pull/128) → squash `cbc82ac`) —
Architect-Reviewed clean, all checks green. **T3 is next: Sonnet/Coder.**

## Just done (Opus/Architect review session, 2026-07-17)
- Posted the fresh-session **Architect Review** on PR #128 (verbatim header + attestation),
  verdict **clean, no blockers**; independently re-ran the affected surface (105 tests, lint clean).
- Cleared a `.ai/next-steps.md`-only **merge conflict** with `main` (PR #129 synced the cursor) the
  sanctioned way — merged `main` INTO the branch (no force-push), re-posted the review against the new
  head; `src/` diff byte-identical.
- Hit and resolved the **BL-35 stale-red trap** on #128 (push-fired `architect-review` failed pre-review,
  review-fired one passed ⇒ `BLOCKED`+rollup `FAILURE`); `gh run rerun` the **old** failed run flipped it
  green. Human merged.
- Two **non-blocking** review notes carried into `.ai/state.json`: the T4 `state/*/*.json` scan must dedupe
  on the `awaiting_slack` snapshot (a Slack pause leaves an `..._awaiting_issue.json` placeholder too); and
  T6 docs must add exit code **5** (`AWAITING_SLACK`) to CLAUDE.md's exit-codes list.

## Next — Task 3: Slack filer/renderer/parser (Coder, **Sonnet**)
Cut a fresh branch off `main`. Add `tools/slack_io/escalation.py`:
- `slack_escalation_filer(state, questions, snapshot_hint) -> SlackRef` — pure `render_question_message`
  (numbered `[origin_stage] text`, **mrkdwn-escaped + length-capped**, finding #7), posts un-threaded via
  bot-token `WebClient.chat.postMessage`, returns `SlackRef(channel_id, message_ts)`.
- `send_thread_message(*, bot_token, channel_id, thread_ts, text)` — finding #5, fail-open, for T5.
- pure count-aware `parse_thread_answers(text, unresolved_count) -> dict[int,str]` — finding #6: bare body
  ⇒ `{1: body}` **only when `unresolved_count == 1`**, else `{}`; out-of-range numbers ignored; no I/O.

`slack_sdk` stays **function-scoped + sole importer**; no `keyring`; no direct file write. Extend
`tests/tools/test_slack_io_boundaries.py`; subprocess surfaces stay **five**. Then green gate → `/critic-gate`
→ `/ship` (PR touches `src/` ⇒ `architect-review` applies). **HITL Gate: NONE OPEN** — a fresh Sonnet session
may auto-start (`implementing` + gate NONE OPEN + model matches).

## Note for Task 3 (carry-forward from T2)
The filer/daemon must resume from the actual `awaiting_slack`-named snapshot on disk, **not** from the
`snapshot_hint` string `_pause_for_escalation` hands it (always built from `AWAITING_ISSUE` — the pre-file
placeholder can't know the transport ahead of a possibly-raising filer call). Findings #1/#4/#9 (T4), #3 (T5)
are **not** T3 — don't pull them forward.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **`/resume` auto-starts here only on Sonnet** — `sprint_status` is `implementing` + gate `NONE OPEN`, so a
  fresh **Sonnet** session starts T3 unattended; a fresh **Opus** session flags the model mismatch and waits.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_failed_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.** (Rebase a stale pushed branch by merging `main` INTO it.)
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1/T2 done+merged; **T3 next**.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).
