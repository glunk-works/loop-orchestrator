# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 40 — BL-2 pass 2 (Slack inbound trigger) — T1/T2/T3 MERGED; T4-T6 REMAIN.**
Six-task, multi-PR sprint. T1 (`a447439`), T2+T3 (`b43c326`, [PR #117](https://github.com/glunk-works/loop-engine/pull/117))
now on `main`. **Do NOT `/archive-sprint` yet** — archive only after **T6** merges.
The next unit of work is **T4 + T5** (a **Coder/Sonnet** session), landing together on one PR.

## Just done (Opus HITL review session)
- Posted the fresh-session **Architect HITL review** on PR #117 (`gh pr review --comment`,
  verbatim header + attestation), verdict **ACCEPT**. Ran `/code-review` (high) as an independent
  cold pass — **no correctness bugs**; the one real HIGH (the `--budget inf/nan/1e999` money-cap
  bypass) was already caught by the T2 critic-gate and is fixed + regression-tested.
- Three **low / known-deferred** notes recorded on #117 (whitespace-collapse in `human_input`;
  no upper budget bound — user-explicit, accepted; `test_boundaries.py` deferred to T5).
- Owner **merged #117** (`b43c326`); synced `main`; pruned the squash-dead
  `sprint/40-bl2-slack-command-dispatch` branch; ruleset healthy (4 rule types, 8 required checks).

## Next — implement T4 + T5 (Coder/Sonnet)
1. `/handoff` is done → new session → `/model sonnet` → `/resume`. **Cut a fresh branch off
   updated `main`** (`b43c326`); the old `sprint/40-bl2-slack-command-dispatch` branch is
   squash-dead (reusing it would re-propose merged T2+T3). A `sprint/40-*` name is fine.
2. **T4** `slack_control/daemon.py` — channel guard (by **ID**, not name), dispatch via the
   merged `SlackRunDispatcher`, ephemeral bot-token `WebClient` replies, **fail-CLOSED** startup.
   **T5** `loop-engine slack-listen` CLI + `tests/slack_control/test_boundaries.py` + a package
   registration check. Land T4+T5 together on one PR.
3. `src/`-touching PR ⇒ **fresh-session `architect-review`** (Opus) + `/critic-gate` applies with
   force after the green gate (untrusted input → model-exec + spend sink). Then **T6** (docs,
   `architect-review`-exempt). **Archive after T6.**

## Implementation traps (baked into the plan — still ahead in T4-T5)
- Channel guard compares **IDs, not names** (resolve a `#name` → ID once at daemon startup, else it silently drops all).
- Socket Mode's **~3 s ack window** → ack promptly on a worker thread; `SlackRunDispatcher` already dedupes on `envelope_id` (redelivery).
- **Fail-CLOSED on start** if any of `LOOP_ENGINE_SLACK_APP_TOKEN` / `_BOT_TOKEN` / `_CHANNEL` is unset — mirrors T1's `build_listener_from_env` FD4 posture.
- `daemon.py` imports **no** `slack_sdk` directly — all Slack I/O via `tools/slack_io` (T1 inbound) + the pass-1 bot-token `WebClient` for ephemeral replies.
- New `tests/slack_control/test_boundaries.py` (T5) mirrors `tests/trigger/test_boundaries.py`; `tests/tools/test_subprocess_surfaces.py` must stay at **five**.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Squash trap:** `sprint/40-bl2-slack-command-dispatch` is **dead** now that PR #117 squash-merged
  (`b43c326`) — do not reuse it; cut T4+T5's branch fresh off `main`.
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.
- **`/critic-gate` proposes, never auto-spawns** — the #117 pass confirmed `security-critic` + `architect` before either ran; keep that pattern for T4/T5's PR.

## Pointers
- [`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md) — the approved plan, Task 4 / Task 5 headers.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 2 in progress, pass 3 open), **BL-24** (webhook, superseded-in-practice), **BL-33** (guard-hardening), **BL-34** (CI `test` docs-only fail-safe defeated by `bash -e`).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ pass 3 once pass 2 lands).
- [`sprints/39_bl2_slack_notify/sprint_plan.md`](../sprints/39_bl2_slack_notify/sprint_plan.md) — pass 1's plan (FD1–FD4 + T1–T4), for reference.
