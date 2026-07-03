### FILEPATH: /sprints/06_default_persona_implementations/sprint_plan.md

**Sprint Goal:** Implement the four default personas — PM, Architecture, Agile Sprint Breakdown, Coder/IaC — as decoupled `BasePersona` modules reproducing the behavior of `prompts/01`–`04`.

**Dependencies:** Sprint 03 (llm_client_and_secrets), Sprint 05 (sequential_execution_engine)

**Security Considerations:** Each persona receives `State` and `LLMClient` only via method injection — no persona may import `keyring` or instantiate its own `LLMClient`. This sprint extends the sole-keyring-importer AST scan (introduced in Sprint 03) to cover these four new modules, re-running it as part of this sprint's acceptance criteria.

**Risks & Blockers:** Behavioral drift risk — porting `prompts/01`–`04` into persona modules without an automated parity check risks silently changing PM, Architecture, Sprint-Breakdown, or Coder output behavior from the originals. Mitigated by Task 5 below.

**Tasks:**

- **Task 1: PM Persona**
  - **Description:** Implement `PMPersona(BasePersona)` in `src/loop_engine/personas/pm/persona.py`, embedding the PM interview prompt structure as a module-level constant `PROMPT_TEMPLATE`, calling `llm_client.call()`, and writing the resulting project-specification fields into `state.artifacts["project_spec"]` as a JSON string.
  - **Target Files:** `src/loop_engine/personas/pm/persona.py`, `src/loop_engine/personas/pm/__init__.py`
  - **Acceptance Criteria:** `tests/personas/test_pm.py` verifies `PMPersona().run(state, mock_llm_client)` returns a `State` whose `artifacts["project_spec"]` parses as valid JSON containing a `problem_statement` key.

- **Task 2: Architecture Persona**
  - **Description:** Implement `ArchitecturePersona(BasePersona)` in `src/loop_engine/personas/architecture/persona.py`, embedding the prompt structure of `prompts/02_architecture_definition_prompt.md` as `PROMPT_TEMPLATE`, consuming `state.artifacts["project_spec"]` as input, and writing the resulting architecture document markdown to `state.artifacts["architecture_definition"]`.
  - **Target Files:** `src/loop_engine/personas/architecture/persona.py`, `src/loop_engine/personas/architecture/__init__.py`
  - **Acceptance Criteria:** `tests/personas/test_architecture.py` verifies the persona raises `KeyError` when `state.artifacts` lacks `project_spec`, and returns a populated `architecture_definition` artifact when it is present.

- **Task 3: Agile Sprint Breakdown Persona**
  - **Description:** Implement `AgileSprintBreakdownPersona(BasePersona)` in `src/loop_engine/personas/agile_sprint_breakdown/persona.py`, embedding this sprint-breakdown prompt's structure as `PROMPT_TEMPLATE`, consuming `state.artifacts["architecture_definition"]`, and writing the resulting sprint content to `state.artifacts["sprint_plans"]` as a JSON-encoded list of `{path, content}` objects.
  - **Target Files:** `src/loop_engine/personas/agile_sprint_breakdown/persona.py`, `src/loop_engine/personas/agile_sprint_breakdown/__init__.py`
  - **Acceptance Criteria:** `tests/personas/test_agile_sprint_breakdown.py` verifies the persona raises `KeyError` when `architecture_definition` is absent from `state.artifacts`, and that a mocked LLM response containing two sprint file blocks produces a two-element list in `sprint_plans`.

- **Task 4: Coder/IaC Persona**
  - **Description:** Implement `CoderIacPersona(BasePersona)` in `src/loop_engine/personas/coder_iac/persona.py`, embedding the structure of `prompts/04_developer_iac_implementation_prompt.md` as `PROMPT_TEMPLATE`, consuming `state.artifacts["sprint_plans"]`, and writing a summary of generated file paths to `state.artifacts["implementation_summary"]`.
  - **Target Files:** `src/loop_engine/personas/coder_iac/persona.py`, `src/loop_engine/personas/coder_iac/__init__.py`
  - **Acceptance Criteria:** `tests/personas/test_coder_iac.py` verifies the persona raises `KeyError` when `sprint_plans` is absent, and returns a non-empty `implementation_summary` string when present.

- **Task 5: Prompt Parity Regression Test**
  - **Description:** Write `tests/personas/test_prompt_parity.py` asserting each persona's embedded `PROMPT_TEMPLATE` constant contains the section headers present in its corresponding `prompts/0N_*.md` source file (for example, asserting the `## ROLE`, `## OBJECTIVE`, and `## TASK INSTRUCTIONS` substrings from `prompts/03_agile_sprint_breakdown_prompt.md` appear in `AgileSprintBreakdownPersona.PROMPT_TEMPLATE`).
  - **Target Files:** `tests/personas/test_prompt_parity.py`
  - **Acceptance Criteria:** The test passes for all four personas against the current `prompts/` files.

---
