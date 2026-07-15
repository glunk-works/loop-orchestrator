# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `38_test_validity_audit` (BL-23) — IMPLEMENTING.** The plan is merged and
authoritative (PR #89, `9cc897a`). **Next session is Coder/Sonnet: implement Task 1.**
No HITL gate is open.

## Just done (this session, Architect/Opus)
- **Archived sprint 37** (BL-22, test-suite velocity) — roadmap got a sprint-37-DONE row
  with NEXT ACTION repointed at BL-23; cursor snapshot in `.ai/archive/`.
- **Planned sprint 38** (BL-23, first pass) — mutation-test `core/` with mutmut, verdict
  per surviving mutant. Locked FD1–FD5.
- **Landed the plan** on `main` (PR #89, squash `9cc897a`; docs-only, `architect-review`-exempt).

## Next — implement Task 1 (Coder/Sonnet)
Cut a fresh `sprint/38-t1-*` branch from `main`, then per
`sprints/38_test_validity_audit/sprint_plan.md` Task 1:
1. Add a **pinned** `mutmut` to `[tool.hatch.envs.default].dependencies`, a `[tool.mutmut]`
   config (`paths_to_mutate = "src/loop_engine/core/"`), and a `mutate` hatch script whose
   runner drives `hatch run test tests/core/` (must load the repo conftest).
2. Regenerate `sbom.json` (`hatch run sbom`) and confirm `hatch run audit` passes.
3. **Verify the unmutated baseline is all-green under the mutmut runner** before trusting any
   survivor (a misconfigured runner reports every mutant as survived — spurious).
4. Run mutmut to completion on `core/`; capture the **full** survivor list + totals + wall-clock
   into a checked-in `sprints/38_test_validity_audit/mutation_baseline.md`.

T1 is `src/`-**exempt** (tooling + config + sbom only) but still needs the full green suite.
T2 (triage survivors → keep/fix/delete) and T3 (land fixes) follow.

## Scope guard — do NOT re-open (FD1, the load-bearing decision)
Mutation-test `core/` **behavioral** tests **only**. The **static structural guards**
(`test_subprocess_surfaces.py`, `test_encoding_boundary.py`/`_ast_open.py`, the
`core/`↔`personas/` import-boundary tests, `test_mcp_provider.py` verb-disjointness) are
**out of scope**: mutmut's operator catalog can't emit the constructs they catch (BL-15's
`import gzip as gz`), so its green on them is **not** coverage. Their adversarial-injection
audit is a separate, deferred backlog item (file it as a follow-up, per the plan).
**FD4:** no numeric score gate — DoD is a reasoned keep/fix/delete verdict per survivor.
**FD3:** cross-check each survivor against the **full** suite before its verdict.

## Gotchas worth remembering
- **PR title ≤ 72 bytes** — `wc -c` it before every `gh pr create/edit --title`; don't eyeball.
- **`architect-review` exempt on no-`src/` PRs.** T1 qualifies; a T3 PR touching
  `src/loop_engine/core/` does **not** — keep source fixes and test-only fixes on separate PRs.
- **A squash-merged branch is dead** — cut a fresh branch off updated `main` per task.
- **`gh pr view` serves a stale `mergeStateStatus`** — checks are the truth, don't close+reopen.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.**
- **`.ai/state.json` is gitignored** — **this file is what travels.**

## Pointers
- [`sprints/38_test_validity_audit/sprint_plan.md`](../sprints/38_test_validity_audit/sprint_plan.md)
  — merged, authoritative: FD1–FD5, T1–T3, and the two follow-ups.
- [`docs/backlog.md`](../docs/backlog.md) — BL-23 (this sprint). Next: BL-2. BL-31 deferred.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION points at sprint 38 / BL-23.
