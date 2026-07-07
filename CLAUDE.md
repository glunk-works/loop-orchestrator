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

- **`core/state.py`** — `State`, a Pydantic v2 model (`schema_version` 2: `run_id`, `status`, `questions`, `pending_issue`, `counters`, `stage_history`, `artifacts`) with `extra="forbid"`. `RunStatus` makes termination explicit (`completed` / `failed_stage` / `budget_exceeded` / `awaiting_issue`) — never inferred from "no exception". `migrate_state_payload()` upgrades v1 snapshots on load.
- **`core/engine.py`** — `run_loop(loop: Loop, ...)`: per stage, a bounded propose → gate → accept/revise/escalate cycle. Gate findings feed revision attempts against the prior artifact — the persona sends it as an assistant turn, gets back only corrected sections, and merges via `personas/sections.py` (identical findings twice = stop paying, escalate); escalated questions walk the stage's `resolvers` ladder; questions nobody answers become a GitHub issue and the run pauses (`AWAITING_ISSUE`). Resolved questions carry an `impact` that routes re-entry via `Loop.impact_reentry`. Hard caps (`MAX_ESCALATIONS_PER_STAGE`, `MAX_REPLANS_PER_RUN`) keep every feedback edge finite. Every exit path persists a snapshot.
- **`core/gates.py`** — `ArtifactGate`: content validation (present, JSON-shaped if declared, not question-shaped) plus `## Open Questions` extraction into `Question` objects.
- **`personas/base.py`** — `BasePersona`: abstract `run(state, llm_client, findings=None)`, `consumes`/`produces` artifact declarations (engine pre-checks inputs), and overridable `resolve_questions()` for resolver duty. Personas receive the LLM client via injection — they cannot construct their own or touch credentials directly.
- **`personas/{pm,architecture,agile_sprint_breakdown,coder_iac}/`** — the four default personas; prompts are batch-mode (assumptions + `## Open Questions`, never "ask and wait"). `PMPersona` keeps its critic revision loop (`personas/pm/critic.py`) with no-progress detection, and additionally implements `resolve_questions` (from the spec) and `fold_answers` (folds human issue answers into the spec and classifies impact). `CoderIacPersona` runs an inner agentic loop — one `run_tool_loop` per sprint block with read/execute tools (`read_file`/`list_files`/`grep`/`run_tests` from `tools/coder_tools/`) — emits full-content or SEARCH/REPLACE edit blocks that the persona applies via `write_artifact` (failures are recorded on the report for the gate), and stops at a sprint that raises questions; on findings re-entry it re-runs only the sprint(s) targeted by resolved questions (`Question.origin_detail`) or by sprint-path-prefixed gate findings, falling back to a full re-run when findings carry no attribution. Its stage gate is `core/coder_gate.py`: content checks plus a deterministic pytest run — ACCEPT is evidence-based, and pytest exit 5 (no tests) is a REVISE. Sprint plans and implementation reports are written to `sprints/` via `write_artifact`.
- **`loops/default/loop.py`** — `DEFAULT_LOOP`, a `Loop` of four `Stage`s wiring gates, the resolver ladder, and `impact_reentry`. No YAML/JSON loop-definition format — loops are just Python.
- **`tools/llm/client.py`** — `LLMClient`: retrieves the API key from `keyring` exactly once per instance, prices every call from the per-model rate table in `tools/llm/pricing.py` and enforces the per-run USD budget *before* each call (`BudgetExceededError`; heuristic estimate, refined via `count_tokens` once it reaches 50% of the remaining budget), sends caller-supplied `system_blocks` as a cached system prefix (`cache_control: ephemeral` on the last block — personas keep these byte-identical across calls and put volatile content in the user prompt), drives the Coder's bounded tool loop via `run_tool_loop` (per-iteration budget debit, executor errors surfaced as `is_error` tool results, iteration cap fails the stage honestly), and raises `TruncatedResponseError` when `stop_reason == "max_tokens"` (a truncated artifact must never propagate). **This is the only module in the codebase permitted to import `keyring`** — enforced by `tests/tools/test_keyring_boundary.py`.
- **`tools/issue_io/`** — the only module that talks to GitHub (shells out to `gh`; no token in-process). Files the escalation issue, parses the human's ```answers comment, maps numbered answers back to questions.
- **`tools/state_io/writer.py`** — the sole writer of `State` snapshots (`state/`) and produced artifacts (`docs/`, `sprints/`, `src/`). Validates `run_id`/artifact paths against path traversal before any filesystem call.
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
- Any change touching `State` must keep `schema_version` accurate (bump it and extend `migrate_state_payload` for breaking shape changes) and keep `extra="forbid"` intact.

## Containers / devcontainer

- Root `Dockerfile` is multi-stage: `dev` (full contributor toolchain — hatch, ruff, git, gh) and `prod` (minimal runtime). Both are local-only, no registry publish.
- `.devcontainer/` targets the `dev` stage. It bind-mounts a forwarded host GPG agent socket (`GPG_HOST_DIR`) for commit signing, and provisions `ANTHROPIC_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`, and `LOOP_ENGINE_KEYRING_PASSPHRASE` from Infisical (project identified by root `.infisical.json`, machine identity via `INFISICAL_CLIENT_ID`/`INFISICAL_CLIENT_SECRET` forwarded from the host shell) on every container start via `infisical-start.sh` → `seed-secrets.sh`. `infisical run` under machine-identity auth needs `--projectId` and `--path=/loop-engine` passed explicitly — it does not read `.infisical.json`'s `workspaceId` automatically the way interactive login does. The keyring passphrase file must be written *before* anything calls `keyring.set_password`, since the container's cryptfile keyring backend reads that file on every call.
- A bare Linux container has no OS-native keyring backend, so `containers/keyring_backend/cryptfile_backend.py` is wired in as a custom encrypted-file backend via `keyring`'s own backend-discovery config (not the PyPI `keyrings.cryptfile` package). It reads two *file paths* from env vars (`LOOP_ENGINE_KEYRING_FILE`, `LOOP_ENGINE_KEYRING_PASSPHRASE_FILE`) — never secret values directly.
- `.mcp.json` connects Claude Code/Cursor to GitHub's hosted remote MCP server using a bearer-token `GITHUB_PERSONAL_ACCESS_TOKEN`, sourced via `gh auth token` (itself seeded by the Infisical flow above) rather than OAuth, so the devcontainer can authenticate non-interactively at container start.

See `docs/architecture_definition.md` for the full architecture and threat-model writeup, and the README's "Running in a container" section for command-level detail on all of the above.
