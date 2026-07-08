# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

loop-engine runs a named sequence of decoupled AI "persona" stages against a single, explicit, versioned `State` object. The default loop is a **PM → Architecture → Agile Sprint Breakdown → Coder/IaC** pipeline, but it is not a one-way conveyor: every stage's output passes a content **gate** (accept / revise / escalate), questions escalate up a resolver ladder (Coder → Architect → PM → human via GitHub issue), and resolved questions route rework back down by blast radius ("task" re-runs the asker, "plan" re-enters Sprint Breakdown, "architecture" re-enters the Architect). A snapshot is persisted after every accepted stage AND on every exit path (completed / failed / budget-exceeded / awaiting-issue).

## Commands

```bash
hatch run test                        # pytest (full suite)
hatch run test tests/core/test_engine.py            # single file
hatch run test tests/core/test_engine.py::test_name  # single test
hatch run lint                        # ruff check . (incl. S/bandit and B/bugbear rule sets)
hatch run format                      # ruff format .
hatch run audit                       # pip-audit CVE scan of pinned deps (CI gate)
hatch run sbom                        # regenerate sbom.json (CycloneDX) — required whenever pyproject.toml deps change
```

Run the loop itself:

```bash
hatch run loop-engine run --input path/to/requirements.md --budget 5.00
hatch run loop-engine run --resume-from state/<run_id>/01_ArchitecturePersona.json
hatch run loop-engine resume --from-issue <N>   # after answering a paused run's GitHub issue
hatch run loop-engine cost-summary --run-id <run_id>
```

Exit codes from `run`/`resume`: 0 completed, 2 awaiting a GitHub issue answer, 3 budget exceeded.

CI (`.github/workflows/ci.yml`) runs, in order: `lint` → `format-check` → `test` → `secrets-scan` (gitleaks) → `sbom`. All must pass; see `sprints/GLOBAL_DEFINITION_OF_DONE.md` for the full merge bar (every new Pydantic-validated I/O boundary needs a test proving invalid input is rejected, no `# noqa` without an inline justification, no hardcoded secrets anywhere including `state/` snapshots, dependencies pinned to CVE-free versions).

## API key setup

The Anthropic API key is **never** a CLI flag or env var — it's retrieved exclusively from the OS keyring:

```bash
hatch run python -c "import keyring; keyring.set_password('loop-engine', 'anthropic_api_key', 'sk-ant-...')"
```

In the devcontainer this is provisioned automatically from Infisical on container start (see `.devcontainer/infisical-start.sh` / `seed-secrets.sh`); the underlying `keyring.get_password(...)` contract is unchanged either way. A double-gated env var fallback (`LOOP_ENGINE_ALLOW_ENV_CREDENTIAL=1` + `LOOP_ENGINE_CI_API_KEY`) exists solely for CI/automation contexts that can't mount an encrypted keyring file — never use it elsewhere.

## Architecture

```
 human ⇄ GitHub Issue (filed by the engine; answers as ```answers comments)
              ⇅
             PM ──────────── owns project_spec; resolver of last automated resort
              ⇅
          Architect ───────── owns architecture_definition; resolves Coder questions
              ⇅
     Sprint Breakdown ─────── re-entered on "plan"-impact rework
              ⇅
            Coder ─────────── per-sprint inner loop; escalates, never guesses

 forward path per stage: persona.run() → gate → ACCEPT (snapshot, next stage)
                                              → REVISE (bounded, findings fed back)
                                              → ESCALATE (resolver ladder → issue)
