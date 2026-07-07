### FILEPATH: /sprints/09_coder_targeted_reentry/sprint_plan.md

**Sprint Goal:** On findings re-entry, the Coder persona re-runs only the sprint(s) whose escalated questions were resolved, instead of re-running every completed sprint.

**Dependencies:** None (independent of all other token-efficiency sprints).

**Security Considerations:** No new I/O or credential surface. The new `Question.origin_detail` field must remain a plain string (sprint path) validated by Pydantic with `extra="forbid"` intact; a snapshot-supplied non-string value must be rejected on load.

**Risks & Blockers:** The engine delivers gate-REVISE findings and resolved-question findings through the same `findings` parameter. If the persona re-runs nothing on a pure gate-REVISE pass it will return an identical artifact and trip the engine's identical-findings escalation — the fallback in Task 2 is mandatory.

**Tasks:**

- **Task 1: Question origin attribution**
  - **Description:** Add `origin_detail: str | None = None` to `Question` in `src/loop_engine/core/state.py` (defaulted — no `schema_version` bump, `extra="forbid"` preserved). In `src/loop_engine/personas/coder_iac/persona.py`, stamp each question extracted from a sprint report with `origin_detail=sprint_path` via `model_copy` before appending to state.
  - **Target Files:** `src/loop_engine/core/state.py`, `src/loop_engine/personas/coder_iac/persona.py`
  - **Acceptance Criteria:** `tests/personas/test_coder_iac.py` verifies extracted questions carry `origin_detail` equal to the sprint plan path. `tests/core/test_state.py` verifies a v2 snapshot payload without `origin_detail` still validates, and a payload with a non-string `origin_detail` is rejected.

- **Task 2: Targeted re-run rule with gate-findings fallback**
  - **Description:** Replace the skip rule `if sprint_path in reports and not findings: continue` in `CoderIacPersona.run` with: re-run a sprint iff (a) it has no report yet, or (b) its path appears in `{q.origin_detail for q in state.questions if q.origin_stage == "CoderIacPersona" and q.resolution is not None}`. Fallback: if `findings` is non-empty but that resolved-sprint set is empty (pure gate-REVISE findings), preserve current behavior and re-run all sprints.
  - **Target Files:** `src/loop_engine/personas/coder_iac/persona.py`
  - **Acceptance Criteria:** All four existing tests in `tests/personas/test_coder_iac.py` pass unchanged. New tests verify: re-entry with reports seeded for both sprints and a resolved question originating from sprint 2 makes exactly one LLM call (sprint 2 only) and preserves sprint 1's report byte-for-byte; re-entry with findings but no resolved coder questions re-runs all sprints.

- **Task 3 (Security): Documentation of re-entry semantics**
  - **Description:** Update the Coder persona bullet in `CLAUDE.md` and `README.md` to state that re-entry re-runs only the sprint(s) whose questions were resolved, falling back to a full re-run for gate-revision findings.
  - **Target Files:** `CLAUDE.md`, `README.md`
  - **Acceptance Criteria:** Both files describe the targeted re-entry behavior; `hatch run test` and `hatch run lint` pass.

---
