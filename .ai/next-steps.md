# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `awaiting_architect_review`.**
Task 1 is merged ([PR #127](https://github.com/glunk-works/loop-engine/pull/127) → `55d6d9d` on `main`).
Task 2 is implemented, green-gated, critic-passed, and open as
[PR #128](https://github.com/glunk-works/loop-engine/pull/128). It needs the fresh-session
`architect-review` CI gate next. Review = **Opus/Architect**.

## Just done (Sonnet coding session, 2026-07-17)
- Implemented **Task 2** on `sprint/41-bl2-t2-escalation-seam`: generalized the escalation seam —
  `_pause_for_issue` → `_pause_for_escalation`, added `EscalationFiler`/`EscalationRef = IssueRef | SlackRef`
  (return-type alias in `core/engine.py` only — finding #12), ref-type dispatch to the correct terminal
  status/field, `build_escalation_filer_from_env()` (mirrors `build_notifier_from_env`, fails closed on
  `=slack` with missing Slack creds — finding #10), and `AWAITING_SLACK` wired through `notify.py` /
  `graph_engine.py` / `cli.py` (exit code **5**). Default (`issue`/unset) transport confirmed byte-for-byte
  unchanged. Also fixed `tools/slack_io/format.py`'s `format_event` (not an explicit T2 target file, but
  required — an existing all-kinds coverage test would otherwise hit its `unhandled EventKind` raise).
- **Green gate:** `hatch run test` (724 passed), `hatch run lint` (clean), `hatch run format` (clean).
- **`/critic-gate`** ran `architect` only (proposed `security-critic` too but the human picked `architect`
  alone — T2 has no untrusted-input taint flow yet, that lands in T3/T5). **Verdict: clean**, no blockers.
  One cosmetic finding (stale `_pause_for_issue` docstring references) fixed. Two informational findings
  accepted-with-reason, not fixed — see `t2_critic_notes_for_t3` in `.ai/state.json` (the pre-file placeholder
  snapshot naming gap, and the deliberate forward-reference import of the not-yet-existing Slack filer module).
- Pushed and opened **[PR #128](https://github.com/glunk-works/loop-engine/pull/128)**
  (`sprint/41-bl2-t2-escalation-seam` → `main`).

## Next — post the Architect Review (Opus, FRESH session)
`/resume` → `/code-review` the PR #128 diff → post the review with the **verbatim two-line header +
attestation block** from `.ai/context/workflow.md` (`**Opus/Architect HITL review (automated)**` + the
fresh-session attestation line) via `gh pr review --comment` (**never `--approve`**). Watch **BL-35**
(stale-red trap: `BLOCKED` + rollup **FAILURE** ⇒ `gh run rerun` the **old** run, not a new push).
**HITL Gate: NONE OPEN** — planning is already approved; the live gate here is the CI check itself, not
a plan decision, which is why `sprint_status` is `awaiting_architect_review` rather than `implementing`
(so `/resume` waits regardless of model).

After the human merges PR #128: cut a fresh branch off updated `main` for **Task 3** — the Slack escalation
filer (outbound) + pure question rendering + pure thread-answer parser (`tools/slack_io/escalation.py`,
findings #5/#6/#7) — Sonnet/Coder's job.

## Note for Task 3 (Slack filer)
When `tools/slack_io/escalation.py` lands, the filer/daemon must resume from the actual `awaiting_slack`-named
snapshot on disk, **not** from the `snapshot_hint` string `_pause_for_escalation` hands it — that hint is
always built from `RunStatus.AWAITING_ISSUE` (the pre-file placeholder can't know the transport ahead of a
possibly-raising filer call). See `t2_critic_notes_for_t3` in `.ai/state.json` for the full reasoning.

## Coder: read these before touching T3 (all folded into the plan)
- **#5** add `tools/slack_io.send_thread_message`. **#6** `parse_thread_answers` is count-aware
  (`{1: body}` only when `unresolved_count == 1`). **#7** escape mrkdwn + truncate question text.
- Findings #1/#4/#9 (T4), #3 (T5) are **not** T3 — don't pull them forward.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **`/resume` waits here regardless of model** — `sprint_status` is `awaiting_architect_review`, not
  `implementing`, so auto-start does not apply; a fresh session (Opus or Sonnet) states the pick-up point
  and waits for the review.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.**
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [PR #128](https://github.com/glunk-works/loop-engine/pull/128) — T2, base `main`, awaiting fresh-session `architect-review`.
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1/T2 done; T3 next.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).

Committed this session: `5c04407`, `bdd00b8` (Task 2) on `sprint/41-bl2-t2-escalation-seam`, pushed.
PR #128 open against `main`.
