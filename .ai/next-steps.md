# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `implementing`.**
The sprint plan is **written and owner-approved**; implementation is the next work. Coding = **Sonnet/Coder**.

## Just done (Opus planning session, 2026-07-17)
- **Planned sprint 41** end to end and wrote [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md).
  Three design forks were decided via HITL gates and locked as **FD1–FD3**:
  - **FD1** correlation = the Slack message **thread (`thread_ts`)**.
  - **FD2** answer resolved by an **on-demand snapshot scan** + **in-process resume** (via the pass-2 dispatcher/`_run_lock`).
  - **FD3** transport chosen by an **exclusive env var `LOOP_ENGINE_ESCALATION_TRANSPORT`** (default `issue` ⇒ zero behavior change).
  - Derived + owner-approved: **FD4** transport-agnostic `EscalationFiler` seam in `core/`; **FD5** distinct
    **`AWAITING_SLACK`** status + **exit code 5**; **FD6** module layout.
- **Self-reviewed the plan** ("where will a coder trip?") and folded **12 findings** back in (each tagged
  `finding #N` in the plan). The standout, **#1**, corrected a *factual error in my own draft*: snapshots are
  pinned to the **main-checkout `state/`**, NOT the worktrees (verified vs `tools/state_io/writer.py`), so the
  correlation scan is a plain `state/*/*.json` glob — not worktree traversal.
- Owner **approved both open calls**: exit-code-5 (FD5) and #10 fail-closed filer build.

## Next — implement Task 1 (Sonnet)
Branch **`sprint/41-bl2-slack-escalation`** is cut from `main` and the approved plan + this cursor are committed on it.
Implement **T1**: `SlackRef` + `State.pending_slack` + `RunStatus.AWAITING_SLACK` + bump `CURRENT_SCHEMA_VERSION` 4→5 +
extend `migrate_state_payload` (**finding #8: ADD `4` to the `(1,2,3)` upgrade set**, or every v4 snapshot raises) +
update the `tests/core/test_state.py` v4 fixture. Keep `extra="forbid"`. T1 is the **pure state/enum layer only**
(event-kind / exit-code plumbing is T2). Green gate (`hatch run test` + `lint`) → open T1's own PR based on `main`.
Full spec in the plan. **HITL Gate: NONE OPEN** — planning is complete; the next gate is T1's fresh-session `architect-review`.

## Coder: read these before touching code (all folded into the plan)
- **#1** scan root = main-checkout `state/`, plain `state/*/*.json` glob (NOT worktrees).
- **#2** the escalation filer is *not* threaded from entrypoints today — add `build_escalation_filer_from_env()`
  called **inside `run_graph_loop` when `issue_filer is None`**, mirroring `build_notifier_from_env`.
- **#3** `events_api` message payload uses `payload["event"]["channel"]` (NOT `["channel_id"]`); branch on `request.type`.
- **#4** compute the just-resolved set from **applied answer ids**, not a `resolved_by` string match.
- **#5** no threaded-post primitive exists — add `tools/slack_io.send_thread_message`.
- **#6** `parse_thread_answers` is **count-aware** (`{1: body}` only when `unresolved_count == 1`).
- **#7** escape mrkdwn + truncate question text. **#8** migration off-by-one. **#10** filer fails **closed** at build.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **`/resume` may auto-start** on a clean cursor (`hitl_gate` NONE OPEN + `implementing` + model == `sonnet` + no drift).
  The branch is cut and the plan is committed, so a fresh **Sonnet** session should auto-start T1; a session on the
  wrong model (Opus) will flag the mismatch and wait.
- **Stale-red `architect-review` (BL-35):** every `src/` PR (T1–T5) gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait. Docs-only T6 exempt.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Cut sprint 41's branch fresh off `main`**; never commit to `main`, never merge, never force-push.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). **Read first.**
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).

Committed this session: the sprint 41 plan + this cursor, on `sprint/41-bl2-slack-escalation` (not yet pushed). No open PR.
