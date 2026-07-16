# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the sprint plan) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 39 — BL-2 Slack outbound notify (pass 1 of 3) — T4 implemented, PR #113
open, critic-clean, awaiting merge.** T1+T2 merged (#107). T3 merged (#112). T4
(docs) is on `sprint/39-bl2-slack-notify-t4`, pushed, tree clean at `a3a8074`.
**Next session: confirm CI green on #113, ask the owner to merge (docs-only ⇒ no
HITL review needed), then `/archive-sprint` — sprint 39 is COMPLETE once it lands.**

## Just done (this session, Coder/Sonnet — T4 docs + critic-gate)
- Cut `sprint/39-bl2-slack-notify-t4` from `main`; updated `docs/architecture_definition.md`
  (§1 trust boundary + §4 secrets management — Slack `chat.postMessage` as a second,
  third-party, fail-open, off-by-default egress; `LOOP_ENGINE_SLACK_BOT_TOKEN`/
  `LOOP_ENGINE_SLACK_CHANNEL` as a new env-var credential class), `CLAUDE.md`
  ("Enforced module boundaries" — added `tools/slack_io`), `.ai/context/modules.md`
  (added `core/notify.py` + `tools/slack_io/` entries — not explicitly named in the
  prior cursor but called for by the sprint plan's T4 acceptance criteria),
  `docs/backlog.md` (`LANDED: pass 1 of 3` note under BL-2), `docs/migration_roadmap.md`
  (flipped NEXT ACTION off "plan BL-2" to a Sprint 39 DONE entry + BL-2-passes-2–3
  pointer). Opened [PR #113](https://github.com/glunk-works/loop-engine/pull/113)
  (`eadbca2`, then `cea6136` filling in the PR URL).
- Ran `/critic-gate docs-consistency` against the diff (user-confirmed critic choice —
  right fit since this PR's whole job is cross-doc consistency). One real finding:
  `CLAUDE.md`'s new `tools/slack_io` bullet had inverted subject/object ("`slack_sdk`
  is the only module that imports it" — swapped subject/object; fact was right, wording
  was garbled). Fixed and pushed (`a3a8074`). Two low-severity non-blocking observations
  (not defects, no action taken): the architecture diagram's egress arrow doesn't show
  Slack (defensible — off by default), and `README.md` doesn't mention the new Slack env
  vars (an omission, not a false claim). Everything else the critic checked (event kinds,
  env var names, fail-open behavior at both layers, the `resuming` gate, cross-doc
  PR/task consistency) matched ground truth.
- Tree is clean at `a3a8074`, fully pushed. No `src/` changes anywhere in T4.

## Next — get #113 merged, then archive
1. `gh pr checks 113` — confirm all required checks green (docs-only ⇒
   `architect-review` exempt, but `lint`/`format-check`/`test`/`secrets-scan`/
   `dependency-audit`/`sbom`/`pr-title` still gate). No HITL review needed for this PR.
2. Ask the owner to merge. Sync local `main`, prune `sprint/39-bl2-slack-notify-t4`.
3. Run `/archive-sprint` — sprint 39 is COMPLETE (all of T1–T4 landed).
4. After archiving, the live NEXT ACTION becomes **BL-2 passes 2–3** (inbound trigger
   surface + escalation round-trip) — see `docs/backlog.md`'s BL-2 entry /
   `docs/migration_roadmap.md`. Needs its own **Opus/Architect planning pass** before
   any implementation.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **PR title:** `wc -c` the byte count AND re-read the text before `gh pr create/edit`.
- **T4 is docs-only ⇒ no `architect-review` gate** (it doesn't touch `src/`).
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Signing Timeout =
  answer the host pinentry and retry.
- The three T3-review observations (in `docs/migration_roadmap.md`/prior cursor
  history) were notes for a future BL-2 pass, not T4 — T4 changed no code.

## Pointers
- [`sprints/39_bl2_slack_notify/sprint_plan.md`](../sprints/39_bl2_slack_notify/sprint_plan.md)
  — the active plan (FD1–FD4 + T1–T4). All four tasks implemented; T4 = PR #113,
  awaiting merge.
- [PR #113](https://github.com/glunk-works/loop-engine/pull/113) — T4, docs-only,
  critic-clean, awaiting CI confirmation + merge.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (pass 1 landed, passes 2–3 open)
  + **BL-33** (guard-hardening, #109 merged, no sprint plan yet).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION line now
  points at BL-2 passes 2–3.
