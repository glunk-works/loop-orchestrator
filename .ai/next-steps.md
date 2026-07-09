# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 23a (`trigger_review_fixes`) — `awaiting_hitl_review`.**
Sonnet/Coder implemented all 3 tasks and the green gate passes. Working tree
is **dirty, not committed**. Next is an Opus/Architect HITL re-review.

## Just done (Sonnet/Coder — 23a implementation)
- **Task 1 (`trigger/dispatch.py`):** added `self._tasks: set[asyncio.Task]`;
  `dispatch` now does `task = asyncio.create_task(...)`,
  `self._tasks.add(task)`, `task.add_done_callback(self._tasks.discard)` —
  closes the GC-cancellation window (finding #1). Added
  `except Exception: logger.exception("run failed for %s#%s", *key)` in
  `_run` before the `finally` (finding #3), swallowed so the dedupe key is
  still released for retry.
- **Task 2 (`trigger/app.py`):** replaced `await request.json()` with
  `try: payload = json.loads(raw_body) except ValueError: return
  Response(status_code=400)`, parsed from the already-read raw body;
  `import json` added; docstring updated to state the `400`-never-`500`
  contract (finding #2).
- **Tests:** added `test_in_flight_task_is_strongly_referenced_and_released_on_completion`
  + `test_run_failure_is_logged_and_releases_the_dedupe_key` to
  `test_dispatch.py`; added `test_signed_but_unparseable_body_returns_400_not_500`
  to `test_app.py`. All pre-existing trigger tests pass **unchanged**.
- **Docs:** `docs/migration_roadmap.md` — status table + NEXT ACTION narrative
  updated (Sprint 23 now "HITL-reviewed"), new **"Sprint-23a HITL-review
  settlements"** decisions-log bullet naming all 3 findings + resolutions.
  `.ai/context/modules.md` — `trigger/dispatch.py`/`app.py` paragraph
  refined with the retained-task and 400-on-bad-body behavior.
  `sprints/DEFERRED_VERIFICATION.md` §6 — added a one-line note to also
  check the bad-body-returns-400 path during the live webhook check.
- **Green gate: full pass.** `hatch run test` → 465 passed (0 failed);
  `hatch run lint` → all checks passed; `hatch run format` → 138 files
  unchanged; `hatch run audit` → no known vulnerabilities, no dep change.
- Nothing committed this session — see "Working tree" below.

## Next
1. **Commit the Sprint 23a diff.** Touched: `src/loop_engine/trigger/dispatch.py`,
   `src/loop_engine/trigger/app.py`, `tests/trigger/test_dispatch.py`,
   `tests/trigger/test_app.py`, `docs/migration_roadmap.md`,
   `.ai/context/modules.md`, `sprints/DEFERRED_VERIFICATION.md`.
2. **(Opus/Architect) HITL re-review the 23a diff** via `/code-review` (high
   effort, mirroring the 23 review). All 3 prior findings are addressed per
   locked decisions — expect a clean pass, but confirm rather than assume.
3. **(Opus/Architect) `/archive-sprint`** to retire both 23 and 23a once
   re-review is approved, then begin planning **Sprint 24 (maintenance flow)**.

## Carry-forward
- **Sprint 24 (maintenance flow)** — the first caller to chain `tools/repo_io`'s factory
  verbs (clone → feature-branch worktree → absorb `CLAUDE.md`/`.agent/STATE.md` →
  green gate → push → open PR against `develop`; auto-merge stays prohibited) and owns
  the deferred local-git subprocess-surface decision (`git push` in a cloned tree).
- **Open low nit (carried from 22b, still unresolved):** bare `python` vs
  `sys.executable` in the committed `loop_engine.mcp.json` github stanza.

## Pointers
- `sprints/23a_trigger_review_fixes/sprint_plan.md` — the 3-task review-fix plan +
  locked decisions (root cause, retention fix, 400-vs-204 split, catch-log).
- `sprints/23_trigger_surface/sprint_plan.md` — the reviewed sprint (context).
- `docs/migration_roadmap.md` — Phase 5 status; ▶ NEXT ACTION → Sprint 24 (gated
  behind 23a landing + re-review).
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- **Dirty — nothing from this session is committed.** Recommend committing
  the 23a diff (listed under "Next" above) before switching sessions so a
  `/resume`'s `last_commit` matches HEAD.
