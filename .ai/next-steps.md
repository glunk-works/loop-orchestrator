# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `38_test_validity_audit` (BL-23) — IMPLEMENTING.** Task 1 is merged (PR #90,
squash `84d4f79`). **Next session is Coder/Sonnet: implement Task 2 (triage).**
No HITL gate is open.

## Just done (this session, Coder/Sonnet)
- **Task 1 landed** (PR #90, squash `84d4f79`): `mutmut==3.6.0` pinned dev dep,
  `hatch run mutate` scoped to `src/loop_engine/core/` against `tests/core/` only
  (FD2/FD3), `sbom.json` regenerated, `hatch run audit` clean. Ran to a green baseline:
  **693 mutants, 546 killed, 147 survived**, ~35s wall-clock, 26.89 mutations/second for
  the testing loop. Full survivor list (file:line + diff) in
  `sprints/38_test_validity_audit/mutation_baseline.md` — the raw material for T2.
- **Deviation from the plan's literal wording (documented on the PR, not a scope change):**
  kept mutmut on the latest 3.x line rather than the plan's 2.x-shaped `runner =
  "hatch run test tests/core/"` description, per owner direction. mutmut 3.x's
  coverage-tracking trampoline re-resolves its `source_paths` config against the *live
  process cwd* during its one-time stats pass, which collided with three `tests/core/`
  files' `_isolated_cwd` fixtures (a real `chdir`, needed because those tests write real
  files into an isolated tmp dir — `coder_gate.py` depends on `Path.cwd()` being the
  worktree). Worked around with a scoped, auto-reverting `monkeypatch.setattr` in a new
  shared `tests/core/conftest.py` helper (`absolutize_mutmut_source_paths`), called from
  `test_coder_gate.py`, `test_engine.py`, and `test_graph_engine.py`'s fixtures. No-op
  outside `hatch run mutate` (gated on mutmut's own `PY_IGNORE_IMPORTMISMATCH` env var) —
  confirmed `hatch run test`/`test-parallel` byte-for-byte unaffected. If T2/T3 add a
  fourth `tests/core/` file with a real-chdir fixture, it needs the same one-line call.
- Also folded in a small catch-up commit: `.ai/next-steps.md`'s cursor (PLANNING →
  IMPLEMENTING) had been left uncommitted after PR #89 landed the plan.

## Next — implement Task 2 (Coder/Sonnet): triage the 147 survivors
Cut a fresh `sprint/38-t2-*` branch from `main`, then per
`sprints/38_test_validity_audit/sprint_plan.md` Task 2:
1. For each of the 147 survivors in `mutation_baseline.md`, produce a verdict:
   `keep` / `fix` / `delete`, with a one-line reason.
2. **FD3 cross-check (mandatory, not optional):** re-run the **full** suite against each
   individual survivor mutant (`mutmut run <mutant_name>` re-tests just that one, or use
   `mutants/mutmut-stats.json` bookkeeping — check current mutmut docs/behavior for the
   cleanest single-mutant re-test path under 3.x) to distinguish killed-elsewhere
   (`fix` — add a local `tests/core/` unit test) from genuinely-uncovered (`fix` real hole,
   or `keep — equivalent mutant` per FD5). Spot-check the re-test mechanics on a couple of
   survivors before scripting all 147 — a full-suite run is meaningfully slower per-mutant
   than the `tests/core/`-scoped T1 run; budget wall-clock accordingly (naively ~1min ×
   147 ≈ 2.5h if each cross-check re-spawns `hatch run test`, so it's worth checking
   whether mutmut's own single-mutant CLI path is faster than a bespoke loop).
3. Output: `sprints/38_test_validity_audit/audit_report.md` — one row per survivor
   (`file:line`, mutation, verdict, reason, cross-check result), plus a methodology note
   restating the FD1 static-guard scope boundary so no reader mistakes their absence for a
   clean bill.

Docs-only task → `architect-review`-exempt. T3 (land the fixes) follows and is **not**
exempt where it touches `src/loop_engine/core/` — keep test-only and source fixes on
separate PRs (Risks section, sprint plan).

## Scope guard — do NOT re-open (FD1, the load-bearing decision)
Mutation-test `core/` **behavioral** tests **only**. The **static structural guards**
(`test_subprocess_surfaces.py`, `test_encoding_boundary.py`/`_ast_open.py`, the
`core/`↔`personas/` import-boundary tests, `test_mcp_provider.py` verb-disjointness) are
**out of scope**: mutmut's operator catalog can't emit the constructs they catch (BL-15's
`import gzip as gz`), so its green on them is **not** coverage. Their adversarial-injection
audit is a separate, deferred backlog item (file it as a follow-up, per the plan).
**FD4:** no numeric score gate — DoD is a reasoned keep/fix/delete verdict per survivor.
**FD5:** equivalent mutants are a legitimate `keep` — don't contort a test to kill one.

## Gotchas worth remembering
- **PR title ≤ 72 bytes** — `wc -c` it before every `gh pr create/edit --title`; don't eyeball.
- **`architect-review` exempt on no-`src/` PRs.** T2 (docs-only report) qualifies; a T3 PR
  touching `src/loop_engine/core/` does **not** — keep source fixes and test-only fixes on
  separate PRs.
- **A squash-merged branch is dead** — cut a fresh branch off updated `main` per task.
- **`gh pr view` serves a stale `mergeStateStatus`** — checks are the truth, don't close+reopen.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.**
- **`.ai/state.json` is gitignored** — **this file is what travels.**
- **mutmut 3.x + real-chdir tests:** any new `tests/core/` fixture that does
  `monkeypatch.chdir`/`os.chdir` needs `absolutize_mutmut_source_paths(monkeypatch)` from
  `tests/core/conftest.py` called first, or a future `hatch run mutate` goes silently 0/0
  (mutmut's own singleton `Config.source_paths` gets corrupted process-wide) or crashes
  outright on that file's stats-collection pass.

## Pointers
- [`sprints/38_test_validity_audit/sprint_plan.md`](../sprints/38_test_validity_audit/sprint_plan.md)
  — merged, authoritative: FD1–FD5, T1–T3, and the two follow-ups.
- [`sprints/38_test_validity_audit/mutation_baseline.md`](../sprints/38_test_validity_audit/mutation_baseline.md)
  — T1's output: 147 survivors, file:line + diff each. T2 triages every row.
- [`docs/backlog.md`](../docs/backlog.md) — BL-23 (this sprint). Next: BL-2. BL-31 deferred.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION points at sprint 38 / BL-23.
