# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `awaiting_architect_review`.**
Task 1 is implemented, green-gated, critic-passed, and open as [PR #127](https://github.com/glunk-works/loop-engine/pull/127). It needs the fresh-session `architect-review` CI gate next. Review = **Opus/Architect**.

## Just done (Sonnet coding session, 2026-07-17)
- Implemented **Task 1** on `sprint/41-bl2-slack-escalation`: added `SlackRef(channel_id, message_ts)`,
  `State.pending_slack: SlackRef | None`, `RunStatus.AWAITING_SLACK`, bumped `CURRENT_SCHEMA_VERSION` 4→5,
  and fixed **finding #8** (added `4` to the `migrate_state_payload` upgrade set) — commit `95add34`.
- Updated `tests/core/test_state.py`: refreshed the `VALID_PAYLOAD` fixture to v5, added a v4→v5 migration
  round-trip test, a `pending_slack`-set validation test, and a `SlackRef` extras-rejection test.
- **Green gate:** `hatch run test` (712 passed), `hatch run lint` (clean), `hatch run format` (no changes).
- **`/critic-gate`** ran with `architect` only (proposed `security-critic` too but skipped it — no taint/trust-boundary
  surface in a pure schema/enum diff). **Zero findings** — off-by-one genuinely fixed, `extra="forbid"` intact on
  `State` and `SlackRef`, no scope creep into T2/T3. One non-blocking note carried forward for T2 below.
- Pushed and opened **[PR #127](https://github.com/glunk-works/loop-engine/pull/127)** (`sprint/41-bl2-slack-escalation` → `main`).

## Next — post the Architect Review (Opus, FRESH session)
`/resume` → `/code-review` the PR #127 diff → post the review with the **verbatim two-line header + attestation
block** from `.ai/context/workflow.md` (`**Opus/Architect HITL review (automated)**` + the fresh-session
attestation line) via `gh pr review --comment` (**never `--approve`**). Watch **BL-35** (stale-red trap: `BLOCKED` +
rollup **FAILURE** ⇒ `gh run rerun` the **old** run, not a new push). **HITL Gate: NONE OPEN** — planning is
already approved; the live gate here is the CI check itself, not a plan decision, which is why `sprint_status`
is `awaiting_architect_review` rather than `implementing` (so `/resume` waits regardless of model).

After the human merges PR #127: cut a fresh branch off updated `main` for **Task 2** (`EscalationFiler` seam in
`core/engine.py` + `AWAITING_SLACK` terminal plumbing + env-selected filer, default=issue, zero behavior change) —
Sonnet/Coder's job. **Carry forward from T1's critic pass:** when `AWAITING_SLACK` becomes live, extend
`cli.py`'s `_EXIT_CODES` and `graph_engine.py`'s `_STATUS_TO_EVENT` (+ a new `EventKind` in `core/notify.py`)
in lockstep, or a live `AWAITING_SLACK` pause `KeyError`s.

## Coder: read these before touching T2+ (all folded into the plan)
- **#1** scan root = main-checkout `state/`, plain `state/*/*.json` glob (NOT worktrees).
- **#2** the escalation filer is *not* threaded from entrypoints today — add `build_escalation_filer_from_env()`
  called **inside `run_graph_loop` when `issue_filer is None`**, mirroring `build_notifier_from_env`.
- **#3** `events_api` message payload uses `payload["event"]["channel"]` (NOT `["channel_id"]`); branch on `request.type`.
- **#4** compute the just-resolved set from **applied answer ids**, not a `resolved_by` string match.
- **#5** no threaded-post primitive exists — add `tools/slack_io.send_thread_message`.
- **#6** `parse_thread_answers` is **count-aware** (`{1: body}` only when `unresolved_count == 1`).
- **#7** escape mrkdwn + truncate question text. **#8** migration off-by-one — **fixed in T1**. **#10** filer fails **closed** at build.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **`/resume` waits here regardless of model** — `sprint_status` is `awaiting_architect_review`, not `implementing`,
  so auto-start does not apply; a fresh session (Opus or Sonnet) states the pick-up point and waits for the review.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.**
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [PR #127](https://github.com/glunk-works/loop-engine/pull/127) — T1, base `main`, awaiting fresh-session `architect-review`.
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline).
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).

Committed this session: `95add34` (Task 1) on `sprint/41-bl2-slack-escalation`, pushed. PR #127 open against `main`.
