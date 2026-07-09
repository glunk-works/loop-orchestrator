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
| 4 · part 1 — Ralph-loop Coder (`AgenticNode`) | ✅ built behind flag, reviewed; 4 review findings hardened in 4a (below). Plan: `sprints/19_ralph_coder/sprint_plan.md` | `195f7b7` |
| 4 · part 1a — Ralph hardening (review findings #6 (a)–(d)) | ✅ complete, reviewed; 3 HITL-review findings resolved (see "Sprint-19a HITL-review settlements"). Plan: `sprints/19a_ralph_hardening/sprint_plan.md` | `d675d5d` → review-fixes |
| 4 · part 2 — Declarative generators (`GeneratorNode`) + PM critic-gate | ✅ complete, reviewed; HITL-review findings resolved via sprint 21 review-fixes. 394 tests green. Plans: `sprints/20_declarative_generators/`, `sprints/21_declarative_review_fixes/` | `cf48b0c` → `aceb23a` → `03818d9` |
| 5 — Autonomous triggers + multi-repo factory | 🟨 22a complete, reviewed, archived. 22b (github MCP server capability slice) implemented — Tasks 1-5 green, pending HITL review. Next: plan Sprint 23 (trigger surface → maintenance flow → bootstrap flow). Plans: `sprints/22a_mcp_multiserver_discovery/`, `sprints/22b_native_github_server/` | `457f675` → `71f1692` → `d0e118d` → (22b, pending) |
| 6 — Collapse the flags (decommission the migration scaffolding) | ⬜ sketch only | — |

Phases 1–3b are detailed and executed (3b's daemon-host e2e is deferred, not
lost — see its plan). Phase 4's planning pass is done and it **split into two
separately-gated sub-phases, Ralph-Coder-first** (see the Phase 4 section and
decisions log below). Part 1 (Ralph Coder, `195f7b7`) is built + reviewed, and
its four review findings are hardened in **part 1a** (`sprints/19a_ralph_hardening/`).
**Part 2** (`GeneratorNode` + PM critic-gate, `sprints/20_declarative_generators/`)
is **built behind `LOOP_ENGINE_PERSONAS=declarative`** (default `classic`),
**reviewed, and its review findings resolved** (sprint 21 review-fixes, `03818d9`).
**▶ NEXT ACTION: Opus HITL review of Sprint 22b**, then **plan Sprint 23**
(trigger surface → maintenance flow → bootstrap flow). Sprint 22b (native
`github_server` + `tools/repo_io` delegate + committed `loop_engine.mcp.json`
github entry + `build_github_provider()`) is **implemented, Tasks 1-5 green**
(`sprints/22b_native_github_server/sprint_plan.md`) — the system's second MCP
server and its first credentialed one. The "cloning target repos introduces a
new git subprocess surface" open item flagged during 22a is **settled
gh-only**: all four factory verbs ride the existing `gh` executable, so
`repo_io` is a second `gh` consumer and adds **no** fourth subprocess surface
(the genuine local-git surface — `git push` inside a cloned tree — is
deferred to Sprint 23's maintenance flow). 22b ships the capability slice only
(server + delegate + committed config + provider helper + hermetic tests +
docs) — no production flow caller yet; that is Sprint 23's job. See the
"Phase 5 planning pass" + "sprint decomposition" subsections below for the
locked decisions.
All Phase-4 sub-phases are now built, reviewed, and their review findings
resolved (part 1a reviewed 2026-07-09). Phase 6
(below) is the tracked teardown that keeps the feature flags from calcifying
into permanent bloat.

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
  orchestrator-invoked, not model tools) and full `loop_engine.mcp.json`-file-driven
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
- **Phase 4 · part 2 build (locked, owner-confirmed 2026-07-08):**
  - **Persona config = PyYAML (owner reaffirmed over stdlib dataclasses).**
    Pinned `PyYAML==6.0.3` (CVE-clean); SBOM regenerated + `pip-audit` green.
    Loader is `yaml.safe_load`-only (asserted by test) — a hostile `!!python/*`
    tag fails to load rather than instantiating.
  - **PM escalation-shape change accepted as in-bounds (owner call).** Retiring
    the internal critic loop into a stateless `CriticGate` means a non-converging
    PM files **one combined** `execute_stage` escalation question (naming every
    blank/vague field) instead of N per-field questions. Documented, flag-gated,
    **NOT parity-claimed** on that path; the gate stays stateless (no loop state
    smuggled back). `fold_answers` on resume is unaffected (folds the free-text
    answer, never needed per-field granularity). Likewise the declarative
    multi-cycle path drops the `revision_history` trail (empty on the happy path
    in both modes — byte-parity holds there).
  - **Parity-preserving deviations from the plan's config sketch (documented):**
    (a) Architecture's config sets `extract_open_questions: false` — its markdown
    artifact *is* what the stage gate reads, so the gate extracts Open Questions
    exactly as classic; having the node also add them would diverge the produced
    `State`. Sprint Breakdown keeps it `true` (its gate sees only the parsed-JSON,
    so the node must lift questions). (b) Two config fields beyond the sketch:
    `prompt_style` (`cached` for Architecture/Sprint; `inline` for PM, matching
    the classic PM single-user-prompt call byte-for-byte) and `static_fields`
    (baseline keys like PM's `revision_history: []` so the clean-path JSON is
    byte-identical). (c) PM prompt files are numbered `00_pm_*` (PM is the first
    stage; `01_` is already `01_architecture_review_prompt.md`). (d) The on-disk
    `prompts/02`/`prompts/03` were regenerated to be **byte-identical to the
    personas' embedded `PROMPT_TEMPLATE`** (they previously differed only by
    line-wrapping) — required so the declarative node's `system_blocks` equal the
    classic persona's; a parity test now pins file==embedded both ways.
  - **`CriticGate` lives in `personas/pm/critic_gate.py`, not `core/`.** The
    import-boundary test forbids `core` importing any persona module but `base`,
    and the gate reuses `critic.review`; so it uses the `ManifestArtifactGate`
    pattern (a gate under `personas/` that imports `core.gates`). Core never
    imports it (the loop wiring does).
  - **Stage identity via thin subclasses.** The engine keys escalation counters
    and question `origin_stage` off `type(persona).__name__`; three identical
    `GeneratorNode` instances would collide. `ArchitectureGenerator` /
    `SprintBreakdownGenerator` / `PMGenerator` are one-line identity subclasses
    (all logic stays in `GeneratorNode`) giving each stage its own name.
