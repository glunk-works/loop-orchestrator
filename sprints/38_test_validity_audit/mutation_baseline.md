### FILEPATH: /sprints/38_test_validity_audit/mutation_baseline.md

# Mutation baseline — `core/` (Sprint 38, Task 1, BL-23)

Raw survivor dump from the first `hatch run mutate` pass against
`src/loop_engine/core/`, scoped to `tests/core/` per FD3. This is T1's
deliverable: the full survivor list + totals + wall-clock, as evidence for
T2's keep/fix/delete triage (not a triage itself — no verdicts here).

**Scope reminder (FD1, do not misread this file):** this run only covers
`core/`'s *behavioral* tests via mutmut. The static structural guards
(`test_subprocess_surfaces.py`, `test_encoding_boundary.py`/`_ast_open.py`,
the `core/`↔`personas/` import-boundary tests, `test_mcp_provider.py`'s
verb-disjointness) were **not** exercised by this instrument and are **not**
represented anywhere below — their absence here is not a clean bill, it's
out of scope by design (mutmut's operator catalog can't emit the constructs
those guards catch). See the sprint plan and `docs/backlog.md`'s new
adversarial-guard-audit item.

## Run

- **Tool:** `mutmut==3.6.0` (pinned dev dependency, hatch `default` env).
- **Scope:** `source_paths = ["src"]` (needed so `core/`'s intra-package
  imports resolve inside mutmut's copied tree), `only_mutate =
  ["src/loop_engine/core/*.py"]` (mutation itself is scoped to `core/` only),
  `pytest_add_cli_args_test_selection = ["tests/core"]` (FD3: per-mutant
  runs are scoped to `tests/core/`, not the full suite).
- **Baseline check:** the unmutated run under the mutmut runner was
  confirmed green (65 passed) before trusting any survivor, per the Risks
  section of the sprint plan. mutmut's own built-in "forced fail" sanity
  check (verifying test failures can actually be observed) also passed.
- **Command:** `hatch run mutate` (`mutmut run`, config in `pyproject.toml`
  `[tool.mutmut]`).

## Totals

| Metric | Count |
| --- | ---: |
| Mutants generated | 693 |
| Killed 🎉 | 546 |
| Survived 🙁 | 147 |
| Timeout ⏰ | 0 |
| Suspicious 🤔 | 0 |
| No tests / skipped 🔇 | 0 |
| Caught by type checker 🧙 | 0 |

**Wall-clock:** ~35.4s end-to-end (mutant generation + stats collection +
baseline re-check + forced-fail check + all 693 mutant runs). The
mutation-testing loop itself (the 693 per-mutant test runs, coverage-guided
so each only re-runs the subset of `tests/core/` that covers that mutant)
ran at **26.89 mutations/second**. Recorded as evidence for the deferred
gate-vs-script decision (sprint plan, "Deliverables / follow-ups") — no
gate is being proposed here.

## Survivors by file

| File | Total mutants | Survived | Survival rate |
| --- | ---: | ---: | ---: |
| `coder_gate.py` | 25 | 13 | 52.0% |
| `engine.py` | 458 | 100 | 21.8% |
| `gates.py` | 32 | 7 | 21.9% |
| `graph_engine.py` | 162 | 27 | 16.7% |
| `state.py` | 16 | 0 | 0.0% |
| `__init__.py` | 0 | 0 | — |
| **Total** | **693** | **147** | **21.2%** |

## A note on how to read a mutmut mutant name

`loop_engine.core.<module>.x_<function>__mutmut_<n>` (or
`x__<function>__mutmut_<n>` when the original function name starts with an
underscore) identifies one mutant of `<function>` in `<module>.py`. The diff
below each name is the exact single-line change mutmut applied and re-ran
`tests/core/` against; a line marked `survived` means every test in
`tests/core/` still passed with that mutation active.

## Full survivor list (147)

### `loop_engine.core.coder_gate.x__manifest_task_ids__mutmut_4`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -2,7 +2,7 @@
     """Task ids from the `task_manifest` artifact — parsed core-safely (no persona
     import), returning None if the artifact is missing or malformed."""
     try:
-        manifest = json.loads(state.artifacts.get(manifest_key, ""))
+        manifest = json.loads(state.artifacts.get(manifest_key, None))
         return [entry["id"] for entry in manifest]
     except (json.JSONDecodeError, KeyError, TypeError):
         return None
```

### `loop_engine.core.coder_gate.x__manifest_task_ids__mutmut_6`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -2,7 +2,7 @@
     """Task ids from the `task_manifest` artifact — parsed core-safely (no persona
     import), returning None if the artifact is missing or malformed."""
     try:
-        manifest = json.loads(state.artifacts.get(manifest_key, ""))
+        manifest = json.loads(state.artifacts.get(manifest_key, ))
         return [entry["id"] for entry in manifest]
     except (json.JSONDecodeError, KeyError, TypeError):
         return None
```

### `loop_engine.core.coder_gate.x__manifest_task_ids__mutmut_7`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -2,7 +2,7 @@
     """Task ids from the `task_manifest` artifact — parsed core-safely (no persona
     import), returning None if the artifact is missing or malformed."""
     try:
-        manifest = json.loads(state.artifacts.get(manifest_key, ""))
+        manifest = json.loads(state.artifacts.get(manifest_key, "XXXX"))
         return [entry["id"] for entry in manifest]
     except (json.JSONDecodeError, KeyError, TypeError):
         return None
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_1`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -1,7 +1,7 @@
 def _status_finding(outstanding: list[str]) -> str:
     """Incomplete-coverage status: tasks remain (possibly all dep-blocked). The
     red-suite-with-all-tasks-done case uses `RALPH_REGRESSION_PREFIX` instead."""
-    next_task = outstanding[0] if outstanding else "none"
+    next_task = None
     remaining = ", ".join(outstanding) if outstanding else "none"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_3`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -1,7 +1,7 @@
 def _status_finding(outstanding: list[str]) -> str:
     """Incomplete-coverage status: tasks remain (possibly all dep-blocked). The
     red-suite-with-all-tasks-done case uses `RALPH_REGRESSION_PREFIX` instead."""
-    next_task = outstanding[0] if outstanding else "none"
+    next_task = outstanding[0] if outstanding else "XXnoneXX"
     remaining = ", ".join(outstanding) if outstanding else "none"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_4`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -1,7 +1,7 @@
 def _status_finding(outstanding: list[str]) -> str:
     """Incomplete-coverage status: tasks remain (possibly all dep-blocked). The
     red-suite-with-all-tasks-done case uses `RALPH_REGRESSION_PREFIX` instead."""
-    next_task = outstanding[0] if outstanding else "none"
+    next_task = outstanding[0] if outstanding else "NONE"
     remaining = ", ".join(outstanding) if outstanding else "none"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_5`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -2,7 +2,7 @@
     """Incomplete-coverage status: tasks remain (possibly all dep-blocked). The
     red-suite-with-all-tasks-done case uses `RALPH_REGRESSION_PREFIX` instead."""
     next_task = outstanding[0] if outstanding else "none"
-    remaining = ", ".join(outstanding) if outstanding else "none"
+    remaining = None
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
         "Implement the next unit."
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_7`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -2,7 +2,7 @@
     """Incomplete-coverage status: tasks remain (possibly all dep-blocked). The
     red-suite-with-all-tasks-done case uses `RALPH_REGRESSION_PREFIX` instead."""
     next_task = outstanding[0] if outstanding else "none"
-    remaining = ", ".join(outstanding) if outstanding else "none"
+    remaining = "XX, XX".join(outstanding) if outstanding else "none"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
         "Implement the next unit."
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_8`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -2,7 +2,7 @@
     """Incomplete-coverage status: tasks remain (possibly all dep-blocked). The
     red-suite-with-all-tasks-done case uses `RALPH_REGRESSION_PREFIX` instead."""
     next_task = outstanding[0] if outstanding else "none"
-    remaining = ", ".join(outstanding) if outstanding else "none"
+    remaining = ", ".join(outstanding) if outstanding else "XXnoneXX"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
         "Implement the next unit."
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_9`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -2,7 +2,7 @@
     """Incomplete-coverage status: tasks remain (possibly all dep-blocked). The
     red-suite-with-all-tasks-done case uses `RALPH_REGRESSION_PREFIX` instead."""
     next_task = outstanding[0] if outstanding else "none"
-    remaining = ", ".join(outstanding) if outstanding else "none"
+    remaining = ", ".join(outstanding) if outstanding else "NONE"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
         "Implement the next unit."
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_10`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -5,5 +5,5 @@
     remaining = ", ".join(outstanding) if outstanding else "none"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
-        "Implement the next unit."
+        "XXImplement the next unit.XX"
     )
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_11`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -5,5 +5,5 @@
     remaining = ", ".join(outstanding) if outstanding else "none"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
-        "Implement the next unit."
+        "implement the next unit."
     )
