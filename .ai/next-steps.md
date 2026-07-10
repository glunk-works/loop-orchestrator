# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 25 (`bootstrap_flow`, piece 4) — `awaiting_hitl_review`.**
Implementation is done and green. The next session is an **Opus/Architect**
HITL review pass over the diff at `79b535d`.

## Just done (Sprint 25 — implementation pass, Sonnet/Coder)
- Implemented all 6 tasks from `sprints/25_bootstrap_flow/sprint_plan.md`:
  1. **`tools/scaffold`** (`src/loop_engine/tools/scaffold/writer.py`) — the
     second sanctioned file-write surface. `write_skeleton(tree, *, kind, pkg_name,
     repo_name)` validates `tree` via `repo_io._validate_clone_dest`, sanitizes
     `pkg_name` to a safe Python identifier, renders bundled `templates/python/*.tmpl`
     + the shared `templates/CLAUDE.md` via plain `str.replace` token substitution
     (no template-engine dependency).
  2. **Boundary invariants widened**: `tests/tools/test_state_io_boundary.py`'s
     allow-set is now `{state_io, scaffold}`; `tests/tools/test_subprocess_surfaces.py`
     still asserts exactly four surfaces + an explicit "scaffold is not a fifth"
     assertion; new conventions sync-guard (`tests/tools/scaffold/test_conventions_sync.py`)
     asserts the bundled `CLAUDE.md` stays byte-identical to `.ai/context/conventions.md`.
  3. **`flows/bootstrap`** (`src/loop_engine/flows/bootstrap/flow.py`) — chains
     `create_repository` -> `clone_repo` -> `checkout_branch(main)` -> `scaffold.
     write_skeleton` -> `commit_all` -> `push_branch(main)` -> `create_branch(develop,
     base=main)`. Skeleton-only: no inner loop, no green gate, no `open_pr`.
  4. `tests/flows/test_boundaries.py` extended with an explicit membership
     assertion provably enumerating `flows/bootstrap`.
  5. Hermetic e2e proof (`tests/flows/bootstrap/test_integration.py`): real
     `tools/scaffold` + real `tools/git_io` against a `tmp_path` repo seeded on a
     non-`main` initial branch (proving the unborn-HEAD handling) + a local bare
     remote, with `repo_io` faked.
  6. Docs updated: `CLAUDE.md` (file-write clause -> two modules, new `flows/bootstrap`
     bullet), `.ai/context/modules.md` (`tools/scaffold/` + `flows/bootstrap/` entries),
     `docs/migration_roadmap.md` (status row, NEXT ACTION, decisions log), and
     `sprints/DEFERRED_VERIFICATION.md` §8 (the deferred live create->clone->
     scaffold->push->`develop` check on a daemon-bearing host).
- **Bug caught + fixed during implementation**: the sprint plan's suggested
  `[tool.hatch.build.targets.wheel.force-include]` for the template files
  actually **breaks** `hatch build` (duplicate-path conflict with hatchling's
  default `packages` inclusion, which already ships non-`.py` files). Verified
  via a real `hatch build -t wheel` + archive inspection that the templates ship
  correctly **without** any force-include entry; removed it from `pyproject.toml`
  and corrected the docs/deferred-verification wording accordingly.
- Green gate: **525 tests pass**, `ruff check`/`ruff format --check` clean,
  `pip-audit` clean, `sbom.json` unchanged (no new dependency). Committed at
  `79b535d` (on top of the approved plan commit `46b82f5`).

## Next
1. **(Opus/Architect) HITL review** the diff at `79b535d` against
   `sprints/25_bootstrap_flow/sprint_plan.md`'s locked decisions and risks.
2. If approved: `/archive-sprint` (retire 25, advance the cursor), then update
   `docs/migration_roadmap.md`'s NEXT ACTION to **Phase 6 planning** (collapse
   the flags — see the Phase 6 sketch section of the roadmap).
3. If findings: route review-fixes back to a Sonnet/Coder session (mirroring
   how sprint 24's 2 HITL findings were fixed in `f8d388a`).

## HITL gate
**OPEN** — Sprint 25 is implemented and green; awaiting Opus/Architect review
of `79b535d` before archiving.

## Carry-forward
- **Sprint-24 review nit (still open):** no unit test over
  `flows/maintenance.flow._default_run_tests`. Orthogonal to bootstrap.
- **22b nit (still open):** bare `python` vs `sys.executable` in the committed
  `loop_engine.mcp.json` github stanza. Orthogonal — not touched in 25.

## Pointers
- `sprints/25_bootstrap_flow/sprint_plan.md` — the plan this session implemented.
- `docs/migration_roadmap.md` — Phase 5 status; ▶ NEXT ACTION → Opus review of 25.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- Clean at HEAD `79b535d` — all Sprint 25 implementation changes committed.
