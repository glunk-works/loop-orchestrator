# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 — Collapse the flags — Sprint 26 (`issue_io_mcp_unification`) —
`awaiting_hitl_review`.** Implementation (Sonnet/Coder) is done, all 6 tasks
green. Next session is **Opus/Architect**, HITL-reviewing the diff.

## Just done (Sonnet/Coder — Sprint 26 implementation pass)
- **Task 1:** split `tools/issue_io` into pure `render_question_issue`/
  `parse_issue_answers` and the two `gh`-touching primitives `create_issue`/
  `read_issue`; `file_question_issue`/`read_issue_answers` are now thin,
  behavior-preserving wrappers (all pre-existing tests pass unmodified).
- **Task 2:** `mcp_servers/issue_io_server.py` (the third native MCP server,
  mirrors `github_server.py`, exposes exactly `{create_issue, read_issue}`,
  no `gh` at import) + a matching `issue` stanza in `loop_engine.mcp.json`.
- **Task 3:** `build_issue_provider()` (`tools/mcp/provider.py`) +
  `tools/issue_io/mcp_client.py`'s `mcp_issue_filer`/`mcp_read_issue`
  client-side adapters (signature-compatible with the classic calls).
- **Task 4:** injectable `issue_filer` write seam threaded `run_loop`/
  `run_graph_loop` → `execute_stage` → `_pause_for_issue`. **Note for
  reviewer:** the default is `None`, resolved to the classic
  `file_question_issue` by module-global lookup *inside* the function body —
  NOT a literal default-argument value. Binding the default directly
  (`issue_filer: IssueFiler = file_question_issue`) snapshots the reference
  at import time and silently breaks the existing
  `monkeypatch.setattr("loop_engine.core.engine.file_question_issue", ...)`
  autouse fixture in `tests/core/test_engine.py`/`test_graph_engine.py` — this
  was caught by the pre-existing test suite going red, not by review.
- **Task 5:** `cli.py`'s `resume --from-issue` gained an analogous read seam
  (`_resolve_issue_reader()`, same module-global-override pattern as
  `_select_engine()`'s `cli.run_loop`); `tests/tools/test_mcp_provider.py`'s
  disjointness assertion extended two-way → three-way
  (`coder_tools`/`github`/`issue`, pairwise disjoint); subprocess-surface
  count confirmed still **four**; keyring-free checks added for the new
  server + client-adapter modules.
- **Task 6:** `CLAUDE.md`, `.ai/context/modules.md`, `docs/migration_roadmap.md`
  (added the "Phase 6 planning pass" decisions log LD1–LD6 + a Sprint 26
  summary — this section did not exist in the roadmap before this session),
  and `sprints/DEFERRED_VERIFICATION.md` (§9: the live `issue`-server
  round-trip check, gated together with the eventual default-flip/deletion)
  all updated.
- **Green gate:** full suite **545 passed**; `lint`/`format` clean; `audit`
  clean; `sbom.json` **confirmed unchanged** (regenerated as a throwaway
  check — only `timestamp`/`serialNumber` differed — then reverted via
  `git checkout -- sbom.json`, so the committed file stays byte-identical).
- **Locked posture respected throughout:** classic direct `issue_io`/`gh`
  calls remain the runtime default everywhere; nothing flipped, nothing
  deleted; no new subprocess surface (still four); no new dependency; no new
  feature flag; no `State` change; no new `keyring` import.
- **Not committed yet** — see Working tree below.

## Next
1. **(Opus/Architect) Commit, then HITL-review Sprint 26's diff.** The tree is
   dirty (see Working tree) — nothing from this implementation session has
   been committed. Review scope: the `tools/issue_io` pure/`gh` split, the
   third MCP server + config stanza, the client adapters, the two injectable
   seams (engine write-side, cli read-side), the three-way disjointness /
   four-surface boundary tests, and the doc updates. Pay particular attention
   to the `issue_filer`/`_issue_reader` module-global-resolution pattern
   (Task 4 note above) — confirm it's the right shape, not just that it works.
2. If approved: `/archive-sprint`, then plan the **host-gated Phase 6 block**
   (the four flag deletions + `artifacts` strip + `loop.py` flag-branch
   collapse + the issue-path default-flip/classic-path deletion) — all
   deferred until a daemon-bearing host is available for live verification.

## HITL gate
**OPEN.** Sprint 26's *implementation* (this session) is unreviewed. The
*plan* was already Opus-approved in the prior planning-pass session.

## Pointers
- `sprints/26_issue_io_mcp_unification/sprint_plan.md` — the task list (all 6
  tasks' acceptance criteria met).
- `docs/migration_roadmap.md` — "Phase 6 planning pass" (LD1–LD6) + the new
  "Sprint 26 — `issue_io` → MCP unification (implemented)" subsection.
- `sprints/DEFERRED_VERIFICATION.md` — §9, the live issue-server round-trip
  check this sprint could not run hermetically.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol.

## Working tree
- HEAD `a3d316a` (unchanged this session — nothing committed). **Dirty:**
  every file Sprint 26 touched is modified/untracked (18 modified, 5 new
  under `src/`/`tests/`, plus the sprint plan dir already untracked from the
  prior session). Commit before the next `/resume` so `last_commit` matches
  HEAD.
