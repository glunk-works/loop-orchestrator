# Architecture Definition Document — loop-engine

**Input specification:** `docs/project_spec.v1.json`, scoped per architect/human clarification to the generalized framework described in `requirements.md` (the pluggable `core/personas/loops/tools` framework), not the narrower literal reading of v1's own text.

**Ambiguities resolved with the human (binding decisions):**

| # | Decision |
|---|---|
| 1 | Deployment model: **local-only, container-optional**. No cloud, no AWS, no IaC/OpenTofu. A dev container and a prod container image (both built locally via a shared multi-stage `Dockerfile`) are supported as of 2026-07, superseding the original "no containers" stance — but the containers are still run locally, not deployed to a cloud runtime; that half of the original decision stands. |
| 2 | Execution model: **standalone Python CLI/library**, own LLM client — not a Claude Code skill. |
| 3 | Scope target: the **loop-engine framework** (pluggable core/personas/loops/tools), not a hardcoded 4-stage script. |
| 4 | Secrets handling: **OS keyring** — no plaintext secret ever touches disk. |
| 5 | Persona contract: **abstract base class** (`BasePersona`), not Protocol or registry/entry-point discovery. |
| 6 | Loop definition format: **pure Python** (ordered list of persona instances), not declarative YAML/JSON. |
| 7 | State persistence: **persisted to disk at every stage transition** (resumability + audit trail). |
| 8 | Execution shape: **strictly sequential** chain only — no DAG/branching/parallel execution in v1. |
| 9 | Cost safeguard: **per-run USD budget cap**, priced from a per-model rate table (input/output/cache-write/cache-read $/MTok), enforced centrally, aborts loop on breach. |
| 10 | Interface: **CLI entrypoint required for v1** (Typer), in addition to the library API. |

---

## 1. System Context & Data Flow

loop-engine is a single local Python process, invoked either via CLI (`loop-engine run ...`) or as an imported library, that drives a **strictly sequential state machine** over one shared, versioned **State** object.

```
                 ┌─────────────────────────────────────────────────────────┐
                 │                    loop-engine process                  │
                 │                                                         │
  human input ──▶│  loops/default  ──▶ [PM] ──▶ [Architecture] ──▶         │
  (requirements   │                                                         │
   / prior state) │        ──▶ [Agile Sprint Breakdown] ──▶ [Coder/IaC]    │──▶ artifacts on disk
                 │                                                         │    (docs/, sprints/,
                 │  after each persona: State snapshot written to disk     │     src/, tests/)
                 │  budget tracker checked before/after each persona call  │
                 └─────────────────────────────────────────────────────────┘
                              │                              │
                              ▼                              ▼
                     OS keyring (LLM API key)        outbound HTTPS to LLM API
```

- **Ingress:** a human-provided artifact (free-form markdown or a prior `State` JSON file) supplied as a CLI argument or library call parameter.
- **Processing boundary:** each persona is a pure function of `State -> State`. A persona may make one or more outbound LLM API calls but must not perform side effects outside what it returns in `State` (file writes belong to `tools/state_io`, not to persona code).
- **Egress:** at the end of each stage, the engine (not the persona) persists the updated `State` to disk. At the end of the loop, the final `State` contains references to all produced artifacts (spec, architecture doc, sprint plans, implementation diff summary).
- **Trust boundary:** the primary network egress is outbound HTTPS from the `tools/llm` client to the configured LLM API endpoint (this includes the token-counting endpoint the client may call to refine a near-cap budget estimate — same host, same credential). **BL-2 (2026-07, pass 1 of 3)** adds a **second, third-party egress**: `tools/slack_io`'s `SlackNotifier.emit` posts a formatted `chat_postMessage` call to the Slack API from a `core/notify` `Notifier` seam invoked inside `run_graph_loop` — fail-open (a formatter bug, bad token, network error, or Slack outage is caught and swallowed, never propagated) and off by default (`build_notifier_from_env()` returns a `NoOpNotifier` unless both env vars below are set). There is still no inbound network surface — this is not a service, it has no listener.
- **Execution boundary (new with the agentic Coder):** the engine executes generated code via subprocess — the Coder's `run_tests` tool and the Coder stage's evidence gate both run `pytest` (fixed argv, no shell, hard timeout, size-capped output) against the run's artifact tree. Generated code runs with the invoking user's privileges. **The stated operating assumption is the sandboxed devcontainer** — run untrusted loops only inside the container; outside it, this is arbitrary code execution by the model on the host.

