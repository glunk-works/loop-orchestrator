# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**THE MIGRATION IS ON `main`.** PR #58 merged as merge commit **`d2135e7`** — two parents, 113
commits preserved, **not squashed**. `main`'s tree is `4aad78e`, byte-for-byte the tree the Task 3
preflight predicted. The two-branch era is over: cut sprint branches from **`main`**, base PRs on
**`main`**. Sprint `35_migration_merge` — **Task 6 (planning) is all that's left.**

## Just done (Opus/Architect session, 2026-07-14)
- **Posted PR #58's `architect-review`** from a genuinely fresh session, bound to head `b669482`,
  scoped per **FD7** as an *integration* review (does the merge produce the predicted workflow set;
  is `ci.yml` post-sprint-33; do the four workflows co-exist) and **explicitly declining** to
  re-review the 113 already-reviewed commits. Owner merged. **Task 4 done.**
- **Task 5 done bar one step.** `allow_merge_commit` held across the merge, merge-commit button
  used, then set back to **`false`** — repo is now squash-only, closing **BL-13** and BL-11's
  "three strategies, one convention" gap. Retiring `feat/**` was **deferred by the owner → BL-17**.
- **Unblocked all four Dependabot PRs (#50–53).** They were never conflicted (FD5 vindicated), but
  were blocked by **two** structural faults: `GITLEAKS_LICENSE` lived in the org **Actions** secret
  store while Dependabot-triggered runs can read only the org **Dependabot** store (owner fixed);
  and Dependabot's default title `Bump X from A to B` fails the required `pr-title` check. Retitled
  all four by hand — **all now `CLEAN`, 8/8**.
- **PR #61** (docs: Task 5 close-out, BL-17/18/19) and **PR #62** (`dependabot.yml` Conventional
  Commits prefix + a test that runs Dependabot's generated subject through `pr-title.yml`'s *own*
  regex). Both **CLEAN**, both docs/CI-config only so `architect-review` is exempt.

## Next — Opus/Architect
**Task 6 (PLANNING, no code).** Two bodies of work the merge released:
1. **Dependabot #50–53.** All green now, but all four are **major** jumps (`checkout` 4→7,
   `upload-artifact` 4→7, `setup-python` 5→6, `gitleaks-action` 2→3). **Green CI is necessary and
   not sufficient — read each changelog.** #50 is entangled with **BL-19**: if the gitleaks-CLI swap
   is taken, #50 is retired by *deletion* rather than review. Decide BL-19 first, or defer it aloud.
2. **`sprints/DEFERRED_VERIFICATION.md`'s five never-run checks** — give each a named, scheduled
   home (recommended shape is in the sprint plan's Task 6). Record outcomes in `docs/backlog.md` +
   this file, **not** a new file.

No HITL gate is open.

## Gotchas worth remembering
- **`gh pr view` serves stale `mergeStateStatus`.** `BLOCKED` with *nothing failing* is usually
  GitHub not having recomputed — re-read via GraphQL before intervening (hit on #58 *and* #62; both
  were actually `CLEAN`). Do **not** close+reopen to "fix" it.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor does its own GPG agent
  forwarding and owns `~/.gnupg/S.gpg-agent`; the script fights it for the same path and breaks
  signing (the key then appears to vanish: `No secret key`). A signing **`Timeout` means answer the
  host pinentry prompt**, not repair the agent. Recovery: reload the Cursor window.

## Human actions
- **Merge #61 and #62** (squash — now the only option).
- **Review #50–53 on their merits** (see Task 6). **BL-17:** retire `feat/**` — it still exists at
  `b669482`, having survived the merge *by design* (FD6: the ruleset's `deletion` rule beat
  `delete_branch_on_merge`).
- **Carried:** delete `glunk-works/loop-engine-v3-scratch`; **trim the PAT** — it lacks
  `actions:write` and any secrets scope (`gh run rerun` and secret reads both 403).

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) — FD1–FD7; only Task 6 remains.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-13 resolved**; BL-12/BL-14's topology pattern **closed by the merge**; **new: BL-17, BL-18, BL-19**; BL-15/BL-16 open.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed; the merge closes the topology question too.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — the five never-run checks (Task 6 homes them).
- Ruleset checked healthy 2026-07-14: 4 rule types, all 8 required checks on `main`.
