# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `implementing`.**
Task 1 is merged ([PR #127](https://github.com/glunk-works/loop-engine/pull/127) → `55d6d9d` on `main`).
Task 2 is **coded, green-gated, and critic-passed** on branch `sprint/41-bl2-t2-escalation-seam`
(3 commits ahead of `main`) — **not yet pushed, no PR open.**

## Just done (Sonnet coding session, 2026-07-17)
- Implemented **Task 2** on `sprint/41-bl2-t2-escalation-seam`: generalized the escalation seam —
  `_pause_for_issue` → `_pause_for_escalation`, added `EscalationFiler`/`EscalationRef = IssueRef | SlackRef`
  (return-type alias in `core/engine.py` only — finding #12), ref-type dispatch to the correct terminal
  status/field, `build_escalation_filer_from_env()` (mirrors `build_notifier_from_env`, fails closed on
  `=slack` with missing Slack creds — finding #10), and `AWAITING_SLACK` wired through `notify.py` /
  `graph_engine.py` / `cli.py` (exit code **5**). Default (`issue`/unset) transport confirmed byte-for-byte
  unchanged. Also fixed `tools/slack_io/format.py`'s `format_event` (not an explicit T2 target file, but
  required — an existing all-kinds coverage test would otherwise hit its `unhandled EventKind` raise).
  Commit `5c04407`.
- **Green gate:** `hatch run test` (724 passed), `hatch run lint` (clean), `hatch run format` (clean).
- **`/critic-gate`** ran `architect` only (proposed `security-critic` too but the human picked `architect`
  alone — T2 has no untrusted-input taint flow yet, that lands in T3/T5). **Verdict: clean**, no blockers.
  One cosmetic finding (stale `_pause_for_issue` docstring references) fixed in `bdd00b8`. Two informational
  findings accepted-with-reason, not fixed: the pre-file placeholder snapshot is always named
  `..._awaiting_issue.json` even on a Slack-bound pause (unreachable/untested until the real Slack filer
  exists — **note for T3** below); the forward-reference import of the not-yet-existing
  `tools/slack_io/escalation` module is a deliberate, correctly-scoped staged-rollout pattern (mirrors the
  existing F7 posture).
- Also committed the `.ai/next-steps.md` drift left over from the prior (Opus review) session — it had been
  regenerated but never committed. Commit `6e74093`.

## Next — push and open the T2 PR (Coder, **Sonnet**)
Run `/ship`: push `sprint/41-bl2-t2-escalation-seam` and open a PR against `main` (title ≤72 bytes,
`architect-review` will apply — this PR touches `src/`). Once the PR is open, it needs the fresh-session
Architect Review: `/handoff` → new session → `/resume` → `/code-review` → post via
`gh pr review --comment` (never `--approve`). **HITL Gate: NONE OPEN.**

## Note for Task 3 (Slack filer)
When `tools/slack_io/escalation.py` lands, the filer/daemon must resume from the actual `awaiting_slack`-named
snapshot on disk, **not** from the `snapshot_hint` string `_pause_for_escalation` hands it — that hint is
always built from `RunStatus.AWAITING_ISSUE` (the pre-file placeholder can't know the transport ahead of a
possibly-raising filer call). See `t2_critic_notes_for_t3` in `.ai/state.json` for the full reasoning.

## Coder: read these before touching T3+ (all folded into the plan)
- **#5** add `tools/slack_io.send_thread_message`. **#6** `parse_thread_answers` is count-aware
  (`{1: body}` only when `unresolved_count == 1`). **#7** escape mrkdwn + truncate question text.
- Findings #1/#4/#9 (T4), #3 (T5) are **not** T3 — don't pull them forward.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **`/resume` auto-starts here only on Sonnet** — `sprint_status` is `implementing` + gate `NONE OPEN`, so a
  fresh **Sonnet** session runs `/ship` unattended; a fresh **Opus** session flags the model mismatch and waits.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.**
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1 done+merged; T2 code done, PR not yet open; T3 next after.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).

Committed this session: `5c04407` (Task 2), `bdd00b8` (critic-gate fix) on `sprint/41-bl2-t2-escalation-seam`,
not yet pushed. No PR open yet for T2.
