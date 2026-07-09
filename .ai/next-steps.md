# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 22a (`.mcp.json` multi-server MCP discovery) — `blocked`.**
Implementation started (Sonnet/Coder) but hit an unanticipated filename collision
that needs an Architect decision before continuing. **HITL gate open:
`architect_decision_pending`.**

## Just done
- **Coder session started Sprint 22a implementation** (uncommitted, still in the
  working tree — nothing committed this session, HEAD still `0275a6c`):
  - **Task 1 (mostly done):** `src/loop_engine/tools/mcp/config.py` (new) —
    `MCPServerSpec`/`MCPConfigFile` pydantic models (`extra="forbid"`),
    `load_mcp_config(path=None)` with built-in `coder_tools` default + merge-over-default
    by logical name. `tests/tools/test_mcp_config.py` (new) — all tests pass an explicit
    `path=` override, so they're unaffected by the blocker below.
  - **Task 2 (done):** `build_provider_for(names, *, cwd)` added to
    `tools/mcp/provider.py`; `build_coder_tool_provider` refactored to a thin wrapper
    over it; `coder_tools`'s isolation-aware (`container`/`sandbox`) launch preserved
    as a special case. `tools/mcp/__init__.py` exports updated.
  - **Tasks 3, 4, 5: not started.**
- **Blocker discovered:** the sprint plan's assumption that loop-engine's own MCP
  client config lives at repo-root **`.mcp.json`** collides with an **already-existing**
  file at that path — **Claude Code's own MCP server config**
  (`{"mcpServers": {"github": {...}}}`, committed in `65ed47c`), a completely different
  schema/purpose (Claude Code's tool wiring for this session, not loop-engine's
  `stdio_client` launch specs). Loading it through our loader throws a validation error
  (`extra="forbid"` rejects the unrecognized `mcpServers` key). User was asked how to
  resolve it and chose: **pause and let Opus/Architect decide**, rather than a Sonnet/Coder
  judgment call — this revises a locked planning-pass decision (the file path was named
  explicitly in the sprint plan's "Context (locked decisions)" section).

## Next
1. **(Opus / Architect) Resolve the `.mcp.json` collision.** Pick a non-colliding
   name/location for loop-engine's own config (candidates raised in the session:
   `loop_engine.mcp.json` at repo root, or `.ai/mcp.json`). Update
   `sprints/22a_mcp_multiserver_discovery/sprint_plan.md` (Task 1 description, Task 5
   docs task, and the "Context (locked decisions)" section) and
   `docs/migration_roadmap.md`'s Phase 5 / 22a decisions section if it names the path.
   Confirm no other Phase 5 planning text assumed the collision-free path.
2. **(Sonnet / Coder) Resume implementation** once the path is settled:
   - Fix `_CONFIG_FILENAME` in `src/loop_engine/tools/mcp/config.py` to the new name.
   - **Task 3:** multi-server discovery + routing test (two-server end-to-end).
   - **Task 4:** consumer-scope guard test (coder provider never sees non-coder tools
     even when `.mcp.json` declares them).
   - **Task 5:** docs (`.ai/context/modules.md`, `CLAUDE.md` boundary bullet,
     `docs/migration_roadmap.md`) + confirm no SBOM change.
   - Run the green gate (lint/format/test) before claiming any acceptance criterion.
   - Then → HITL-review the 22a diff (Opus).

## Pointers
- `sprints/22a_mcp_multiserver_discovery/sprint_plan.md` — the active sprint task list
  (needs the path-collision edit described above).
- `docs/migration_roadmap.md` — Phase 5 "planning pass" + "sprint decomposition"
  subsections (locked decisions) and the ▶ NEXT ACTION line.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree (uncommitted)
- Modified: `src/loop_engine/tools/mcp/__init__.py`, `src/loop_engine/tools/mcp/provider.py`
- New: `src/loop_engine/tools/mcp/config.py`, `tests/tools/test_mcp_config.py`