```

- **`core/state.py`** — `State`, a Pydantic v2 model (`schema_version` 3: `run_id`, `status`, `questions`, `pending_issue`, `counters`, `stage_history`, `artifacts`, `artifact_refs`) with `extra="forbid"`. `RunStatus` makes termination explicit (`completed` / `failed_stage` / `budget_exceeded` / `awaiting_issue`) — never inferred from "no exception". `migrate_state_payload()` upgrades v1/v2 snapshots on load. `artifacts` (inline bodies) and `artifact_refs` (disk pointers: `ArtifactRef` = path + sha256 digest + size) coexist during the LangGraph migration — the inline bodies are dropped once the LangGraph engine is the sole reader.
- **`core/engine.py`** — `run_loop(loop: Loop, ...)`: per stage, a bounded propose → gate → accept/revise/escalate cycle. The per-stage cycle is factored into `execute_stage()` (returning a `StageOutcome`), the shared primitive both engines drive so they stay behaviorally identical.
- **`core/graph_engine.py`** — the LangGraph engine (`run_graph_loop`): a `StateGraph` of one node per stage plus a completion node, with conditional edges that advance / re-enter (blast radius) / terminate by calling `execute_stage`. Selected at runtime by `LOOP_ENGINE_ENGINE=langgraph`; the classic `run_loop` stays the default until this path proves out. Parity is guarded by `tests/core/test_graph_engine.py`, which reruns `run_loop`'s own scenarios against the graph. Gate findings feed revision attempts against the prior artifact — the persona sends it as an assistant turn, gets back only corrected sections, and merges via `personas/sections.py` (identical findings twice = stop paying, escalate); escalated questions walk the stage's `resolvers` ladder; questions nobody answers become a GitHub issue and the run pauses (`AWAITING_ISSUE`). Resolved questions carry an `impact` that routes re-entry via `Loop.impact_reentry`. Hard caps (`MAX_ESCALATIONS_PER_STAGE`, `MAX_REPLANS_PER_RUN`) keep every feedback edge finite. Every exit path persists a snapshot.
- **`core/gates.py`** — `ArtifactGate`: content validation (present, JSON-shaped if declared, not question-shaped) plus `## Open Questions` extraction into `Question` objects.
- **`personas/base.py`** — `BasePersona`: abstract `run(state, llm_client, findings=None)`, `consumes`/`produces` artifact declarations (engine pre-checks inputs), and overridable `resolve_questions()` for resolver duty. Personas receive the LLM client via injection — they cannot construct their own or touch credentials directly.
- **`personas/{pm,architecture,agile_sprint_breakdown,coder_iac}/`** — the four default personas; prompts are batch-mode (assumptions + `## Open Questions`, never "ask and wait"). `PMPersona` keeps its critic revision loop (`personas/pm/critic.py`) with no-progress detection, and additionally implements `resolve_questions` (from the spec) and `fold_answers` (folds human issue answers into the spec and classifies impact). `CoderIacPersona` runs an inner agentic loop — one `run_tool_loop` per sprint block with read/execute tools (`read_file`/`list_files`/`grep`/`run_tests` from `tools/coder_tools/`) — emits full-content or SEARCH/REPLACE edit blocks that the persona applies via `write_artifact` (failures are recorded on the report for the gate), and stops at a sprint that raises questions; on findings re-entry it re-runs only the sprint(s) targeted by resolved questions (`Question.origin_detail`) or by sprint-path-prefixed gate findings, falling back to a full re-run when findings carry no attribution. Its stage gate is `core/coder_gate.py`: content checks plus a deterministic pytest run — ACCEPT is evidence-based, and pytest exit 5 (no tests) is a REVISE. Sprint plans and implementation reports are written to `sprints/` via `write_artifact`.
- **`loops/default/loop.py`** — `DEFAULT_LOOP`, a `Loop` of four `Stage`s wiring gates, the resolver ladder, and `impact_reentry`. No YAML/JSON loop-definition format — loops are just Python.
- **`tools/llm/client.py`** — `LLMClient`: retrieves the API key from `keyring` exactly once per instance, prices every call from the per-model rate table in `tools/llm/pricing.py` and enforces the per-run USD budget *before* each call (`BudgetExceededError`; heuristic estimate, refined via `count_tokens` once it reaches 50% of the remaining budget), sends caller-supplied `system_blocks` as a cached system prefix (`cache_control: ephemeral` on the last block — personas keep these byte-identical across calls and put volatile content in the user prompt), drives the Coder's bounded tool loop via `run_tool_loop` (per-iteration budget debit, executor errors surfaced as `is_error` tool results, iteration cap fails the stage honestly), and raises `TruncatedResponseError` when `stop_reason == "max_tokens"` (a truncated artifact must never propagate). **This is the only module in the codebase permitted to import `keyring`** — enforced by `tests/tools/test_keyring_boundary.py`.
- **`tools/issue_io/`** — the only module that talks to GitHub (shells out to `gh`; no token in-process). Files the escalation issue, parses the human's ```answers comment, maps numbered answers back to questions.
- **`tools/state_io/writer.py`** — the sole writer of `State` snapshots (`state/`) and produced artifacts (`docs/`, `sprints/`, `src/`). Validates `run_id`/artifact paths against path traversal before any filesystem call. Also owns the `.agent/` writers (`write_agent_scratchpad`, `append_agent_memory` — the latter enforces the append-only ledger invariant), kept separate from the model-facing `write_artifact` allow-list.
- **`tools/agent_state/`** — the `.agent/` semantic-state layer: `.agent/STATE.md` (mutable scratchpad) and `.agent/MEMORY.md` (append-only decisions/lessons ledger), parsed/rendered via deterministic anchors; all writes delegate to `state_io`.
- **`tools/artifact_store.py`** — mirrors inline artifact bodies to disk and maintains `State.artifact_refs`; `mirror_to_disk` (idempotent, called by the engine at snapshot time), plus `get_artifact`/`has_artifact` readers that new (LangGraph) code uses instead of touching `state.artifacts`.
- **`mcp_servers/coder_tools_server.py`** — the Coder's read/execute tools (`read_file`/`list_files`/`grep`/`run_tests`) as a stdio MCP server, delegating to `tools/coder_tools` (logic re-fronted, not rewritten). Run as `python -m loop_engine.mcp_servers.coder_tools_server`.
- **`tools/mcp/`** — the runtime MCP client: `MCPToolProvider` connects to stdio servers on a background event-loop thread, discovers tools via `list_tools`, and exposes `(tools, execute)` to `run_tool_loop`. Selected by `LOOP_ENGINE_TOOLS=mcp`; the Coder's `_CoderToolBackend` opens one provider per run (lazily, on first tool-loop use) and closes it in a `finally`. Default stays the in-process `CODER_TOOLS`/`_execute_tool` dispatch.
- **`tools/logging_config.py`** — structured per-stage cost logging.
- **`cli.py`** — the Typer entrypoint (`run`, `resume`, `cost-summary`). A thin wrapper; all logic lives in the library layer. Resume verifies snapshot stage names against the loop before slicing (never resumes a mismatched loop).

