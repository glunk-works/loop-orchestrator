# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 40 — BL-2 pass 2 (Slack inbound trigger) — AWAITING HITL REVIEW (T1).**
T1 is implemented, green, and critic-gate-clean on
[PR #115](https://github.com/glunk-works/loop-engine/pull/115) (branch
`sprint/40-bl2-slack-inbound`, head `24b08df`). It needs the fresh-session
`architect-review` before it can merge. Next session is **Architect/Opus**.

## Just done (this session, Coder/Sonnet)
- **T1**: added `tools/slack_io/inbound.py` — a fail-closed wrapper over
  `slack_sdk.socket_mode.SocketModeClient` (`build_listener_from_env()`, `SocketModeListener`),
  `slack_sdk` kept function-scoped so `tools/slack_io` stays the sole importer (now
  bidirectional). Plus `tests/tools/test_slack_io_inbound.py` and an extension to
  `tests/tools/test_slack_io_boundaries.py` pinning `inbound.py` into the boundary sweep.
  Commits `86880d3` (feature) + `24b08df` (critic-gate fixups).
- Full green gate: `hatch run lint`/`format` clean, 25 targeted tests + **644/644** full
  suite passing.
- Opened **PR #115** (base `main`, title 60 bytes) and ran `/critic-gate`:
  **security-critic** + **architect** both ran (human-approved pair, given the sprint plan's
  explicit "applies with force" note), both came back clean — no trust-boundary violation,
  no correctness bug. Two overlapping non-security nits (unused `_logger`, missing
  `WebClient(timeout=5)`) fixed in `24b08df` and re-gated locally (not re-spawned — both
  critics had already called the nits harmless pre-fix). One forward-looking note for T4
  (not a T1 defect): `build_listener_from_env`'s `WebClient` is discarded; T4's daemon will
  build its own bot-token `WebClient` for ephemeral replies, mirroring `build_notifier_from_env`.

## Next — Architect HITL review (Opus)
1. Fresh session: `/model opus` → `/resume` → `/code-review` on PR #115 (head `24b08df`).
2. Post the review with `gh pr review --comment` (never `--approve`) — body must **open with
   the verbatim two-line header + attestation block** from `.ai/context/workflow.md`
   (`**Opus/Architect HITL review (automated)**` then the fresh-session attestation line,
   pasted not paraphrased — the check matches by literal `contains()`).
3. Once merged (human's call), the next **Coder/Sonnet** session starts **T2 + T3**
   (`slack_control/command.py` pure parser + `dispatch.py` `SlackRunDispatcher`), landing
   together on the next PR — see the PR structure note in the sprint plan.

## Implementation traps (baked into the plan — still ahead in T2-T5)
- `RunRequest` is **not** reusable (GitHub-shaped required fields) → separate `SlackRunCommand`.
- Channel guard compares **IDs, not names** (resolve a `#name` → ID once at startup, else it silently drops all).
- Socket Mode's **~3 s ack window** → ack promptly, run on a worker thread, **dedupe on `envelope_id`** (redelivery).
- **Fail-CLOSED on start** (the deliberate inverse of pass 1's fail-open notify) — T1 already does this for the transport; T4's daemon needs the same posture for the channel env var.
- New `slack_control/` needs `tests/slack_control/test_boundaries.py` mirroring `tests/trigger/`;
  `tests/tools/test_subprocess_surfaces.py` must stay at **five**.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Not yet pushed:** the plan/cursor commit lives on local `sprint/40-bl2-slack-inbound` only —
  push + open the docs PR (base `main`) when ready, or let the Sonnet session carry it.
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer the host pinentry and retry.
- **`/critic-gate` proposes, never auto-spawns** — it asked before running security-critic + architect this session; keep that pattern for T2-T5's PRs too (the plan flags critic-gate as applying "with force" through this sprint).

## Pointers
- [PR #115](https://github.com/glunk-works/loop-engine/pull/115) — T1, awaiting `architect-review`.
- [`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md) — the approved plan.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 2 in progress, pass 3 open), **BL-24** (webhook, superseded-in-practice), **BL-33** (guard-hardening).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ pass 3 once this lands).
- [`sprints/39_bl2_slack_notify/sprint_plan.md`](../sprints/39_bl2_slack_notify/sprint_plan.md) — pass 1's plan (FD1–FD4 + T1–T4), for reference.
