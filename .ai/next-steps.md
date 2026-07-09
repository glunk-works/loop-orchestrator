# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 23a (`trigger_review_fixes`) — `implementing`.**
Opus/Architect HITL-reviewed the Sprint 23 diff and planned a review-fixes
sprint (23a). Plan is HITL-approved; next is a Sonnet/Coder implementation session.

## Just done (Opus/Architect — 23 HITL review + 23a planning)
- **HITL-reviewed the Sprint 23 trigger-surface diff (`62a3de2`)** via `/code-review`
  (high effort). Verdict: otherwise correct (HMAC-before-JSON ordering, fail-closed
  secret, parser grammar, `cli.run → runner.run_new` refactor, mirrored engine
  indirection all hold), but **3 findings** surfaced on the dispatch/webhook path.
- **Finding #1 (high):** `InProcessDispatcher.dispatch` discards the `asyncio.create_task`
  result and nothing holds a strong ref → the run task can be GC-cancelled mid-flight,
  which also permanently wedges its `(repo, issue)` dedupe key in `_active`.
- **Finding #2 (medium):** `await request.json()` is unguarded → a signed-but-non-JSON
  body (e.g. a form-encoded webhook) raises → HTTP 500, breaking the "never 500 on a
  malformed delivery" contract. **HITL decision: return `400`** (not 204, not 500).
- **Finding #3 (low-med):** run failures in `_run` are never logged (no `except`).
- **Wrote `sprints/23a_trigger_review_fixes/sprint_plan.md`** (3 tasks, all decisions
  locked) per the user's choice to route the fixes into a dedicated review-fixes sprint
  (mirrors 19a/21). No new dep / sbom / subprocess / State change.
- Working tree carries the new `sprints/23a_trigger_review_fixes/` (untracked); nothing
  committed this session.

## Next
1. **(Sonnet/Coder) Implement Sprint 23a's 3 tasks** against
   `sprints/23a_trigger_review_fixes/sprint_plan.md`:
   - **Task 1 (`trigger/dispatch.py`):** retain the task in a strong-ref `self._tasks`
     set + `add_done_callback(self._tasks.discard)` (fixes #1); add
     `except Exception: logger.exception("run failed for %s#%s", *key)` before the
     `finally` (fixes #3).
   - **Task 2 (`trigger/app.py`):** guard the parse — `json.loads(raw_body)` in a
     `try/except ValueError: return Response(status_code=400)` (fixes #2); `import json`;
     update the docstring. 400 is deliberate — unrelated/`ping` bodies still 204.
   - **Task 3:** docs — roadmap (mark 23 reviewed + "Sprint-23a HITL-review settlements"
     bullet; NEXT ACTION stays Sprint 24) + `modules.md`.
   - Green gate (`hatch run test` + `lint` + `format`); boundary tests + all existing
     trigger tests must stay green **verbatim**. Then `/handoff` back to Opus.
2. **(Opus/Architect) HITL re-review the 23a diff**, then `/archive-sprint` to retire
   both 23 and 23a, and begin planning **Sprint 24 (maintenance flow)**.

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
- `sprints/23a_trigger_review_fixes/` is untracked (the new plan). Recommend committing
  it before switching sessions so a `/resume`'s `last_commit` matches HEAD.