`tests/` mirrors `src/loop_engine/` layout, plus `tests/integration/` for cross-module tests (e.g. `test_budget_abort.py`, `test_no_credential_leakage.py`).

## Enforced module boundaries

These are checked by static tests, not just convention — don't casually violate them:

- `core/` imports no concrete persona module, only `personas/base.py`.
- `tools/state_io/` is the only module with direct file-write calls (`open`/`write_text`/`write_bytes`); everything else goes through `write_artifact`/`write_state_snapshot`.
- `tools/llm/client.py` is the only module that imports `keyring`.
- `tools/issue_io/` is by convention the only module that talks to GitHub.
- `tools/coder_tools/` is read/execute-only: paths are traversal- and symlink-validated (reusing `state_io`'s validator); its `run_tests` pytest subprocess (also used by the Coder gate) is the only subprocess surface besides `issue_io`'s `gh`. It runs model-generated code — the operating assumption is the sandboxed devcontainer.
- `mcp_servers/` re-front native tools over MCP (`coder_tools_server` = read/execute-only, delegating to `tools/coder_tools` with the same path validation and no credentials). On the `LOOP_ENGINE_TOOLS=mcp` path, tool execution runs in the server subprocess, out of the orchestrator process entirely — the boundary is moved, not relaxed. `tools/mcp` is the client side (discovery + dispatch) and imports no keyring/writes no files. The coder-tools server exposes exactly `{read_file, list_files, grep, run_tests}` (asserted by `tests/tools/test_mcp_provider.py`).
- Any change touching `State` must keep `schema_version` accurate (bump it and extend `migrate_state_payload` for breaking shape changes) and keep `extra="forbid"` intact.

## Global Conventions (portable skill repository)

This section is the engine's **global directive/skill repository**: repo-agnostic ground rules the personas load as conventions, and the block the bootstrapping/maintenance workflows inject into every managed `glunk-works` repo. Keep it self-contained — no references to files that only exist in *this* repo — so it stays valid when copied elsewhere.

### Python conventions
- **Formatting is not negotiable:** `ruff format` (line length 100) is the single source of truth; never hand-format against it. Lint with `ruff check` under rule sets `E, F, I, B, S` (pycodestyle, pyflakes, isort, bugbear, bandit). Import order is isort-managed — do not hand-order.
- **No `# noqa` without an inline justification** on the same line (`# noqa: RULE — reason`). A bare `# noqa` fails review.
- Target `python >= 3.12`. Full type hints on public functions; prefer `X | None` over `Optional[X]`, `list`/`dict` over `typing.List`/`Dict`.
- **No hardcoded secrets anywhere** — not in source, tests, or committed state/snapshot files. Credentials come from the OS keyring (or the documented double-gated CI fallback), never CLI flags or plain env vars.
- Every Pydantic-validated I/O boundary needs a test proving invalid input is rejected. Pin dependencies to CVE-free versions and regenerate the SBOM whenever deps change.

### OpenTofu / IaC conventions
- Format with `tofu fmt`; every change must pass `tofu validate` with exit 0 (this is the deterministic gate — no LLM judges IaC).
- One concern per module; expose inputs via `variables.tf`, outputs via `outputs.tf`, pin provider **and** module versions (no floating `latest`).
- Remote, locked state only — never commit `.tfstate` or `.terraform/`. No secrets in `.tf` or `.tfvars`; source them from the secret manager at plan/apply time.
- Name resources `snake_case`; tag every resource with owner + managing-repo so the factory can attribute drift.

### Commit / PR conventions
- Commits are small, self-contained, and green (`ruff check` + `ruff format --check` + the test suite all pass before committing). Sign commits.
- PRs target the integration branch (`develop`), never `main`/`master` directly, and never auto-merge — human review or remote CI validation is always required before merge.
- A change touching a versioned state schema must bump its `schema_version` and extend the migration path in the same commit.

### Definition of Done
A unit of work is done only when: formatting + lint + the full test suite pass; new validated boundaries have negative-input tests; dependencies are pinned and CVE-clean with the SBOM regenerated; no unjustified `# noqa`; and no secrets in any committed file. For managed repos the repo's own `sprints/GLOBAL_DEFINITION_OF_DONE.md` (if present) extends, never relaxes, this bar.

## Containers / devcontainer

- Root `Dockerfile` is multi-stage: `dev` (full contributor toolchain — hatch, ruff, git, gh) and `prod` (minimal runtime). Both are local-only, no registry publish.
- `.devcontainer/` targets the `dev` stage. It bind-mounts a forwarded host GPG agent socket (`GPG_HOST_DIR`) for commit signing, and provisions `ANTHROPIC_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`, and `LOOP_ENGINE_KEYRING_PASSPHRASE` from Infisical (project identified by root `.infisical.json`, machine identity via `INFISICAL_CLIENT_ID`/`INFISICAL_CLIENT_SECRET` forwarded from the host shell) on every container start via `infisical-start.sh` → `seed-secrets.sh`. `infisical run` under machine-identity auth needs `--projectId` and `--path=/loop-engine` passed explicitly — it does not read `.infisical.json`'s `workspaceId` automatically the way interactive login does. The keyring passphrase file must be written *before* anything calls `keyring.set_password`, since the container's cryptfile keyring backend reads that file on every call.
- A bare Linux container has no OS-native keyring backend, so `containers/keyring_backend/cryptfile_backend.py` is wired in as a custom encrypted-file backend via `keyring`'s own backend-discovery config (not the PyPI `keyrings.cryptfile` package). It reads two *file paths* from env vars (`LOOP_ENGINE_KEYRING_FILE`, `LOOP_ENGINE_KEYRING_PASSPHRASE_FILE`) — never secret values directly.
- `.mcp.json` connects Claude Code/Cursor to GitHub's hosted remote MCP server using a bearer-token `GITHUB_PERSONAL_ACCESS_TOKEN`, sourced via `gh auth token` (itself seeded by the Infisical flow above) rather than OAuth, so the devcontainer can authenticate non-interactively at container start.

See `docs/architecture_definition.md` for the full architecture and threat-model writeup, and the README's "Running in a container" section for command-level detail on all of the above.
