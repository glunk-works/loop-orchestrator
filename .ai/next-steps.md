# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 41 — BL-2 pass 3 of 3 (Slack escalation round-trip) — `awaiting_merge`.**
Task 1 is merged ([PR #127](https://github.com/glunk-works/loop-engine/pull/127) → `55d6d9d` on `main`).
Task 2 is implemented, green-gated, critic-passed, **Architect-Reviewed (clean, no blockers)**, and open as
[PR #128](https://github.com/glunk-works/loop-engine/pull/128) with **all 8 required checks green**. It now
awaits the **human merge** (the approval). After merge → Task 3.

## Just done (Opus/Architect review session, 2026-07-17)
- **Posted the fresh-session Architect Review** on [PR #128](https://github.com/glunk-works/loop-engine/pull/128)
  via `gh pr review --comment` (verbatim `**Opus/Architect HITL review (automated)**` + attestation header).
  **Verdict: clean, no blockers.** Independently re-ran the affected surface (105 tests pass, lint clean).
  `architect-review` went **SUCCESS**; all 8 required checks green. No BL-35 stale-red.
- Two **non-blocking** review notes (in the PR review body, not defects in shipped behavior):
  **(1)** a Slack pause leaves a contradictory `..._awaiting_issue.json` placeholder beside the real
  `..._awaiting_slack.json` — structurally unavoidable here; **the T4 `state/*/*.json` scan (findings #1/#9)
  must dedupe on the awaiting_slack snapshot.** **(2)** CLAUDE.md's exit-codes list still says `0/2/3/4` —
  add `5` (`AWAITING_SLACK`) in the **T6 docs task** (exit 5 unreachable until Slack goes live).
- Merged `origin/main` (#129, a docs-cursor sync) into the branch to clear a `.ai/next-steps.md`-only
  conflict — no `src/` conflict. Re-posted the Architect Review against the new head after the merge push.

## T2 recap (Sonnet coding session, 2026-07-17)
- Generalized the escalation seam — `_pause_for_issue` → `_pause_for_escalation`,
  `EscalationFiler`/`EscalationRef = IssueRef | SlackRef` (return-type alias in `core/engine.py` only —
  finding #12), ref-type dispatch to the correct terminal status/field, `build_escalation_filer_from_env()`
  (mirrors `build_notifier_from_env`, fails closed on `=slack` with missing Slack creds — finding #10), and
  `AWAITING_SLACK` wired through `notify.py` / `graph_engine.py` / `cli.py` (exit code **5**). Default
  (`issue`/unset) transport confirmed byte-for-byte unchanged. Commits `5c04407`, `bdd00b8`.

## Next — after the human merges PR #128: Task 3 (Coder, **Sonnet**)
Cut a fresh branch off updated `main` for **Task 3** — the Slack escalation filer (outbound) + pure question
rendering + pure thread-answer parser (`tools/slack_io/escalation.py`, findings #5/#6/#7). Sonnet/Coder's job.
**HITL Gate: NONE OPEN.**

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
- **`/resume` waits here regardless of model** — `sprint_status` is `awaiting_merge`, not `implementing`,
  so auto-start does not apply; a fresh session states the pick-up point and waits for the human merge.
- **Stale-red `architect-review` (BL-35):** every `src/` PR here gets two check-runs on one SHA; `BLOCKED` +
  rollup **FAILURE** = stale red ⇒ `gh run rerun <old_run_id>`; `BLOCKED` + rollup **SUCCESS** = lag, wait.
- **PR title:** `wc -c` the byte count (≤72) AND re-read the text before `gh pr create/edit`.
- **Never commit to `main`, never merge, never force-push.** (Rebase a stale pushed branch by merging `main` INTO it.)
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [PR #128](https://github.com/glunk-works/loop-engine/pull/128) — T2, base `main`, Architect-Reviewed clean, all checks green, **awaiting human merge**.
- [`sprints/41_bl2_slack_escalation/sprint_plan.md`](../sprints/41_bl2_slack_escalation/sprint_plan.md) — the approved plan (6 tasks, FD1–FD6, 12 findings inline). T1/T2 done; T3 next.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 3 = this sprint; T6 marks it complete), **BL-24**, **BL-35**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ BL-2 pass 3; T6 flips to complete).

Committed on `sprint/41-bl2-t2-escalation-seam`: `5c04407`, `bdd00b8` (Task 2), then a merge of `origin/main`
(#129) to clear the docs-cursor conflict. PR #128 open against `main`, awaiting merge.