- **Sprint-21 HITL-review settlements (owner-confirmed 2026-07-09):**
  - **Classic PM escalate-on-exhaustion is intentional, not inert.** The PM
    stage's `max_revisions=4` + `escalate_on_exhaustion=True` are live on the
    *classic* path too: its `ArtifactGate` returns REVISE on a
    missing/empty/invalid `project_spec`, so a non-converging classic PM now
    escalates to a human issue instead of hard-failing (`FAILED_STAGE`). The
    earlier "inert for classic — its gate never REVISEs" comment was wrong; a
    corrected comment + a pinning test
    (`test_classic_default_loop_pm_stage_escalates_on_exhaustion`) replace it.
    Deliberately *not* scoped to declarative — escalating a dead-end PM (its
    only resolver is the human) beats hard-failing on both paths.
  - **`key_merge` findings-accumulation accepted as in-bounds non-parity
    (review finding #4).** The engine accumulates findings across revision
    cycles — its *uniform* contract for every revise loop (`section_merge`,
    `full_reextract`, Coder/Ralph all share it); `_revise_key_merge` dedups only
    exact duplicates, so a 2nd+ PM revision's followup prompt can re-list a field
    already fixed in an earlier cycle. Classic's retired internal loop fed only
    the *latest* critic pass. Accepted, **NOT parity-claimed** (parity is the
    single-cycle happy path; multi-cycle is a declared replacement): a
    latest-only fix would be a special-case carve-out on shared infra (an
    engine-wide accumulation change → broad blast radius, or gate re-derivation
    inside the persona → boundary violation), both worse than the redundancy —
    and `key_merge` passes the *current artifact* alongside the findings, so a
    re-listed already-fixed field is reconciled against the spec, not a
    misdirection.
- **Sprint-19a HITL-review settlements (owner-confirmed 2026-07-09):** the
  Ralph-hardening pass (`d675d5d`) was reviewed; 3 findings, all fixed (flag-scoped
  to `LOOP_ENGINE_CODER=ralph`):
  - **`_upsert_task_section` orphaning (correctness).** Its terminator matched any
    `\n### `, so a model report body's own `### ` subheadings truncated the match
    mid-body and orphaned the tail — leaking stale content (including a resolved
    `## Edit Application Failures`, which could wedge the gate) across re-runs and
    defeating the idempotency finding (c) added. Fixed to key only off the section
    headers this module writes (`### Task ` / `### Regression fix`); pinned by a
    `### `-in-body test.
  - **`_repair` false-success ledger.** An escalating repair (one that raised Open
    Questions instead of fixing the suite) recorded a "Repaired…" memory lesson and
    a `### Regression fix` claim. Now branches its outcome on `new_questions` like
    `_task_increment`.
  - **Dependency name-matching precision (owner chose to tighten).** Bare
    single-word sprint names (`api`, `beta`) matched from incidental prose ("the
    public api"), reintroducing a milder version of the false-dep problem finding
    (b) fixed. Tightened to *distinctive* (underscore-bearing) tokens only — the
    full `NN_name` dir or a multi-word name; single words must be referenced by
    full dir or `Sprint N`/`#N`. Changed the deliberately-tested `beta`→sprint
    contract (test updated to a distinctive `data_layer` name + a false-positive
    negative test).

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
- `LOOP_ENGINE_PERSONAS=declarative` → the three document personas (PM,
  Architecture, Sprint Breakdown) become config-driven `GeneratorNode`s and the
  PM stage gate becomes `CriticGate` (default `classic` keeps the persona
  classes byte-identical). Composes with `LOOP_ENGINE_CODER`. *(Phase 4 · part 2.)*

## What exists now (key modules)

- `core/engine.py` — `execute_stage()` (shared per-stage primitive) + classic `run_loop`.
- `core/graph_engine.py` — LangGraph `StateGraph` engine; `tests/core/test_graph_engine.py` guards parity.
- `core/state.py` — schema v3, `ArtifactRef`, `migrate_state_payload` (v1/v2→v3).
- `tools/artifact_store.py` — `mirror_to_disk`, `get_artifact`, `has_artifact`.
- `tools/agent_state/` + `.agent/STATE.md`/`.agent/MEMORY.md` — semantic-state layer.
- `mcp_servers/coder_tools_server.py` — stdio MCP server (read/execute-only).
- `tools/mcp/` — `MCPToolProvider` (discovery + dispatch on a background event loop); Phase 3b `container_server_params`/`sandbox_server_params` + preflight (inert).
- `tools/isolation.py` — single reader of `LOOP_ENGINE_ISOLATION` (`none|worktree|container|sandbox`) + `IsolationUnavailableError`.
- `personas/declarative/` — Phase 4 · part 2. `mode.py` (single reader of `LOOP_ENGINE_PERSONAS`), `config.py` (`GeneratorConfig` + `yaml.safe_load` loader), `services.py` (the shared-services registry: input-wrappers / output-adapters / revision-styles / `resolve_via_document`), `node.py` (`GeneratorNode` + the three identity subclasses `ArchitectureGenerator`/`SprintBreakdownGenerator`/`PMGenerator`), `configs/*.yaml`. Prompts externalized to `prompts/` (byte-identical to the personas' embedded templates).
- `personas/pm/critic_gate.py` — `CriticGate`, the PM critic *checks* re-expressed as a structural stage gate (core-safe home, like `ManifestArtifactGate`).
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

### Part 2 — Declarative generators (`GeneratorNode`) + PM critic-gate — sprint 20 *(built behind flag)*

Built behind `LOOP_ENGINE_PERSONAS=declarative` (default `classic`). See
`sprints/20_declarative_generators/sprint_plan.md` and the Phase 4 · part 2
decisions above.

- **`GeneratorNode`:** one YAML-driven node (prompt file, model, max_tokens,
  consumes/produces, input-context+wrap, output-adapter, revision-style,
  optional resolver) replaces the per-class boilerplate of **Architecture,
  Sprint Breakdown, and PM**. The genuinely-varying logic is a registry of
  **shared services** in `services.py` (input-wrappers `none`/`untrusted`;
  output-adapters `markdown`/`sprint_blocks`/`json_object`; revision-styles
  `section_merge`/`key_merge`/`full_reextract`; `resolve_via_document`), each
  factored from the classic persona code so the accept-path output is
  byte-identical. Pinned PyYAML; SBOM regenerated, audit green.
- **PM critic-gate:** the `MAX_REVISION_CYCLES` loop inside `PMPersona.run` is
  retired; `critic.review()` is re-expressed as a structural `CriticGate` the
  engine's revise loop drives (its identical-findings→escalate is the
  no-progress detector). `fold_answers` stays a resume-time resolver service on
  `PMPersona`, outside the node. Parity on the clean-extraction path; a
  documented, flag-gated escalation-shape change otherwise (see decisions).
- **Verification:** unit-level against the fake-LLM harness (byte-parity of
  Architecture/Sprint artifacts + `task_manifest`, PM clean-path `project_spec`,
  `system_blocks`/revision-message equality, `untrusted` wrapper bytes,
  `CriticGate` decisions, cross-engine `run_loop`≡LangGraph). Live-run
  parity/cost deferred to `sprints/DEFERRED_VERIFICATION.md` §4.

## Phase 5 — Autonomous Triggers & Multi-Repo Factory *(planning underway)*

**Scope (four separable pieces, dependency-ordered):**
- **(1) github MCP server** — the deferred cross-cutting #2; both flows below need it.
- **(2) Trigger surface** — FastAPI webhook server; trigger a graph run on an issue
  labeled `agent-action` or a slash command in an issue comment.
- **(3) Maintenance flow** — clone + feature-branch worktree → absorb target repo's
  `CLAUDE.md` + `.agent/STATE.md` → on green gate, push branch and open a PR against
  `develop`. **Auto-merge stays prohibited.**
- **(4) Bootstrap flow** — `create_repository` in `glunk-works` → scaffold
  (`hatch new` / OpenTofu boilerplate) in a fresh worktree → inject global `CLAUDE.md`
  → commit/push.

### Phase 5 planning pass (locked 2026-07-09, Opus/Architect)

- **Foundation-first: the github MCP server is the first slice** (piece 1), built
  before the trigger/flows. Both flows stack on it; it is the lowest-risk, best-understood
  piece.
- **Native re-front, not the official GitHub MCP server.** Build `mcp_servers/github_server`
  mirroring `coder_tools_server`: it delegates to a `tools/` module (never calls `gh`
  directly), so the "only the GitHub-owning `tools/` module talks to GitHub" boundary
  holds. Rationale: this repo enforces *exact* tool-set invariants by static test —
  a native server can assert "exposes exactly `{create_repository, clone_repo,
  create_branch, open_pr}`"; the official server is a large, evolving, ~60-tool surface
  (incl. `merge_pull_request`, contradicting "auto-merge prohibited") that we don't
  control and can't fake offline in CI. We pay more code for the enforced-minimal,
  testable boundary the migration exists to protect.
- **Credential = `gh` CLI's own auth** (as `tools/issue_io` already does) — no new secret
  path, nothing touches the `tools/llm/client.py`-only-imports-keyring invariant. Infisical
  (available) is an **orthogonal** secrets-provider decision, **deferred** until the factory
  host needs non-interactive PAT auth. Note: a github server is nonetheless the system's
  **first credentialed MCP server** (unlike credential-free `coder_tools_server`).
- **Tool surface = factory verbs only** — `{create_repository, clone_repo, create_branch,
  open_pr}`. The existing `issue_io` escalation verbs (create/read/comment) **stay on their
  current direct path** (don't destabilize `resume --from-issue`); unify onto MCP in Phase 6.
- **Full `loop_engine.mcp.json`-driven multi-server discovery** (pays down cross-cutting #3), not a
  bespoke second provider. Two design constraints, both locked: **(a) consumer split** —
  the provider feeds the **model's** coder tool loop only; github verbs are
  **orchestrator-invoked** and must never enter that loop, so discovery is
  **consumer-scoped** (each consumer builds a provider for the servers *it* names).
  **(b) heterogeneous launch profiles** — coder-tools is sandboxed/no-network (runs
  untrusted model code, runtime-computed launch); github runs un-sandboxed with
  network + `gh` auth (trusted first-party code, static `loop_engine.mcp.json` spec). `loop_engine.mcp.json`
  is **optional** with a built-in `coder_tools` default so absence is byte-identical to today.
- **Config filename = `loop_engine.mcp.json` at repo root** *(revised 2026-07-09, Opus/Architect,
  during 22a implementation)*. The planning pass originally named this file `.mcp.json`, but
  repo-root `.mcp.json` is **already** Claude Code's own project MCP config (`{"mcpServers":
  {"github": …}}`, the devcontainer's hosted-github wiring, committed `65ed47c`) — a different
  schema and purpose, and a filename Claude Code reserves by convention. loop-engine takes a
  distinct, product-namespaced file (`loop_engine.mcp.json`) for its own stdio launch specs; the
  two never mix. (`.ai/mcp.json` was rejected: `.ai/` is the dev-workflow layer, not product
  runtime.)

### Phase 5 sprint decomposition (Phase 4 split precedent)

- **Sprint 22a — `loop_engine.mcp.json` multi-server discovery** *(implemented, all 5
  tasks green: `sprints/22a_mcp_multiserver_discovery/sprint_plan.md`)*. Pure client-side
  refactor of `tools/mcp` — config-driven, N-server, consumer-scoped provider. **No** new
  server / subprocess / credential / file-write surface (confirmed — no dependency added,
  SBOM unchanged). Load-bearing gate: **coder-tools parity**, held (existing
  `test_mcp_provider.py` isolation assertions pass unchanged). `MCPToolProvider` already
  did multi-session routing; the gap — discovery + scoping — is closed by
  `load_mcp_config`/`build_provider_for` and proven by `tests/tools/test_mcp_multiserver.py`
  (two-server discovery/routing) and `test_mcp_provider.py::test_extra_config_server_never_reaches_coder_provider`
  (consumer-scope guard).
  **HITL gate after 22a before 22b.**
- **Sprint 22b — native `github_server` + `tools/repo_io` delegate + `loop_engine.mcp.json` entry**
  *(implemented, all 5 tasks green: `sprints/22b_native_github_server/sprint_plan.md`;
  pending Opus HITL review)*. Ships the server (factory verbs), the GitHub-owning
  delegate module (new `tools/repo_io` sibling to `issue_io`; issue_io untouched), a
  **committed** repo-root `loop_engine.mcp.json` github stanza (the first real instance
  of that file), and the consumer-scoped `build_github_provider()` orchestrator helper
  — plus hermetic tests and the bidirectional coder⟂github scope guard
  (`tests/tools/test_mcp_provider.py`). **Open design item from 22a planning, now
  settled gh-only:** all four verbs ride the existing `gh` executable (`create_branch`
  via `gh api …/git/refs`, a remote ref) — `repo_io` is a **second `gh` consumer**, not
  a new subprocess surface; the "exactly three sanctioned surfaces" invariant holds,
  only its `gh` clause widens. The genuine local-git surface (`git push` inside a
  cloned tree) isn't needed by these four verbs and is deferred to Sprint 23's
  maintenance flow. **Capability slice only** — no production flow caller (no CLI
  subcommand, no loop wiring) until Sprint 23 chains the verbs. First real
  network+`gh`-auth server launch; live verification deferred to a daemon-bearing host
  (`sprints/DEFERRED_VERIFICATION.md`).
- **Sprints 23+ — trigger surface, then maintenance flow, then bootstrap flow** (pieces
  2→3→4), each separately planned + gated after the github foundation lands.

**Still-open questions (deferred to their sprints, not the github foundation):** webhook
auth model + where the server is hosted; org access to `glunk-works`; how runs are
queued/rate-limited.

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
| `LOOP_ENGINE_PERSONAS=declarative` | **Delete classic** (declarative becomes the personas) | Declarative ports verified on a real run to hold parity at acceptable cost. Then flip default → delete the classic `PMPersona`/`ArchitecturePersona`/`AgileSprintBreakdownPersona` `run()` bodies + their embedded prompt templates + the plain-`ArtifactGate` PM wiring, leaving the `prompts/` files as the sole source of truth. The classic classes have no parity-oracle value once declarative is proven. |
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
2. **state-io + github MCP servers** (deferred from Phase 2) — ✅ the github one
   **delivered as a capability** in 22b (`mcp_servers/github_server.py` +
   `tools/repo_io`, exactly `{create_repository, clone_repo, create_branch,
   open_pr}`); no production flow caller wires it into a run yet — Sprint 23.
3. **Full `loop_engine.mcp.json`-driven multi-server discovery** — ✅ mechanism
   generalized to N servers via `loop_engine.mcp.json` (22a: `load_mcp_config` +
   `build_provider_for`, proven by `tests/tools/test_mcp_multiserver.py`'s
   two-server discovery/routing test); `loop_engine.mcp.json`-declared static
   servers — ✅ the first (`github`) landed with 22b, **committed** at the repo
   root.
4. **Ralph cap-exhaustion → escalate, not fail.** Part-1 v1 hard-fails
   (`FAILED_STAGE` snapshot) when the Ralph loop hits its iteration cap while
   still making progress; a nicer behavior is to file a human issue ("did not
   converge") instead. Deferred so `execute_stage` stays generic for now. **Still
   open** — the Phase 4a repair increment (#6a) also terminates at the cap via
   `FAILED_STAGE`, so this deferral now covers the repair path too.
5. **Real Ralph-run convergence/cost is unverified on this branch** (no LLM key
   + no container runtime here) — deferred to a live host run, recorded in
   `sprints/DEFERRED_VERIFICATION.md`. Now includes the **self-healing** repair
   path (#6a): whether a real regression-repair increment converges at acceptable
   cost is part of the deferred live verification.
6. **Ralph code-review findings (`195f7b7`) — ✅ addressed in the Phase 4a
   hardening pass** (`sprints/19a_ralph_hardening/sprint_plan.md`), a dedicated
   green commit before sprint 20. All four are flag-scoped to `LOOP_ENGINE_CODER=ralph`:
   - **(a, most substantive) Ralph can't fix a cross-task test regression.** ✅
     `RalphCoderGate` now emits a distinct `RALPH_REGRESSION_PREFIX` finding when
     *every* manifest task is checked off but the suite is red; `RalphCoderPersona`
     routes that (no selectable task + regression finding) to a **repair increment**
     — one fresh-context tool loop scoped to fixing the regression, marking no task,
     upserting a single `### Regression fix` report section — instead of the
     escalate-when-blocked dead-end. The persona distinguishes this from an
     all-blocked-deps state purely by the gate's finding prefix (never by sniffing
     pytest output). Residual: cap-exhaustion still routes through `FAILED_STAGE`
     (see #4). Fix stayed persona/gate-local — no `execute_stage` change.
   - **(b) Spurious cross-sprint deps from incidental digits.** ✅
     `manifest._dependency_sprint_paths` no longer matches bare `\d+`; it matches
     sprint-qualified number tokens (`Sprint 3`, `#3`) or a sprint directory/name
     token (`01_ci_cd_foundation` / `ci_cd_foundation`) appearing whole in the
     `Dependencies:` field. The order-safe "nothing matched ⇒ immediately-preceding
     sprint" fallback is retained (strictly more conservative — can only remove
     spurious edges).
   - **(c) Duplicate report sections.** ✅ Report sections are now **upserted** by
     task id (`_upsert_task_section`): a re-run task (or repeated repair) replaces
     its `### Task <id>:`/`### Regression fix` block rather than appending a
     duplicate.
   - **(d) Only `findings[-1]` reaches the model.** ✅ The persona partitions
     carried findings into resolution answers (shared `RESOLUTION_FINDING_PREFIX`)
     and gate status, and composes the prompt from **all** resolution answers plus
     the **latest** status line — so a resolution answer survives every
     post-re-entry iteration while the prompt stays bounded and current.

## How to run / verify

```bash
hatch run test            # full suite (215 after P1, 226 after P2, 246 after P3a, 279 after P3b, 385 after P4·part2)
hatch run lint && hatch run format && hatch run audit && hatch run sbom
LOOP_ENGINE_ENGINE=langgraph    hatch run test tests/core/test_graph_engine.py
LOOP_ENGINE_TOOLS=mcp           hatch run test tests/tools/test_mcp_provider.py
LOOP_ENGINE_PERSONAS=declarative hatch run test tests/personas/declarative tests/loops/test_declarative_pipeline.py
```