```

### `loop_engine.core.coder_gate.x__status_finding__mutmut_12`
```diff
--- src/loop_engine/core/coder_gate.py
+++ src/loop_engine/core/coder_gate.py
@@ -5,5 +5,5 @@
     remaining = ", ".join(outstanding) if outstanding else "none"
     return (
         f"Ralph status — next task: {next_task}; tasks still to complete: {remaining}. "
-        "Implement the next unit."
+        "IMPLEMENT THE NEXT UNIT."
     )
```

### `loop_engine.core.engine.x__record_stage__mutmut_1`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -3,7 +3,7 @@
     stage_name: str,
     tokens_used: int,
     cost_usd: float,
-    cache_creation_input_tokens: int = 0,
+    cache_creation_input_tokens: int = 1,
     cache_read_input_tokens: int = 0,
 ) -> State:
     record = StageRecord(
```

### `loop_engine.core.engine.x__record_stage__mutmut_2`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -4,7 +4,7 @@
     tokens_used: int,
     cost_usd: float,
     cache_creation_input_tokens: int = 0,
-    cache_read_input_tokens: int = 0,
+    cache_read_input_tokens: int = 1,
 ) -> State:
     record = StageRecord(
         stage_name=stage_name,
```

### `loop_engine.core.engine.x__record_stage__mutmut_16`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -10,7 +10,7 @@
         stage_name=stage_name,
         tokens_used=tokens_used,
         cost_usd=cost_usd,
-        completed_at=datetime.now(UTC).isoformat(),
+        completed_at=datetime.now(None).isoformat(),
         cache_creation_input_tokens=cache_creation_input_tokens,
         cache_read_input_tokens=cache_read_input_tokens,
     )
```

### `loop_engine.core.engine.x__record_stage__mutmut_17`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -15,7 +15,7 @@
         cache_read_input_tokens=cache_read_input_tokens,
     )
     log_stage_completion(
-        stage_name=record.stage_name,
+        stage_name=None,
         tokens_used=record.tokens_used,
         cost_usd=record.cost_usd,
         cache_creation_input_tokens=record.cache_creation_input_tokens,
```

### `loop_engine.core.engine.x__record_stage__mutmut_18`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -16,7 +16,7 @@
     )
     log_stage_completion(
         stage_name=record.stage_name,
-        tokens_used=record.tokens_used,
+        tokens_used=None,
         cost_usd=record.cost_usd,
         cache_creation_input_tokens=record.cache_creation_input_tokens,
         cache_read_input_tokens=record.cache_read_input_tokens,
```

### `loop_engine.core.engine.x__record_stage__mutmut_19`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -17,7 +17,7 @@
     log_stage_completion(
         stage_name=record.stage_name,
         tokens_used=record.tokens_used,
-        cost_usd=record.cost_usd,
+        cost_usd=None,
         cache_creation_input_tokens=record.cache_creation_input_tokens,
         cache_read_input_tokens=record.cache_read_input_tokens,
     )
```

### `loop_engine.core.engine.x__record_stage__mutmut_20`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -18,7 +18,7 @@
         stage_name=record.stage_name,
         tokens_used=record.tokens_used,
         cost_usd=record.cost_usd,
-        cache_creation_input_tokens=record.cache_creation_input_tokens,
+        cache_creation_input_tokens=None,
         cache_read_input_tokens=record.cache_read_input_tokens,
     )
     return state.model_copy(update={"stage_history": [*state.stage_history, record]})
```

### `loop_engine.core.engine.x__record_stage__mutmut_21`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -19,6 +19,6 @@
         tokens_used=record.tokens_used,
         cost_usd=record.cost_usd,
         cache_creation_input_tokens=record.cache_creation_input_tokens,
-        cache_read_input_tokens=record.cache_read_input_tokens,
+        cache_read_input_tokens=None,
     )
     return state.model_copy(update={"stage_history": [*state.stage_history, record]})
```

### `loop_engine.core.engine.x__record_stage__mutmut_25`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -18,7 +18,6 @@
         stage_name=record.stage_name,
         tokens_used=record.tokens_used,
         cost_usd=record.cost_usd,
-        cache_creation_input_tokens=record.cache_creation_input_tokens,
         cache_read_input_tokens=record.cache_read_input_tokens,
     )
     return state.model_copy(update={"stage_history": [*state.stage_history, record]})
```

### `loop_engine.core.engine.x__record_stage__mutmut_26`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -19,6 +19,5 @@
         tokens_used=record.tokens_used,
         cost_usd=record.cost_usd,
         cache_creation_input_tokens=record.cache_creation_input_tokens,
-        cache_read_input_tokens=record.cache_read_input_tokens,
-    )
+        )
     return state.model_copy(update={"stage_history": [*state.stage_history, record]})
```

### `loop_engine.core.engine.x__merge_questions__mutmut_3`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -1,6 +1,6 @@
 def _merge_questions(state: State, updated: list[Question]) -> State:
     by_id = {q.id: q for q in updated}
-    merged = [by_id.get(q.id, q) for q in state.questions]
+    merged = [by_id.get(None, q) for q in state.questions]
     known_ids = {q.id for q in state.questions}
     merged.extend(q for q in updated if q.id not in known_ids)
     return state.model_copy(update={"questions": merged})
```

### `loop_engine.core.engine.x__run_resolver_ladder__mutmut_5`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -6,7 +6,7 @@
     for resolver in stage.resolvers:
         unresolved = [q for q in current if q.resolution is None]
         if not unresolved:
-            break
+            return
         answered = resolver.resolve_questions(unresolved, state, llm_client)
         answered_by_id = {q.id: q for q in answered}
         current = [answered_by_id.get(q.id, q) for q in current]
```

### `loop_engine.core.engine.x__run_resolver_ladder__mutmut_8`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -7,7 +7,7 @@
         unresolved = [q for q in current if q.resolution is None]
         if not unresolved:
             break
-        answered = resolver.resolve_questions(unresolved, state, llm_client)
+        answered = resolver.resolve_questions(unresolved, None, llm_client)
         answered_by_id = {q.id: q for q in answered}
         current = [answered_by_id.get(q.id, q) for q in current]
     return current
```

