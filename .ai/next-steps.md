# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 22b (`native github_server`) — `review_approved`.**
Opus/Architect HITL review of `7b46227` done: **approved with one required
fix**, which has now landed (see below). Ready to `/archive-sprint` and advance
to Sprint 23 planning.

## Just done (Opus/Architect — 22b HITL review + review-fix)
- **HITL review of `7b46227`** — boundaries held (repo_io mirrors
  `issue_io.github` transport exactly; `build_github_provider` consumer-scope
  guard is airtight; side-effect-free import proven; no merge verb). **One
  required finding:**
- **Finding 1 (fixed):** `_validate_clone_dest` gated its symlink-escape check
  on `path.exists()`, so the normal clone case (target not yet created, parent
  a symlink escaping the run tree — `link/repo` where `link -> /outside`) sailed
  through. Fix: resolve unconditionally (`Path.resolve()` resolves the symlinked
  prefix even for a non-existent tail); added
  `test_clone_repo_rejects_symlinked_parent_with_nonexistent_target`. Green gate
  re-run: **426 passed**, lint/format clean.
- **Finding 2 (deferred, low):** committed `loop_engine.mcp.json` launches the
  github server with bare `python` vs `coder_tools`' `sys.executable` — a latent
  PATH-ambiguity nit, left as-is (static JSON can't call `sys.executable`).

## Was done (Sonnet/Coder — 22b implementation, commit `7b46227`)
- **Task 1:** `tools/repo_io` — new GitHub-owning delegate (sibling to
  `issue_io`): `create_repository`, `clone_repo`, `create_branch`, `open_pr`,
  all shelling to `gh` (mirrors `issue_io.github`'s `_run_gh` shape exactly).
  `clone_repo`'s `dest` is traversal/symlink-validated before any `gh` call.
- **Task 2:** `mcp_servers/github_server.py` — native MCP re-front (mirrors
  `coder_tools_server.py`), exposes exactly
  `{create_repository, clone_repo, create_branch, open_pr}`; import is
  side-effect-free (offline/hermetic discovery, verified by real-server launch).
- **Task 3:** Committed the **first real** `loop_engine.mcp.json` (repo root,
  `github` stanza) + `build_github_provider()` in `tools/mcp/provider.py`
  (`GITHUB_SERVER_NAME` added to `tools/mcp/config.py`), exported from
  `tools/mcp/__init__.py`.
- **Task 4:** Bidirectional consumer-scope guard tests in
  `tests/tools/test_mcp_provider.py` — with the real committed config in
  effect, the coder provider and github provider tool sets are proven exactly
  their own four tools each and disjoint.
- **Task 5:** Docs updated — `CLAUDE.md` (GitHub-owner + subprocess-surface +
  `mcp_servers/` bullets widened), `.ai/context/modules.md` (`repo_io` +
  `github_server` entries), `docs/migration_roadmap.md` (status row, NEXT
  ACTION, sprint-decomposition entry, cross-cutting #2/#3 marked delivered),
  `sprints/DEFERRED_VERIFICATION.md` (§5, the live `gh`-auth check deferred to
  a daemon-bearing host).
- **Green gate:** `hatch run lint`/`format`/`test` — 425 passed. No new
  dependency, no SBOM change, no new subprocess surface (gh-only decision
  held: `repo_io` is a second `gh` consumer, not a fourth surface).

## Next
1. **`/archive-sprint`** to retire 22b (review approved, fix landed, committed),
   snapshot this cursor into `.ai/archive/`, and advance `.ai/state.json` to
   Sprint 23.
2. **Plan Sprint 23** (Opus/Architect) — trigger surface → maintenance flow →
   bootstrap flow (the first production caller of the github factory verbs) —
   see `docs/migration_roadmap.md`'s Phase 5 sprint-decomposition section.

## Pointers
- `sprints/22b_native_github_server/sprint_plan.md` — the implemented plan
  (5 tasks + the two locked-decision Context block).
- `docs/migration_roadmap.md` — Phase 5 status + sprint decomposition; the
  ▶ NEXT ACTION line now points at this review, then Sprint 23 planning.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- The 22b review-fix commit (this one) lands `tools/repo_io/github.py` +
  `tests/tools/test_repo_io.py` + this cursor on `feat/mcp-langgraph-migration`;
  update `.ai/state.json` `last_commit` to that hash at archive time.
