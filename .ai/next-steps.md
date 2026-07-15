# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `38_test_validity_audit` (BL-23) — IMPLEMENTING.** Task 2 is merged (PR #92,
squash `875f591`). **Next session is Coder/Sonnet: implement Task 3 (land the fixes).**
No HITL gate is open.

## Just done (this session, Coder/Sonnet)
- **Task 2 landed** (PR #92, squash `875f591`): all 147 `core/` mutation survivors from
  `mutation_baseline.md` triaged into `sprints/38_test_validity_audit/audit_report.md` —
  **58 keep** (52 provably equivalent by construction, 6 cosmetic message text),
  **89 fix** (18 mislocated coverage, 71 genuinely uncovered), **0 delete**. Every
  `fix` row names the concrete test (or, for a couple of genuine defects, source change)
  T3 makes. Restates the FD1 static-guard scope boundary explicitly so a reader never
  mistakes this report's silence on the structural guards for a clean bill. Docs-only,
  `architect-review`-exempt; full suite green (573/573), lint/format clean.
- **FD3's mandatory full-suite cross-check was actually run** for all 147 survivors —
  each mutant applied directly to the real `src/loop_engine/core/` tree (not just the
  mutmut-copied `mutants/` tree) and the full suite re-run, not inferred from absence of
  a `tests/core/` assertion. Parallelized across 4 `git worktree add --detach` checkouts
  (each with its own `hatch run mutate`-generated mutant database, sharded mutant names,
  `pytest -n 7` per shard to avoid oversubscribing a 28-core host) — cut ~110min
  sequential to ~15min. Full method recorded in `.ai/state.json`'s `fd3_crosscheck_method`.
- **The cross-check caught real mistakes before they shipped**, not just confirmed
  priors: a few survivors first reasoned as "genuinely uncovered" from a `tests/core/`-only
  grep turned out killed by tests **outside** `tests/core/` once actually run —
  `execute_stage`'s `has_artifact(state, None)` masking bug (killed by
  `tests/integration/test_revision_flow.py`), the token-delta addition-vs-subtraction bug
  (killed by `tests/tools/test_logging_config.py`), and the `BudgetExceededError` mid-loop
  except-block mutants (killed by `tests/integration/test_budget_abort.py`). All
  reclassified to mislocated coverage with the actual covering test named — this is
  exactly the failure mode FD3's cross-check exists to catch.

## Next — implement Task 3 (Coder/Sonnet): land the fixes
Cut a fresh `sprint/38-t3-*` branch from `main`, then per
`sprints/38_test_validity_audit/sprint_plan.md` Task 3, working row-by-row through
`sprints/38_test_validity_audit/audit_report.md`'s **89 `fix` rows** (each already names
the concrete test/source change — this is not a re-triage):
1. For each `fix`, add/strengthen the named `tests/core/` test so it kills that mutant.
   A handful of rows named a genuine `src/loop_engine/core/` defect rather than a missing
   test (e.g. the `has_artifact`/token-delta bugs above) — fix the source there.
2. **Keep test-only changes and any `src/core/` source fix on separate PRs** (sprint plan
   Risks section, restated in the audit report's summary): test-only stays
   `architect-review`-exempt; a source-touching PR needs a **fresh-session** Opus review
   on its head commit before merge.
3. Re-run `hatch run mutate` after landing a batch and confirm the residual survivor set
   matches `audit_report.md`'s 58 `keep`s **exactly** — no more (a fix that didn't
   actually kill its mutant), no fewer (don't accidentally over-fit and kill an
   `equivalent` — FD5 still applies).
4. Full suite green + lint/format clean gates every PR regardless of exemption status.

## Scope guard — do NOT re-open (FD1, still the load-bearing decision)
Mutation-test `core/` **behavioral** tests **only**. The **static structural guards**
(`test_subprocess_surfaces.py`, `test_encoding_boundary.py`/`_ast_open.py`, the
`core/`↔`personas/` import-boundary tests, `test_mcp_provider.py` verb-disjointness)
remain **out of scope** and untouched by T1/T2 — their adversarial-injection audit is a
separate, still-unfiled backlog item (file it as a follow-up per the plan; do not fold it
into T3). **FD4:** no numeric score gate — DoD is T3 matching the audit report's verdicts
exactly. **FD5:** equivalent mutants are a legitimate `keep` — don't contort a test to
kill one just to shrink the survivor count.

## Gotchas worth remembering
- **PR title ≤ 72 bytes** — `wc -c` it before every `gh pr create/edit --title`; don't eyeball.
- **`architect-review` exempt on no-`src/` PRs** — confirmed working on T2's PR (auto-passed).
  A T3 PR touching `src/loop_engine/core/` does **not** qualify — separate PR, fresh-session review.
- **A squash-merged branch is dead** — cut a fresh branch off updated `main` per task
  (`sprint/38-t2-triage-survivors` already pruned locally post-merge).
- **`gh pr view` serves a stale `mergeStateStatus`** — checks are the truth, don't close+reopen.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** A signing Timeout =
  answer the host pinentry and retry the commit (worked cleanly on retry this session).
- **`.ai/state.json` is gitignored** — **this file is what travels.**
- **mutmut 3.x + real-chdir tests:** any new `tests/core/` fixture that does
  `monkeypatch.chdir`/`os.chdir` needs `absolutize_mutmut_source_paths(monkeypatch)` from
  `tests/core/conftest.py` called first, or a future `hatch run mutate` goes silently 0/0
  or crashes outright on that file's stats-collection pass.
- **`mutants/`/`.mutmut-cache` are gitignored** and must be regenerated (`hatch run mutate`)
  per checkout/worktree before `mutmut apply <name>` will find a mutant by name.
- **A full-suite run against a working tree with a stray `mutants/` dir present** causes
  pytest import-file-mismatch errors (it collects the copied `mutants/tests/` too) —
  always run against an explicit `tests` path, or clean `mutants/`/`.mutmut-cache` first.
- **The FD3 cross-check parallelizes cleanly across `git worktree` checkouts** — see
  `.ai/state.json`'s `fd3_crosscheck_method` for the exact recipe if T3 needs to re-run it
  at scale (e.g. after a batch of fixes, to check the residual survivor set).

## Pointers
- [`sprints/38_test_validity_audit/sprint_plan.md`](../sprints/38_test_validity_audit/sprint_plan.md)
  — merged, authoritative: FD1–FD5, T1–T3, and the two follow-ups.
- [`sprints/38_test_validity_audit/audit_report.md`](../sprints/38_test_validity_audit/audit_report.md)
  — T2's output: 147 survivors triaged, 89 `fix` rows are T3's worklist.
- [`sprints/38_test_validity_audit/mutation_baseline.md`](../sprints/38_test_validity_audit/mutation_baseline.md)
  — T1's raw survivor dump (file:line + diff each) that audit_report.md was triaged against.
- [`docs/backlog.md`](../docs/backlog.md) — BL-23 (this sprint). Next: BL-2. BL-31 deferred.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION points at sprint 38 / BL-23.
