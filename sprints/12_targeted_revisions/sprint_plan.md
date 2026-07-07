### FILEPATH: /sprints/12_targeted_revisions/sprint_plan.md

**Sprint Goal:** Gate revisions stop regenerating whole documents: personas revise via a multi-turn call (previous artifact as an assistant turn, findings as the final user turn) that returns only corrected sections, merged into the prior artifact.

**Dependencies:** Sprint 11 (prompt_caching).

**Security Considerations:** The multi-turn entry point must reject a trailing assistant turn client-side — an assistant-final message is a prefill and returns a 400 on claude-sonnet-5; this is a new validated I/O boundary and needs an invalid-input rejection test per the Global Definition of Done. The section-merge helper is a pure function with no file I/O.

**Risks & Blockers:** The engine's "identical findings twice ⇒ escalate" comparison operates on gate findings, not artifacts — merging must not launder identical findings into superficially different artifacts (it does not: the gate re-evaluates the merged artifact; verify with existing engine tests). Corrections naming unknown sections are rejected and logged, keeping merges deterministic.

**Tasks:**

- **Task 1: Message-list entry point in LLMClient**
  - **Description:** Refactor `call`'s body into a private `_execute`; add `call_messages(messages, *, model, max_tokens, system_blocks=None)` sharing pre-flight, cost accounting, cache-usage recording, and truncation handling. Raise a dedicated error if the final message role is not `user`.
  - **Target Files:** `src/loop_engine/tools/llm/client.py`, `tests/tools/test_llm_client.py`
  - **Acceptance Criteria:** Tests verify messages pass through verbatim, a trailing-assistant list is rejected without a transport call, budget/truncation behavior matches `call`, and the legacy `call(prompt, model=...)` signature still works.

- **Task 2: Section-merge helper**
  - **Description:** Create `src/loop_engine/personas/sections.py`: split a markdown artifact at `##`-level headers; replace sections whose headers appear in a correction response; leave all others byte-identical; reject-and-log corrections referencing unknown sections. Pure function, no I/O.
  - **Target Files:** `src/loop_engine/personas/sections.py`, `tests/personas/test_sections.py`
  - **Acceptance Criteria:** New tests cover replace-one, replace-many, unknown-section rejection, idempotence, and section-order preservation.

- **Task 3: Revision paths in Architect, Sprint Breakdown, and Coder**
  - **Description:** In each persona's `run`, when `findings` is present **and** its own produced artifact already exists in state: call `call_messages` with `[user: the attempt-1 user message, assistant: previous artifact, user: findings + "Return ONLY the corrected sections, reproducing their ## headers verbatim."]`, the same byte-identical `system_blocks` as attempt 1, then merge via `sections.merge`. Coder applies this per sprint (previous = that sprint's report). Full regeneration remains the fallback when no prior artifact exists. Add a short revision-protocol paragraph to `prompts/02/03/04_*.md` and the embedded templates together; any new header must appear in both.
  - **Target Files:** `src/loop_engine/personas/architecture/persona.py`, `src/loop_engine/personas/agile_sprint_breakdown/persona.py`, `src/loop_engine/personas/coder_iac/persona.py`, `prompts/02_architecture_definition_prompt.md`, `prompts/03_agile_sprint_breakdown_prompt.md`, `prompts/04_developer_iac_implementation_prompt.md`, `tests/personas/test_architecture.py`, `tests/personas/test_agile_sprint_breakdown.py`, `tests/personas/test_coder_iac.py`
  - **Acceptance Criteria:** Persona tests verify the 3-turn revision shape and that a finding about one section leaves other sections byte-identical after merge. `tests/personas/test_prompt_parity.py` passes. Existing engine tests (including identical-findings escalation) pass unchanged. A new integration-style test verifies one gate-REVISE round on Architecture makes exactly 2 architecture transport calls with a 3-turn second request.

- **Task 4 (Security): Revision documentation**
  - **Description:** Update the REVISE description in `README.md` ("findings fed back against the prior artifact; only flagged sections regenerate"), `CLAUDE.md` engine/persona bullets, and `docs/architecture_definition.md` §7 (revision passes are incremental).
  - **Target Files:** `README.md`, `CLAUDE.md`, `docs/architecture_definition.md`
  - **Acceptance Criteria:** Docs updated; `hatch run test`, `hatch run lint`, `hatch run format` pass.

---
