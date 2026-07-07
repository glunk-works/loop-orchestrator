### FILEPATH: /sprints/10_usd_budget_and_pricing/sprint_plan.md

**Sprint Goal:** Replace the raw-token budget with a USD budget priced from a per-model rate table; make `StageRecord.cost_usd` real; surface real dollars and cache-token columns in `cost-summary`.

**Dependencies:** None (Sprint 09 recommended first but not required).

**Security Considerations:** The pricing module must not import `keyring` (AST test `tests/tools/test_keyring_boundary.py` allows it only in `tools/llm/client.py`) and must not perform file I/O (`tests/tools/test_state_io_boundary.py` flags bare `open`). An unknown model must raise, never silently price at $0 — silent zero-pricing would disable the budget cap. Do not alter how `anthropic.Anthropic(api_key=...)` is constructed: `tests/tools/test_llm_client_tls.py` asserts on the SDK's internal transport.

**Risks & Blockers:** Every existing test mock builds `usage` as `SimpleNamespace(input_tokens=..., output_tokens=...)` with no cache fields — the client must read cache usage with `getattr(response.usage, "cache_creation_input_tokens", 0) or 0` (same for `cache_read_input_tokens`) or all persona and integration tests break. The pre-flight estimate prices `max_tokens` at the output rate, giving a per-call floor of roughly $0.13 at `max_tokens=8192` — integration-test budget literals must clear this floor while still exhausting after the mocked calls. Sonnet 5 has introductory pricing ($2/$10 per MTok) through 2026-08-31; the table encodes standard rates ($3/$15) with a comment noting recorded cost will slightly overstate real spend until then.

**Tasks:**

- **Task 1: Price table module**
  - **Description:** Create `src/loop_engine/tools/llm/pricing.py`: a Pydantic `ModelRates` model (`input_usd_per_mtok`, `output_usd_per_mtok`, `cache_write_usd_per_mtok`, `cache_read_usd_per_mtok`, all `ge=0`, `extra="forbid"`); a `RATES: dict[str, ModelRates]` table with `"claude-sonnet-5": ModelRates(3.00, 15.00, 3.75, 0.30)`; `cost_usd(model, input_tokens, output_tokens, cache_creation_tokens=0, cache_read_tokens=0) -> float`; and `estimate_cost_usd(model, estimated_input_tokens, max_tokens) -> float` pricing `max_tokens` at the output rate. Unknown model raises a dedicated error.
  - **Target Files:** `src/loop_engine/tools/llm/pricing.py`, `tests/tools/test_pricing.py`
  - **Acceptance Criteria:** New tests verify the arithmetic including cache write/read components, that an unknown model raises, and that `ModelRates` rejects negative rates and extra fields. `tests/tools/test_keyring_boundary.py` and `tests/tools/test_state_io_boundary.py` still pass.

- **Task 2: LLMClient USD budget and cost accounting**
  - **Description:** In `src/loop_engine/tools/llm/client.py`: rename the constructor parameter to `budget_usd: float`; `remaining() -> float` returns dollars; add cumulative properties `cost_used`, `cache_creation_tokens_used`, `cache_read_tokens_used` alongside the existing `tokens_used` (tokens_used counts all classes: input + output + cache creation + cache read). `call()` debits `pricing.cost_usd(...)` per call using the four usage components (cache fields read via `getattr(..., 0) or 0`), and the pre-flight check compares `pricing.estimate_cost_usd(model, len(prompt)//4, max_tokens)` to `remaining()`. `LLMResponse` gains `cost_usd: float`, `cache_creation_input_tokens: int = 0`, `cache_read_input_tokens: int = 0`. The `anthropic.Anthropic(api_key=...)` construction line is unchanged.
  - **Target Files:** `src/loop_engine/tools/llm/client.py`, `tests/tools/test_llm_client.py`
  - **Acceptance Criteria:** Updated tests verify: cost accumulation matches the rate table; `BudgetExceededError` raised pre-flight with the transport never invoked (tiny USD budget); truncation still raises `TruncatedResponseError` with tokens and cost still accounted; a response lacking cache fields is treated as zero; a response carrying cache fields has them recorded on `LLMResponse` and the cumulative counters. `tests/tools/test_llm_client_tls.py` passes unchanged.

- **Task 3: Engine records real cost and cache tokens**
  - **Description:** In `src/loop_engine/core/state.py`, add `cache_creation_input_tokens: int = 0` and `cache_read_input_tokens: int = 0` (`ge=0`) to `StageRecord` (defaulted — no schema bump). In `src/loop_engine/core/engine.py`, capture `cost_before`/cache counters alongside `tokens_before`, pass the deltas into `_record_stage`, populate `cost_usd` with the real delta, and delete the "cost_usd is a placeholder" comment. Extend `log_stage_completion` in `tools/logging_config.py` with the cache counts.
  - **Target Files:** `src/loop_engine/core/state.py`, `src/loop_engine/core/engine.py`, `src/loop_engine/tools/logging_config.py`, `tests/core/test_engine.py`, `tests/core/test_state.py`
  - **Acceptance Criteria:** The `_stub_llm_client` in `tests/core/test_engine.py` gains `cost_used`/cache counters and a USD `remaining()`; a test asserts `StageRecord.cost_usd` equals the client's cost delta. `tests/core/test_state.py` verifies an old StageRecord payload without cache fields validates and negative cache counts are rejected.

- **Task 4: CLI budget flag and cost-summary columns**
  - **Description:** In `src/loop_engine/cli.py`: `--budget` becomes a float USD cap, default `5.00`, help text "Hard cap on cumulative LLM spend for the run, in USD"; `run` and `resume` construct `LLMClient(budget_usd=budget)`; `cost-summary` shows real dollars and adds `Cache W` / `Cache R` columns with an extended totals row. Exit code 3 semantics unchanged.
  - **Target Files:** `src/loop_engine/cli.py`, `tests/test_cli.py`, `tests/integration/test_budget_abort.py`, `tests/integration/test_no_credential_leakage.py`, `tests/test_public_api.py`
  - **Acceptance Criteria:** `test_budget_abort.py` passes with a USD budget literal that clears each call's pre-flight estimate but is exhausted after the two mocked responses — transport call count stays exactly 2 and exit code stays 3. `test_no_credential_leakage.py` passes with only its budget literal changed. `test_cli.py` cost-summary test verifies the new columns.

- **Task 5 (Security): Budget documentation sweep**
  - **Description:** Update `README.md` (--budget table row, all `--budget 100000` examples including the docker-run sections, cost-summary section, library-usage snippet to `LLMClient(budget_usd=...)` — also fix its stale `schema_version=1`), `docs/architecture_definition.md` (binding decision #9 → per-run USD cap priced from a per-model rate table; §2 CLI line; §7 FinOps bullets rewritten for USD cap, rate table, cache economics; §8 LLMClient directive), and `CLAUDE.md` (command examples, client/engine bullets).
  - **Target Files:** `README.md`, `docs/architecture_definition.md`, `CLAUDE.md`
  - **Acceptance Criteria:** No document still describes the budget in raw tokens; `hatch run test`, `hatch run lint`, `hatch run format` pass. No dependency changed, so `sbom.json` is untouched.

---
