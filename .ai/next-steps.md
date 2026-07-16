# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 39 — BL-2 Slack outbound notify (pass 1 of 3) — IMPLEMENTING.** Planning is
**complete and reviewed** (Opus, this session, 3 critic passes); **no code exists yet**.
The plan is at `sprints/39_bl2_slack_notify/sprint_plan.md` (currently **untracked**).
No HITL gate is blocking — owner drove the plan review and said handoff.
**Next session: Coder/Sonnet implements.**

## Just done (previous session, Opus/Architect — planning + review)
- **Planned BL-2 Sprint 39** end-to-end via the one-question-at-a-time HITL flow.
  Locked **FD1–FD4** (owner-confirmed): notify first (inbound=S2, escalation=S3);
  official `slack_sdk` in a new `tools/slack_io`, **not** an MCP server; creds from
  **Infisical like the others** but runtime store = env var (not keyring); a fail-open
  `Notifier` seam resolved+emitted **inside `run_graph_loop`** mirroring the
  `issue_filer` seam.
- **Three critic passes** hardened the plan against the actual engine. Pass 2 caught a
  real defect in pass-1's own text (**E1**: gating `started` on `start_index == 0` is
  wrong — resumes can re-enter at stage 0), now fixed with an explicit `resuming: bool`
  param. Also fixed fail-open location (call-site, not just impl), a T1/T2 PR-ordering
  inversion, an unbound-`result` crash footgun, and 5 smaller precision items.
- **No commits this session.** HEAD == origin/main == `0b03773`, tree clean except the
  new `sprints/39_bl2_slack_notify/` dir.

## Next — implement Sprint 39 (Coder/Sonnet)
1. **First:** cut `sprint/39-bl2-slack-notify` from `main`; commit the untracked
   `sprint_plan.md`.
2. **T1+T2 as ONE PR** (coupled — `SlackNotifier.emit` calls `format_event`): pinned
   `slack_sdk` + sbom regen + audit; `core/notify.py` (pure contract, no `slack_sdk`);
   `tools/slack_io` (`SlackNotifier` w/ function-scoped `slack_sdk` + `WebClient(timeout=5)`
   + internal fail-open, `build_notifier_from_env`, `format_event -> str` mrkdwn); a
   boundary test mirroring `tests/trigger/test_boundaries.py`; fail-open + no-op-default tests.
3. **T3:** emit inside `run_graph_loop` — `resuming: bool` gate (**not** `start_index`),
   each emit wrapped in its own `try/except`, `crashed` carries the pre-invoke primed
   state; only the two cli resume sites pass `resuming=True`.
4. **T4:** docs / CLAUDE.md boundary / threat model / backlog + roadmap; add the two
   Slack keys to Infisical, launched under `infisical run` (not `seed-secrets.sh`).
- **Follow FD1–FD4 verbatim.** Every `src/`-touching PR needs a fresh-session
  `architect-review` (`/handoff` → new session → `/resume` → `/code-review` → post).

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **Local `main` vs `origin/main` after a squash merge diverge** (identical content, new
  commit object): verify `git diff origin/main main` empty, then `git reset --hard
  origin/main`. (Moot right now — no commits this session.)
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **A squash-merged branch is dead** — prune via `gh pr list --state merged` + `git branch -D`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout =
  answer the host pinentry and retry.

## Pointers
- [`sprints/39_bl2_slack_notify/sprint_plan.md`](../sprints/39_bl2_slack_notify/sprint_plan.md)
  — the active plan (FD1–FD4 + T1–T4, grounded with file:line refs). **Read this first.**
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** + its `SCHEDULED` note; BL-24 (the
  unverified inbound webhook, deliberately not a Sprint-1 dependency).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION line still
  says "plan BL-2"; T4 flips it to "implement Sprint 39".
