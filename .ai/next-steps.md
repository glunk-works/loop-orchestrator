# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 24 (`maintenance_flow`) — `awaiting_hitl_review`.**
Implementation is done, green, and committed (`6172ad1`). The next session
is **Opus/Architect** HITL-reviewing the diff.

## Just done (Sonnet/Coder — Sprint 24 implementation, tasks 1–6)
- **Task 1:** `tools/git_io` — new local-git write surface (`checkout_branch`,
  `commit_all`, `push_branch`) against a cloned tree; the **fourth** sanctioned
  subprocess surface. Mirrors `tools/worktree/manager.py::_git`'s posture,
  validates every `tree` arg via `repo_io._validate_clone_dest`. Hermetic
  tests against a `tmp_path` repo + local bare remote (`tests/tools/git_io/`).
- **Task 2:** `runner.run_in_tree(human_input, tree_path, *, budget_usd,
  loop_name) -> State` — same loop-build as `run_new`, cwd pinned to the
  clone, deliberately **not** opening `worktree_run`. Cwd restored via
  `finally` on every exit path; proven to never re-enter `worktree_run` even
  with `LOOP_ENGINE_ISOLATION=worktree` set.
- **Task 3:** `src/loop_engine/flows/maintenance/` — `MaintenanceRequest` /
  `MaintenanceResult` (pydantic, `extra="forbid"`) + `run_maintenance()`
  chaining `clone_repo` → `checkout_branch` → `run_step` (defaults to
  `run_in_tree`) → green gate (`coder_tools.run_pytest` against the clone's
  `src/`) → **green-only** `commit_all`/`push_branch`/`open_pr` (base
  `develop`); red ⇒ no commit/push/PR. Every collaborator injectable.
- **Task 4:** `tests/flows/test_boundaries.py` (no `keyring`, no direct file
  write, no subprocess surface of its own in `flows/`) +
  `tests/tools/test_subprocess_surfaces.py` (repo-wide static assertion,
  sanctioned surfaces **three → four**, naming `tools/git_io`).
- **Task 5:** `tests/flows/maintenance/test_integration.py` — hermetic
  green/red end-to-end proof: real `git_io` against a `tmp_path` repo + local
  bare remote (`repo_io`/the loop run faked). Green pushes + opens a PR
  against `develop`; red touches neither.
- **Task 6:** Updated `CLAUDE.md` (module boundaries: four surfaces, new
  `tools/git_io` + `flows/` entries), `.ai/context/modules.md` (`git_io`,
  `run_in_tree`, `flows/maintenance`), `docs/migration_roadmap.md` (status
  row, NEXT ACTION → Sprint 25, Sprint 24 decisions log entry), and
  `sprints/DEFERRED_VERIFICATION.md` (§7, the deferred live clone→push→PR
  check).
- **Green gate:** full suite **493 passed**; `hatch run lint`/`format`/`audit`
  clean; `sbom.json` **unchanged** (no dependency added).

## Next
1. **(Opus/Architect) HITL-review the Sprint 24 diff** (`6172ad1`) against
   `sprints/24_maintenance_flow/sprint_plan.md`'s locked decisions (capability
   slice; `git_io` as the 4th surface; `run_in_tree` no-`worktree_run`;
   green-only push/PR; `flows/` boundary posture). Fix any findings, re-verify
   green.
2. `/archive-sprint` only after the review is clean and committed.
3. After archival: plan **Sprint 25 (bootstrap flow, piece 4)**.

## Carry-forward
- **Open low nit (carried from 22b, still unresolved):** bare `python` vs
  `sys.executable` in the committed `loop_engine.mcp.json` github stanza —
  orthogonal to this flow, not touched in 24.

## Pointers
- `sprints/24_maintenance_flow/sprint_plan.md` — the task list this sprint
  implemented (all 6 tasks, all acceptance criteria met).
- `docs/migration_roadmap.md` — Phase 5 status; ▶ NEXT ACTION → HITL review
  Sprint 24, then plan Sprint 25.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- **Clean.** Sprint 24's implementation is committed at `6172ad1` (`Phase 5
  sprint 24: implement maintenance flow, handoff to Opus`).
