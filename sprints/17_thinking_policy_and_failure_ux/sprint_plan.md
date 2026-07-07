### FILEPATH: /sprints/17_thinking_policy_and_failure_ux/sprint_plan.md

**Sprint Goal:** Stop paying for invisible adaptive thinking on mechanical JSON calls (the likely real cause of the terse-call truncations at 2048/4096), keep it deliberately on document-emitting calls, and replace the raw traceback a failed stage dumps on the operator with a clean CLI report and dedicated exit code.

**Dependencies:** None strictly; Sprint 15 (streaming_transport) recommended first so the whole transport story lands together.

**Security Considerations:** No new modules, imports, or dependencies — `thinking` flows through the client's existing `**kwargs` pass-through into the transport call, so `tools/llm/client.py`'s signature and boundaries are untouched (`tests/tools/test_keyring_boundary.py`, `tests/tools/test_state_io_boundary.py`, `tests/tools/test_llm_client_tls.py` all pass unchanged). The CLI error handler must echo the failure reason and snapshot path only — never request/response bodies, which could carry spec content into CI logs.

**Risks & Blockers:** Background for the coder: on `claude-sonnet-5`, a request that omits `thinking` runs **adaptive thinking by default**; thinking tokens count against `max_tokens` and bill at the output rate. For terse JSON-mapping calls that means a 2048-token cap can be consumed by reasoning before the JSON payload finishes — raising ceilings treats the symptom, disabling thinking on those calls treats the cause. Do NOT disable thinking on the three document-emitting `MAX_TOKENS = 64000` calls (Architecture/Sprint-Breakdown/Coder full-document generation) — reasoning quality is wanted there and the 64000 ceiling exists to absorb it. Prompt-parity risk: `tests/personas/test_prompt_parity.py` guards prompt text against drift — this sprint changes call kwargs and comments only, never `PROMPT_TEMPLATE` content. The CLI currently maps only COMPLETED/AWAITING_ISSUE/BUDGET_EXCEEDED to exit codes 0/2/3; failed stages escape as exceptions and rich tracebacks (observed three times in real runs) — exit code 4 becomes the failed-stage code.

**Tasks:**

- **Task 1: Disable thinking on terse JSON calls**
  - **Description:** Pass `thinking={"type": "disabled"}` on every mechanical JSON-mapping call: in `src/loop_engine/personas/pm/persona.py` the extraction call, the critic follow-up call, the `resolve_questions` call, and the `fold_answers` call; in `src/loop_engine/personas/architecture/persona.py` the `resolve_questions` call. Add one rationale comment beside each file's `*_MAX_TOKENS` constants (adaptive thinking is Sonnet 5's default, bills against `max_tokens` at the output rate, and is waste on mechanical JSON mapping — the terse-call truncations came from exactly this). The client needs no changes: kwargs already flow through `call()`/`call_messages()` to the transport.
  - **Target Files:** `src/loop_engine/personas/pm/persona.py`, `src/loop_engine/personas/architecture/persona.py`, `tests/personas/test_pm.py`, `tests/personas/test_architecture.py`
  - **Acceptance Criteria:** Persona tests assert `thinking={"type": "disabled"}` in `mock_llm_client.call.call_args.kwargs` for each of the five call sites. `tests/personas/test_prompt_parity.py` passes unchanged (no prompt text touched).

- **Task 2: Document calls keep adaptive thinking deliberately**
  - **Description:** At each document-emitting `MAX_TOKENS = 64000` constant (`src/loop_engine/personas/architecture/persona.py`, `src/loop_engine/personas/agile_sprint_breakdown/persona.py`, `src/loop_engine/personas/coder_iac/persona.py`), replace the accreted "8192 then 16000 proved insufficient" comment history with the settled rationale: adaptive thinking stays enabled for document generation (quality), thinking spend counts against this ceiling, and 64000 is sized to absorb both; cost is governed by the run budget, not this constant.
  - **Target Files:** `src/loop_engine/personas/architecture/persona.py`, `src/loop_engine/personas/agile_sprint_breakdown/persona.py`, `src/loop_engine/personas/coder_iac/persona.py`
  - **Acceptance Criteria:** No `thinking` kwarg on the three document-generation calls (adaptive default preserved); comments updated; `hatch run test` green.

- **Task 3: Clean CLI failure reporting with exit code 4**
  - **Description:** In `src/loop_engine/cli.py`: wrap the `run_loop(...)` invocations in `run` and `resume` with `try/except (InvalidStateTransitionError, MissingArtifactError)` (import both from `loop_engine.core.engine`); on catch, `typer.echo` a concise report — run id, the failure reason (the exception message already names the stage), and the snapshot directory `state/<run_id>/` with a pointer to `--resume-from` — then `raise typer.Exit(code=4)`. Add `RunStatus.FAILED_STAGE: 4` to `_EXIT_CODES` so a future non-raising failed-stage path agrees. Document exit code 4 alongside 0/2/3.
  - **Target Files:** `src/loop_engine/cli.py`, `tests/test_cli.py`
  - **Acceptance Criteria:** A CLI test drives `run` with a mocked transport whose response truncates (`stop_reason="max_tokens"`) and asserts: exit code 4, output names the failed stage and the snapshot directory, and no traceback text (e.g. `"Traceback"` absent from output). Existing exit-code tests for 0/2/3 pass unchanged.

- **Task 4: Documentation sweep**
  - **Description:** Update `README.md`'s exit-code documentation (0 completed, 2 awaiting issue, 3 budget exceeded, 4 failed stage) and `CLAUDE.md` (exit-code line under Commands; add the thinking policy to the personas/client bullets: terse JSON calls run with thinking disabled, document calls keep Sonnet 5's adaptive default).
  - **Target Files:** `README.md`, `CLAUDE.md`
  - **Acceptance Criteria:** Exit code 4 documented everywhere 0/2/3 are; thinking policy stated once in CLAUDE.md. `hatch run test`, `hatch run lint`, `hatch run format` pass.

---
