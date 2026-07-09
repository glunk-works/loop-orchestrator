# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 22b (`native github_server`) — `implementing`.**
Plan written and **HITL-approved**. Ready for a Sonnet/Coder session to implement it.
This is the foundation slice of Phase 5 proper: the system's *second* MCP server.

## Just done (Opus/Architect — 22b planning pass)
- **Settled the two gating design decisions** and wrote the plan
  (`sprints/22b_native_github_server/sprint_plan.md`, HITL-approved):
  1. **gh-only; local-git surface deferred to Sprint 23.** All four factory verbs
     ride the existing `gh` executable (`gh repo create` / `gh repo clone` /
     `gh api …/git/refs` / `gh pr create`), so `tools/repo_io` is a **second `gh`
     consumer** and adds **NO fourth subprocess surface** — the invariant stays at
     three (its `gh` clause widens to name `issue_io` + `repo_io`).
  2. **Capability slice + committed config.** Ships server + `tools/repo_io` delegate
     + a **committed** repo-root `loop_engine.mcp.json` github stanza + consumer-scoped
     `build_github_provider()` + hermetic tests + docs; **no** production flow caller
     (that's Sprint 23).
- **Pre-verified** the committed-config risk: every `test_mcp_config.py` case uses a
  `tmp_path` override; the only no-arg `load_mcp_config()` is inside consumer-scoped
  `build_provider_for` — so committing the first real `loop_engine.mcp.json` cannot
  perturb the coder path.

## Next
1. **(Sonnet/Coder) Implement Sprint 22b** — Tasks 1–5 in order from the sprint_plan:
   (1) `tools/repo_io` delegate, (2) `mcp_servers/github_server` re-front,
   (3) committed `loop_engine.mcp.json` + `build_github_provider()`, (4) bidirectional
   consumer-scope guard, (5) docs + roadmap→Sprint 23 + `DEFERRED_VERIFICATION.md`.
   **Do not re-open the two locked decisions** (Context section of the plan).
2. **Mirror precedents exactly:** `mcp_servers/coder_tools_server.py` (re-front shape),
   `tools/issue_io/github.py` (gh-shelling delegate + `patch("...._run_gh")` test style).
3. **All tests hermetic** (no `gh`/network on this branch); append the live
   `github_server`-launch check to `sprints/DEFERRED_VERIFICATION.md`. Run the green
   gate (lint/format/test) before handing back for **Opus HITL review**.

## Pointers
- `sprints/22b_native_github_server/sprint_plan.md` — the approved plan (5 tasks +
  the two locked-decision Context block).
- `docs/migration_roadmap.md` — Phase 5 planning-pass + sprint decomposition; the
  22b outline and the ▶ NEXT ACTION line.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- **Clean.** The approved plan + this cursor are committed on
  `feat/mcp-langgraph-migration` (see `.ai/state.json` `last_commit` for the exact HEAD).
