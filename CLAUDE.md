# CLAUDE.md

Lean routing layer for this repo — kept small and stable so it stays prompt-cached.
Day-to-day guardrails (commands, module boundaries, model routing) live here; the
heavy reference (module walkthrough, conventions, container setup) is in `.ai/context/`,
loaded on demand. **Where we are right now** lives in `.ai/next-steps.md`.

## What this is

loop-engine runs a named sequence of decoupled AI "persona" stages against a single, explicit, versioned `State` object. The default loop is a **PM → Architecture → Agile Sprint Breakdown → Coder/IaC** pipeline, but it is not a one-way conveyor: every stage's output passes a content **gate** (accept / revise / escalate), questions escalate up a resolver ladder (Coder → Architect → PM → human via GitHub issue), and resolved questions route rework back down by blast radius ("task" re-runs the asker, "plan" re-enters Sprint Breakdown, "architecture" re-enters the Architect). A snapshot is persisted after every accepted stage AND on every exit path (completed / failed / budget-exceeded / awaiting-issue).

> **Migration in progress.** The engine is mid-migration toward MCP tooling +
> LangGraph + an isolated multi-repo factory. **Status, decisions, and the
> remaining phases live in [`docs/migration_roadmap.md`](docs/migration_roadmap.md)** —
> read it before extending this work. Phases 1–3 are done behind flags
> (`LOOP_ENGINE_ENGINE=langgraph`, `LOOP_ENGINE_TOOLS=mcp`, `LOOP_ENGINE_ISOLATION`);
> Phase 4 · part 1 is the Ralph-loop Coder (`LOOP_ENGINE_CODER=ralph`) and part 2 is
> the declarative `GeneratorNode` personas + PM `CriticGate` (`LOOP_ENGINE_PERSONAS=declarative`);
> all default off/`classic`. Phase 5 remains sketched.

## Working here: personas & model routing

Development on this repo is split by model to keep each session lean and single-model
(the token/session-limit fix). The workflow is externalized into `.ai/` and driven by
three skills — **`/resume`** (rehydrate from `.ai/` at the start of a session),
**`/handoff`** (serialize state before switching model/session), **`/archive-sprint`**
(retire a completed, HITL-approved sprint). See `.ai/context/workflow.md` for the protocol.

- **Architect (Opus).** Architecture, design, sprint/phase **planning** (planning pass, one question at a time, HITL gates), **HITL review** of a coding session's diff, module-boundary decisions, non-trivial debugging, and roadmap/memory updates. This is the default model for planning and review sessions.
- **Coder (Sonnet).** Implementing an already-**defined** sprint task, writing/adjusting tests, mechanical refactors, running the green gate, fixing lint. Sonnet runs the implementation sessions (or is dispatched as the `coder` subagent for a small in-session task).

Rule of thumb: if the task requires deciding *what* to build or *whether* a diff is
correct → **Opus**; if the task is executing a spec that already exists → **Sonnet**.
Switch at sprint boundaries via `/handoff` → fresh session → `/resume`.

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
(The `loop-engine resume` CLI subcommand is unrelated to the `/resume` dev-workflow skill.)

CI (`.github/workflows/ci.yml`) runs, in order: `lint` → `format-check` → `test` → `secrets-scan` (gitleaks) → `sbom`. All must pass; see `sprints/GLOBAL_DEFINITION_OF_DONE.md` for the full merge bar. The API key is **never** a CLI flag or env var — it comes only from the OS keyring (setup + fallback detail in `.ai/context/modules.md`).

## Enforced module boundaries

These are checked by static tests, not just convention — don't casually violate them:

- `core/` imports no concrete persona module, only `personas/base.py`.
- `tools/state_io/` is the only module with direct file-write calls (`open`/`write_text`/`write_bytes`); everything else goes through `write_artifact`/`write_state_snapshot`.
- `tools/llm/client.py` is the only module that imports `keyring`.
- `tools/issue_io/` is by convention the only module that talks to GitHub.
- `tools/coder_tools/` is read/execute-only: paths are traversal- and symlink-validated (reusing `state_io`'s validator); its `run_tests` pytest subprocess (also used by the Coder gate) is a sanctioned subprocess surface. It runs model-generated code — the operating assumption is the sandboxed devcontainer.
- Sanctioned subprocess surfaces are exactly three, each fixed-argv and `shell=False`: `coder_tools`' `pytest`, `issue_io`'s `gh`, and `tools/worktree`'s `git worktree` (args derive only from a `validate_run_id`-checked run_id). Nothing else shells out. The Phase 3b container/sandbox launch is **not** a fourth surface: it is spawned by the MCP `stdio_client` (the same mechanism that launches the local coder-tools server — only `command`/`args` differ), and runtime detection uses `shutil.which`, not a subprocess.
- `mcp_servers/` re-front native tools over MCP (`coder_tools_server` = read/execute-only, delegating to `tools/coder_tools` with the same path validation and no credentials). On the `LOOP_ENGINE_TOOLS=mcp` path, tool execution runs in the server subprocess, out of the orchestrator process entirely — the boundary is moved, not relaxed. `tools/mcp` is the client side (discovery + dispatch) and imports no keyring/writes no files. Server discovery is config-driven and consumer-scoped: `tools/mcp/config.py` reads an optional repo-root **`loop_engine.mcp.json`** (distinct from Claude Code's own `.mcp.json`) into logical-name → launch-spec, and `build_provider_for(names, ...)` builds a provider for **only** the named servers, so a consumer only ever sees the tools of the server(s) it asked for. The coder-tools server exposes exactly `{read_file, list_files, grep, run_tests}` (asserted by `tests/tools/test_mcp_provider.py`), and that stays true even when the config also declares another server (`tests/tools/test_mcp_provider.py::test_extra_config_server_never_reaches_coder_provider`).
- Any change touching `State` must keep `schema_version` accurate (bump it and extend `migrate_state_payload` for breaking shape changes) and keep `extra="forbid"` intact.

## Pointers (load on demand)

- **`.ai/next-steps.md`** — the live dev-workflow cursor: current phase/sprint, next action, which model. Read this first (or run `/resume`).
- **`.ai/context/modules.md`** — module-by-module walkthrough, the architecture diagram, API-key setup, container/devcontainer detail.
- **`.ai/context/conventions.md`** — the portable Global Conventions (Python / IaC / commit / Definition of Done) the personas inject into managed repos.
- **`.ai/context/workflow.md`** — the `/resume` → `/handoff` → `/archive-sprint` handoff protocol and Opus↔Sonnet switch points.
- **`docs/migration_roadmap.md`** — the deep, authoritative migration status + decisions log (the resume point of record).
- **`docs/architecture_definition.md`** — the full architecture + threat-model writeup.

> Note: `.agent/STATE.md` + `.agent/MEMORY.md` are the loop-engine **product's** own
> runtime Ralph state (written when the engine *runs*), NOT this dev-workflow layer.
> Don't confuse them with `.ai/`.
