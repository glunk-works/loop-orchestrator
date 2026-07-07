### FILEPATH: /sprints/11_prompt_caching/sprint_plan.md

**Sprint Goal:** Cut repeated input cost ~90% by moving each persona's stable prefix (prompt template + consumed artifact) into cached system blocks, and tighten the pre-flight budget estimate with the token-counting endpoint when near the cap.

**Dependencies:** Sprint 10 (usd_budget_and_pricing).

**Security Considerations:** Caching sends the same bytes to the same Anthropic endpoint — no new egress; note in `docs/architecture_definition.md` §1 that the client may additionally call the token-count endpoint (same host, outbound HTTPS only). System blocks must be built from state fields only — never timestamps, attempt counters, or findings — both to keep the cache prefix byte-identical and to keep volatile user data out of the cached span.

**Risks & Blockers:** Sonnet 5's minimum cacheable prefix is ~2048 tokens: small artifacts silently don't cache (usage fields come back 0) and nothing may branch on cache hits. The PM persona is deliberately left unrestructured (already targeted-revision; prompt typically below the minimum). `tests/personas/test_prompt_parity.py` requires every `#`-header line in `prompts/0{2,3,4}_*.md` to appear in the matching `PROMPT_TEMPLATE` — body rewording is safe, header changes are not. Integration tests assert exact transport call counts, so `count_tokens` must only fire near the budget cap.

**Tasks:**

- **Task 1: system_blocks support in LLMClient**
  - **Description:** Extend `LLMClient.call` with `system_blocks: list[str] | None = None`. When provided, pass `system=[{"type": "text", "text": ...}, ...]` to `messages.create` with `cache_control: {"type": "ephemeral"}` on the **last** block only; when omitted, send no `system` kwarg. Include system-block length in the pre-flight size estimate.
  - **Target Files:** `src/loop_engine/tools/llm/client.py`, `tests/tools/test_llm_client.py`
  - **Acceptance Criteria:** Tests verify the `system` kwarg shape (cache_control on last block only), absence of the kwarg when `system_blocks` is omitted, and that a response with zero/absent cache-usage fields behaves identically to one with them (cache-no-op safety).

- **Task 2: Personas restructured onto cached prefixes**
  - **Description:** Architecture, Sprint Breakdown, and Coder personas call with `system_blocks=[PROMPT_TEMPLATE, <consumed artifact>]` and put volatile content (sprint plan, findings, a brief "Begin" instruction) in the user message. The Coder's system blocks must be byte-identical across all sprint invocations in its inner loop. Reword the "included at the end of this prompt" sentences in `prompts/02/03/04_*.md` **and** the embedded templates together to "provided in the system context", changing no header lines. PM persona unchanged.
  - **Target Files:** `src/loop_engine/personas/architecture/persona.py`, `src/loop_engine/personas/agile_sprint_breakdown/persona.py`, `src/loop_engine/personas/coder_iac/persona.py`, `prompts/02_architecture_definition_prompt.md`, `prompts/03_agile_sprint_breakdown_prompt.md`, `prompts/04_developer_iac_implementation_prompt.md`, `tests/personas/test_architecture.py`, `tests/personas/test_agile_sprint_breakdown.py`, `tests/personas/test_coder_iac.py`
  - **Acceptance Criteria:** Persona tests assert the template and consumed artifact appear in `call_args.kwargs["system_blocks"]` and findings/sprint content in the user prompt (`args[0]`). `tests/personas/test_prompt_parity.py` passes unchanged. Integration call counts stay 2 and 4.

- **Task 3: count_tokens pre-flight refinement near the cap**
  - **Description:** In `LLMClient`, when the heuristic estimate reaches ≥50% of `remaining()` (module constant), call `self._anthropic.messages.count_tokens(...)` with the same model/messages/system shape and use its `input_tokens` for the estimate; any exception falls back to the heuristic and the call proceeds (pre-flight must never become a new hard-failure mode).
  - **Target Files:** `src/loop_engine/tools/llm/client.py`, `tests/tools/test_llm_client.py`
  - **Acceptance Criteria:** Tests verify: far from budget, `count_tokens` is never invoked; near budget, it is invoked and its integer used; when it raises, the heuristic is used and the call succeeds. Integration tests remain at exact call counts (their budgets stay outside the guard band).

- **Task 4 (Security): Caching and trust-boundary documentation**
  - **Description:** Update `README.md` client bullet and security bullets (pre-flight wording: "heuristic, refined by the token-counting endpoint near the cap"), `docs/architecture_definition.md` §1 (token-count endpoint note), §2 and §7 (cached system prefix, cache economics), and `CLAUDE.md` client bullet.
  - **Target Files:** `README.md`, `docs/architecture_definition.md`, `CLAUDE.md`
  - **Acceptance Criteria:** Docs describe caching and the count_tokens refinement; `hatch run test`, `hatch run lint`, `hatch run format` pass.

---
