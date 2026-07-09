# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 22b (`native github_server`) — `planning`.**
Sprint 22a is complete, reviewed, and **archived**. 22b is the foundation slice of
Phase 5 proper: the system's *second* MCP server, built native re-front. **No plan
written yet** — the next action is to write it (Opus/Architect, planning pass, one
question at a time, HITL-gated).

## Just done (Opus/Architect — 22a HITL review + archive)
- **Reviewed the Sprint 22a diff** (`457f675` → `71f1692`): coder-tools parity held,
  consumer-scoping confirmed as a real enforced invariant (not a docstring), fixture
  servers hermetic/offline, docs distinguish `loop_engine.mcp.json` from Claude Code's
  `.mcp.json`. **Approved.**
- **Fixed 2 quality findings** (review-fixes, `d0e118d`): deleted the now-dead
  `coder_tools_server_params()` (+ export + unused `sys` import) — `config.py::_default_servers()`
  is now the single source of truth for the coder-tools local launch; renamed the
  `.mcp.json`-named config fixture in `tests/tools/test_mcp_config.py` to
  `loop_engine.mcp.json`. Lint clean, format unchanged, **406 passed**.
- **Archived 22a**: snapshot at `.ai/archive/22a_mcp_multiserver_discovery-next-steps.md`;
  roadmap Phase 5 row + ▶ NEXT ACTION advanced to 22b; `.ai/state.json` → `22b_native_github_server` / `planning`.

## Next
1. **(Opus/Architect) Plan Sprint 22b** — write `sprints/22b_native_github_server/sprint_plan.md`.
   Scope (from the roadmap decisions log): the native `github_server` MCP server (factory
   verbs `{create_repository, clone_repo, create_branch, open_pr}`), a new `tools/repo_io`
   delegate (GitHub-owning sibling to `issue_io`; `issue_io` stays on its current direct
   path, untouched), its `loop_engine.mcp.json` github stanza (static launch spec), and the
   **orchestrator-side** consumer (`provider.execute("open_pr", …)`, no LLM loop — github
   verbs must never enter the model's tool loop; the 22a consumer-scope guard already enforces
   this pre-emptively).
2. **Settle the open design item first** (it gates the plan): cloning target repos introduces
   a **new git subprocess surface**. Reconcile against the "exactly three sanctioned subprocess
   surfaces" invariant — extend `tools/worktree` vs. add a fourth sanctioned surface. This is an
   Architect decision, explicitly deferred out of 22a.
3. **Note:** 22b's first real network + `gh`-auth server launch has **no live verification on
   this branch** (no daemon host, no second real server e2e). Plan for unit/hermetic coverage
   and append the live check to `sprints/DEFERRED_VERIFICATION.md`.

## Pointers
- `docs/migration_roadmap.md` — Phase 5 planning-pass + sprint-decomposition (locked decisions),
  the 22b outline, and the ▶ NEXT ACTION line.
- `sprints/22a_mcp_multiserver_discovery/sprint_plan.md` — the completed 22a plan (precedent
  for the 22b plan's shape; the discovery/scoping substrate 22b builds on).
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- 22a review-fixes committed as `d0e118d`. This archival edit (roadmap + `.ai/`) is uncommitted —
  commit it to make the archive durable.
