### FILEPATH: /sprints/14_agentic_coder_persona_and_gate/sprint_plan.md

**Sprint Goal:** The Coder persona becomes a bounded agentic loop (read tools + run_tests) emitting edit-style output, and the Coder stage's gate re-runs the sprint's tests deterministically so ACCEPT is evidence-based.

**Dependencies:** Sprint 13 (agentic_coder_tooling); Sprint 09 (coder_targeted_reentry); Sprint 12 recommended.

**Security Considerations:** The tool set remains read/execute-only — file writes still route exclusively through `write_artifact` (`tools/state_io` stays the sole writer; the AST boundary test enforces it). The new execution boundary must be documented: the engine now executes generated code via subprocess inside the run tree with the invoking user's privileges; the stated operating assumption is the sandboxed devcontainer, and `docs/architecture_definition.md` must warn explicitly that untrusted loops run only in the container. Edit-block application is new validated I/O: malformed or non-applying edit blocks are rejected with tests proving rejection (Global DoD).

**Risks & Blockers:** `core/` must not import concrete persona modules (`tests/core/test_boundaries.py`); if it also restricts importing `tools/`, inject the test-runner callable through the `Stage` dataclass rather than importing `coder_tools` from `core/`. Integration fixtures' mocked transports return `end_turn` with no tool_use blocks (one create per sprint keeps counts at 2/4), but the evidence gate will run pytest against fixture artifact trees — fixtures must gain a trivial passing test file because pytest exit 5 (no tests collected) is treated as REVISE ("the Global Definition of Done requires tests"), not a pass.

**Tasks:**

- **Task 1: Agentic Coder persona**
  - **Description:** Rework `CoderIacPersona.run` to drive one `llm_client.run_tool_loop(...)` per sprint with the four tools from `tools/coder_tools/` (read_file, list_files, grep, run_tests), cached system prefix = template + architecture definition. Output format: str_replace-style edit blocks (search/replace pairs per `### FILEPATH:`) with the existing full-content form as fallback; the persona applies edits and writes results via `write_artifact` only; malformed or non-applying blocks are rejected and reported as findings. Update `prompts/04_developer_iac_implementation_prompt.md` and the embedded `PROMPT_TEMPLATE` together: tool usage, run-the-tests-before-claiming-done, edit-block grammar; keep header parity in one commit.
  - **Target Files:** `src/loop_engine/personas/coder_iac/persona.py`, `prompts/04_developer_iac_implementation_prompt.md`, `tests/personas/test_coder_iac.py`, `tests/personas/test_prompt_parity.py`
  - **Acceptance Criteria:** Reworked coder tests (mocking `run_tool_loop`) verify one loop per sprint, preserved skip/re-entry semantics from Sprint 09, preserved stop-at-open-questions, edit-block application, and rejection of malformed edit blocks. Prompt parity passes.

- **Task 2: Evidence-based Coder gate**
  - **Description:** Create `src/loop_engine/core/coder_gate.py` (keeping `gates.py` generic): run the content `ArtifactGate`, then deterministically execute `run_tests` against the produced sprint tree. Failing tests ⇒ REVISE with the pytest output as findings, each finding prefixed with the sprint path (so Sprint 09's targeting applies to gate findings); pytest exit 5 ⇒ REVISE with a "no tests were produced; the Global Definition of Done requires tests" finding; green ⇒ ACCEPT. Wire the gate onto the Coder stage in `loops/default/loop.py`. Respect core-import boundaries (inject the runner via `Stage` if needed).
  - **Target Files:** `src/loop_engine/core/coder_gate.py`, `src/loop_engine/loops/default/loop.py`, `tests/core/test_coder_gate.py`, `tests/loops/test_default.py`
  - **Acceptance Criteria:** New tests verify REVISE-on-red with pytest output and sprint-path prefix in findings, ACCEPT-on-green, and exit-5 ⇒ REVISE. `tests/core/test_boundaries.py` passes.

- **Task 3: Integration fixtures and end-to-end counts**
  - **Description:** Update `tests/integration/test_budget_abort.py` and `test_no_credential_leakage.py`: mocked responses keep `end_turn` with no tool_use (one transport call per sprint preserves exact counts 2 and 4); fixture artifact trees gain a trivial passing test file so the evidence gate accepts.
  - **Target Files:** `tests/integration/test_budget_abort.py`, `tests/integration/test_no_credential_leakage.py`
  - **Acceptance Criteria:** Both integration tests pass with unchanged call-count and exit-code assertions.

- **Task 4 (Security): Execution-boundary documentation**
  - **Description:** Update `docs/architecture_definition.md`: §1 keeps the network-egress sentence and adds the new execution boundary (subprocess pytest on generated code; devcontainer assumption; explicit container-only warning for untrusted loops); §3 file-system scope (read-only tools + test execution, writes via state_io only); §4 tool inputs are model-controlled and path-validated; §8 directives. Update `README.md` security section (subprocess execution + sandbox assumption; ACCEPT is evidence-based) and `CLAUDE.md` (client tool loop with per-iteration debits, coder tool list, boundaries list noting `run_tests` as the only subprocess surface besides issue_io's `gh`, pytest as runtime dep).
  - **Target Files:** `docs/architecture_definition.md`, `README.md`, `CLAUDE.md`
  - **Acceptance Criteria:** All three documents describe the tool loop, tool set, and execution boundary; `hatch run test`, `hatch run lint`, `hatch run format` pass.

---
