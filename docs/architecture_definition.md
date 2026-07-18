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
- **Trust boundary:** the primary network egress is outbound HTTPS from the `tools/llm` client to the configured LLM API endpoint (this includes the token-counting endpoint the client may call to refine a near-cap budget estimate — same host, same credential). **BL-2 (2026-07, pass 1 of 3)** adds a **second, third-party egress**: `tools/slack_io`'s `SlackNotifier.emit` posts a formatted `chat_postMessage` call to the Slack API from a `core/notify` `Notifier` seam invoked inside `run_graph_loop` — fail-open (a formatter bug, bad token, network error, or Slack outage is caught and swallowed, never propagated) and off by default (`build_notifier_from_env()` returns a `NoOpNotifier` unless both env vars below are set). **Superseded by pass 2 (Sprint 40): the engine now has an inbound *control* path — see the inbound-trigger boundary below.** The claim that previously stood here ("no inbound network surface — not a service, no listener") held only for pass 1 and is retained here solely to mark what changed.
- **Inbound trigger boundary (BL-2 pass 2, Sprint 40 — `slack_control/` + `tools/slack_io`'s Socket Mode listener):** `loop-engine slack-listen` accepts `/agent-run` slash commands from Slack and starts real runs. This is the engine's **first inbound control path**, and it is deliberately *not* an inbound **network** surface: Socket Mode is a **WebSocket the daemon dials out to Slack**, so there is still **no bound port, no ingress, no public URL, and no TLS/DNS surface of our own** — the connection is outbound-initiated and authenticated by the app-level token. That is the security argument for choosing it over the parked `trigger/` webhook (**BL-24**), which needed a listener, a reachable URL, and hand-rolled HMAC verification. It is opt-in: nothing listens unless an operator runs the subcommand.
  - **Sink class — unchanged, deliberately.** A Slack command reaches exactly the same sink the CLI already exposes: `runner.run_new` → the persona loop → the Coder's `pytest` subprocess. It adds **no new sink class** over the existing CLI/webhook paths — the execution boundary above (model-generated code executing under the devcontainer assumption) is the same one, reached by a new door. What genuinely changes is **who may open that door**: previously a shell user on the host, now any member of the configured Slack channel.
  - **Authentication + scope (the trust boundary).** Two tokens establish it — the app-level token (`connections:write`) authenticates the socket, the bot token the API calls; both are workspace-scoped, so only *our* workspace can deliver events at all. Inside that, the **FD3 channel-scope guard** narrows further: `SlackDaemon` drops any command whose `channel_id` ≠ the ID resolved at startup from `LOOP_ENGINE_SLACK_CHANNEL`, silently, before any parse or dispatch. The guard compares **IDs, not names** (Socket Mode payloads carry only the ID), and startup **fails closed** if the channel cannot be resolved rather than running with a guard that matches nothing.
  - **Accepted residual risk — channel membership is the authorization model.** There is no per-user allowlist: **anyone who can post in `LOOP_ENGINE_SLACK_CHANNEL` can spend money and run the Coder.** Authorization is therefore exactly Slack channel membership, delegated to workspace administration. This is accepted knowingly for a private operating channel and is the reason the channel is configured explicitly rather than defaulted, and the reason a private channel with a controlled member list is the intended deployment. **Revisit before any multi-tenant or shared-channel use** — a compromised or over-shared channel is full compromise of this surface.
  - **Spend bound.** `--budget` is **required** and parsed fail-closed (missing / non-numeric / non-finite / non-positive ⇒ ephemeral rejection, no run) — the trigger spends real money, so the per-invocation cap is always explicit and can never silently fall back to `DEFAULT_BUDGET_USD`. Concurrency is bounded too: runs serialize behind a single `_run_lock` (BL-8's process-global `os.chdir`), and redelivered envelopes dedupe on `envelope_id`, so a redelivery storm cannot fan out into parallel spend.
  - **Untrusted input handling.** The command payload is untrusted: the parser never raises (every malformed shape yields a typed rejection), and the requirements text flows onward as `human_input` — already covered by the zero-trust-between-stages rule in §3 and the `<untrusted_artifact>` framing. Text echoed back to Slack (a rejection reason) is mrkdwn-escaped and truncated, so a crafted command cannot inject markup or blow the message limit.
  - **Credentials.** The three `LOOP_ENGINE_SLACK_*` vars are env vars, not keyring (see the Slack credential class in §4); none is ever logged, including on the fail-open reply path.
- **Escalation round-trip boundary (BL-2 pass 3, Sprint 41 — `slack_control/`'s message-event path + `tools/state_io`'s correlation scan):** with `LOOP_ENGINE_ESCALATION_TRANSPORT=slack`, a paused run posts its questions to `LOOP_ENGINE_SLACK_CHANNEL` and a human's thread reply is folded back to resume it. A **second inbound door on the pass-2 surface**, with the same trust properties and one new read path:
  - **Sink class — still unchanged.** A thread reply reaches `runner.resume_run` → `PM.fold_answers` → the persona loop → the Coder's `pytest` subprocess: the *same* model-execution sink the CLI/webhook/`/agent-run` paths already reach, entered by a new door. The human's answer text becomes a question `resolution` folded into the run — covered by the zero-trust-between-stages rule (§3) and the `<untrusted_artifact>` framing, exactly as the `/agent-run` requirements text is. **No new sink class.**
  - **Same channel-scope authorization.** The FD3 channel guard is applied to `message` events too (`event["channel"]` ≠ the resolved ID ⇒ dropped silently, **before any state read**), so authorization is still exactly membership of `LOOP_ENGINE_SLACK_CHANNEL` — the accepted residual risk above is unchanged, not widened. The self-trigger loop is closed by dropping the bot's own posts (`bot_id`/`bot_message`/`message_changed`/`message_deleted`).
  - **New read path — the correlation scan.** `find_paused_snapshot_by_slack_thread` reads the main-checkout `state/` tree (read-only; one snapshot per run dir, latest by mtime; tolerates foreign/older snapshots without raising) to match a reply's `thread_ts` to a paused run's `pending_slack.message_ts`. It writes nothing and executes nothing; `slack_control/` reaches it **only through `tools/state_io`**, holding the no-direct-file-I/O boundary.
  - **Idempotency.** Socket Mode redelivers unacked envelopes and a human can send several replies before a resume finishes; `dispatch_resume` dedupes on both `envelope_id` (redelivery) and `thread_ts` (distinct replies to a still-`awaiting_slack` thread), and the `_run_lock` serializes the resume's process-global `os.chdir` against any concurrent start — a reply can drive at most one resume of a run.
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
  - **Slack credential class (BL-2, 2026-07; extended pass 2, Sprint 40):** `LOOP_ENGINE_SLACK_BOT_TOKEN` and `LOOP_ENGINE_SLACK_CHANNEL` (read by `tools/slack_io.build_notifier_from_env()`), plus **`LOOP_ENGINE_SLACK_APP_TOKEN`** (the Socket Mode app-level token, `xapp-…`/`connections:write`, read by `build_listener_from_env()`/`build_daemon_from_env()`), are a **distinct credential class from the LLM API key** — env vars by design (FD3), not keyring, and not gated by the CI exception above. None is a bypass of the keyring rule: they authenticate a different service (Slack, not the LLM API), `tools/llm/client.py`'s keyring-only import boundary is unchanged, and no token is ever logged — including in the swallowed-exception paths when a post or an ephemeral reply fails, and in the fail-closed `RuntimeError` raised when channel resolution errors. The app token is a **second, differently-scoped** Slack credential rather than a broader one: it authenticates only the socket, never the Web API. In the devcontainer all three are inherited via `infisical run`, deliberately **not** seeded through `seed-secrets.sh` (which exists for the keyring and `gh`).
- **Encryption in transit:** all LLM API calls use TLS (enforced by the underlying SDK/HTTP client defaults — do not disable certificate verification).
- **Encryption at rest:** `state/<run_id>/*.json` files are plaintext on the local filesystem, consistent with "local personal tool" threat model. They must never contain the API key or any other credential (enforced by the Pydantic `State` schema simply having no field capable of holding one). The `state/` directory must be `.gitignore`d.
- **Network isolation:** none required — every connection is **outbound-initiated** and there is **no listening socket** and no inter-process network surface. This still holds under BL-2 pass 2 (Sprint 40): `slack-listen` receives commands over a **Socket Mode WebSocket the daemon dials out to Slack**, so the process accepts inbound *control messages* on a connection it opened, but still **binds no port and exposes no ingress** — the property this bullet asserts is unchanged, while "outbound-only" now describes the *connection direction*, not the direction of control. See the inbound-trigger boundary in §1.
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