### `loop_engine.core.engine.x__run_resolver_ladder__mutmut_9`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -7,7 +7,7 @@
         unresolved = [q for q in current if q.resolution is None]
         if not unresolved:
             break
-        answered = resolver.resolve_questions(unresolved, state, llm_client)
+        answered = resolver.resolve_questions(unresolved, state, None)
         answered_by_id = {q.id: q for q in answered}
         current = [answered_by_id.get(q.id, q) for q in current]
     return current
```

### `loop_engine.core.engine.x__run_resolver_ladder__mutmut_16`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -9,5 +9,5 @@
             break
         answered = resolver.resolve_questions(unresolved, state, llm_client)
         answered_by_id = {q.id: q for q in answered}
-        current = [answered_by_id.get(q.id, q) for q in current]
+        current = [answered_by_id.get(q.id, None) for q in current]
     return current
```

### `loop_engine.core.engine.x__run_resolver_ladder__mutmut_18`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -9,5 +9,5 @@
             break
         answered = resolver.resolve_questions(unresolved, state, llm_client)
         answered_by_id = {q.id: q for q in answered}
-        current = [answered_by_id.get(q.id, q) for q in current]
+        current = [answered_by_id.get(q.id, ) for q in current]
     return current
```

### `loop_engine.core.engine.x__exhaustion_escalation__mutmut_10`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -11,7 +11,7 @@
             new_question(
                 stage_name,
                 f"{stage_name} could not satisfy its output gate after "
-                f"repeated attempts: {'; '.join(findings)}",
+                f"repeated attempts: {'XX; XX'.join(findings)}",
             )
         ],
     )
```

### `loop_engine.core.engine.x_reentry_index__mutmut_3`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -1,7 +1,7 @@
 def reentry_index(loop: Loop, stage_index: int, resolved: list[Question]) -> int:
     """Worst impact among resolutions decides how far back the run re-enters."""
     impacts = {q.impact for q in resolved if q.resolution is not None}
-    for impact in ("architecture", "plan"):
+    for impact in ("XXarchitectureXX", "plan"):
         if impact in impacts and impact in loop.impact_reentry:
             return min(loop.impact_reentry[impact], stage_index)
     return stage_index
```

### `loop_engine.core.engine.x_reentry_index__mutmut_4`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -1,7 +1,7 @@
 def reentry_index(loop: Loop, stage_index: int, resolved: list[Question]) -> int:
     """Worst impact among resolutions decides how far back the run re-enters."""
     impacts = {q.impact for q in resolved if q.resolution is not None}
-    for impact in ("architecture", "plan"):
+    for impact in ("ARCHITECTURE", "plan"):
         if impact in impacts and impact in loop.impact_reentry:
             return min(loop.impact_reentry[impact], stage_index)
     return stage_index
```

### `loop_engine.core.engine.x_reentry_index__mutmut_7`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -2,6 +2,6 @@
     """Worst impact among resolutions decides how far back the run re-enters."""
     impacts = {q.impact for q in resolved if q.resolution is not None}
     for impact in ("architecture", "plan"):
-        if impact in impacts and impact in loop.impact_reentry:
+        if impact in impacts or impact in loop.impact_reentry:
             return min(loop.impact_reentry[impact], stage_index)
     return stage_index
```

### `loop_engine.core.engine.x__pause_for_issue__mutmut_2`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -5,7 +5,7 @@
     issue_filer: IssueFiler | None = None,
 ) -> State:
     state = state.model_copy(
-        update={"counters": {**state.counters, PAUSED_STAGE_COUNTER: stage_index}}
+        update=None
     )
     # F4: persist before filing. A raise inside the filer (e.g. an
     # unresolvable escalation destination) must leave a resumable
```

### `loop_engine.core.engine.x__pause_for_issue__mutmut_3`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -5,7 +5,7 @@
     issue_filer: IssueFiler | None = None,
 ) -> State:
     state = state.model_copy(
-        update={"counters": {**state.counters, PAUSED_STAGE_COUNTER: stage_index}}
+        update={"XXcountersXX": {**state.counters, PAUSED_STAGE_COUNTER: stage_index}}
     )
     # F4: persist before filing. A raise inside the filer (e.g. an
     # unresolvable escalation destination) must leave a resumable
```

### `loop_engine.core.engine.x__pause_for_issue__mutmut_4`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -5,7 +5,7 @@
     issue_filer: IssueFiler | None = None,
 ) -> State:
     state = state.model_copy(
-        update={"counters": {**state.counters, PAUSED_STAGE_COUNTER: stage_index}}
+        update={"COUNTERS": {**state.counters, PAUSED_STAGE_COUNTER: stage_index}}
     )
     # F4: persist before filing. A raise inside the filer (e.g. an
     # unresolvable escalation destination) must leave a resumable
```

### `loop_engine.core.engine.x__pause_for_issue__mutmut_12`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -12,7 +12,7 @@
     # AWAITING_ISSUE snapshot behind rather than discarding the run's work —
     # the snapshot is written again below once the issue is actually filed.
     state = _finalize(state, stage_index, RunStatus.AWAITING_ISSUE)
-    snapshot_hint = f"state/{state.run_id}/{stage_index:02d}_{RunStatus.AWAITING_ISSUE.value}.json"
+    snapshot_hint = None
     issue = (issue_filer or default_issue_filer)(state, questions, snapshot_hint)
     state = state.model_copy(update={"pending_issue": issue})
     return _finalize(state, stage_index, RunStatus.AWAITING_ISSUE)
```

### `loop_engine.core.engine.x__pause_for_issue__mutmut_16`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -13,6 +13,6 @@
     # the snapshot is written again below once the issue is actually filed.
     state = _finalize(state, stage_index, RunStatus.AWAITING_ISSUE)
     snapshot_hint = f"state/{state.run_id}/{stage_index:02d}_{RunStatus.AWAITING_ISSUE.value}.json"
-    issue = (issue_filer or default_issue_filer)(state, questions, snapshot_hint)
+    issue = (issue_filer or default_issue_filer)(state, questions, None)
     state = state.model_copy(update={"pending_issue": issue})
     return _finalize(state, stage_index, RunStatus.AWAITING_ISSUE)
```

### `loop_engine.core.engine.x__prime_resume__mutmut_1`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -3,7 +3,7 @@
 ) -> tuple[State, list[str], int]:
     """Shared run/graph setup: seed carried findings for a resumed run and clear
     the paused-stage bookkeeping counter."""
-    carried_findings: list[str] = list(initial_findings or [])
+    carried_findings: list[str] = None
     carried_until = -1
     if carried_findings:
         carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
```

### `loop_engine.core.engine.x__prime_resume__mutmut_5`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -4,7 +4,7 @@
     """Shared run/graph setup: seed carried findings for a resumed run and clear
     the paused-stage bookkeeping counter."""
     carried_findings: list[str] = list(initial_findings or [])
-    carried_until = -1
+    carried_until = +1
     if carried_findings:
         carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
     if PAUSED_STAGE_COUNTER in state.counters:
```

### `loop_engine.core.engine.x__prime_resume__mutmut_6`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -4,7 +4,7 @@
     """Shared run/graph setup: seed carried findings for a resumed run and clear
     the paused-stage bookkeeping counter."""
     carried_findings: list[str] = list(initial_findings or [])
