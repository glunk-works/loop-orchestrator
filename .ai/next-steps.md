# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 40 — BL-2 pass 2 (Slack inbound trigger) — T1-T5 done; only T6 remains.**
T4+T5 are on an open PR awaiting HITL review. **Do NOT `/archive-sprint` yet** —
archive only after **T6** merges (the whole sprint).

## Just done (Coder/Sonnet session)
- Rehydrated via `/resume`: cut `sprint/40-bl2-slack-daemon-cli` fresh off updated `main`
  (`b43c326`); no stale branches to prune; ruleset healthy (4 rule types, 8 required checks).
- Implemented **T4** (`slack_control/daemon.py` — `SlackDaemon` wiring the T1 listener to
  T2/T3 parse+dispatch under the FD3 channel-ID guard, `build_daemon_from_env()` fail-closed
  on any of the three env vars, ephemeral replies) and **T5** (`loop-engine slack-listen` CLI
  subcommand + `tests/slack_control/test_boundaries.py`).
- Added two small supporting pieces inside `tools/slack_io` (kept behind its existing
  boundary, not named individually in the sprint plan but load-bearing for FD3/T4):
  `resolve_channel_id` (name/`#name`/ID → ID resolution, paginated `conversations.list`) and
  `send_ephemeral_reply` + `format_command_accepted`/`format_command_rejected` (fail-open
  ephemeral-reply transport + mrkdwn-escaped/truncated formatting).
- Green gate: lint clean, format clean, full suite 706 passed, five subprocess surfaces
  intact, `slack_control/` confirmed keyring- and `slack_sdk`-free.
- Committed (`c26c610`), pushed, opened **[PR #119](https://github.com/glunk-works/loop-engine/pull/119)**
  (base `main`, title ≤72 bytes checked). Folded in the prior session's uncommitted
  `.ai/next-steps.md` regeneration into this commit.
- Ran **`/critic-gate`**: proposed `security-critic` + `architect` (both indicated —
  untrusted Slack input → model-exec + spend sink, matching the T2/T3 precedent), human
  confirmed both, spawned in parallel. `security-critic`: **zero security findings** (channel
  guard, fail-closed ordering, mrkdwn escaping, token non-logging, async bridge all sound);
  flagged one non-security robustness gap (`resolve_channel_id` could raise `slack_sdk`'s
  `SlackApiError` instead of `RuntimeError`, bypassing the CLI's fail-closed catch).
  `architect`: 3 low-severity findings, no blockers — met all Task 4/5 acceptance criteria.
  Fixed 2 (the `SlackApiError`-wrapping gap, and `_handle_request` no longer sends a
  misleading "accepted" reply when a command wasn't actually dispatched — covers both the
  `_loop is None` path and a `run_coroutine_threadsafe` failure during shutdown teardown,
  with the orphaned coroutine explicitly `.close()`d). Left one as an accepted judgment call
  (a redelivered Socket Mode envelope can still produce a duplicate "accepted" reply even
  though the dispatcher correctly dedupes the run — UX-only; fixing it would mean changing
  `dispatch.py`'s already-merged T3 return contract). Re-ran the green gate after fixes: 709
  passed, lint/format clean. Committed (`da5a2d2`), pushed to the same PR.

## Next — post the architect-review (Opus)
1. **New session** → `/model opus` → `/resume` → `/code-review` → post the fresh-session
   Architect HITL review on PR #119 (`gh pr review --comment`, verbatim two-line header +
   attestation block — **never `--approve`**). Cite the critic-gate pass (zero security
   findings, two low-severity fixes landed, one accepted-with-reason) as evidence of the
   defense-in-depth pass. Review focus: the FD3 channel-ID guard (`resolve_channel_id`'s
   name-vs-ID regex + pagination + the new API-error wrapping), FD4 fail-closed ordering in
   `build_daemon_from_env` (all three env vars checked before any socket/API call), and the
   sync→async bridge in `daemon.py`'s `_handle_request`.
2. After the owner merges #119: **T6** (docs — operator setup, `CLAUDE.md` boundary update,
   threat-model note, `docs/backlog.md`/roadmap update; `architect-review`-exempt) is the
   last sprint task. **Archive after T6.**

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Squash trap:** `sprint/40-bl2-slack-command-dispatch` (T2+T3, PR #117) is dead. The live
  branch is now `sprint/40-bl2-slack-daemon-cli` (PR #119) — once it merges it too goes dead;
  cut T6's branch fresh off updated `main`.
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout = answer
  the host pinentry and retry.
- **`/critic-gate` proposes, never auto-spawns** — this session confirmed `security-critic` +
  `architect` before either ran; keep that pattern going forward.

## Pointers
- [PR #119](https://github.com/glunk-works/loop-engine/pull/119) — T4+T5, awaiting `architect-review`.
- [`sprints/40_bl2_slack_inbound/sprint_plan.md`](../sprints/40_bl2_slack_inbound/sprint_plan.md) — the approved plan, Task 6 header for what's left.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 2 nearly done, pass 3 open), **BL-24** (webhook, superseded-in-practice), **BL-33** (guard-hardening), **BL-34** (CI `test` docs-only fail-safe defeated by `bash -e`).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — Status table + NEXT ACTION (→ pass 3 once this lands).
