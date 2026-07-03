### FILEPATH: /sprints/05_sequential_execution_engine/sprint_plan.md

**Sprint Goal:** Implement the core engine that drives an ordered list of personas over shared `State` with per-stage persistence and budget checks.

**Dependencies:** Sprint 02 (state_and_persona_contract), Sprint 03 (llm_client_and_secrets), Sprint 04 (state_persistence_and_artifacts)

**Security Considerations:** The engine is the trust-boundary enforcement point between stages. Even though a persona's return value is already typed as `State`, the engine must revalidate it via `State.model_validate()` before passing it to the next persona, to catch a persona that mutated the object in place into an invalid state after construction.

**Risks & Blockers:** None identified.

**Tasks:**

- **Task 1: Sequential Run Loop**
  - **Description:** Implement `run_loop(loop: list[BasePersona], initial_state: State, llm_client: LLMClient) -> State` in `src/loop_engine/core/engine.py` as a plain `for persona in loop: state = persona.run(state, llm_client)` loop, with no async orchestration, threading, or DAG resolution.
  - **Target Files:** `src/loop_engine/core/engine.py`
  - **Acceptance Criteria:** `tests/core/test_engine.py` verifies a loop of three stub `BasePersona` implementations executes in list order, and the final returned `State` reflects all three stubs' modifications.

- **Task 2: Post-Stage State Validation**
  - **Description:** After each persona's `run()` call inside `run_loop`, revalidate the returned object via `State.model_validate(state.model_dump())`, raising `InvalidStateTransitionError` (defined in `core/engine.py`) if validation fails. The error message must name the offending persona's class.
  - **Target Files:** `src/loop_engine/core/engine.py`
  - **Acceptance Criteria:** `tests/core/test_engine.py` verifies `InvalidStateTransitionError` is raised when a stub persona returns a `State` with a corrupted `stage_history` entry, and that the error message contains the stub persona's class name.

- **Task 3: Per-Stage Snapshot Persistence**
  - **Description:** After each persona's `run()` call and successful revalidation, call `write_state_snapshot` (from `tools/state_io/writer.py`) from within `run_loop`, passing the persona's list index and class name as `stage_index`/`stage_name`.
  - **Target Files:** `src/loop_engine/core/engine.py`
  - **Acceptance Criteria:** `tests/core/test_engine.py` verifies, using a temp-directory fixture, that a snapshot file exists after each of the three stub personas in a three-stage loop.

- **Task 4 (Security): Budget Check Before Each Stage**
  - **Description:** Before invoking each persona's `run()`, `run_loop` queries `llm_client`'s current cumulative usage against its configured `budget_tokens` and raises `BudgetExceededError` without invoking the persona if usage has already reached or exceeded budget, persisting the last valid `State` snapshot before raising.
  - **Target Files:** `src/loop_engine/core/engine.py`
  - **Acceptance Criteria:** `tests/core/test_engine.py` verifies that when a stub `LLMClient` reports usage already at budget, the second stage in a two-stage loop is never invoked, and `BudgetExceededError` propagates out of `run_loop`.

---
