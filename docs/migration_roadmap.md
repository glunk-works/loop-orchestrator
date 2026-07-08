# Migration Roadmap — MCP / LangGraph / Isolated Factory

Working roadmap + status for the migration to `migration_architecture_plan.md`.
This is the **resume point**: a new session should read this file first, then
`git log` the branch. Target requirements live in `migration_architecture_plan.md`;
this file tracks *how far we've got and what's next*.

- **Branch:** `feat/mcp-langgraph-migration` (cut from `origin/main`). Nothing
  merges to `main` until the whole migration works end to end.
- **Workflow:** one phase at a time; each phase ends with a green commit
  (`hatch run lint`/`format`/`test` + `audit`/`sbom`) and a **hard stop for
  human review** before the next phase starts. Earlier behavior stays runnable
  behind flags so any phase boundary is checkout-able.

## Status

| Phase | State | Commit |
|---|---|---|
| 1 — State & skill externalization + LangGraph engine | ✅ complete, reviewed | `ee89718` |
| 2 — MCP tooling (coder tools as MCP server) | ✅ complete, reviewed | `7368411` |
| 3a — Execution isolation (per-run git worktrees) | ✅ built behind flag, reviewed | `951e377` |
| 3b — Execution isolation (disposable container/sandbox) | ✅ inert seam built behind flag, tests green — **awaiting HITL review** (docker/podman primary, bwrap secondary; real `docker run` + sandboxed gate deferred to a daemon host). Plan: `sprints/18_execution_isolation_container/sprint_plan.md` | — |
| 4 — Flattening orchestration (declarative personas, exit-code gates) | ⬜ sketch only | — |
| 5 — Autonomous triggers + multi-repo factory | ⬜ sketch only | — |

Phases 1–2 were detailed and executed. **Phases 3–5 are only sketched** (below)
and need a detailed planning pass before implementation.

## Decisions log (locked)

- **Adopt LangGraph literally** — the pre-existing engine was a bespoke
  `while`-loop, not LangGraph. Now a `StateGraph` in `core/graph_engine.py`,
  selected by `LOOP_ENGINE_ENGINE=langgraph`; classic `run_loop` is still the
  default. Both drive the shared `execute_stage()` primitive (parity-tested).
- **Doc stages keep deterministic structural validators**; exit-code gates
  apply only to code stages. "No LLM Critic" = no LLM *judge* (already true).
  The PM's *revision loop* is what Phase 4 retires — its checks survive as a
  structural gate.
- **1c used the "dual-field" path (not the full strip):** `State` gained
  `artifact_refs` (path + sha256) alongside the inline `artifacts` body-dict
  (schema v3); `tools/artifact_store.mirror_to_disk` populates refs at snapshot
  time. **The inline bodies are NOT yet dropped** — that strip is deferred to
  when the LangGraph engine is the sole reader. This is a live follow-up.
- **Phase 2 scope:** built only the coder-tools MCP server (the sole
  LLM-callable tool set). **Deferred:** state-io/github MCP servers (they're
  orchestrator-invoked, not model tools) and full `.mcp.json`-file-driven
  multi-server discovery (the `list_tools` runtime-discovery mechanism is in
  place, pointed at a default server).

## Feature flags introduced

- `LOOP_ENGINE_ENGINE=langgraph` → LangGraph engine (default: classic `run_loop`).
- `LOOP_ENGINE_TOOLS=mcp` → Coder dispatches tools via the MCP provider
  (default: in-process `CODER_TOOLS`/`_execute_tool`).
- `LOOP_ENGINE_ISOLATION=worktree` → per-run git worktree; the CLI chdir's the
  run into it (default: no isolation, runs in the checkout). Worktree base dir
  overridable via `LOOP_ENGINE_WORKTREE_ROOT` (default `.worktrees/`).

## What exists now (key modules)

- `core/engine.py` — `execute_stage()` (shared per-stage primitive) + classic `run_loop`.
- `core/graph_engine.py` — LangGraph `StateGraph` engine; `tests/core/test_graph_engine.py` guards parity.
- `core/state.py` — schema v3, `ArtifactRef`, `migrate_state_payload` (v1/v2→v3).
- `tools/artifact_store.py` — `mirror_to_disk`, `get_artifact`, `has_artifact`.
- `tools/agent_state/` + `.agent/STATE.md`/`.agent/MEMORY.md` — semantic-state layer.
- `mcp_servers/coder_tools_server.py` — stdio MCP server (read/execute-only).
- `tools/mcp/` — `MCPToolProvider` (discovery + dispatch on a background event loop); Phase 3b `container_server_params`/`sandbox_server_params` + preflight (inert).
- `tools/isolation.py` — single reader of `LOOP_ENGINE_ISOLATION` (`none|worktree|container|sandbox`) + `IsolationUnavailableError`.
- `CLAUDE.md` — expanded with a portable "Global Conventions" skill section.