## 2. Technology Stack

- **Language/runtime:** Python 3.12+, matching existing `pm-agent-loop` conventions.
- **Package layout:** `src/loop_engine/{core,personas,loops,tools}/`, `tests/` mirroring that layout, per `requirements.md`.
- **Schema/validation:** Pydantic v2 for the `State` model and all persona input/output contracts.
- **CLI:** Typer, exposing `loop-engine run --loop <name> --input <path> [--resume-from <state.json>] [--budget <usd>]`.
- **LLM client:** a thin wrapper in `tools/llm/` around the Anthropic SDK (or equivalent), the **only** module permitted to read the API key from the OS keyring. Pricing (`pricing.py`), prompt-cache placement (a `cache_control` breakpoint on the caller-supplied stable system prefix), and near-cap token counting all live inside `tools/llm/` — personas only pass content.
- **State persistence:** `tools/state_io/` — Pydantic `.model_dump_json()` writes to `state/<run_id>/<NN_stage_name>.json`.
- **Packaging/tooling:** `hatch` for environment and script management (`hatch run test`, `hatch run ruff check .`, `hatch run ruff format .`), matching `pm-agent-loop` precedent so both tools share one contributor workflow.
- **No cloud services, no IaC tooling** are part of this stack. Containers are supported as an optional, local-only packaging/dev-environment path (2026-07): a shared multi-stage `Dockerfile` (repo root) with `dev` and `prod` build stages, plus `.devcontainer/devcontainer.json` targeting the `dev` stage for VS Code. Deployment remains `pip install` / local checkout / `docker run` — no registry publish step, no cloud runtime.
- **Dev-container-only tooling additions (2026-07):** the Infisical CLI (one-shot secrets bootstrap, see Section 4) and a `.mcp.json`-configured connection to GitHub's hosted remote MCP server. Neither is a runtime dependency of `loop_engine` itself — both are contributor-workflow conveniences confined to the `dev` build stage and the devcontainer's `postStartCommand`.

## 3. IAM & Workload Identity (Strict Least Privilege)

There is no cloud IAM in this architecture; least privilege is enforced at the **module boundary** instead:

- **Credential holder:** only `tools/llm/client.py` may call the keyring API to retrieve the LLM API key. No persona module, no `core/` module, and no `tools/state_io` module may import the keyring library.
- **Persona isolation:** a `BasePersona` implementation receives only the `State` object (via its `run(state) -> state` method) and a handle to the shared LLM client passed in by `core/`. Personas must not be able to instantiate their own LLM client or read credentials directly — this is enforced by constructor injection, not by convention alone.
- **Zero trust between stages:** each persona must treat the incoming `State` as untrusted input and validate it against the Pydantic schema before acting on it, even though it was produced by another in-process persona. A persona must not assume a prior stage's output is well-formed merely because it's in-process.
- **File-system scope:** the agentic Coder's tool set is read/execute-only (`read_file`/`list_files`/`grep` plus `run_tests`); every write still routes through `write_artifact`. `tools/state_io` is the only module permitted to write to the `state/` directory. `tools/state_io` (or a dedicated `tools/artifacts/` module) is the only module permitted to write to `docs/`, `sprints/`, and `src/` output paths — persona logic returns data, it does not open file handles itself.

## 4. Security & Network Posture

