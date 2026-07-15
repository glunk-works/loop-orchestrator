# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `37_test_suite_velocity` — PLANNING (Opus/Architect).** Sprint 36 (live factory
verification) is **complete, merged, and archived**. The next unit is the **test-review
block**, front-loaded ahead of BL-2 (owner decision 2026-07-15). **No HITL gate is open.**
No `sprint_plan` for 37 exists yet — **writing it is the first action.**

## Just done
- **Sprint 36 archived** (cursor snapshotted to `.ai/archive/36_live_factory_verification-next-steps.md`).
  It landed via #79 (squash `212cc56`) + #80 (`f5d95c5`): §5/§7/§8 discharged live, **BL-21 closed**,
  BL-28/29/30 filed, three scratch repos torn down (FD11), `administration=write` kept (owner call).
- **Branch pruning is now standard practice** (in `/resume` + `/archive-sprint`); 33 stale branches
  pruned. `sprint/35-tasks-3-4` was left (no merged PR under that name — glance before deleting).

## Next — plan BL-22 (Opus/Architect planning pass)
**BL-22 = CI/runner-time velocity.** Do the planning pass (one question at a time, HITL-gated),
then write `sprints/37_test_suite_velocity/sprint_plan.md`. Two-part shape (see `docs/backlog.md`
BL-22 for the measurements and the trap warning):
- **(a) Safe, high-value:** session-scope the MCP-subprocess fixtures. `test_mcp_provider`,
  `test_github_server`, `test_issue_io_server`, `test_issue_provider` and the `test_ralph_coder`
  tests each spawn a real MCP server subprocess — ~30% of the 555-test / ~380 s suite is 10 tests.
  Amortizing server launch makes the suite faster *everywhere*, incl. local TDD; touches no CI logic.
  **Land this first.**
- **(b) Dangerous:** docs-only PRs run the full ~380 s `test` job (every sprint-36 PR did). The fix
  is **not** `paths-ignore` on required checks — that is exactly what caused **BL-10/BL-12**. It needs
  a deliberate **aggregator-job** design (`if: always()`, inspect `needs.*.result`). Design it, don't
  bolt it on.

Then **BL-23** (test-validity audit: mutation-test the boundary guards + `core/`, hunt orphan tests
and guards weaker than their docstring), then **BL-2** (Slack control plane).

## Gotchas worth remembering
- **`architect-review` is exempt on docs-only PRs** (passes with no review). A `src/` PR still needs
  the fresh-session review (`/handoff` → new session → `/resume` → `/code-review` → post).
- **PR title ≤ 72 chars**, `^(feat|fix|docs|…)(\(scope\))?!?: [a-z].*[^.]$`; avoid `§` (byte-count).
- **Branch prune is squash-aware:** `git branch --merged main` can't see squash-merged branches; the
  prune asks `gh` which PRs merged and `-D`s only those.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** A signing `Timeout` = answer the
  host pinentry and retry.
- **`administration=write` is LIVE on the token** — can delete any org repo. FD11 guards apply.
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — **Next: BL-22 → BL-23 → BL-2.** Open: BL-1..BL-5,
  BL-15/16/18/20, BL-22..BL-30. BL-21 closed (sprint 36).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — migration DONE (sprint 35); post-migration
  work is backlog-driven. Sprint 36 recorded done there.
- `sprints/37_test_suite_velocity/sprint_plan.md` — **to be written** (first action of sprint 37).
