### FILEPATH: /sprints/08_observability_and_hardening/sprint_plan.md

**Sprint Goal:** Deliver end-to-end visibility into per-stage cost usage and prove the complete system's security and budget controls under adversarial and failure conditions.

**Dependencies:** Sprint 05 (sequential_execution_engine), Sprint 06 (default_persona_implementations), Sprint 07 (default_loop_and_cli)

**Security Considerations:** This sprint is the final verification gate before v1 completion. The threat surface is any gap between the individual unit-level security tests from prior sprints and actual end-to-end behavior. An integration test suite exercises the full default loop with a mocked `LLMClient` and asserts no plaintext credential appears in any file under `state/` after a complete run.

**Risks & Blockers:** None identified.

**Tasks:**

- **Task 1: Structured Cost Logging**
  - **Description:** Implement a `logging` configuration in `src/loop_engine/tools/logging_config.py` that emits a structured JSON log line after each persona's `run()` call in `engine.py`, containing `stage_name`, `tokens_used`, and `cost_usd` read from the `State.stage_history` entry just appended.
  - **Target Files:** `src/loop_engine/tools/logging_config.py`, `src/loop_engine/core/engine.py`
  - **Acceptance Criteria:** `tests/tools/test_logging_config.py` captures log output during a stub three-stage loop run and verifies three JSON-parseable log lines, each containing the three required keys.

- **Task 2: End-to-End Budget Abort Integration Test**
  - **Description:** Write `tests/integration/test_budget_abort.py` running the full `DEFAULT_LOOP` with a mocked `LLMClient` configured with a `budget_tokens` value exceeded partway through the third stage, and asserting the run aborts with `BudgetExceededError`, exits with a non-zero CLI exit code (via Typer's `CliRunner`), and that a valid `State` snapshot exists on disk for the two completed stages.
  - **Target Files:** `tests/integration/test_budget_abort.py`
  - **Acceptance Criteria:** The test passes and demonstrates a non-zero process exit code from the CLI invocation.

- **Task 3 (Security): End-to-End Credential Non-Leakage Test**
  - **Description:** Write `tests/integration/test_no_credential_leakage.py` running the full `DEFAULT_LOOP` with a mocked `LLMClient` seeded with a known fake API key value, then scanning every file written under a temp `state/` directory and asserting the fake key string does not appear in any of them.
  - **Target Files:** `tests/integration/test_no_credential_leakage.py`
  - **Acceptance Criteria:** The test passes against the full default loop.

- **Task 4: Cost Visibility Summary Command**
  - **Description:** Add a `loop-engine cost-summary --run-id <id>` Typer subcommand in `cli.py` that reads all `state/<run_id>/*.json` snapshots and prints a per-stage table of `tokens_used` and `cost_usd`, plus a cumulative total row.
  - **Target Files:** `src/loop_engine/cli.py`
  - **Acceptance Criteria:** `tests/test_cli.py` verifies `cost-summary` run against a fixture `state/<run_id>/` directory of three snapshot files prints three per-stage rows and one total row with a correctly summed value.

- **Task 5: Full Supply Chain Gate Verification**
  - **Description:** Run the complete Global Definition of Done command sequence (`hatch run test`, `hatch run lint`, `hatch run format --check .`, `gitleaks detect --source . --config .gitleaks.toml`, `hatch run sbom`) against the fully assembled `src/loop_engine/` tree, resolving any violation surfaced by this first full-tree run.
  - **Target Files:** none — this is a verification task; it may touch any file needed to resolve a violation surfaced during the run.
  - **Acceptance Criteria:** All five commands exit zero in a single sequential run, recorded in the CI run for the final commit of this sprint.

---