-    carried_until = -1
+    carried_until = -2
     if carried_findings:
         carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
     if PAUSED_STAGE_COUNTER in state.counters:
```

### `loop_engine.core.engine.x__prime_resume__mutmut_7`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -6,7 +6,7 @@
     carried_findings: list[str] = list(initial_findings or [])
     carried_until = -1
     if carried_findings:
-        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
+        carried_until = None
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
```

### `loop_engine.core.engine.x__prime_resume__mutmut_8`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -6,7 +6,7 @@
     carried_findings: list[str] = list(initial_findings or [])
     carried_until = -1
     if carried_findings:
-        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
+        carried_until = state.counters.get(None, len(loop.stages) - 1)
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
```

### `loop_engine.core.engine.x__prime_resume__mutmut_9`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -6,7 +6,7 @@
     carried_findings: list[str] = list(initial_findings or [])
     carried_until = -1
     if carried_findings:
-        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
+        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, None)
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
```

### `loop_engine.core.engine.x__prime_resume__mutmut_10`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -6,7 +6,7 @@
     carried_findings: list[str] = list(initial_findings or [])
     carried_until = -1
     if carried_findings:
-        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
+        carried_until = state.counters.get(len(loop.stages) - 1)
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
```

### `loop_engine.core.engine.x__prime_resume__mutmut_11`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -6,7 +6,7 @@
     carried_findings: list[str] = list(initial_findings or [])
     carried_until = -1
     if carried_findings:
-        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
+        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, )
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
```

### `loop_engine.core.engine.x__prime_resume__mutmut_12`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -6,7 +6,7 @@
     carried_findings: list[str] = list(initial_findings or [])
     carried_until = -1
     if carried_findings:
-        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
+        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) + 1)
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
```

### `loop_engine.core.engine.x__prime_resume__mutmut_13`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -6,7 +6,7 @@
     carried_findings: list[str] = list(initial_findings or [])
     carried_until = -1
     if carried_findings:
-        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
+        carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 2)
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
```

### `loop_engine.core.engine.x__prime_resume__mutmut_14`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -7,7 +7,7 @@
     carried_until = -1
     if carried_findings:
         carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
-    if PAUSED_STAGE_COUNTER in state.counters:
+    if PAUSED_STAGE_COUNTER not in state.counters:
         state = state.model_copy(
             update={
                 "counters": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
```

### `loop_engine.core.engine.x__prime_resume__mutmut_15`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -8,9 +8,5 @@
     if carried_findings:
         carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
     if PAUSED_STAGE_COUNTER in state.counters:
-        state = state.model_copy(
-            update={
-                "counters": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
-            }
-        )
+        state = None
     return state, carried_findings, carried_until
```

### `loop_engine.core.engine.x__prime_resume__mutmut_16`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -9,8 +9,6 @@
         carried_until = state.counters.get(PAUSED_STAGE_COUNTER, len(loop.stages) - 1)
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
-            update={
-                "counters": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
-            }
+            update=None
         )
     return state, carried_findings, carried_until
```

### `loop_engine.core.engine.x__prime_resume__mutmut_17`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -10,7 +10,7 @@
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
-                "counters": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
+                "XXcountersXX": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
             }
         )
     return state, carried_findings, carried_until
```

### `loop_engine.core.engine.x__prime_resume__mutmut_18`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -10,7 +10,7 @@
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
-                "counters": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
+                "COUNTERS": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
             }
         )
     return state, carried_findings, carried_until
```

### `loop_engine.core.engine.x__prime_resume__mutmut_19`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -10,7 +10,7 @@
     if PAUSED_STAGE_COUNTER in state.counters:
         state = state.model_copy(
             update={
-                "counters": {k: v for k, v in state.counters.items() if k != PAUSED_STAGE_COUNTER}
+                "counters": {k: v for k, v in state.counters.items() if k == PAUSED_STAGE_COUNTER}
             }
         )
     return state, carried_findings, carried_until
```

### `loop_engine.core.engine.x_execute_stage__mutmut_4`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -15,7 +15,7 @@
     stage = loop.stages[stage_index]
     stage_name = type(stage.persona).__name__
 
-    if stage_index > carried_until:
+    if stage_index >= carried_until:
         carried_findings = []
 
     missing = [k for k in stage.persona.consumes if not has_artifact(state, k)]
```

### `loop_engine.core.engine.x_execute_stage__mutmut_9`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -18,7 +18,7 @@
     if stage_index > carried_until:
         carried_findings = []
 
-    missing = [k for k in stage.persona.consumes if not has_artifact(state, k)]
+    missing = [k for k in stage.persona.consumes if not has_artifact(state, None)]
     if missing:
         state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
         raise MissingArtifactError(
```

### `loop_engine.core.engine.x_execute_stage__mutmut_20`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -23,7 +23,7 @@
         state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
         raise MissingArtifactError(
             f"Stage {stage_index} ({stage_name}) requires artifact(s) {missing} "
-            "which no prior stage produced."
+            "XXwhich no prior stage produced.XX"
         )
 
     if llm_client.remaining() <= 0:
```

### `loop_engine.core.engine.x_execute_stage__mutmut_21`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -23,7 +23,7 @@
         state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
         raise MissingArtifactError(
             f"Stage {stage_index} ({stage_name}) requires artifact(s) {missing} "
-            "which no prior stage produced."
+            "WHICH NO PRIOR STAGE PRODUCED."
         )
 
     if llm_client.remaining() <= 0:
```

### `loop_engine.core.engine.x_execute_stage__mutmut_23`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -26,7 +26,7 @@
             "which no prior stage produced."
         )
 
-    if llm_client.remaining() <= 0:
+    if llm_client.remaining() <= 1:
         return StageOutcome(
             _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
             stage_index,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_25`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -29,7 +29,7 @@
     if llm_client.remaining() <= 0:
         return StageOutcome(
             _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
-            stage_index,
+            None,
             carried_findings,
             carried_until,
             terminal=True,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_26`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -30,7 +30,7 @@
         return StageOutcome(
             _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
             stage_index,
-            carried_findings,
+            None,
             carried_until,
             terminal=True,
         )
```

### `loop_engine.core.engine.x_execute_stage__mutmut_27`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -31,7 +31,7 @@
             _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
             stage_index,
             carried_findings,
-            carried_until,
+            None,
             terminal=True,
         )
 
```

### `loop_engine.core.engine.x_execute_stage__mutmut_43`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -36,7 +36,7 @@
         )
 
     stage_findings = list(carried_findings)
-    gate_result = GateResult(GateDecision.REVISE)
+    gate_result = None
     previous_gate_findings: list[str] | None = None
     tokens_before = llm_client.tokens_used
     cost_before = llm_client.cost_used
```

### `loop_engine.core.engine.x_execute_stage__mutmut_44`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -36,7 +36,7 @@
         )
 
     stage_findings = list(carried_findings)
-    gate_result = GateResult(GateDecision.REVISE)
+    gate_result = GateResult(None)
     previous_gate_findings: list[str] | None = None
     tokens_before = llm_client.tokens_used
     cost_before = llm_client.cost_used
```

### `loop_engine.core.engine.x_execute_stage__mutmut_45`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -37,7 +37,7 @@
 
     stage_findings = list(carried_findings)
     gate_result = GateResult(GateDecision.REVISE)
-    previous_gate_findings: list[str] | None = None
+    previous_gate_findings: list[str] | None = ""
     tokens_before = llm_client.tokens_used
     cost_before = llm_client.cost_used
     cache_creation_before = llm_client.cache_creation_tokens_used
