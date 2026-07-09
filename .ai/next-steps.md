# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 22a (`loop_engine.mcp.json` multi-server MCP discovery) — `awaiting_hitl_review`.**
All 5 tasks implemented and green. **HITL gate open: 22a diff review (Opus/Architect).**
Working tree has uncommitted changes for Tasks 3-5 (see "Working tree" below) — review
before or after committing, your call, but commit before archiving.

## Just done (Sonnet/Coder — Tasks 3, 4, 5 implementation session)
- **Task 3 — two-server discovery/routing test:** new hermetic stdio fixtures
  `tests/tools/fixtures/{echo_server,greet_server}.py` (trivial FastMCP servers, no
  `loop_engine` dependency) + `tests/tools/test_mcp_multiserver.py`. Asserts a
  `MCPToolProvider` built from a two-server config discovers both tool sets, routes
  each call to the correct owning session, raises `MCPToolError` on an unknown tool,
  and its background thread is not alive after `__exit__`.
- **Task 4 — consumer-scope guard:** added
  `test_mcp_provider.py::test_extra_config_server_never_reaches_coder_provider` —
  monkeypatches `tools/mcp/config._repo_root` to a tmp dir holding a
  `loop_engine.mcp.json` with a `github`-like entry (bogus command, never launched)
  alongside `coder_tools`; asserts `build_coder_tool_provider` still yields exactly
  `{read_file, list_files, grep, run_tests}`.
- **Task 5 — docs:** `.ai/context/modules.md` (`tools/mcp/` bullet now describes
  config-driven, consumer-scoped discovery via `loop_engine.mcp.json`; the `.mcp.json`
  bullet at ~line 64 now explicitly distinguishes it from `loop_engine.mcp.json`),
  `CLAUDE.md` boundary bullet (mentions config-driven/consumer-scoped discovery + the
  new guard test), `docs/migration_roadmap.md` (status table, ▶ NEXT ACTION, cross-cutting
  #3 marked ✅, 22a sprint-decomposition bullet marked implemented). No dependency added —
  SBOM confirmed unchanged (no `pyproject.toml`/`sbom.json` diff).
- **Verified green:** `hatch run lint` clean, `hatch run format` clean (122 files
  unchanged), full suite **406 passed** (404 → 406, the two new tests).

## Next
1. **(Opus/Architect) HITL-review the Sprint 22a diff** — everything above, plus the
   already-committed Tasks 1-2 (`457f675`, `10df727`). Check: coder-tools parity held,
   consumer-scoping is a real enforced invariant (not just a docstring), fixture servers
   are truly hermetic/offline, docs don't conflate `loop_engine.mcp.json` with Claude
   Code's `.mcp.json`.
2. **On approval:** commit the Task 3-5 diff (currently uncommitted), then
   `/archive-sprint` 22a, then plan **Sprint 22b** (native `github_server` +
   `tools/repo_io` delegate + `loop_engine.mcp.json` github entry — outline exists in
   `docs/migration_roadmap.md`; open design item: reconcile the new git-clone subprocess
   surface against the "exactly three sanctioned subprocess surfaces" invariant).

## Pointers
- `sprints/22a_mcp_multiserver_discovery/sprint_plan.md` — the active sprint task list
  (all 5 tasks' acceptance criteria to check against during review).
- `docs/migration_roadmap.md` — Phase 5 planning-pass + decomposition (locked decisions)
  and the ▶ NEXT ACTION line.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- **Uncommitted:** `.ai/context/modules.md`, `CLAUDE.md`, `docs/migration_roadmap.md`,
  `tests/tools/test_mcp_provider.py` (modified); `tests/tools/fixtures/` (new dir),
  `tests/tools/test_mcp_multiserver.py` (new file); this file. `last_commit` in
  `.ai/state.json` (`10df727`) reflects HEAD, not this uncommitted diff — it will advance
  once the reviewer commits.