---

## Phase 3 — Execution Isolation *(planned — see `docs/phase3_execution_isolation_plan.md`)*

Detailed buildable spec lives in **`docs/phase3_execution_isolation_plan.md`**.
Summary + the decisions that resolved the earlier open questions:

- **Split into 3a (build now) + 3b (spec the seam, defer the build).** Forced by
  the environment: the devcontainer has **no `docker`/`podman`** and is itself an
  unprivileged container. DinD needs `--privileged`; DooD mounts the host socket
  (host-root-equivalent) into a process that already runs untrusted model code
  in-process — that *enlarges* the surface. So no DinD/DooD here.
- **3a — worktree isolation:** a `tools/worktree/` manager (`git worktree` per
  run, a new sanctioned subprocess surface) + a `worktree_run(run_id)` context
  manager that **`chdir`s** into the worktree for the run. Rooting is by chdir
  (not root-threading) because everything already keys off `Path.cwd()` — this
  needs ~zero signature changes, converges the MCP `cwd` param and the in-process
  tool path, and auto-tightens the existing traversal/symlink checks to the
  worktree. Gated by `LOOP_ENGINE_ISOLATION=worktree` (default off).
- **Snapshots stay in the main checkout** (state_io grows a `state_root()` the
  context manager pins to the orchestrator home); only the artifact tree
  (`src/`/`docs/`/`sprints/`/`.agent/`) follows the chdir into the worktree. So
  `mirror_to_disk`'s `docs/artifacts/<run_id>/…` lands in the worktree; the
  snapshot's *relative* artifact refs are valid only inside the worktree context
  (matters for the deferred inline-artifacts strip — cross-cutting #1).
- **3b — container/sandbox:** preserved as a drop-in via the MCP provider seam
  (only the server *launch params* change: `docker`/`podman` on a daemon-bearing
  host, or `bwrap`/`nsjail` daemon-free). Reuses the `dev` Dockerfile stage;
  mounts worktree only. Spec + flag stub now, no executing code until a runtime
  is chosen and verified.
- **Honest caveat:** 3a is blast-radius isolation, **not** a security sandbox —
  on the default tools path untrusted code still runs in-process. The security
  boundary is 3b.

## Phase 4 — Flattening Orchestration *(sketch)*

- **Declarative personas:** move `system_prompt` + `tools` + `model`/`max_tokens`
  + `consumes`/`produces` into YAML/TOML (3 of 4 prompts already file-backed in
  `prompts/*.md`). A generic node loader replaces per-class boilerplate; residual
  imperative logic (section-merge revision, SEARCH/REPLACE apply, PM fold/critic)
  becomes shared services invoked by config-driven nodes.
- **Gates:** retire the PM Critic *revision loop*; keep its deterministic checks
  as a structural doc-stage gate. Code stages gate strictly on a `0` exit code
  from the test-runner MCP server. **Error looping:** non-zero exit routes
  `stderr` back to the Coder node until green (a LangGraph conditional edge).

**Open questions:** YAML vs TOML? How much persona logic can truly go
declarative vs stay as shared Python services? Does retiring the PM revision
loop change PM outputs/tests, and how is that gated safely (flag + parity)?

## Phase 5 — Autonomous Triggers & Multi-Repo Factory *(sketch)*

- **FastAPI webhook server** alongside the engine; trigger a graph run on an
  issue labeled `agent-action` or a slash command in an issue comment.
- **Bootstrapping:** GitHub MCP `create_repository` in `glunk-works` → scaffold
  (`hatch new` / OpenTofu boilerplate) in a fresh worktree → inject global
  `CLAUDE.md` → commit/push. *(Pulls forward the deferred github MCP server.)*
- **Maintenance:** clone + feature-branch worktree → absorb target repo's
  `CLAUDE.md` + `.agent/STATE.md` → on green gate, push branch and open a PR
  against `develop`. **Auto-merge stays prohibited.**

**Open questions:** webhook auth model + where the server is hosted; org access
to `glunk-works`; how runs are queued/rate-limited.

## Cross-cutting follow-ups (don't lose these)

1. **Drop the inline `artifacts` body-dict** once the LangGraph engine is the
   sole reader (completes the 1c "strip" — makes state truly thin).
2. **state-io + github MCP servers** (deferred from Phase 2) — Phase 5's
   bootstrapping needs the github one.
3. **Full `.mcp.json`-driven multi-server discovery** (mechanism exists).

## How to run / verify

```bash
hatch run test            # full suite (215 after P1, 226 after P2, 246 after P3a)
hatch run lint && hatch run format && hatch run audit && hatch run sbom
LOOP_ENGINE_ENGINE=langgraph  hatch run test tests/core/test_graph_engine.py
LOOP_ENGINE_TOOLS=mcp         hatch run test tests/tools/test_mcp_provider.py
```
