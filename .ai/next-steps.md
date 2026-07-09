# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Autonomous triggers + multi-repo factory — `implementing` (Sprint 22a).**
Phase 5 planning is done and decomposed **foundation-first** (github MCP server first).
The first sub-sprint — **22a, `.mcp.json` multi-server discovery** — has a written,
**HITL-approved** plan and is ready to implement. No HITL gate open (the next gate is
review of the 22a diff, after implementation).

## Just done
- **Phase 5 planning pass (Opus/Architect), locked & recorded in the roadmap:**
  foundation = **native** `github_server` (not the official server; keeps the enforced
  exact-tool-set + least-privilege boundary); credential = **`gh` CLI's own auth**
  (Infisical deferred); tool surface = **factory verbs only** (`create_repository,
  clone_repo, create_branch, open_pr`); discovery = **full `.mcp.json` multi-server**
  (cross-cutting #3) with **consumer-scoping** (github tools never reach the model loop)
  + **heterogeneous launch profiles** (coder sandboxed/no-net; github network+auth).
  Split into **22a** (discovery) / **22b** (github server), separately gated.
- **Wrote `sprints/22a_mcp_multiserver_discovery/sprint_plan.md`** (5 tasks) and updated
  `docs/migration_roadmap.md` (Phase 5 section: planning decisions + 22a/22b decomposition
  + 22b outline; status row + ▶ NEXT ACTION line).

## Next
1. **(Sonnet / Coder) Implement Sprint 22a** per its `sprint_plan.md`. Pure client-side
   refactor of `tools/mcp`: `.mcp.json` loader + consumer-scoped `build_provider_for(names)`;
   `MCPToolProvider` already does multi-session routing. **Coder-tools parity is the
   load-bearing gate**; adds **no** new server/subprocess/credential/file-write surface.
   Green gate (lint/format/test) before claiming any AC. → then HITL-review the 22a diff (Opus).
2. **22b (later, after 22a review):** native `github_server` + `tools/repo_io` delegate.
   **Flag for 22b planning:** cloning target repos = a **new git subprocess surface** vs.
   the "exactly three sanctioned surfaces" invariant — Architect decision.

## Pointers
- `sprints/22a_mcp_multiserver_discovery/sprint_plan.md` — the active sprint task list.
- `docs/migration_roadmap.md` — Phase 5 "planning pass" + "sprint decomposition" subsections
  (locked decisions) and the ▶ NEXT ACTION line.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.
