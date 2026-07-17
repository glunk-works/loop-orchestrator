# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `implementing`.**
Task 1 is **merged** ([PR #127](https://github.com/glunk-works/loop-engine/pull/127) → squash `55d6d9d` on `main`). Next up is **Task 2**, a Coder task → **Sonnet**.

## Just done (Opus/Architect review session, 2026-07-17)
- Posted the fresh-session **Architect Review** on [PR #127](https://github.com/glunk-works/loop-engine/pull/127) via `gh pr review --comment` (verbatim header + attestation). **Verdict: approve.**
  Independently confirmed finding #8 (migration off-by-one) genuinely fixed, `extra="forbid"` intact on `State` + new `SlackRef`, `AWAITING_SLACK`/`pending_slack` added but **not** wired live (correctly scoped, no KeyError risk).
- Watched **BL-35**: two `architect-review` check-runs on head SHA `fda6689` (pre-review `fail 4s` + post-review `pass 4s`); it cleared on its own once **both** check-runs on the head SHA reported success (lag, not a stale-red needing a rerun).
- **PR #127 merged** by the owner → `55d6d9d` on `main`; local `main` synced.
- Preflight: ruleset healthy (4 rule types, 8 required checks); no stale branches to prune.

## Next — implement Task 2 (Coder, **Sonnet**)
Cut a fresh branch off updated `main` (`sprint/41-bl2-t2-escalation-seam`) and implement **Task 2**: generalize the escalation
seam so `core/` is transport-agnostic — rename `_pause_for_issue` → `_pause_for_escalation`, add `EscalationFiler` +
`EscalationRef = IssueRef | SlackRef` (return-type alias in `core/engine.py` **only**; `State` keeps the two separate
`pending_*` fields — **finding #12**), select terminal status/field by ref type, and wire `AWAITING_SLACK` through
`notify.py` / `graph_engine.py` / `cli.py` (exit code **5**). **Default (`issue`/unset) must be byte-for-byte the current
behavior.** Then green gate → `/critic-gate` → `/handoff` for the Opus architect-review. **HITL Gate: NONE OPEN.**

## Coder: read these before touching T2 (all folded into the plan)
- **#2** the filer is **not** threaded from entrypoints — add `build_escalation_filer_from_env()` in `graph_engine` and
  call it **inside `run_graph_loop` when `issue_filer is None`**, mirroring `build_notifier_from_env`.
- **#10** `build_escalation_filer_from_env()` fails **closed**: `=slack` but `LOOP_ENGINE_SLACK_BOT_TOKEN`/`_CHANNEL` unset ⇒ **raise**.
- **#12** `EscalationRef` is a return-type union in `core/engine.py` only; **no** union field on `State`.
- Keep the **F4 persist-before-file** ordering (pre-file finalize uses the correct status for the selected transport).
- `core/` must import **no** concrete `tools/slack_io`/`tools/issue_io` transport (only the protocol + the `State` union). The Slack filer itself lands in **T3**.
- Findings #1/#4 (T4), #3 (T5), #5/#6/#7 (T3) are **not** T2 — don't pull them forward.

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **`/resume` auto-starts here only on Sonnet** — `sprint_status` is `implementing` + gate `NONE OPEN`, so a fresh **Sonnet** session starts T2 unattended; a fresh **Opus** session flags the model mismatch and waits.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` + rollup **FAILURE** = stale red ⇒ `gh run rerun <old_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.**
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1 done+merged; T2 next.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).

Merged this session: **PR #127 → `55d6d9d`** on `main` (T1). Branch for T2: cut fresh off `main`.
