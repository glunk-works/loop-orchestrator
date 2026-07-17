# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 40 — BL-2 pass 2 (Slack inbound trigger) — T1 MERGED; T2–T6 REMAIN.**
T1 landed on `main` as squash commit `a447439` ([PR #115](https://github.com/glunk-works/loop-engine/pull/115),
merged 2026-07-16). **This is a six-task, multi-PR sprint — T1 is 1/6.** The next unit of
work is **T2 + T3** (a **Coder/Sonnet** session), landing together on the next PR.
**Do NOT `/archive-sprint` yet** — archive only after **T6** merges (the whole sprint).

## Just done (Opus HITL review session)
- Posted the fresh-session **Architect HITL review** on PR #115 (`gh pr review --comment`,
  verbatim header + attestation), verdict **ACCEPT** — `/code-review` (high) found only two
  non-blocking nits (recorded on the PR). All eight required checks green; the owner merged.
- Resolved a docs-only `.ai/next-steps.md` conflict (from #114's sprint-plan squash on `main`)
  via a merge commit before merge; re-posted the review against the new head.
- **T1 itself** (prior Coder/Sonnet session): `tools/slack_io/inbound.py` — a fail-closed wrapper
  over `slack_sdk.socket_mode.SocketModeClient` (`build_listener_from_env()`, `SocketModeListener`),
  `slack_sdk` function-scoped so `tools/slack_io` stays the sole importer (now bidirectional),
  plus `tests/tools/test_slack_io_inbound.py` + the boundary-sweep extension. Forward note for T4
  (not a T1 defect): `build_listener_from_env`'s `WebClient` is discarded; T4's daemon builds its
  own bot-token `WebClient` for ephemeral replies, mirroring `build_notifier_from_env`.

## Next — implement T2 + T3 (Coder/Sonnet)
1. `/handoff` → new session → `/model sonnet` → `/resume`. **Cut a fresh branch off updated `main`**
   (main already has T1 via `a447439`; the old `sprint/40-bl2-slack-inbound` branch is squash-dead —
   reusing it would re-propose merged T1). A `sprint/40-*` name is fine.
2. **T2** `slack_control/command.py` — pure `parse_command(payload) -> SlackRunCommand | CommandRejection`
   (FD5 grammar `/agent-run --budget <n> <requirements>`; required budget, fail-closed on the money cap;
   no I/O, no `slack_sdk`). **T3** `slack_control/dispatch.py` — `SlackRunDispatcher` (fire-and-forget via
   `runner.run_new`, mirrors `InProcessDispatcher`). Land T2+T3 together on one PR.
3. `src/`-touching PR ⇒ **fresh-session `architect-review`** + `/critic-gate` applies with force
   (untrusted input → model-exec + spend sink). Then T4+T5, then T6 docs-only. **Archive after T6.**

## Implementation traps (baked into the plan — still ahead in T2-T5)
- `RunRequest` is **not** reusable (GitHub-shaped required fields) → separate `SlackRunCommand`.
- Channel guard compares **IDs, not names** (resolve a `#name` → ID once at startup, else it silently drops all).
- Socket Mode's **~3 s ack window** → ack promptly, run on a worker thread, **dedupe on `envelope_id`** (redelivery).
- **Fail-CLOSED on start** (the deliberate inverse of pass 1's fail-open notify) — T1 already does this for the transport; T4's daemon needs the same posture for the channel env var.
- New `slack_control/` needs `tests/slack_control/test_boundaries.py` mirroring `tests/trigger/`;
  `tests/tools/test_subprocess_surfaces.py` must stay at **five**.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Squash trap:** the `sprint/40-bl2-slack-inbound` branch is **dead** now that PR #115 squash-merged
  (`a447439`) — do not reuse it; cut T2+T3's branch fresh off `main`.
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.
- **`/critic-gate` proposes, never auto-spawns** — it asked before running security-critic + architect this session; keep that pattern for T2-T5's PRs too (the plan flags critic-gate as applying "with force" through this sprint).

## Pointers
- [PR #115](https://github.com/glunk-works/loop-engine/pull/115) — T1, awaiting `architect-review`.
- [`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md) — the approved plan.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 2 in progress, pass 3 open), **BL-24** (webhook, superseded-in-practice), **BL-33** (guard-hardening), **BL-34** (CI `test` docs-only fail-safe defeated by `bash -e` — surfaced on PR #115).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ pass 3 once this lands).
- [`sprints/39_bl2_slack_notify/sprint_plan.md`](../sprints/39_bl2_slack_notify/sprint_plan.md) — pass 1's plan (FD1–FD4 + T1–T4), for reference.
