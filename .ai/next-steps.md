# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `awaiting_architect_review`.**
T1 merged ([PR #127](https://github.com/glunk-works/loop-engine/pull/127) → `55d6d9d`).
T2 merged ([PR #128](https://github.com/glunk-works/loop-engine/pull/128) → squash `cbc82ac`).
T3 merged ([PR #131](https://github.com/glunk-works/loop-engine/pull/131) → squash `954572a`) — Architect-Reviewed clean.
**T4 shipped: [PR #133](https://github.com/glunk-works/loop-engine/pull/133) (branch `sprint/41-bl2-t4-resume-seam` → `e346f3c`) — awaiting the fresh-session Architect Review.**

## Just done (Coder/Sonnet session, 2026-07-17)
- Extracted `runner.resume_run(state, resolved_answers, *, resolved_by, budget_usd, loop_name)`
  from `cli.resume` — the shared resume-execution seam T5's Slack path will also call.
  Re-entry keys on the **explicit resolved question-id set** `core.engine.apply_resolved_answers`
  returns, never a `resolved_by` string match (finding #4); `resolved_by` is provenance-only.
- Refactored `cli.resume` to keep its issue-specific read/verify and call the seam — issue-path
  behavior is regression-tested byte-for-byte unchanged. Retired the now-superseded
  `issue_io.apply_answers_to_questions`.
- Added `tools/state_io/reader.py::find_paused_snapshot_by_slack_thread` — read-only,
  raw-JSON-defensive main-checkout `state/*/*.json` scan (T5 dependency, landed unwired).
- Green gate clean (755 tests, lint, format). `/critic-gate` (architect pass) found one real
  issue — `cli.resume`'s `except ValueError` was catching more than the intended
  "no fold_answers persona" guard, which could relabel a deep loop-internal `ValueError` as
  `typer.BadParameter` (exit 2, colliding with `AWAITING_ISSUE`'s exit code). Fixed with a
  dedicated `runner.LoopHasNoFoldAnswersPersonaError`, regression-tested, included in PR #133.
- Shipped via `/ship`: PR #133 open against `main`, labeled `feature`/`area/core`/`area/tools`.

## Next — post the Architect Review on PR #133 (Architect, **Opus**, fresh session)
This session authored the diff and cannot review it. In a **new** Opus session: `/resume` →
`/code-review` the PR #133 diff → post with `gh pr review --comment` (never `--approve`) against
its current head commit, opening with the verbatim header + attestation block from
`.ai/context/workflow.md`. Once merged, **T5 is next** (Coder, Sonnet): `slack_control/dispatch.py`
gains `dispatch_resume(...)` calling `runner.resume_run`, and `slack_control/daemon.py` extends
`_handle_request` to correlate an `events_api` thread reply via
`state_io.find_paused_snapshot_by_slack_thread` (see `.ai/state.json`'s `t5_next` pointer for
findings #3/#11 detail).

## Open decisions left for the owner (do not silently resolve)
- **BL-24 — retire or verify `trigger/`** (dead code carrying `LOOP_ENGINE_WEBHOOK_SECRET`). **Still open.**
- **BL-35 — which stale-red fix, if any** (owner chose file-don't-fix; manual `gh run rerun` stays the workaround). **Not decided.**
- **Three low, non-blocking T3-review notes** (aggregate Slack message-length cap; duplicated
  `_ANSWER_LINE_RE`; the oversized-digit `int()` guard missing from `issue_io.parse_issue_answers`)
  are still unaddressed — candidates for `docs/backlog.md` if T6 doesn't pick them up.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **This cursor does not auto-start** — `sprint_status` is `awaiting_architect_review`, not
  `implementing`, so `/resume` states the pick-up point and waits regardless of model/gate state.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_failed_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.** (Rebase a stale pushed branch by merging `main` INTO it.)
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1–T4 done; **T4's architect-review next, then T5**.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).
- [PR #133](https://github.com/glunk-works/loop-engine/pull/133) — T4, open, awaiting architect-review.
