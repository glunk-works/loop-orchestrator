### FILEPATH: /sprints/13_agentic_coder_tooling/sprint_plan.md

**Sprint Goal:** Give the LLM client a bounded tool-use loop and build the Coder's tool set: path-validated read tools plus a sandbox-justified `run_tests` subprocess tool.

**Dependencies:** Sprint 11 (prompt_caching). Sprint 12 recommended but not required.

**Security Considerations:** This sprint introduces the system's second subprocess surface (after `issue_io`'s `gh`) and its first execution of model-influenced inputs. Mitigations: `run_tests` executes only `[sys.executable, "-m", "pytest", <path>]` with `shell` never used, a hard timeout, output size cap, and the target path validated against the run's artifact tree; the ruff `S603` suppression carries an inline justification citing the sandboxed devcontainer (Global DoD forbids unexplained `# noqa`). Read tools use `Path.read_text()`/`Path.iterdir()` only — bare `open()` anywhere outside `tools/state_io/` fails the AST boundary test. Path validation is reused from `tools/state_io/writer.py` by exporting its traversal check as a public helper, not duplicated. No module here imports `keyring`. `pytest` becomes an exact-pinned runtime dependency: run `hatch run audit` and `hatch run sbom`, and confirm the prod Dockerfile stage includes it.

**Risks & Blockers:** Tool-loop iterations re-send conversation history each round — the cached system prefix must stay on every iteration or input cost multiplies. Executor exceptions must surface to the model as `is_error: true` tool results, not crash the loop. An iteration cap breach is an honest stage failure (like truncation), not a silent stop.

**Tasks:**

- **Task 1: Bounded tool loop in LLMClient**
  - **Description:** Add `run_tool_loop(messages, *, model, max_tokens, tools, execute, system_blocks=None, max_iterations=<cap>) -> LLMResponse` to `src/loop_engine/tools/llm/client.py`: call `messages.create(..., tools=tools)`; while `stop_reason == "tool_use"`, run `execute(name, input)` for each tool_use block, append the assistant content and **all** tool_result blocks in **one** user message, and iterate. Per-iteration budget pre-flight and cost debit; `BudgetExceededError` propagates mid-loop; `max_tokens` stop mid-loop raises `TruncatedResponseError`; exceeding `max_iterations` raises a dedicated error; executor exceptions become `is_error: true` tool results. `cache_control` stays on the system prefix each iteration.
  - **Target Files:** `src/loop_engine/tools/llm/client.py`, `tests/tools/test_llm_client.py`
  - **Acceptance Criteria:** Tests verify: loop ends on `end_turn`; tool_result `tool_use_id`s match and arrive in a single user message; `BudgetExceededError` on iteration k leaves exactly k−1 transport calls; the iteration cap raises; an executor exception produces an `is_error` tool result and the loop continues.

- **Task 2: Read-only coder tools**
  - **Description:** Create `src/loop_engine/tools/coder_tools/` with `read_file`, `list_files`, and `grep` (pure-Python line match over `read_text`, no subprocess), each validating its path against the run's artifact tree via the traversal helper exported from `tools/state_io/writer.py`. Define the three tool JSON schemas in the same module.
  - **Target Files:** `src/loop_engine/tools/coder_tools/__init__.py`, `src/loop_engine/tools/state_io/writer.py` (export the validation helper), `tests/tools/test_coder_tools.py`
  - **Acceptance Criteria:** New tests verify traversal rejection (`..`, absolute paths, symlink escape) for each tool plus happy paths. `tests/tools/test_state_io_boundary.py` and `tests/tools/test_keyring_boundary.py` pass.

- **Task 3 (Security): run_tests tool**
  - **Description:** Add `run_tests` to `tools/coder_tools/`: `subprocess.run([sys.executable, "-m", "pytest", <validated path>], capture_output=True, timeout=<limit>)`, output truncated to a size cap before being returned as a tool result. Inline-justified `# noqa: S603` citing the devcontainer sandbox. Add `pytest` (exact-pinned) to `[project.dependencies]` in `pyproject.toml`; regenerate `sbom.json` (`hatch run sbom`) and run `hatch run audit`; verify the prod Dockerfile stage ships pytest.
  - **Target Files:** `src/loop_engine/tools/coder_tools/run_tests.py`, `pyproject.toml`, `sbom.json`, `Dockerfile`, `tests/tools/test_coder_tools.py`
  - **Acceptance Criteria:** Tests run a trivial passing and failing test tree under `tmp_path` and assert exit codes/output capture; timeout is enforced; path validation rejects escapes (DoD invalid-input test); oversized pytest output is truncated. `hatch run audit` reports no critical/high CVE for the pinned pytest.

---
