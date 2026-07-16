# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 40 — BL-2 pass 2 (Slack inbound trigger) — IMPLEMENTING.**
The Opus/Architect planning pass is done and the plan is approved:
[`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md)
(Goal, out-of-scope, **FD1–FD6**, security considerations, risks, **T1–T6**). Next session is
**Coder/Sonnet** implementation. Switch model: `/handoff` is done → new session → `/model sonnet`
→ `/resume`.

## Just done (this session, Opus)
- **Planned BL-2 pass 2** end to end via five HITL gates; wrote + committed the sprint plan
  on branch `sprint/40-bl2-slack-inbound` (docs-only, `architect-review`-exempt; not yet pushed).
- **FD1** Socket Mode **supersedes** the GitHub webhook (`trigger/` parked in place, **not** deleted;
  BL-24 superseded-in-practice). **FD2** trigger-surface-only (escalation round-trip = pass 3).
  **FD3** channel-scoped authz **only** (residual risk accepted; user-allowlist = future tightening).
  **FD4** app token = env var `LOOP_ENGINE_SLACK_APP_TOKEN`; daemon **fails closed** if any cred unset.
  **FD5** `/agent-run` slash command, budget **required** (fail-closed). **FD6** module layout below.
- No code yet; the only commit is the plan/cursor on `sprint/40-bl2-slack-inbound` (base `main`).

## Next — implement (Coder/Sonnet)
1. Cut `sprint/40-bl2-slack-inbound` from `main`. Work under the **synced project env**
   (`slack_sdk==3.43.0` must import — the planning env lacked it).
2. **T1** `tools/slack_io/inbound.py` (Socket Mode transport, `slack_sdk` function-scoped,
   fail-closed builder) — own PR. Then **T2+T3** (`slack_control/command.py` + `dispatch.py`),
   **T4+T5** (`daemon.py` + `slack-listen` CLI + boundary tests), **T6** docs-only last.
3. Each `src/`-touching PR ⇒ **fresh-session `architect-review`** (never `/model opus` mid-session:
   `/handoff` → new session → `/resume` → `/code-review` → post the verbatim-header review).
   `/critic-gate` applies hard here (security-critic + architect — untrusted-input → model-exec sink).

## FD6 module layout (owner-reviewable at PR)
- `tools/slack_io/inbound.py` — Socket Mode transport; keeps `slack_sdk` **single-importer** (function-scoped).
- `slack_control/` — **new top-level caller** (sibling of `trigger/`/`flows/`), imports no `slack_sdk`:
  `command.py` (pure parser → `SlackRunCommand`), `dispatch.py` (`SlackRunDispatcher`, mirrors
  `InProcessDispatcher`, `_run_lock` for BL-8), `daemon.py` (channel guard + dispatch + ephemeral replies).
- CLI `loop-engine slack-listen` (blocking daemon). No new subprocess surface; no `sbom`/`audit` churn.

## Implementation traps (baked into the plan — don't relearn them)
- `RunRequest` is **not** reusable (GitHub-shaped required fields) → separate `SlackRunCommand`.
- Channel guard compares **IDs, not names** (resolve a `#name` → ID once at startup, else it silently drops all).
- Socket Mode's **~3 s ack window** → ack promptly, run on a worker thread, **dedupe on `envelope_id`** (redelivery).
- **Fail-CLOSED on start** (the deliberate inverse of pass 1's fail-open notify).
- New `slack_control/` needs `tests/slack_control/test_boundaries.py` mirroring `tests/trigger/`;
  `tests/tools/test_subprocess_surfaces.py` must stay at **five**.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Not yet pushed:** the plan/cursor commit lives on local `sprint/40-bl2-slack-inbound` only —
  push + open the docs PR (base `main`) when ready, or let the Sonnet session carry it.
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.

## Pointers
- [`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md) — the approved plan.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 2 in progress, pass 3 open), **BL-24** (webhook, superseded-in-practice), **BL-33** (guard-hardening).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ pass 3 once this lands).
- [`sprints/39_bl2_slack_notify/sprint_plan.md`](../sprints/39_bl2_slack_notify/sprint_plan.md) — pass 1's plan (FD1–FD4 + T1–T4), for reference.
