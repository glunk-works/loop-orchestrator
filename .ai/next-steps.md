# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 22a (`loop_engine.mcp.json` multi-server MCP discovery) — `implementing`.**
The blocker is resolved (Architect decision made + applied, branch verified green).
Tasks 1 & 2 done; **Tasks 3, 4, 5 remain** (Sonnet/Coder). No HITL gate open.

## Just done (Opus/Architect — blocker resolution session)
- **Resolved the `.mcp.json` collision.** Decision: loop-engine's own MCP config
  file is **`loop_engine.mcp.json`** at repo root — NOT `.mcp.json`, which is
  already Claude Code's reserved project MCP config (`{"mcpServers": …}`, the
  devcontainer github wiring, committed `65ed47c`). User confirmed the name.
- **Root cause fixed:** the branch was in fact **red at HEAD** — `build_provider_for`'s
  no-arg `load_mcp_config()` read Claude Code's `.mcp.json` and crashed `extra="forbid"`,
  erroring all 8 `test_mcp_provider.py` tests. Renaming `_CONFIG_FILENAME` restores the
  absent-file → built-in-default fallback.
- **Edits:** `src/loop_engine/tools/mcp/config.py` (`_CONFIG_FILENAME` + docstrings +
  a why-not-`.mcp.json` note), `provider.py` (docstring + `KeyError` msg),
  `sprints/22a_.../sprint_plan.md` (path swap + dated locked-decision bullet + Task 5
  now requires docs to distinguish from Claude Code's `.mcp.json`),
  `docs/migration_roadmap.md` (path swap + dated revision bullet),
  `tests/tools/test_mcp_config.py` (pre-existing E501 that was also failing lint).
  Left untouched (correct): the *Claude Code* `.mcp.json` refs in
  `docs/architecture_definition.md:58` & `.ai/context/modules.md:64`.
- **Verified green:** `hatch run lint` clean, `hatch run format` clean, full suite
  **404 passed**. No new file created (`loop_engine.mcp.json` absent = default; 22a
  tests use `path=` overrides).

## Next
1. **(Human) Commit the resolution first** — the tree is dirty and `/resume` expects
   `last_commit` to match HEAD. Suggested message:
   `Phase 5 sprint 22a: rename loop-engine MCP config to loop_engine.mcp.json (unblock)`.
2. **(Sonnet / Coder) Implement Tasks 3, 4, 5** of the sprint plan:
   - **Task 3:** two-server discovery + routing test through the real `MCPToolProvider`
     (hermetic/offline — two trivial stdio servers or coder-tools declared twice).
   - **Task 4:** consumer-scope guard — `build_coder_tool_provider` yields exactly
     `{read_file, list_files, grep, run_tests}` even when the config also declares a
     github-like server.
   - **Task 5:** docs (`.ai/context/modules.md` — **must distinguish `loop_engine.mcp.json`
     from Claude Code's existing `.mcp.json` at ~line 64**; `CLAUDE.md` boundary bullet;
     roadmap cross-cutting #3 note) + confirm no SBOM change.
   - Run the green gate before claiming any acceptance criterion.
3. **(Opus) HITL-review the 22a diff**, then archive on approval.

## Pointers
- `sprints/22a_mcp_multiserver_discovery/sprint_plan.md` — the active sprint task list
  (path decision now locked to `loop_engine.mcp.json`).
- `docs/migration_roadmap.md` — Phase 5 planning-pass + decomposition (locked decisions,
  incl. the 2026-07-09 config-filename revision) and the ▶ NEXT ACTION line.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree (uncommitted — commit before `/resume`)
- Modified: `src/loop_engine/tools/mcp/config.py`, `src/loop_engine/tools/mcp/provider.py`,
  `tests/tools/test_mcp_config.py`, `sprints/22a_mcp_multiserver_discovery/sprint_plan.md`,
  `docs/migration_roadmap.md`