```

### `loop_engine.core.engine.x_execute_stage__mutmut_52`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -43,7 +43,7 @@
     cache_creation_before = llm_client.cache_creation_tokens_used
     cache_read_before = llm_client.cache_read_tokens_used
 
-    for _attempt in range(stage.max_revisions + 1):
+    for _attempt in range(stage.max_revisions + 2):
         try:
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
```

### `loop_engine.core.engine.x_execute_stage__mutmut_61`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -48,7 +48,7 @@
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
             return StageOutcome(
-                _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
+                None,
                 stage_index,
                 carried_findings,
                 carried_until,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_62`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -49,7 +49,7 @@
         except BudgetExceededError:
             return StageOutcome(
                 _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
-                stage_index,
+                None,
                 carried_findings,
                 carried_until,
                 terminal=True,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_63`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -50,7 +50,7 @@
             return StageOutcome(
                 _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
-                carried_findings,
+                None,
                 carried_until,
                 terminal=True,
             )
```

### `loop_engine.core.engine.x_execute_stage__mutmut_64`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -51,7 +51,7 @@
                 _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
                 carried_findings,
-                carried_until,
+                None,
                 terminal=True,
             )
         except ToolLoopExceededError:
```

### `loop_engine.core.engine.x_execute_stage__mutmut_65`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -52,7 +52,7 @@
                 stage_index,
                 carried_findings,
                 carried_until,
-                terminal=True,
+                terminal=None,
             )
         except ToolLoopExceededError:
             # A persona's inner tool loop exhausted its iteration cap without
```

### `loop_engine.core.engine.x_execute_stage__mutmut_66`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -48,7 +48,6 @@
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
             return StageOutcome(
-                _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
                 carried_findings,
                 carried_until,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_67`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -49,7 +49,6 @@
         except BudgetExceededError:
             return StageOutcome(
                 _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
-                stage_index,
                 carried_findings,
                 carried_until,
                 terminal=True,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_68`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -50,7 +50,6 @@
             return StageOutcome(
                 _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
-                carried_findings,
                 carried_until,
                 terminal=True,
             )
```

### `loop_engine.core.engine.x_execute_stage__mutmut_69`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -51,7 +51,6 @@
                 _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
                 carried_findings,
-                carried_until,
                 terminal=True,
             )
         except ToolLoopExceededError:
```

### `loop_engine.core.engine.x_execute_stage__mutmut_70`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -52,8 +52,7 @@
                 stage_index,
                 carried_findings,
                 carried_until,
-                terminal=True,
-            )
+                )
         except ToolLoopExceededError:
             # A persona's inner tool loop exhausted its iteration cap without
             # finishing. Like budget exhaustion, this is a bounded-resource
```

