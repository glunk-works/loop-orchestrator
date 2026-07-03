### FILEPATH: /sprints/03_llm_client_and_secrets/sprint_plan.md

**Sprint Goal:** Implement the sole LLM client module, retrieving credentials exclusively from the OS keyring and enforcing a hard per-run token budget cap.

**Dependencies:** Sprint 02 (state_and_persona_contract)

**Security Considerations:** This sprint owns the only credential-handling code path in the system. The threat surface is credential leakage via logging, exception messages, or accidental serialization into `State`. Mitigations: the raw key value is never logged; no exception message ever includes the key; a static AST test asserts `keyring` is imported nowhere outside `tools/llm/client.py`.

**Risks & Blockers:** Exercising the retrieval path requires a configured OS keyring backend (Windows Credential Manager / macOS Keychain / Secret Service). CI must mock the `keyring` module rather than depend on a live keyring backend being present in the runner.

**Tasks:**

- **Task 1: LLM Client with Keyring-Only Credential Retrieval**
  - **Description:** Implement `LLMClient` in `src/loop_engine/tools/llm/client.py` with a constructor that retrieves the API key via `keyring.get_password("loop-engine", "anthropic_api_key")` exactly once, caching it in a private instance attribute for the process lifetime. Raise a dedicated `MissingCredentialError(Exception)` if `keyring.get_password` returns `None`.
  - **Target Files:** `src/loop_engine/tools/llm/client.py`
  - **Acceptance Criteria:** `tests/tools/test_llm_client.py` verifies `MissingCredentialError` is raised when `keyring.get_password` is mocked to return `None`, and that `keyring.get_password` is called exactly once across two separate method calls on the same client instance.

- **Task 2 (Security): Sole Keyring Importer Enforcement**
  - **Description:** Write a static AST-based test in `tests/tools/test_keyring_boundary.py` scanning every `.py` file under `src/loop_engine/` and asserting `keyring` is imported only in `src/loop_engine/tools/llm/client.py`.
  - **Target Files:** `tests/tools/test_keyring_boundary.py`
  - **Acceptance Criteria:** The test passes against the current tree.

- **Task 3: Per-Run Budget Tracking**
  - **Description:** Add a `budget_tokens: int` constructor parameter and a private cumulative `_tokens_used: int` counter to `LLMClient`. Implement `call(self, prompt: str, **kwargs) -> LLMResponse`, which checks, before dispatching the underlying API call, whether the request's estimated token count plus `_tokens_used` would exceed `budget_tokens`.
  - **Target Files:** `src/loop_engine/tools/llm/client.py`
  - **Acceptance Criteria:** `tests/tools/test_llm_client.py` verifies `call()` increments `_tokens_used` by the actual token count returned in a mocked API response.

- **Task 4: Hard Abort on Budget Breach**
  - **Description:** Define `BudgetExceededError(Exception)` in `src/loop_engine/tools/llm/client.py`. Raise it from `call()` before making the underlying API request whenever the Task 3 pre-flight check would breach `budget_tokens` — the underlying API transport call must not execute in this case.
  - **Target Files:** `src/loop_engine/tools/llm/client.py`
  - **Acceptance Criteria:** `tests/tools/test_llm_client.py` verifies `BudgetExceededError` is raised and that the mocked underlying transport method is never invoked when the pre-flight check fails.

- **Task 5: TLS Enforcement Regression Test**
  - **Description:** Write `tests/tools/test_llm_client_tls.py` asserting the underlying HTTP client/SDK instance constructed inside `LLMClient` has certificate verification enabled by default, and that no code path in `client.py` sets it to disabled.
  - **Target Files:** `tests/tools/test_llm_client_tls.py`
  - **Acceptance Criteria:** The test passes against the current `client.py` implementation.

---
