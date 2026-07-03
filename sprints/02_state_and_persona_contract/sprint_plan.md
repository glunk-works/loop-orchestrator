### FILEPATH: /sprints/02_state_and_persona_contract/sprint_plan.md

**Sprint Goal:** Define the versioned Pydantic `State` model and the `BasePersona` abstract contract that every persona and the engine depend on.

**Dependencies:** Sprint 01 (ci_cd_foundation)

**Security Considerations:** The `State` model is the sole data structure passed between trust-boundary-crossing persona stages. It must have no field capable of holding a raw credential. This is enforced by a dedicated negative-path test and by the model's `extra="forbid"` configuration, which rejects any field a compromised or buggy persona attempts to smuggle through.

**Risks & Blockers:** None identified.

**Tasks:**

- **Task 1: State Model Definition**
  - **Description:** Define a Pydantic v2 `State` model in `src/loop_engine/core/state.py` with fields `schema_version: int`, `run_id: str`, `stage_history: list[StageRecord]`, and `artifacts: dict[str, str]` (artifact name to file path or inline content). Define a nested `StageRecord` model with fields `stage_name: str`, `tokens_used: int`, `cost_usd: float`, and `completed_at: str` (ISO 8601 timestamp). Configure both models with `model_config = ConfigDict(extra="forbid")`.
  - **Target Files:** `src/loop_engine/core/state.py`
  - **Acceptance Criteria:** `tests/core/test_state.py` verifies `State.model_validate({...})` round-trips through `model_dump_json()` and `model_validate_json()` without field loss for a representative fixture.

- **Task 2 (Security): Reject Invalid and Extra-Field State**
  - **Description:** Write `tests/core/test_state.py` assertions that `State.model_validate()` raises `pydantic.ValidationError` on: a payload missing `schema_version`; a `stage_history` entry with a negative `tokens_used`; and a payload containing one unrecognized top-level field.
  - **Target Files:** `tests/core/test_state.py`
  - **Acceptance Criteria:** All three negative-path assertions pass against the `State` model defined in Task 1.

- **Task 3: BasePersona Abstract Contract**
  - **Description:** Define `BasePersona` as an `abc.ABC` in `src/loop_engine/personas/base.py` with a single abstract method `run(self, state: State, llm_client: "LLMClient") -> State`. Import `State` from `loop_engine.core.state` and reference `LLMClient` only via a `TYPE_CHECKING`-guarded forward import from `loop_engine.tools.llm.client` — the module imports no other persona-specific or credential-handling code.
  - **Target Files:** `src/loop_engine/personas/base.py`
  - **Acceptance Criteria:** `tests/personas/test_base.py` verifies that instantiating a subclass of `BasePersona` which does not implement `run` raises `TypeError` at instantiation.

- **Task 4: Module Boundary Test**
  - **Description:** Write a static test in `tests/core/test_boundaries.py` that parses the AST of every `.py` file under `src/loop_engine/core/` and asserts none imports any module path under `src/loop_engine/personas/` other than `loop_engine.personas.base`.
  - **Target Files:** `tests/core/test_boundaries.py`
  - **Acceptance Criteria:** The test passes against the current `core/` package.

---
