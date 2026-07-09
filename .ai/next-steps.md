# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 23 (`trigger_surface`) — `awaiting_hitl_review`.**
Sonnet/Coder implementation is done, committed, all green. Next is an
Opus/Architect HITL review session.

## Just done (Sonnet/Coder — 23 implementation, `62a3de2`)
- **Task 1 — `src/loop_engine/runner.py`**: `run_new(human_input, *, budget_usd,
  loop_name) -> State`, the shared "start a fresh run" orchestration factored
  out of `cli.run`'s fresh-run path (which now delegates to it). Carries its
  own mirrored `_resolve_loop`/`_select_engine`/`NAMED_LOOPS` (independently
  patchable from `cli.py`'s copy — two fresh-run-path tests in `test_cli.py`
  were retargeted to patch `loop_engine.runner.*` instead of `loop_engine.cli.*`
  accordingly). `cli.run`'s `--resume-from` path is untouched.
- **Task 2 — `trigger/parse.py`**: `RunRequest` (pydantic, `extra="forbid"`)
  + `parse_event(event_name, payload) -> RunRequest | None` implementing the
  locked grammar (`agent-action` label / `/agent-run` comment; `human_input`
  = title+body; everything else, including malformed payloads and `ping`, is
  a defensive `None`, never a raise).
- **Task 3 — `trigger/dispatch.py`**: `RunDispatcher` `Protocol` +
  `InProcessDispatcher` — in-memory dedupe on `(repo, issue)`, worker-thread
  dispatch (`asyncio.to_thread` via `asyncio.create_task`) so `dispatch()`
  returns before the run finishes and the event loop never blocks.
- **Task 4 — `trigger/app.py`**: `create_app(dispatcher=None) -> FastAPI`,
  fail-closed on missing `LOOP_ENGINE_WEBHOOK_SECRET`; `POST /webhook` reads
  the raw body, HMAC-SHA256-verifies `X-Hub-Signature-256` over those exact
  bytes before any JSON parsing, then parses → `204` no-op or dispatch →
  `202`; `GET /health`. The module-level `app` is built only when the secret
  is already set in the environment, so importing the module never raises in
  a dev/test env lacking it (still `create_app()` for eventual `uvicorn`
  hosting).
- **Task 5 — `tests/trigger/test_boundaries.py`**: AST-scanned (mirrors the
  `keyring`/`state_io` boundary tests) — no `keyring`, no direct file write,
  no subprocess surface anywhere under `trigger/`; plus a hermetic signed
  webhook → `202` → fake-dispatcher-observed end-to-end proof.
- **Task 6 — deps/SBOM/docs**: `fastapi==0.139.0` pinned runtime (`uvicorn`
  deferred), `httpx==0.28.1` dev/test-only; `sbom.json` regenerated, `hatch
  run audit` green. `CLAUDE.md`, `.ai/context/modules.md`,
  `docs/migration_roadmap.md` (status row, NEXT ACTION → Sprint 24, decisions
  log entry, sprint-decomposition entry) and
  `sprints/DEFERRED_VERIFICATION.md` (§6, live webhook check) all updated.
- Full suite green throughout (462 tests at commit time), lint/format clean.
- Committed as `62a3de2` ("Phase 5 sprint 23: implement trigger surface (all
  6 tasks)").

## Next
1. **(Opus/Architect) HITL-review the Sprint 23 diff** (`62a3de2`) —
   `/code-review` against it. Points of interest: the deliberately-mirrored
   (not shared) engine-selection indirection in `cli.py` vs `runner.py`; the
   HMAC raw-body-before-JSON-parse ordering in `trigger/app.py`; the
   guarded (not unconditional) module-level `app` construction; the
   in-memory dedupe + worker-thread dispatch in `trigger/dispatch.py`.
2. **On approval:** confirm `docs/migration_roadmap.md`'s NEXT ACTION (already
   advanced to Sprint 24 as part of Task 6) reads correctly, then
   **`/archive-sprint`** to retire 23 and begin planning Sprint 24
   (maintenance flow).

## Carry-forward
- **Sprint 24 (maintenance flow)** is the first caller to chain
  `tools/repo_io`'s factory verbs (clone → feature-branch worktree → absorb
  target repo's `CLAUDE.md`/`.agent/STATE.md` → green gate → push → open PR
  against `develop`; auto-merge stays prohibited) and owns the deferred
  local-git subprocess-surface decision (`git push` inside a cloned tree).
- **Open low nit (carried from 22b, still unresolved):** bare `python` vs
  `sys.executable` in the committed `loop_engine.mcp.json` github stanza —
  pick up if convenient.

## Pointers
- `sprints/23_trigger_surface/sprint_plan.md` — the completed task list (6
  tasks) + locked decisions, for review context.
- `docs/migration_roadmap.md` — Phase 5 sprint-decomposition entry for 23;
  ▶ NEXT ACTION now points at Sprint 24 (maintenance flow).
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- Clean. Everything for Sprint 23 landed in `62a3de2` on
  `feat/mcp-langgraph-migration`.
