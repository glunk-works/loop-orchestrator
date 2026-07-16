# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 39 — BL-2 Slack outbound notify (pass 1 of 3) — AWAITING HITL REVIEW.**
T1+T2 are implemented, tested, and open as
[PR #107](https://github.com/glunk-works/loop-engine/pull/107)
(`sprint/39-bl2-slack-notify` → `main`, head `5dd66c3`). It touches `src/`, so the
fresh-session `architect-review` gate is open and blocking merge.
**Next session: Opus/Architect posts the review.**

## Just done (this session, Coder/Sonnet — T1+T2 implementation)
- Cut `sprint/39-bl2-slack-notify` from `main`, committed the sprint plan (`617bd54`).
- Implemented **T1**: `core/notify.py` — the pure `EventKind`/`LifecycleEvent`/
  `Notifier`/`NoOpNotifier` contract, a leaf module, no `slack_sdk` import — and
  `tools/slack_io`'s `SlackNotifier`/`build_notifier_from_env` (function-scoped
  `slack_sdk` import, `WebClient(timeout=5)`, internally fail-open — the `try/except`
  wraps both `format_event` and the post).
- Implemented **T2**: `tools/slack_io/format.py`'s pure `format_event()`, mrkdwn over
  all six `EventKind`s (cost summed from `stage_history`, budget from
  `event.budget_usd`, awaiting-issue link from `pending_issue` with a graceful
  `None` degrade).
- Pinned `slack_sdk==3.43.0`, regenerated `sbom.json`; `hatch run audit` clean.
- New tests: `tests/core/test_notify.py`, `tests/tools/test_slack_io.py`,
  `tests/tools/test_slack_io_format.py`, `tests/tools/test_slack_io_boundaries.py`
  (mirrors `tests/trigger/test_boundaries.py` — no `keyring`, no direct file write,
  no subprocess surface, `slack_sdk` stays function-scoped).
- Full suite green (624 tests), lint clean, format-check clean, local `gitleaks`
  scan clean. Landed as one commit (`5dd66c3`), pushed, PR #107 opened against
  `main`, labeled `feature`/`area/tools`.
- **No emission call sites yet** — `run_graph_loop` doesn't call the notifier.
  Every existing test/call site is unchanged; the module is inert until T3.

## Next — post the architect-review on PR #107 (Opus/Architect)
1. Fresh session → `/resume` (this file) → `/code-review` the diff on
   `sprint/39-bl2-slack-notify` against `main`.
2. Post via `gh pr review 107 --comment` headed
   `**Opus/Architect HITL review (automated)**` with the fresh-session
   attestation — **never `--approve`**.
3. If findings come back, they route to a Coder/Sonnet fix pass, then a re-review
   against the new head commit.
4. Once `architect-review` is green and the owner merges #107, switch back to
   Coder/Sonnet for **T3**: add `notifier`/`resuming: bool` to `run_graph_loop`
   ([`graph_engine.py:110`](../src/loop_engine/core/graph_engine.py#L110)), the two
   emit points (`started` gated on `not resuming` — **not** `start_index`, per E1;
   the terminal event via an explicit `RunStatus`→`EventKind` dict; `crashed` on an
   escaping exception carrying the pre-invoke primed state, then re-raise), each
   wrapped in its own `try/except`; the two `cli.py` resume call sites pass
   `resuming=True`. Then **T4** (docs/boundaries/threat-model/backlog + roadmap).

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **A squash-merged branch is dead** — prune via `gh pr list --state merged` + `git branch -D`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout =
  answer the host pinentry and retry.

## Pointers
- [PR #107](https://github.com/glunk-works/loop-engine/pull/107) — T1+T2, open,
  awaiting `architect-review`.
- [`sprints/39_bl2_slack_notify/sprint_plan.md`](../sprints/39_bl2_slack_notify/sprint_plan.md)
  — the active plan (FD1–FD4 + T1–T4, grounded with file:line refs). T3/T4 remain.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** + its `SCHEDULED` note.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION line
  still says "implement Sprint 39"; leave until T3/T4 land.
