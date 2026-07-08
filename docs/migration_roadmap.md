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
| 3b — Execution isolation (disposable container/sandbox) — **inert seam** | ✅ built behind flag, reviewed (docker/podman primary, bwrap secondary; real `docker run` + sandboxed gate pytest deferred to a daemon host). Plan: `sprints/18_execution_isolation_container/sprint_plan.md` | `cdc7c8f` |
| 4 · part 1 — Ralph-loop Coder (`AgenticNode`) | ✅ built behind flag, 311 tests green — awaiting HITL review. Plan: `sprints/19_ralph_coder/sprint_plan.md` | `195f7b7` |
| 4 · part 2 — Declarative generators (`GeneratorNode`) + PM critic-gate | ⬜ sketch (planned next, sprint 20) | — |
| 5 — Autonomous triggers + multi-repo factory | ⬜ sketch only | — |
| 6 — Collapse the flags (decommission the migration scaffolding) | ⬜ sketch only | — |

Phases 1–3b are detailed and executed (3b's daemon-host e2e is deferred, not
lost — see its plan). Phase 4's planning pass is done and it **split into two
separately-gated sub-phases, Ralph-Coder-first** (see the Phase 4 section and
decisions log below). **▶ NEXT ACTION: build Phase 4 · part 1** from
`sprints/19_ralph_coder/sprint_plan.md` (green commit + HITL gate), then write
the part-2 (`GeneratorNode` + PM critic-gate) sprint plan and build it. Phase 5
remains sketch-only after that; Phase 6 (below) is the tracked teardown that
keeps the feature flags from calcifying into permanent bloat.

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
- **Phase 4 planning pass (locked):**
  - **Persona config format = YAML (PyYAML).** The declarative persona config
    (`GeneratorNode`, part 2) lives in per-persona YAML parsed by a node
    loader. This adds PyYAML as a *pinned* dependency → SBOM regen + `pip-audit`
    must clear it (a first-class task in the part-2 plan). Loop *wiring* stays
    Python ("loops are just Python"); only persona **config** goes declarative.
  - **Two node archetypes, not one-generic-vs-four-custom.** A misfit persona
    is holding control flow that belongs in a gate or edge. (1) `GeneratorNode`
    — single-shot generate + optional section-merge revision + optional
    `resolve_via_document` resolver — drives **Architecture, Sprint Breakdown,
    and PM**; its only varying logic is a small registry of shared services
    (output-adapters `markdown`/`sprint_blocks`/`json_object`, revision-style
    `section_merge`/`full_reextract`, `untrusted` input-wrapper). (2)
    `AgenticNode` (tool loop) — drives the **Coder**. Guiding principle:
    *personas generate, gates accept, the graph routes.*
  - **PM collapses onto `GeneratorNode` once its critic *loop* is retired.**
    The `MAX_REVISION_CYCLES` loop inside `PMPersona.run` is misplaced control
    flow → it becomes a structural `CriticGate` (the `critic.review()` *checks*
    survive; the engine's existing revise loop drives re-extraction). PM's
    `fold_answers` is a resume-time resolver *service*, not forward-path node
    logic. (Part 2.)
  - **Coder = a Ralph loop** (project owner's call). One **task** of work per
    invocation from a **fresh context**; the worktree filesystem + the `.agent/`
    ledger (`STATE.md` task checklist / `MEMORY.md` lessons, built Phase 1,
    underused) are its progress + cross-iteration memory; the exit-code gate is
    its termination condition. Implemented as **Strategy A — reuse
    `execute_stage`'s revise loop** (no new `StateGraph` topology): incremental
    idempotent `run()`, a coverage-aware gate (green is necessary, not
    sufficient — *every manifest task* must be checked off), and the Coder
    stage's `max_revisions` raised to the Ralph iteration cap. The engine's
    existing identical-findings→escalate is the no-progress guard; the USD
    budget is the hard cost governor. Behind `LOOP_ENGINE_CODER=ralph`; a
    behavior change, so **flag-gated, not parity-claimed** (only the default
    `classic` path and cross-engine equivalence are parity-tested).
  - **Sprints ARE the right input for Ralph — keep the planner, add a manifest.**
    The Agile Sprint Breakdown already decomposes work into sprints → tasks →
    acceptance-criteria: exactly the discrete, dependency-ordered,
    independently-verifiable checklist a Ralph loop needs. So `AgileSprintBreakdownPersona`
    and its prompt stay unchanged; it *additionally* emits a **structured
    `task_manifest`** (`[{id, sprint_path, title, description, acceptance_criteria,
    target_files, deps}]`), **deterministically parsed from its own `**Task N:**`
    markdown — no new LLM call**, `sprint_plans` byte-identical. Ralph's increment
    unit is a **task** (dependency-respecting), and per-task "done" = *its
    acceptance-criteria test passes* — which closes the "report-presence is a
    proxy for done" gap. `.agent/STATE.md` holds the authoritative task checklist;
    `implementation_reports` stays sprint-keyed prose. The manifest is a new
    Pydantic boundary (negative-input test) but its *validation gate* + the Ralph
    persona are wired **only under `LOOP_ENGINE_CODER=ralph`**, so the default
    Sprint-Breakdown/Coder acceptance behavior is untouched.
  - **Sequencing: Ralph Coder first (part 1, sprint 19), declarative generators
    + PM critic-gate second (part 2, sprint 20).** De-risk the higher-uncertainty
    piece first; each part is its own green commit + HITL gate.

## Feature flags introduced

- `LOOP_ENGINE_ENGINE=langgraph` → LangGraph engine (default: classic `run_loop`).
- `LOOP_ENGINE_TOOLS=mcp` → Coder dispatches tools via the MCP provider
  (default: in-process `CODER_TOOLS`/`_execute_tool`).
- `LOOP_ENGINE_ISOLATION=worktree` → per-run git worktree; the CLI chdir's the
  run into it (default: no isolation, runs in the checkout). Worktree base dir
  overridable via `LOOP_ENGINE_WORKTREE_ROOT` (default `.worktrees/`).
- `LOOP_ENGINE_CODER=ralph` → the Ralph-loop Coder (one increment per
  invocation, self-loop via `execute_stage`) instead of the classic per-sprint
  Coder (default `classic`). *(Phase 4 · part 1 — planned, sprint 19.)*
- `LOOP_ENGINE_RALPH_MAX_ITERS` → Ralph iteration cap = the Coder stage's
  `max_revisions` under `ralph` mode (default `30`). *(Phase 4 · part 1.)*

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

## Phase 4 — Flattening Orchestration *(planned; split into part 1 + part 2)*

Planning pass complete — the open questions below are resolved in the decisions
log above. Phase 4 is two separately-gated sub-phases, **Ralph-Coder-first**.

**Reality check that shaped the plan** (the earlier sketch was stale):
- Prompts already exist as `prompts/0N_*.md` but are *embedded verbatim* in each
  persona and pinned by a header **parity test** — not loaded from disk. PM has
  no prompt file (ported from pm-agent-loop, pinned by phrase).
- The code-stage exit-code gate **already exists** (`CoderGate` ACCEPTs only on
  pytest exit 0) and `execute_stage` **already runs a bounded revise loop**
  feeding gate findings back. So "error-loop until green" is largely already the
  shared primitive — Phase 4 reshapes the Coder *around* it rather than adding a
  new conditional edge.

### Part 1 — Ralph-loop Coder (`AgenticNode`) — sprint 19 *(detailed plan ready)*

See `sprints/19_ralph_coder/sprint_plan.md`. Two moves in one sprint: (1) the
Sprint Breakdown additionally emits a deterministic `task_manifest` (its prompt
+ `sprint_plans` unchanged); (2) the Coder becomes a Ralph loop that works the
manifest down **one task per invocation** from a fresh context, tracking
progress as a `.agent/STATE.md` checklist, driven to completion by
`execute_stage`'s existing revise loop + a **coverage-aware** exit-code gate
(green + *every task checked off*). Per-task "done" = its acceptance-criteria
test passes. Behind `LOOP_ENGINE_CODER=ralph` (default `classic`); flag-gated,
not parity-claimed. Termination is hard-bounded (iteration cap
`LOOP_ENGINE_RALPH_MAX_ITERS`, no-progress escalation via identical-findings,
USD budget as governor).

### Part 2 — Declarative generators (`GeneratorNode`) + PM critic-gate — sprint 20 *(sketch)*

- **`GeneratorNode`:** one YAML-driven node (prompt file, model, max_tokens,
  consumes/produces, output-adapter, revision-style, optional resolver) replaces
  the per-class boilerplate of **Architecture, Sprint Breakdown, and PM**. The
  genuinely-varying logic becomes a small registry of **shared services**
  (output-adapters, `section_merge`/`full_reextract` revision, `resolve_via_document`,
  `untrusted` input-wrapper). Adds PyYAML (pinned) → SBOM/audit tasks.
- **PM critic-gate:** retire the `MAX_REVISION_CYCLES` loop inside `PMPersona.run`;
  re-express `critic.review()` as a structural `CriticGate` the engine's revise
  loop drives. `fold_answers` stays a resume-time resolver service. Flag-gated +
  parity where the output shape is meant to be unchanged.

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

## Phase 6 — Collapse the flags (decommission the scaffolding) *(sketch)*

**Why this phase exists.** Every phase adds a feature flag so earlier behavior
stays runnable and each phase boundary is checkout-able — the right call *during*
an unmerged migration. But the flags are **temporary scaffolding, not permanent
optionality**; left unmanaged they calcify into a combinatorial matrix of
untested cross-products, doubled maintenance, and a confusing surface. Phase 6
is the tracked teardown so that never happens: the migration ends with **one
path**, not N. It runs last, after every new path is proven end-to-end on a
daemon-bearing host (the same host the deferred 3b/Ralph verification needs).

**Not all flags are scaffolding — classify before deleting:**

| Flag | Fate | Sunset criterion |
|---|---|---|
| `LOOP_ENGINE_ENGINE=langgraph` | **Delete** (langgraph becomes the engine) | LangGraph path verified end-to-end on a real run; parity harness has held across all of P4/P5. Then flip default → delete `run_loop` + the classic-vs-graph parity harness. |
| `LOOP_ENGINE_TOOLS=mcp` | **Delete** (MCP becomes the tool path) | MCP tool path verified against a real coder-tools server run. Then flip default → delete the in-process `CODER_TOOLS`/`_execute_tool` dispatch. |
| `LOOP_ENGINE_CODER=ralph` | **Delete classic** (Ralph becomes the Coder) | Ralph verified to *actually converge at acceptable cost* on a real multi-sprint run on a host (the deferred verification). Then flip default → delete `CoderIacPersona` + `CoderGate` + the classic per-sprint targeted-re-entry logic. **Note:** classic has no parity-oracle value for Ralph (Ralph is intentionally different), so its *only* justification is "known-good fallback until Ralph is proven" — the moment Ralph is proven, classic is pure bloat. |
| `LOOP_ENGINE_ISOLATION` | **Keep** (genuine runtime config) | Not old-vs-new: `none` for local dev, `container` for the factory host. Stays permanently. |

**Also collapses here:**
- The **dual-field `artifacts`/`artifact_refs` strip** (cross-cutting #1) — once
  `run_loop` is gone, the LangGraph engine is the sole reader, so the inline
  bodies drop and `State` becomes truly thin (bump `schema_version` + extend
  `migrate_state_payload`).
- Any **flag-branching in `loops/default/loop.py`** (Ralph-vs-classic stage
  wiring, manifest-gate selection) collapses to the single surviving wiring.

**Discipline:** each deletion is its own dedicated, green commit (flip default →
remove the dead path + its tests/flag in one reviewable change), never bundled
with feature work. A path is only deleted *after* its replacement is verified on
a host — Phase 6 removes proven-redundant scaffolding, it does not take the
migration's remaining risk.

**Open questions:** does any flag deserve to survive as a documented escape
hatch (e.g. a "classic engine" break-glass) rather than full deletion? Is the
verification bar per-flag or one big end-to-end factory run that clears several
at once?

## Cross-cutting follow-ups (don't lose these)

1. **Drop the inline `artifacts` body-dict** once the LangGraph engine is the
   sole reader (completes the 1c "strip" — makes state truly thin). **Now scoped
   into Phase 6** — it can only happen after `run_loop` is deleted.
2. **state-io + github MCP servers** (deferred from Phase 2) — Phase 5's
   bootstrapping needs the github one.
3. **Full `.mcp.json`-driven multi-server discovery** (mechanism exists).
4. **Ralph cap-exhaustion → escalate, not fail.** Part-1 v1 hard-fails
   (`FAILED_STAGE` snapshot) when the Ralph loop hits its iteration cap while
   still making progress; a nicer behavior is to file a human issue ("did not
   converge") instead. Deferred so `execute_stage` stays generic for now.
5. **Real Ralph-run convergence/cost is unverified on this branch** (no LLM key
   + no container runtime here) — deferred to a live host run, recorded in
   `sprints/DEFERRED_VERIFICATION.md`.

## How to run / verify

```bash
hatch run test            # full suite (215 after P1, 226 after P2, 246 after P3a, 279 after P3b)
hatch run lint && hatch run format && hatch run audit && hatch run sbom
LOOP_ENGINE_ENGINE=langgraph  hatch run test tests/core/test_graph_engine.py
LOOP_ENGINE_TOOLS=mcp         hatch run test tests/tools/test_mcp_provider.py
```