### `loop_engine.core.engine.x_execute_stage__mutmut_71`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -48,7 +48,7 @@
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
             return StageOutcome(
-                _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
+                _finalize(None, stage_index, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
                 carried_findings,
                 carried_until,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_72`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -48,7 +48,7 @@
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
             return StageOutcome(
-                _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
+                _finalize(state, None, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
                 carried_findings,
                 carried_until,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_73`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -48,7 +48,7 @@
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
             return StageOutcome(
-                _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
+                _finalize(state, stage_index, None),
                 stage_index,
                 carried_findings,
                 carried_until,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_74`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -48,7 +48,7 @@
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
             return StageOutcome(
-                _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
+                _finalize(stage_index, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
                 carried_findings,
                 carried_until,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_75`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -48,7 +48,7 @@
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
             return StageOutcome(
-                _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
+                _finalize(state, RunStatus.BUDGET_EXCEEDED),
                 stage_index,
                 carried_findings,
                 carried_until,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_76`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -48,7 +48,7 @@
             state = stage.persona.run(state, llm_client, findings=stage_findings or None)
         except BudgetExceededError:
             return StageOutcome(
-                _finalize(state, stage_index, RunStatus.BUDGET_EXCEEDED),
+                _finalize(state, stage_index, ),
                 stage_index,
                 carried_findings,
                 carried_until,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_77`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -52,7 +52,7 @@
                 stage_index,
                 carried_findings,
                 carried_until,
-                terminal=True,
+                terminal=False,
             )
         except ToolLoopExceededError:
             # A persona's inner tool loop exhausted its iteration cap without
```

### `loop_engine.core.engine.x_execute_stage__mutmut_79`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -63,7 +63,7 @@
             # increment; this is the safety net for every other persona.)
             return StageOutcome(
                 _finalize(state, stage_index, RunStatus.FAILED_STAGE),
-                stage_index,
+                None,
                 carried_findings,
                 carried_until,
                 terminal=True,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_80`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -64,7 +64,7 @@
             return StageOutcome(
                 _finalize(state, stage_index, RunStatus.FAILED_STAGE),
                 stage_index,
-                carried_findings,
+                None,
                 carried_until,
                 terminal=True,
             )
```

### `loop_engine.core.engine.x_execute_stage__mutmut_81`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -65,7 +65,7 @@
                 _finalize(state, stage_index, RunStatus.FAILED_STAGE),
                 stage_index,
                 carried_findings,
-                carried_until,
+                None,
                 terminal=True,
             )
         except TruncatedResponseError as exc:
```

### `loop_engine.core.engine.x_execute_stage__mutmut_95`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -71,7 +71,7 @@
         except TruncatedResponseError as exc:
             # Truncation is an output-sizing failure a blind retry won't
             # fix; fail the stage honestly with the snapshot persisted.
-            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
+            state = None
             raise InvalidStateTransitionError(
                 f"{stage_name} produced a truncated response: {exc}"
             ) from exc
```

### `loop_engine.core.engine.x_execute_stage__mutmut_96`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -71,7 +71,7 @@
         except TruncatedResponseError as exc:
             # Truncation is an output-sizing failure a blind retry won't
             # fix; fail the stage honestly with the snapshot persisted.
-            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
+            state = _finalize(None, stage_index, RunStatus.FAILED_STAGE)
             raise InvalidStateTransitionError(
                 f"{stage_name} produced a truncated response: {exc}"
             ) from exc
```

### `loop_engine.core.engine.x_execute_stage__mutmut_97`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -71,7 +71,7 @@
         except TruncatedResponseError as exc:
             # Truncation is an output-sizing failure a blind retry won't
             # fix; fail the stage honestly with the snapshot persisted.
-            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
+            state = _finalize(state, None, RunStatus.FAILED_STAGE)
             raise InvalidStateTransitionError(
                 f"{stage_name} produced a truncated response: {exc}"
             ) from exc
```

### `loop_engine.core.engine.x_execute_stage__mutmut_98`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -71,7 +71,7 @@
         except TruncatedResponseError as exc:
             # Truncation is an output-sizing failure a blind retry won't
             # fix; fail the stage honestly with the snapshot persisted.
-            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
+            state = _finalize(state, stage_index, None)
             raise InvalidStateTransitionError(
                 f"{stage_name} produced a truncated response: {exc}"
             ) from exc
```

### `loop_engine.core.engine.x_execute_stage__mutmut_99`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -71,7 +71,7 @@
         except TruncatedResponseError as exc:
             # Truncation is an output-sizing failure a blind retry won't
             # fix; fail the stage honestly with the snapshot persisted.
-            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
+            state = _finalize(stage_index, RunStatus.FAILED_STAGE)
             raise InvalidStateTransitionError(
                 f"{stage_name} produced a truncated response: {exc}"
             ) from exc
```

### `loop_engine.core.engine.x_execute_stage__mutmut_100`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -71,7 +71,7 @@
         except TruncatedResponseError as exc:
             # Truncation is an output-sizing failure a blind retry won't
             # fix; fail the stage honestly with the snapshot persisted.
-            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
+            state = _finalize(state, RunStatus.FAILED_STAGE)
             raise InvalidStateTransitionError(
                 f"{stage_name} produced a truncated response: {exc}"
             ) from exc
```

### `loop_engine.core.engine.x_execute_stage__mutmut_101`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -71,7 +71,7 @@
         except TruncatedResponseError as exc:
             # Truncation is an output-sizing failure a blind retry won't
             # fix; fail the stage honestly with the snapshot persisted.
-            state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
+            state = _finalize(state, stage_index, )
             raise InvalidStateTransitionError(
                 f"{stage_name} produced a truncated response: {exc}"
             ) from exc
```

### `loop_engine.core.engine.x_execute_stage__mutmut_102`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -73,7 +73,7 @@
             # fix; fail the stage honestly with the snapshot persisted.
             state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
             raise InvalidStateTransitionError(
-                f"{stage_name} produced a truncated response: {exc}"
+                None
             ) from exc
 
         state = _revalidate(state, stage_name)
```

### `loop_engine.core.engine.x_execute_stage__mutmut_138`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -96,7 +96,7 @@
         else:
             state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
             raise StageGateFailedError(
-                f"{stage_name} failed its gate after {stage.max_revisions + 1} attempts: "
+                f"{stage_name} failed its gate after {stage.max_revisions - 1} attempts: "
                 f"{'; '.join(gate_result.findings)}"
             )
 
```

### `loop_engine.core.engine.x_execute_stage__mutmut_139`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -96,7 +96,7 @@
         else:
             state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
             raise StageGateFailedError(
-                f"{stage_name} failed its gate after {stage.max_revisions + 1} attempts: "
+                f"{stage_name} failed its gate after {stage.max_revisions + 2} attempts: "
                 f"{'; '.join(gate_result.findings)}"
             )
 
```

### `loop_engine.core.engine.x_execute_stage__mutmut_141`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -97,7 +97,7 @@
             state = _finalize(state, stage_index, RunStatus.FAILED_STAGE)
             raise StageGateFailedError(
                 f"{stage_name} failed its gate after {stage.max_revisions + 1} attempts: "
-                f"{'; '.join(gate_result.findings)}"
+                f"{'XX; XX'.join(gate_result.findings)}"
             )
 
     if gate_result.decision is GateDecision.ESCALATE:
```

### `loop_engine.core.engine.x_execute_stage__mutmut_173`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -110,7 +110,7 @@
         if escalations >= MAX_ESCALATIONS_PER_STAGE:
             state = _merge_questions(state, gate_result.questions)
             paused = _pause_for_issue(state, stage_index, unresolved_questions(state), issue_filer)
-            return StageOutcome(paused, stage_index, carried_findings, carried_until, terminal=True)
+            return StageOutcome(paused, None, carried_findings, carried_until, terminal=True)
 
         resolved = _run_resolver_ladder(stage, gate_result.questions, state, llm_client)
         state = _merge_questions(state, resolved)
```

### `loop_engine.core.engine.x_execute_stage__mutmut_174`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -110,7 +110,7 @@
         if escalations >= MAX_ESCALATIONS_PER_STAGE:
             state = _merge_questions(state, gate_result.questions)
             paused = _pause_for_issue(state, stage_index, unresolved_questions(state), issue_filer)
-            return StageOutcome(paused, stage_index, carried_findings, carried_until, terminal=True)
+            return StageOutcome(paused, stage_index, None, carried_until, terminal=True)
 
         resolved = _run_resolver_ladder(stage, gate_result.questions, state, llm_client)
         state = _merge_questions(state, resolved)
```

### `loop_engine.core.engine.x_execute_stage__mutmut_175`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -110,7 +110,7 @@
         if escalations >= MAX_ESCALATIONS_PER_STAGE:
             state = _merge_questions(state, gate_result.questions)
             paused = _pause_for_issue(state, stage_index, unresolved_questions(state), issue_filer)
-            return StageOutcome(paused, stage_index, carried_findings, carried_until, terminal=True)
+            return StageOutcome(paused, stage_index, carried_findings, None, terminal=True)
 
         resolved = _run_resolver_ladder(stage, gate_result.questions, state, llm_client)
         state = _merge_questions(state, resolved)
```

### `loop_engine.core.engine.x_execute_stage__mutmut_186`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -112,7 +112,7 @@
             paused = _pause_for_issue(state, stage_index, unresolved_questions(state), issue_filer)
             return StageOutcome(paused, stage_index, carried_findings, carried_until, terminal=True)
 
-        resolved = _run_resolver_ladder(stage, gate_result.questions, state, llm_client)
+        resolved = _run_resolver_ladder(stage, gate_result.questions, None, llm_client)
         state = _merge_questions(state, resolved)
 
         if unresolved_questions(state):
```

### `loop_engine.core.engine.x_execute_stage__mutmut_187`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -112,7 +112,7 @@
             paused = _pause_for_issue(state, stage_index, unresolved_questions(state), issue_filer)
             return StageOutcome(paused, stage_index, carried_findings, carried_until, terminal=True)
 
-        resolved = _run_resolver_ladder(stage, gate_result.questions, state, llm_client)
+        resolved = _run_resolver_ladder(stage, gate_result.questions, state, None)
         state = _merge_questions(state, resolved)
 
         if unresolved_questions(state):
```

### `loop_engine.core.engine.x_execute_stage__mutmut_209`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -117,7 +117,7 @@
 
         if unresolved_questions(state):
             paused = _pause_for_issue(state, stage_index, unresolved_questions(state), issue_filer)
-            return StageOutcome(paused, stage_index, carried_findings, carried_until, terminal=True)
+            return StageOutcome(paused, None, carried_findings, carried_until, terminal=True)
 
         # Everything was resolved within the ladder: deliver resolutions
         # as findings and route rework by blast radius.
```

### `loop_engine.core.engine.x_execute_stage__mutmut_210`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -117,7 +117,7 @@
 
         if unresolved_questions(state):
             paused = _pause_for_issue(state, stage_index, unresolved_questions(state), issue_filer)
-            return StageOutcome(paused, stage_index, carried_findings, carried_until, terminal=True)
+            return StageOutcome(paused, stage_index, None, carried_until, terminal=True)
 
         # Everything was resolved within the ladder: deliver resolutions
         # as findings and route rework by blast radius.
```

### `loop_engine.core.engine.x_execute_stage__mutmut_211`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -117,7 +117,7 @@
 
         if unresolved_questions(state):
             paused = _pause_for_issue(state, stage_index, unresolved_questions(state), issue_filer)
-            return StageOutcome(paused, stage_index, carried_findings, carried_until, terminal=True)
+            return StageOutcome(paused, stage_index, carried_findings, None, terminal=True)
 
         # Everything was resolved within the ladder: deliver resolutions
         # as findings and route rework by blast radius.
```

### `loop_engine.core.engine.x_execute_stage__mutmut_229`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -124,7 +124,7 @@
         carried_findings = _resolution_findings(resolved)
         carried_until = stage_index
         reentry = reentry_index(loop, stage_index, resolved)
-        if reentry < stage_index:
+        if reentry <= stage_index:
             replans = state.counters.get("replans", 0)
             if replans >= MAX_REPLANS_PER_RUN:
                 paused = _pause_for_issue(state, stage_index, resolved, issue_filer)
```

### `loop_engine.core.engine.x_execute_stage__mutmut_249`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -129,7 +129,7 @@
             if replans >= MAX_REPLANS_PER_RUN:
                 paused = _pause_for_issue(state, stage_index, resolved, issue_filer)
                 return StageOutcome(
-                    paused, stage_index, carried_findings, carried_until, terminal=True
+                    paused, None, carried_findings, carried_until, terminal=True
                 )
             state = state.model_copy(
                 update={"counters": {**state.counters, "replans": replans + 1}}
```

### `loop_engine.core.engine.x_execute_stage__mutmut_250`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -129,7 +129,7 @@
             if replans >= MAX_REPLANS_PER_RUN:
                 paused = _pause_for_issue(state, stage_index, resolved, issue_filer)
                 return StageOutcome(
-                    paused, stage_index, carried_findings, carried_until, terminal=True
+                    paused, stage_index, None, carried_until, terminal=True
                 )
             state = state.model_copy(
                 update={"counters": {**state.counters, "replans": replans + 1}}
```

### `loop_engine.core.engine.x_execute_stage__mutmut_251`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -129,7 +129,7 @@
             if replans >= MAX_REPLANS_PER_RUN:
                 paused = _pause_for_issue(state, stage_index, resolved, issue_filer)
                 return StageOutcome(
-                    paused, stage_index, carried_findings, carried_until, terminal=True
+                    paused, stage_index, carried_findings, None, terminal=True
                 )
             state = state.model_copy(
                 update={"counters": {**state.counters, "replans": replans + 1}}
```

### `loop_engine.core.engine.x_execute_stage__mutmut_288`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -140,7 +140,7 @@
     state = _record_stage(
         state,
         stage_name,
-        llm_client.tokens_used - tokens_before,
+        llm_client.tokens_used + tokens_before,
         llm_client.cost_used - cost_before,
         llm_client.cache_creation_tokens_used - cache_creation_before,
         llm_client.cache_read_tokens_used - cache_read_before,
```

### `loop_engine.core.engine.x_execute_stage__mutmut_289`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -141,7 +141,7 @@
         state,
         stage_name,
         llm_client.tokens_used - tokens_before,
-        llm_client.cost_used - cost_before,
+        llm_client.cost_used + cost_before,
         llm_client.cache_creation_tokens_used - cache_creation_before,
         llm_client.cache_read_tokens_used - cache_read_before,
     )
```

### `loop_engine.core.engine.x_execute_stage__mutmut_290`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -142,7 +142,7 @@
         stage_name,
         llm_client.tokens_used - tokens_before,
         llm_client.cost_used - cost_before,
-        llm_client.cache_creation_tokens_used - cache_creation_before,
+        llm_client.cache_creation_tokens_used + cache_creation_before,
         llm_client.cache_read_tokens_used - cache_read_before,
     )
     publish_artifacts(state)
```

### `loop_engine.core.engine.x_execute_stage__mutmut_291`
```diff
--- src/loop_engine/core/engine.py
+++ src/loop_engine/core/engine.py
@@ -143,7 +143,7 @@
         llm_client.tokens_used - tokens_before,
         llm_client.cost_used - cost_before,
         llm_client.cache_creation_tokens_used - cache_creation_before,
-        llm_client.cache_read_tokens_used - cache_read_before,
+        llm_client.cache_read_tokens_used + cache_read_before,
     )
     publish_artifacts(state)
     write_state_snapshot(
```

### `loop_engine.core.gates.x_new_question__mutmut_7`
```diff
--- src/loop_engine/core/gates.py
+++ src/loop_engine/core/gates.py
@@ -1,2 +1,2 @@
 def new_question(origin_stage: str, text: str) -> Question:
-    return Question(id=uuid.uuid4().hex[:8], origin_stage=origin_stage, text=text)
+    return Question(id=uuid.uuid4().hex[:9], origin_stage=origin_stage, text=text)
```

### `loop_engine.core.gates.x__is_question_shaped__mutmut_3`
```diff
--- src/loop_engine/core/gates.py
+++ src/loop_engine/core/gates.py
@@ -1,3 +1,3 @@
 def _is_question_shaped(text: str) -> bool:
     stripped = text.strip()
-    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
+    return 1 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
```

### `loop_engine.core.gates.x__is_question_shaped__mutmut_4`
```diff
--- src/loop_engine/core/gates.py
+++ src/loop_engine/core/gates.py
@@ -1,3 +1,3 @@
 def _is_question_shaped(text: str) -> bool:
     stripped = text.strip()
-    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
+    return 0 <= len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
```

### `loop_engine.core.gates.x__is_question_shaped__mutmut_5`
```diff
--- src/loop_engine/core/gates.py
+++ src/loop_engine/core/gates.py
@@ -1,3 +1,3 @@
 def _is_question_shaped(text: str) -> bool:
     stripped = text.strip()
-    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
+    return 0 < len(stripped) < _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
```

### `loop_engine.core.gates.x__is_question_shaped__mutmut_7`
```diff
--- src/loop_engine/core/gates.py
+++ src/loop_engine/core/gates.py
@@ -1,3 +1,3 @@
 def _is_question_shaped(text: str) -> bool:
     stripped = text.strip()
-    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
+    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip(None).endswith("?")
```

### `loop_engine.core.gates.x__is_question_shaped__mutmut_8`
```diff
--- src/loop_engine/core/gates.py
+++ src/loop_engine/core/gates.py
@@ -1,3 +1,3 @@
 def _is_question_shaped(text: str) -> bool:
     stripped = text.strip()
-    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
+    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.lstrip("*_`").endswith("?")
```

### `loop_engine.core.gates.x__is_question_shaped__mutmut_9`
```diff
--- src/loop_engine/core/gates.py
+++ src/loop_engine/core/gates.py
@@ -1,3 +1,3 @@
 def _is_question_shaped(text: str) -> bool:
     stripped = text.strip()
-    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("*_`").endswith("?")
+    return 0 < len(stripped) <= _QUESTION_SHAPED_MAX_LENGTH and stripped.rstrip("XX*_`XX").endswith("?")
```

### `loop_engine.core.graph_engine.x__make_complete_node__mutmut_12`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -1,6 +1,6 @@
 def _make_complete_node(loop: Loop):
     def node(gs: GraphState) -> dict:
         final = _finalize(gs["state"], len(loop.stages), RunStatus.COMPLETED)
-        return {"state": final, "done": True}
+        return {"state": final, "XXdoneXX": True}
 
     return node
```

### `loop_engine.core.graph_engine.x__make_complete_node__mutmut_13`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -1,6 +1,6 @@
 def _make_complete_node(loop: Loop):
     def node(gs: GraphState) -> dict:
         final = _finalize(gs["state"], len(loop.stages), RunStatus.COMPLETED)
-        return {"state": final, "done": True}
+        return {"state": final, "DONE": True}
 
     return node
```

### `loop_engine.core.graph_engine.x__make_complete_node__mutmut_14`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -1,6 +1,6 @@
 def _make_complete_node(loop: Loop):
     def node(gs: GraphState) -> dict:
         final = _finalize(gs["state"], len(loop.stages), RunStatus.COMPLETED)
-        return {"state": final, "done": True}
+        return {"state": final, "done": False}
 
     return node
```

### `loop_engine.core.graph_engine.x_build_state_graph__mutmut_29`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -8,7 +8,7 @@
 
     stage_targets = {_node_name(i): _node_name(i) for i in range(len(loop.stages))}
     entry_map = {**stage_targets, _COMPLETE_NODE: _COMPLETE_NODE}
-    graph.add_conditional_edges(START, lambda gs: _next_target(loop, gs), entry_map)
+    graph.add_conditional_edges(START, lambda gs: _next_target(loop, gs), None)
 
     route_map = {**entry_map, END: END}
     for index in range(len(loop.stages)):
```

### `loop_engine.core.graph_engine.x_build_state_graph__mutmut_32`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -8,7 +8,7 @@
 
     stage_targets = {_node_name(i): _node_name(i) for i in range(len(loop.stages))}
     entry_map = {**stage_targets, _COMPLETE_NODE: _COMPLETE_NODE}
-    graph.add_conditional_edges(START, lambda gs: _next_target(loop, gs), entry_map)
+    graph.add_conditional_edges(START, lambda gs: _next_target(loop, gs), )
 
     route_map = {**entry_map, END: END}
     for index in range(len(loop.stages)):
```

### `loop_engine.core.graph_engine.x_build_state_graph__mutmut_38`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -10,7 +10,7 @@
     entry_map = {**stage_targets, _COMPLETE_NODE: _COMPLETE_NODE}
     graph.add_conditional_edges(START, lambda gs: _next_target(loop, gs), entry_map)
 
-    route_map = {**entry_map, END: END}
+    route_map = None
     for index in range(len(loop.stages)):
         graph.add_conditional_edges(_node_name(index), lambda gs: _next_target(loop, gs), route_map)
     graph.add_edge(_COMPLETE_NODE, END)
```

### `loop_engine.core.graph_engine.x_build_state_graph__mutmut_42`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -12,6 +12,6 @@
 
     route_map = {**entry_map, END: END}
     for index in range(len(loop.stages)):
-        graph.add_conditional_edges(_node_name(index), lambda gs: _next_target(loop, gs), route_map)
+        graph.add_conditional_edges(_node_name(index), lambda gs: _next_target(loop, gs), None)
     graph.add_edge(_COMPLETE_NODE, END)
     return graph.compile()
```

### `loop_engine.core.graph_engine.x_build_state_graph__mutmut_45`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -12,6 +12,6 @@
 
     route_map = {**entry_map, END: END}
     for index in range(len(loop.stages)):
-        graph.add_conditional_edges(_node_name(index), lambda gs: _next_target(loop, gs), route_map)
+        graph.add_conditional_edges(_node_name(index), lambda gs: _next_target(loop, gs), )
     graph.add_edge(_COMPLETE_NODE, END)
     return graph.compile()
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_3`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -8,7 +8,7 @@
 ) -> State:
     """Drive `loop` to a terminal state, returning the final, already-persisted
     `State`."""
-    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
+    state = initial_state.model_copy(update=None)
     state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)
 
     compiled = build_state_graph(loop, llm_client, issue_filer)
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_4`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -8,7 +8,7 @@
 ) -> State:
     """Drive `loop` to a terminal state, returning the final, already-persisted
     `State`."""
-    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
+    state = initial_state.model_copy(update={"XXstatusXX": RunStatus.RUNNING, "pending_issue": None})
     state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)
 
     compiled = build_state_graph(loop, llm_client, issue_filer)
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_5`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -8,7 +8,7 @@
 ) -> State:
     """Drive `loop` to a terminal state, returning the final, already-persisted
     `State`."""
-    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
+    state = initial_state.model_copy(update={"STATUS": RunStatus.RUNNING, "pending_issue": None})
     state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)
 
     compiled = build_state_graph(loop, llm_client, issue_filer)
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_6`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -8,7 +8,7 @@
 ) -> State:
     """Drive `loop` to a terminal state, returning the final, already-persisted
     `State`."""
-    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
+    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "XXpending_issueXX": None})
     state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)
 
     compiled = build_state_graph(loop, llm_client, issue_filer)
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_7`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -8,7 +8,7 @@
 ) -> State:
     """Drive `loop` to a terminal state, returning the final, already-persisted
     `State`."""
-    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
+    state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "PENDING_ISSUE": None})
     state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)
 
     compiled = build_state_graph(loop, llm_client, issue_filer)
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_9`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -9,7 +9,7 @@
     """Drive `loop` to a terminal state, returning the final, already-persisted
     `State`."""
     state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