- **Secrets management:** LLM API key(s) stored exclusively in the OS-native credential store (Windows Credential Manager / macOS Keychain / Secret Service on Linux) via the `keyring` library. No `.env` file, no plaintext config value, no CLI flag may ever carry the raw key. `tools/llm/client.py` retrieves it once per process at first use.
  - **Container credential path (2026-07):** a bare Linux container has no OS-native keyring backend. The primary path is a custom encrypted file-based `keyring` backend (`containers/keyring_backend/cryptfile_backend.py`) inside the container, with both the encrypted credential file and its decryption passphrase bind-mounted in at run time as files — the "no env var/CLI flag ever carries the raw key" rule holds unchanged for this path, and `client.py`'s contract (`keyring.get_password(...)`) is untouched.
    - **Dev-container Infisical bootstrap (2026-07):** in the dev container only, those two files/native stores (the keyring passphrase, `gh`'s own credential file) are populated once per container start by a one-shot `infisical login` + `infisical run -- <seed script>` invocation authenticated via a Universal Auth machine identity, rather than a human manually running `keyring.set_password(...)`. This does not change the trust boundary: secrets exist only as env vars inside that single child process (never written to disk except the passphrase file, which the app already reads from disk on this path), `client.py`'s import boundary is untouched, and the prod image's `/run/secrets/...` mount path is unaffected — this is a bootstrap mechanism for the dev container's local files, not a new runtime dependency of `loop_engine` itself.
  - **Narrow CI/automation exception:** `client.py` also checks a **double-gated** env var pair (`LOOP_ENGINE_ALLOW_ENV_CREDENTIAL=1` *and* `LOOP_ENGINE_CI_API_KEY`) before falling back to `keyring`. Both variables must be set together, deliberately, so a stray env var can't silently bypass keyring in an interactive session. This is the one documented exception to "no env var may ever carry the raw key," scoped to CI/automation contexts where mounting a pre-encrypted keyring file is impractical.
  - **Slack credential class (BL-2, 2026-07):** `LOOP_ENGINE_SLACK_BOT_TOKEN` and `LOOP_ENGINE_SLACK_CHANNEL`, read by `tools/slack_io.build_notifier_from_env()`, are a **distinct credential class from the LLM API key** — env vars by design (FD3), not keyring, and not gated by the CI exception above. Neither is a bypass of the keyring rule: they authenticate a different outbound service (Slack, not the LLM API), `tools/llm/client.py`'s keyring-only import boundary is unchanged, and the token is never logged, including in the swallowed-exception path when a post fails.
- **Encryption in transit:** all LLM API calls use TLS (enforced by the underlying SDK/HTTP client defaults — do not disable certificate verification).
- **Encryption at rest:** `state/<run_id>/*.json` files are plaintext on the local filesystem, consistent with "local personal tool" threat model. They must never contain the API key or any other credential (enforced by the Pydantic `State` schema simply having no field capable of holding one). The `state/` directory must be `.gitignore`d.
- **Network isolation:** none required — this is a single outbound-only local process with no listening socket and no inter-process network surface.
- **Input handling:** all persona-to-persona and human-to-persona payloads pass through Pydantic validation before use; reject and fail loudly on schema violation rather than coercing or guessing. Coder tool inputs (paths, patterns) are model-controlled: every path is validated with the same traversal rules as the write side plus a symlink-escape check before any filesystem access.

## 5. Supply Chain Security

Matches and extends existing `pm-agent-loop` conventions so both projects share one enforcement bar:

- **Static analysis / linting:** `ruff check .` including the `S` (bandit-equivalent security) and `B` (bugbear) rule sets, zero violations, no unexplained `# noqa`.
- **Formatting:** `ruff format --check .` clean.
- **Secrets scanning:** `gitleaks` run in CI against every diff — zero findings.
- **Dependency vulnerability management:** Dependabot enabled on the new `glunk-works/loop-engine` repo; any new dependency must be pinned to a version with no known critical/high CVE at merge time.
- **SBOM:** CycloneDX SBOM (`sbom.json`) generated and updated in CI on every dependency change, per the "SBOM tracking per modern best practices" requirement in both spec documents.
- **CI enforcement:** all of the above are required, green-CI gates on `.github/workflows/ci.yml` — no merge without them passing, mirroring the `pm-agent-loop` Definition of Done that the downstream Coder/IaC persona already enforces.

## 6. Regulatory & Compliance Impacts

- **Data residency / PII:** none applicable. This is a personal-scale developer tool; `State` payloads consist of project specifications, architecture text, and code — not personal data of third parties. No data-residency controls are required.
- **Compliance regime:** none named in either spec document (`regulatory_and_compliance_constraints: N/A`). No action required beyond standard supply-chain hygiene (Section 5).
- **Caution:** if a future persona/loop ingests third-party or customer data, this section must be revisited before that loop is enabled — this architecture assumes personal/project-internal content only.

## 7. FinOps / Cost Considerations

This is the **primary risk the human explicitly named** ("loops will run out of control and run up costs") and is treated as a hard runtime constraint, not a dashboard-only concern:

- **Per-run budget cap:** every invocation of `loop-engine run` requires (or defaults to) a maximum spend in USD. `tools/llm/client.py` prices every call from the per-model rate table in `tools/llm/pricing.py` — input, output, cache-write, and cache-read tokens each at their own $/MTok rate — and tracks cumulative cost centrally across all persona calls in the run. An unknown model raises rather than pricing at $0.
- **Hard abort on breach:** the moment cumulative usage would exceed the configured budget, the engine aborts the loop **before** making the call that would breach it, persists the current `State` to disk (Section 1/3), and exits with a non-zero status and a clear message — it does not let an in-flight call finish over-budget.
- **No silent retries that inflate cost:** any persona-internal retry logic must count against the same run-level budget; retries are not a separate, unbounded cost pool.
- **Cost visibility:** every stage's `State` snapshot on disk records tokens, real `cost_usd` (from the rate table), and cache write/read token counts for that stage, so a human can inspect exactly where budget was spent after the fact (`loop-engine cost-summary`).
- **Prompt caching:** each persona's stable prefix (prompt template + consumed artifact) is sent as cached system blocks (`cache_control: ephemeral`); cache reads bill at 0.1x the input rate and writes at 1.25x (rates in `tools/llm/pricing.py`). The prefix must be byte-identical across calls — volatile content (findings, sprint plans) stays in the user turn. Caching is best-effort: prefixes under the model's minimum cacheable size silently don't cache, and nothing may branch on a cache hit.
- **Incremental revisions:** gate-revision and question-resolution passes do not regenerate whole documents; the prior artifact is sent as an assistant turn, the model returns only the corrected sections, and the persona merges them locally (`personas/sections.py`) — output spend scales with the size of the correction, not the document.
- **Pre-flight refinement:** far from the cap, a chars/4 heuristic estimates a call's cost; once the estimate reaches 50% of the remaining budget, the client refines it via the (free) token-counting endpoint before deciding to abort. A count failure falls back to the heuristic — never a new failure mode.
- **Model selection:** left to per-persona configuration (not hardcoded in `core/`), so a cheaper model can be substituted for lower-stakes personas (e.g., sprint breakdown) without changing engine code — a concrete, low-effort cost lever the Coder/IaC stage should expose as a config value, not a constant.

## 8. IaC Handoff Directives

*(No cloud IaC is in scope — these are the equivalent strict build directives for the Developer/Coder-IaC persona.)*

- Implement under `src/loop_engine/{core,personas,loops,tools}/` exactly as specified; `core/` must not import any concrete persona module — only `personas/base.py`'s `BasePersona` ABC.
- Define `State` as a Pydantic v2 model including a `schema_version` field (matching the `spec_version` convention already used in `docs/project_spec*.json`), plus per-stage usage/cost fields (Section 7).
- `BasePersona` is an ABC with a single abstract method: `run(self, state: State, llm_client: LLMClient) -> State`. Constructor injection only — no persona may construct its own `LLMClient` or touch `keyring` directly.
- `tools/llm/client.py` is the sole module permitted to import `keyring`; it exposes a USD-budget-tracking `LLMClient` (priced via `tools/llm/pricing.py`) that raises a dedicated `BudgetExceededError` rather than allowing an over-budget call.
- `tools/state_io/` is the sole module permitted to write to `state/`, `docs/`, or `sprints/` output paths; it writes a `State` snapshot after every persona completes, before the next persona starts. `tools/coder_tools/` is read/execute-only and reuses `state_io`'s path validation; its `run_tests` subprocess (with the Coder gate's deterministic pytest re-run) is the only subprocess surface besides `issue_io`'s `gh`.
- `loops/default/loop.py` exposes an ordered `list[BasePersona]` reproducing `PM → Architecture → Agile Sprint Breakdown → Coder/IaC`; no YAML/JSON loop config format is to be introduced in v1.
- The engine's run loop (`core/engine.py` or equivalent) must be a plain `for persona in loop: state = persona.run(state, llm_client)` — no async orchestration, no DAG resolution, no parallel stage execution in v1.
- CLI: implement via Typer as `loop-engine run --loop <name> --input <path> [--budget <value>] [--resume-from <path>]`; the CLI is a thin wrapper — all logic lives in the library layer so `import loop_engine` remains fully usable without the CLI.
- `state/` must be added to `.gitignore` in the new `glunk-works/loop-engine` repo scaffold.
- Enforce, per sprint, the Global Definition of Done: `hatch run test` clean, `hatch run ruff check .` clean (including `S`/`B` rules), `hatch run ruff format --check .` clean, `gitleaks` zero findings, no unaddressed Dependabot alert, CycloneDX `sbom.json` current, and every new Pydantic-validated I/O path has a test proving invalid input is rejected — identical bar to `pm-agent-loop`'s existing Definition of Done.
