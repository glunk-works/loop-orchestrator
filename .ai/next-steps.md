# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, Tasks 1–2 reviewed — verdict REVISE.** The Opus HITL review of
PR #57 found Task 1's encoding fix is **inverted** (it introduces the mismatch it claims to
prevent) and its regression test is a **tautology** (it passes with the fix removed — verified).
**The review was deliberately NOT posted to the PR.** `architect-review` binds to the head
commit, so a fix commit invalidates any review posted now; the gate should go green on code
that is right. **Next session is Sonnet/Coder** to revise on the live `sprint/35-tasks-1-2`.

## Just done (Opus/Architect review session, 2026-07-13)
- **`/code-review` of PR #57 at head `d2c3797`** — 7 findings, 2 of them blocking. Nothing was
  pushed and nothing was posted to GitHub; the working tree is unchanged.
- **F1 (blocking) — the encoding fix is backwards.** `publish_artifacts` now reads with
  `encoding="utf-8"`, but `state_io/writer.py::write_artifact` still writes with bare
  `write_text(content)` (locale default). The two sides **matched before this change** (both
  default) and **mismatch after it**. On a non-UTF-8 default host (Windows cp1252, or
  `PYTHONUTF8=0` + non-UTF-8 locale), stage 1 writes `café` as cp1252 and stage 2 reads it as
  UTF-8 → `UnicodeDecodeError` (reproduced), which propagates and kills the stage.
  The handoff's rationale — *"`write_artifact` uses the same default-text-encoding path, so no
  mismatch"* — is exactly inverted.
- **F2 (blocking) — the regression test does not test the regression.** Deleting the
  `encoding="utf-8"` kwarg and re-running `tests/tools/test_artifact_store.py` still gives
  **6 passed** (verified). The `read_bytes() == body.encode("utf-8")` assertion is satisfied by
  the *write* side's locale default on a UTF-8 host — a tautology on CI.
- F3–F7 (non-blocking, listed below).

## Next — Sonnet/Coder
**Fresh session. Push revision commits to the EXISTING `sprint/35-tasks-1-2` branch** — PR #57
is open and **not** merged, so the branch is **live, not dead**. Do not cut a new branch.

1. **F1** — pin the **write** side: `write_artifact`'s `write_text(content, encoding="utf-8")`.
   Do it at the **`state_io` single-writer boundary**, not at the caller (**F3**, altitude):
   `write_state_snapshot`, `write_agent_scratchpad`, `append_agent_memory` (both its read and
   write), plus the snapshot read-backs in `cli.py` and the `.agent/` reads in
   `agent_state/store.py` are all still on the locale default. `State.artifacts` is embedded in
   the snapshot, so the resume path carries the identical latent bug.
2. **F2** — make the test fail without the fix: force a non-UTF-8 default (subprocess with
   `PYTHONUTF8=0` + `LC_ALL=C`, or monkeypatch `locale.getpreferredencoding`). **F7:**
   `@pytest.mark.parametrize` it over the existing idempotence test rather than copy-pasting it.
3. **F4** — the new docstrings over-correct: *"the read still happens for every artifact on every
   stage"* is false, because `path.exists()` short-circuits — there is **no** read on first
   publish. Say "every artifact that already exists on disk."
4. **F5 (docs)** — `.ai/context/workflow.md`'s historical note is past-tense about a merge that
   **hasn't happened**, and CLAUDE.md's new "cut from `main`" rule goes live the moment #57
   merges — several tasks before `main` actually contains the migration. Add a one-line window
   marker (rule takes effect once the sprint-35 merge lands; removable in Task 5).
5. **F6 (docs)** — `workflow.md`'s "(and on pushes to `main` only)" contradicts `ci.yml`
   (`push: branches: [main, 'feat/**']`). Correct it, and note the `feat/**` strip from `ci.yml`
   + the ruleset as post-merge cleanup for Task 5.

Then run the green gate (`hatch run test` / `lint` / `format`), push, and hand to a **fresh Opus
session** to review the corrected head and post the `**Opus/Architect HITL review (automated)**`
via `gh pr review --comment` (never `--approve`).

Task 2's substance is otherwise **sound** — every integration-gate rule survives, and the only
residual `feat/` references are the four intentional ones.

**Then (Opus/human):** Task 3 pre-merge preflight → Task 4 open the migration PR → **Task 5 the
merge + settings sequence (HUMAN-ONLY)** → Task 6 sequence the follow-on work.
**PR #55 approved the plan, not Tasks 3–5's execution — that HITL gate is still open.**

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Last verified live
  2026-07-13: `allow_squash_merge=true`, `allow_merge_commit=true`, `allow_rebase_merge=false`,
  `squash_merge_commit_title=PR_TITLE`, `delete_branch_on_merge=true`. Ordinary sprint PRs
  (including #57) are **SQUASH** — the merge-commit button exists only for the one migration PR.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major** action
  bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends on being
  identical. They get real review in Task 6, *after* the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the PAT's
  repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) — the
  approved plan. FD1–FD7 locked.
- PR #57 — Tasks 1–2, **no review posted**, verdict REVISE. Branch is live.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design** (closes in
  Task 5); BL-12/BL-14's topology gap closes with the merge itself.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2, pushed, PR #57 open against `feat/mcp-langgraph-migration`.
  **Live — push the revision commits here.** Clean at `d2c3797`.
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as #55/#56)
  — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is tracked.