-    state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)
+    state, carried_findings, carried_until = _prime_resume(None, state, initial_findings)
 
     compiled = build_state_graph(loop, llm_client, issue_filer)
     init: GraphState = {
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_11`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -9,7 +9,7 @@
     """Drive `loop` to a terminal state, returning the final, already-persisted
     `State`."""
     state = initial_state.model_copy(update={"status": RunStatus.RUNNING, "pending_issue": None})
-    state, carried_findings, carried_until = _prime_resume(loop, state, initial_findings)
+    state, carried_findings, carried_until = _prime_resume(loop, state, None)
 
     compiled = build_state_graph(loop, llm_client, issue_filer)
     init: GraphState = {
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_34`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -19,6 +19,6 @@
         "carried_until": carried_until,
         "done": False,
     }
-    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
+    recursion_limit = None
     result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_35`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -19,6 +19,6 @@
         "carried_until": carried_until,
         "done": False,
     }
-    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
+    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) - 50
     result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_36`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -19,6 +19,6 @@
         "carried_until": carried_until,
         "done": False,
     }
-    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
+    recursion_limit = len(loop.stages) / (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
     result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_37`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -19,6 +19,6 @@
         "carried_until": carried_until,
         "done": False,
     }
-    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
+    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) - 4) + 50
     result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_38`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -19,6 +19,6 @@
         "carried_until": carried_until,
         "done": False,
     }
