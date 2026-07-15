# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `38_test_validity_audit` (BL-23) — PLANNING.** No `sprint_plan.md` exists yet.
This is an Architect/Opus planning session: decide the scope of the test-validity audit,
one question at a time, HITL-gated. **No implementation until a plan is locked and approved.**

## Just done
- **Sprint 37 (`37_test_suite_velocity`, BL-22) archived** (2026-07-15, last commit `633b30b`).
  Roadmap got a sprint-37-DONE row and its NEXT ACTION repointed at BL-23; the final sprint-37
  cursor is snapshotted in `.ai/archive/37_test_suite_velocity-next-steps.md`. CI full suite is
  now ~54s (was ~380s) via mocked MCP providers, module-scoped fixtures, a docs-only pytest
  short-circuit, and `pytest-xdist --dist=loadscope`.

## Next — plan BL-23 (Architect/Opus)
BL-23 is the **test-validity audit**: are the tests actually testing what they claim? Concretely:
1. **Mutation-test the enforced boundary guards** — the static tests the module boundaries lean
   on: `tests/test_subprocess_surfaces.py` (the five sanctioned subprocess surfaces),
   `tests/test_ci_config.py` (SHA-pinning + no `name:` override on required jobs), the
   `core/`↔`personas/` import-boundary tests, and the MCP pairwise-disjoint verb-set assertions
   in `tests/tools/test_mcp_provider.py`. A guard that survives its own mutant is a guard that
   isn't guarding.
2. **Hunt orphan/weak tests** — tests asserting on nothing, tautological asserts, over-mocked
   tests that never exercise real code, and coverage the sprint-37 speedups may have hollowed out.
3. Decide the tooling (e.g. `mutmut`/`cosmic-ray` vs. targeted hand-written mutants) and whether
   any of it becomes a CI gate or stays a periodic manual pass — the sprint-37 velocity work makes
   affordable mutation runs the enabling precondition.

After BL-23: **BL-2** (Slack control plane). **BL-31** (reduce the MCP per-spawn ~5s cold-start)
stays deferred — its own `src/`-touching unit, off this path.

## Gotchas worth remembering
- **PR title ≤ 72 chars** — `wc -c` it before every `gh pr create/edit --title`; don't eyeball it.
- **`architect-review` is exempt on PRs with no `src/` change** — but a BL-23 sprint that touches
  `src/` (e.g. adds a mutation-testing dev dep to `pyproject.toml`, or reshapes a tested module)
  is **not** exempt and needs a fresh-session Opus review posted on the PR head.
- **A squash-merged branch is dead** — cut a fresh branch off updated `main` per task.
- **`gh pr view` serves a stale `mergeStateStatus`** — checks are the truth, don't close+reopen.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.**
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — BL-22 RESOLVED (sprint 37). Next: **BL-23** → BL-2.
  BL-31 filed (deferred). Open: BL-1..BL-5, BL-15/16/18/20, BL-23..BL-31 (minus resolved).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — migration DONE; the NEXT ACTION
  line now points at sprint 38 / BL-23. Post-migration work is backlog-driven.
- `sprints/38_test_validity_audit/sprint_plan.md` — **to be written** this session.
- [`sprints/37_test_suite_velocity/sprint_plan.md`](../sprints/37_test_suite_velocity/sprint_plan.md)
  — the completed T1–T4 specs, for reference.
