# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 40 — BL-2 pass 2 (Slack inbound trigger) — T1 MERGED; T2+T3 on an open PR
awaiting HITL review; T4-T6 REMAIN.** This is a six-task, multi-PR sprint. **Do NOT
`/archive-sprint` yet** — archive only after **T6** merges (the whole sprint).

## Just done (Coder/Sonnet session)
- Rehydrated via `/resume`: merged docs PR #116 was already landed on `main`; pruned two
  squash-dead local branches (`sprint/40-bl2-slack-inbound`, `docs/sprint40-t1-followups`);
  ruleset check healthy (4 rule types, 8 required checks).
- Cut `sprint/40-bl2-slack-command-dispatch` fresh off updated `main`.
- Implemented **T2** (`slack_control/command.py` — pure `parse_command`, FD5 grammar,
  required/fail-closed budget) and **T3** (`slack_control/dispatch.py` — `SlackRunDispatcher`,
  fire-and-forget, `envelope_id` dedupe, mirrors `trigger/dispatch.py`'s `InProcessDispatcher`
  for the BL-8 `os.chdir` serialization lock).
- Green gate: lint clean, format clean, full suite 677 passed, five subprocess surfaces intact,
  `slack_control/` confirmed keyring-free (repo-wide boundary test).
- **`/critic-gate`** ran `security-critic` + `architect` (both proposed, both confirmed by the
  human — indicated per the sprint plan's Security Considerations for this first
  live-exercised inbound sink). Both independently caught the same **HIGH**: `--budget
  inf`/`nan`/`1e999` bypassed the fail-closed money-cap guard. Fixed with `math.isfinite()` +
  duplicate-`--budget` rejection; both critics re-verified the fix clean on re-spawn.
- Committed (`490fb1c`), pushed, opened **[PR #117](https://github.com/glunk-works/loop-engine/pull/117)**
  (base `main`, title ≤72 bytes checked).

## Next — post the architect-review (Opus)
1. **New session** → `/model opus` → `/resume` → `/code-review` → post the fresh-session
   Architect HITL review on PR #117 (`gh pr review --comment`, verbatim two-line header +
   attestation block from `.ai/context/workflow.md` — **never `--approve`**). Cite the
   critic-gate finding (the fixed budget bypass) as evidence of the defense-in-depth pass.
2. After the owner merges #117: **T4** (`slack_control/daemon.py` — channel guard, dispatch,
   ephemeral replies, fail-closed startup) + **T5** (`loop-engine slack-listen` CLI +
   `tests/slack_control/test_boundaries.py` + package registration check) land together on
   the next PR (Coder/Sonnet). Then **T6** (docs, `architect-review`-exempt). **Archive after T6.**

## Implementation traps (baked into the plan — still ahead in T4-T5)
- Channel guard compares **IDs, not names** (resolve a `#name` → ID once at daemon startup).
- Socket Mode's **~3 s ack window** → ack promptly; `SlackRunDispatcher` already dedupes on
  `envelope_id` for redelivery.
- **Fail-CLOSED on start** if any of `LOOP_ENGINE_SLACK_APP_TOKEN` / `_BOT_TOKEN` / `_CHANNEL`
  is unset — mirrors T1's `build_listener_from_env` FD4 posture.
- `daemon.py` imports **no** `slack_sdk` directly — all Slack I/O via `tools/slack_io` (T1
  inbound) + the pass-1 bot-token `WebClient` for ephemeral replies.
- New `tests/slack_control/test_boundaries.py` (T5) mirrors `tests/trigger/test_boundaries.py`;
  `tests/tools/test_subprocess_surfaces.py` must stay at **five**.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Squash trap:** `sprint/40-bl2-slack-inbound` and `docs/sprint40-t1-followups` are both dead
  and already pruned. The live branch is `sprint/40-bl2-slack-command-dispatch` (PR #117) — once
  it merges it too goes dead; cut T4+T5 fresh off updated `main`, don't reuse it.
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer
  the host pinentry and retry.
- **`/critic-gate` proposes, never auto-spawns** — this session confirmed `security-critic` +
  `architect` before either ran; keep that pattern for T4/T5's PR too.

## Pointers
- [PR #117](https://github.com/glunk-works/loop-engine/pull/117) — T2+T3, awaiting `architect-review`.
- [`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md) — the approved plan, Task 4/Task 5 headers.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 2 in progress, pass 3 open), **BL-24** (webhook, superseded-in-practice), **BL-33** (guard-hardening), **BL-34** (CI `test` docs-only fail-safe defeated by `bash -e`).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ pass 3 once this lands).
