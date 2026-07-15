# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `37_test_suite_velocity` — DONE.** All four tasks (T1–T4) implemented, tested,
and merged as separate PRs. **No HITL gate is open.** The sprint is ready to be formally
archived by the next (Architect/Opus) session.

## Just done (this implementation session, Coder/Sonnet)
- **T1** (PR #82): mocked `build_coder_tool_provider` in `tests/personas/test_ralph_coder.py`
  (pattern already used in `test_coder_tool_backend.py`) so the ~9 ralph tests stop spawning
  a real MCP server for a fully-stubbed `MagicMock` LLM. File duration ~75s → ~5s; suite
  278s → 174.58s.
- **T2** (PR #83): moved four direct-spawner MCP test files' provider fixtures to **module
  scope** (`test_mcp_provider.py`, `test_github_server.py`, `test_issue_io_server.py`; audited
  `test_issue_provider.py` and found only one real spawn already — left unchanged). Used
  `scope="module"`, not the plan's literal "session" wording, since a true session-scoped
  autouse cwd fixture in one file risks leaking into later-collected test files. Suite
  174.58s → ~86–89s, repeatable, no flake.
- **T3** (PR #86): step-level `if:` short-circuit in `ci.yml`'s `test` job — skips
  `hatch run test` only when every changed file is docs (`**/*.md`, `.ai/**`, `sprints/**`,
  `docs/**`), fails safe on any API error/empty result, SIGPIPE-safe capture-then-match
  (mirrors `hitl-review.yml:70-74`). **Verified live** on a throwaway docs-only PR (skip=true,
  13s) and a throwaway code-touching PR (skip=false, full suite ran) — both closed without
  merging afterward.
- **T4** (PR #87): landed `pytest-xdist==3.8.0` as a new `test-parallel` hatch script
  (`-n auto --dist=loadscope`) — NOT wired into the default `test` script, to protect the
  documented single-file/single-test fast path. `--dist=loadscope` was required (not
  optional): xdist's default distribution can scatter one module's tests across many
  workers, and Task 2's module-scoped MCP fixtures don't amortize that way (one transient
  >120s stall observed under default distribution before switching). CI now runs the full
  suite in **~54s** on a real GitHub runner (4 workers, 573 passed) — down from the
  ~380s CI estimate the sprint started from.
- All four branches (`sprint/37-test-velocity`, `sprint/37-t2-session-scope-mcp-tests`,
  `sprint/37-t3-docs-only-skip`, `sprint/37-t4-xdist-spike`) pruned locally after each merge.

## Next — archive sprint 37, then plan BL-23 (Architect/Opus)
1. Run **`/archive-sprint`** to formally retire sprint 37 (snapshot this file into
   `.ai/archive/`, advance `.ai/state.json`, seed a fresh `next-steps.md`).
2. Begin planning the next sprint. Priority order per `docs/backlog.md`: **BL-23** (the
   test-validity audit — mutation-testing the boundary guards, hunting orphan/weak tests)
   is next, then **BL-2** (Slack control plane). **BL-31** (reducing the MCP per-spawn ~5s
   cold-start itself) was filed during sprint 37 planning and deliberately deferred — it's
   a separate `src/`-touching unit, not on this immediate path.

## Gotchas worth remembering
- **PR title ≤ 72 chars** — `wc -c` it before every `gh pr create/edit --title`; don't
  eyeball it (this session hit the limit once, at 76 chars, on PR #82's first title).
- **`architect-review` is exempt on PRs with no `src/` change.** All four sprint 37 PRs
  qualified (tests/CI/docs only) — none needed a posted Architect review.
- **A squash-merged branch is dead** — this session cut a fresh branch off updated `main`
  for each of T1→T2→T3→T4 rather than reusing one.
- **`gh pr view` serves a stale `mergeStateStatus`** — checks are the truth, don't
  close+reopen.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.**
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Pointers
- [`sprints/37_test_suite_velocity/sprint_plan.md`](../sprints/37_test_suite_velocity/sprint_plan.md) —
  the completed T1–T4 specs + locked findings FD1–FD5, for reference before archiving.
- [`docs/backlog.md`](../docs/backlog.md) — BL-22 now RESOLVED via sprint 37. Next: BL-23 → BL-2.
  BL-31 filed (deferred). Open: BL-1..BL-5, BL-15/16/18/20, BL-23..BL-31.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — migration DONE (sprint 35);
  post-migration work is backlog-driven.
