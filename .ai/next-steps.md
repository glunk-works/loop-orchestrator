# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 39 — BL-2 Slack outbound notify (pass 1 of 3) — T4 implemented, PR open.**
T1+T2 merged (#107). T3 merged (#112). **T4 (docs) is implemented on
`sprint/39-bl2-slack-notify-t4` and its PR is open against `main`** — docs-only,
`architect-review`-exempt. **Next session: once the T4 PR merges, sprint 39 is
COMPLETE → run `/archive-sprint`.**

## Just done (this session, Coder/Sonnet — T4 docs)
- Cut `sprint/39-bl2-slack-notify-t4` from `main`.
- Updated `docs/architecture_definition.md` §1 trust boundary + §4 secrets management:
  recorded the Slack `chat.postMessage` egress (second network egress, third-party,
  fail-open, off by default) and the `LOOP_ENGINE_SLACK_BOT_TOKEN`/
  `LOOP_ENGINE_SLACK_CHANNEL` env-var credential class distinct from the keyring-only
  Anthropic key.
- Added a `tools/slack_io` bullet to `CLAUDE.md`'s "Enforced module boundaries".
- Added a `LANDED: pass 1 of 3` note under BL-2 in `docs/backlog.md` (what shipped
  across T1–T4; passes 2–3 — inbound trigger, escalation round-trip — still open).
- Flipped `docs/migration_roadmap.md`'s NEXT ACTION line off "plan BL-2" to a
  Sprint 39 DONE entry + a new NEXT ACTION pointing at BL-2 passes 2–3.
- Also updated `.ai/context/modules.md` (not explicitly listed in the cursor, but
  in the sprint plan's T4 target files/acceptance criteria): added `core/notify.py`
  and `tools/slack_io/` module entries, and a note on `core/graph_engine.py`'s new
  emit points.
- No `src/` changes — verified no test asserts on the specific prose touched
  (`tests/test_ci_config.py`'s CLAUDE.md check is about the abort exit code, unrelated).
- PR opened: <FILL IN PR URL/NUMBER AFTER `gh pr create`>.

## Next — once the T4 PR merges
1. Confirm all required checks green (docs-only ⇒ `architect-review` exempt, but
   `lint`/`format-check`/`test`/`secrets-scan`/`dependency-audit`/`sbom`/`pr-title`
   still gate).
2. Owner merges. Sync local `main`, prune `sprint/39-bl2-slack-notify-t4`.
3. Run `/archive-sprint` — sprint 39 is COMPLETE (all of T1–T4 landed).
4. After archiving, the live NEXT ACTION becomes BL-2 passes 2–3 (see
   `docs/backlog.md`'s BL-2 entry / `docs/migration_roadmap.md`) — needs its own
   planning pass (Opus/Architect) before implementation.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **T4 is docs-only ⇒ no `architect-review` gate** (it doesn't touch `src/`).
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout =
  answer the host pinentry and retry.
- The three T3-review observations are **notes for a future BL-2 pass, not T4** — T4
  changed no code.

## Pointers
- [`sprints/39_bl2_slack_notify/sprint_plan.md`](../sprints/39_bl2_slack_notify/sprint_plan.md)
  — the active plan (FD1–FD4 + T1–T4). All four tasks implemented; T4 awaiting merge.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 1 landed, passes 2–3 open)
  + **BL-33** (guard-hardening, #109 merged, no sprint plan yet).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION line now
  points at BL-2 passes 2–3.