-    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
+    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM / max(len(loop.stages), 1) + 4) + 50
     result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_43`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -19,6 +19,6 @@
         "carried_until": carried_until,
         "done": False,
     }
-    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
+    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 2) + 4) + 50
     result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_44`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -19,6 +19,6 @@
         "carried_until": carried_until,
         "done": False,
     }
-    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
+    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 5) + 50
     result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_45`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -19,6 +19,6 @@
         "carried_until": carried_until,
         "done": False,
     }
-    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
+    recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 51
     result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_48`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -20,5 +20,5 @@
         "done": False,
     }
     recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
-    result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
+    result = compiled.invoke(init, config=None)
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_50`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -20,5 +20,5 @@
         "done": False,
     }
     recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
-    result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
+    result = compiled.invoke(init, )
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_51`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -20,5 +20,5 @@
         "done": False,
     }
     recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
-    result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
+    result = compiled.invoke(init, config={"XXrecursion_limitXX": recursion_limit})
     return result["state"]
```

### `loop_engine.core.graph_engine.x_run_graph_loop__mutmut_52`
```diff
--- src/loop_engine/core/graph_engine.py
+++ src/loop_engine/core/graph_engine.py
@@ -20,5 +20,5 @@
         "done": False,
     }
     recursion_limit = len(loop.stages) * (_RECURSION_HEADROOM // max(len(loop.stages), 1) + 4) + 50
-    result = compiled.invoke(init, config={"recursion_limit": recursion_limit})
+    result = compiled.invoke(init, config={"RECURSION_LIMIT": recursion_limit})
     return result["state"]
```

