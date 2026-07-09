# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 4 · part 2 review-fixes (sprint `21_declarative_review_fixes`) — `awaiting_hitl_review`.**
All 5 sprint-21 tasks are implemented and the green gate is passing. Next session is
**Opus / Architect** for the HITL review + the deferred finding #4 decision.

## Just done
- **(Sonnet / Coder) Implemented sprint 21 tasks 1–5:**
  1. Extracted `fold_answers` to a module-level function in `personas/pm/persona.py`; `PMPersona.fold_answers` and the new `PMGenerator.fold_answers` (`personas/declarative/node.py`) both delegate to it — restores `resume --from-issue` under `declarative`.
  2. Added `Stage.escalate_on_exhaustion: bool = False` (`core/engine.py`) — an exhausted REVISE converts to ESCALATE instead of raising `StageGateFailedError` when set. Default off; the two existing hard-fail tests pass unedited.
  3. Wired the PM stage in `loops/default/loop.py`: `max_revisions=4`, `escalate_on_exhaustion=True` (inert for classic — its PM gate never REVISEs).
  4. Added `encoding="utf-8"` to both `read_text()` calls in `personas/declarative/config.py`.
  5. Cleanups: `_OUTPUT_ADAPTERS`/`_REVISION_STYLES` now derived via `typing.get_args` from `config.py`'s Literals (dedup); `repo_root()` cached with `@functools.cache`; hoisted the duplicated `effective = merge_sections(...)` computation; `CriticGate`'s inner `ArtifactGate` is now a `cached_property`.
- **Deviation from plan:** did NOT remove the `GeneratorNode.__init__` strategy-name guards (task 5's "or drop the redundant guards" option) — an existing test (`test_construction_validates_strategy_names`) proved they're reachable via `model_copy` (which skips Pydantic validation), so only the tuple dedup was applied, guards kept.
- **Green gate passing:** `hatch run test` (393 passed), `lint` (clean), `format` (clean), `audit` (no known vulnerabilities).

## Next
1. **(Opus / Architect) Commit sprint 21's implementation first** — the tree is currently **dirty** (14 modified files under `src/` and `tests/`, uncommitted); `last_commit` in `.ai/state.json` still points at `7017a0c` (the plan-only commit).
2. **(Opus / Architect) HITL-review the diff** against `sprint_plan.md`'s 5 tasks and their acceptance criteria (new tests are in `tests/core/test_engine.py`, `test_graph_engine.py`, `tests/loops/test_declarative_pipeline.py`, `test_default.py`, `tests/personas/declarative/test_config.py`, `test_pm_parity.py`, `tests/test_cli.py`).
3. **(Opus / Architect) Settle review finding #4** (accumulation: re-derive latest-only for `key_merge` vs. document as accepted non-parity) — a small decision before it becomes a task. See the "Deferred" note at the bottom of the sprint plan.
4. After sprint 21 is committed + reviewed → `/archive-sprint` for 20 **and** 21, then plan Phase 5 (FastAPI webhook triggers + multi-repo factory).

## Pointers
- `docs/migration_roadmap.md` — deep status + decisions log (resume point of record).
- `sprints/21_declarative_review_fixes/sprint_plan.md` — the active sprint (review fixes).
- `sprints/20_declarative_generators/sprint_plan.md` — the reviewed/approved sprint the fixes derive from.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.
