# CLAUDE.md

Lean routing layer for this repo — kept small and stable so it stays prompt-cached.
Day-to-day guardrails (commands, module boundaries, model routing) live here; the
heavy reference (module walkthrough, conventions, container setup) is in `.ai/context/`,
loaded on demand. **Where we are right now** lives in `.ai/next-steps.md`.

## What this is

loop-engine runs a named sequence of decoupled AI "persona" stages against a single, explicit, versioned `State` object. The default loop is a **PM → Architecture → Agile Sprint Breakdown → Coder/IaC** pipeline, but it is not a one-way conveyor: every stage's output passes a content **gate** (accept / revise / escalate), questions escalate up a resolver ladder (Coder → Architect → PM → human via GitHub issue), and resolved questions route rework back down by blast radius ("task" re-runs the asker, "plan" re-enters Sprint Breakdown, "architecture" re-enters the Architect). A snapshot is persisted after every accepted stage AND on every exit path (completed / failed / budget-exceeded / awaiting-issue).

> **Migration in progress — but the flag era is over.** The engine has migrated to
> MCP tooling + LangGraph + an isolated multi-repo factory. **Status, decisions, and
> the remaining work live in [`docs/migration_roadmap.md`](docs/migration_roadmap.md)** —
> read it before extending this. Phase 6 (sprint 27) **deleted** the four migration
> flags and the classic paths they selected, rather than keeping live break-glass
> branches (decision FD2 — a break-glass kept live is a path kept untested). There is
> now **one** path: the LangGraph engine, MCP tool dispatch, the declarative
> `GeneratorNode` personas + PM `CriticGate`, and the Ralph-loop Coder. The classic
> engine/tools/personas/Coder are recoverable in history at the **`pre-phase6-classic`**
> tag. **`LOOP_ENGINE_ISOLATION` survives** — it is genuine runtime config
> (`none` for local dev, `container` for the factory host), never old-vs-new.
> Still open in Phase 6: the `State.artifacts` strip (deferred — see the roadmap;
> it is a refactor, not a deletion) and the issue-path flip onto MCP (gated on the
> V3 host verification).

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

**Every sprint lands via a pull request — a merged PR is the human approval.** Work on a
`sprint/NN-slug` branch cut from `feat/mcp-langgraph-migration`; commit and push freely
there, then open a PR whose **base is `feat/mcp-langgraph-migration`** (not `main`). Post the
Opus HITL review on it with `gh pr review --comment` (**never `--approve`** — the human's merge
is the approval, and `gh` authenticates as the PR author anyway). **Never merge, and never
force-push a pushed branch.** Full protocol in `.ai/context/workflow.md`.

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
hatch run loop-engine run --resume-from state/<run_id>/01_ArchitectureGenerator.json
hatch run loop-engine resume --from-issue <N>   # after answering a paused run's GitHub issue
hatch run loop-engine cost-summary --run-id <run_id>
```

Exit codes from `run`/`resume`: 0 completed, 2 awaiting a GitHub issue answer, 3 budget exceeded.
(The `loop-engine resume` CLI subcommand is unrelated to the `/resume` dev-workflow skill.)

CI (`.github/workflows/ci.yml`) runs, in order: `lint` → `format-check` → `test` → `secrets-scan` (gitleaks) → `sbom`. All must pass; see `sprints/GLOBAL_DEFINITION_OF_DONE.md` for the full merge bar. The API key is **never** a CLI flag or env var — it comes only from the OS keyring (setup + fallback detail in `.ai/context/modules.md`).

## Enforced module boundaries

These are checked by static tests, not just convention — don't casually violate them:

- `core/` imports no concrete persona module, only `personas/base.py`. It is otherwise unrestricted on `tools/*`: `core/coder_gate.py` (Sprint 28) imports `tools/mcp` — scoped to that one file, no other `core/` module — so the `RalphCoderGate`'s evidence pytest run can dispatch through `tools/mcp.run_gate_pytest` (in-process on `none`/`worktree`, the sandboxed coder-tools provider on `container`/`sandbox`) instead of refusing under sandbox modes as `_raise_if_sandboxed` (deleted) once did.
- `tools/state_io` and `tools/scaffold` are the file-write-owning modules (`open`/`write_text`/`write_bytes`); everything else goes through `write_artifact`/`write_state_snapshot`. `tools/scaffold` (Phase 5 piece 4) is the **second** such surface — it writes a bundled skeleton (Python templates + the injected Global Conventions `CLAUDE.md`) into a foreign clone tree, validated via `repo_io._validate_clone_dest`; it imports no `subprocess`/`keyring`, so the five sanctioned subprocess surfaces below are unchanged.
- `tools/llm/client.py` is the only module that imports `keyring`.
- `tools/issue_io` and `tools/repo_io` are the GitHub-owning modules — `issue_io` files/reads human-escalation issues, `repo_io` is the repo/branch/PR factory (`create_repository`, `clone_repo`, `create_branch`, `open_pr`; no merge verb — auto-merge is prohibited). Both shell out to the already-authenticated `gh`; no other module talks to GitHub.
- `tools/coder_tools/` is read/execute-only: paths are traversal- and symlink-validated (reusing `state_io`'s validator); its `run_tests` pytest subprocess (also used by the Coder gate) is a sanctioned subprocess surface. It runs model-generated code — the operating assumption is the sandboxed devcontainer. `tools/coder_tools/run_lint.py` (Sprint 29) is a **second** subprocess surface in this module — `ruff check` + `ruff format --check` against a validated path, same containment (fixed argv, `shell=False`, hard timeout, output-capped). Unlike `run_tests`, ruff statically parses the target and never executes model-generated code, so it is strictly lower-risk; it stays in the model's Coder tool loop only, never a gate verb (gate-enforced lint is out of scope for Sprint 29).
- `tools/git_io` (Phase 5 piece 3) owns local-git working-tree writes (`checkout_branch`, `commit_all`, `push_branch`) plus a read-only `has_changes` probe (`git status --porcelain`, so a no-op run never reaches `commit_all`'s empty-index failure) in a **foreign** cloned tree — distinct from `repo_io` (shells `gh`, the remote GitHub API) and `worktree` (the orchestrator's own per-run isolation, keyed off `run_id`). It mirrors `tools/worktree/manager.py::_git`'s posture exactly (fixed argv, `shell=False`, a hard timeout, `check`-handling) and validates every `tree` argument by reusing `tools/repo_io/github.py::_validate_clone_dest`. `git push` rides `gh`'s clone-established credential helper — no `keyring` import, no new credential path.
- Sanctioned subprocess surfaces are exactly **five**, each fixed-argv and `shell=False`: `coder_tools`' `pytest`, `coder_tools`' `ruff` (Sprint 29, `run_lint.py` — statically parses, never executes model-generated code), `issue_io`'s **and `repo_io`'s** `gh` (two consumers of the same surface — `repo_io` adds no sixth), `tools/worktree`'s `git worktree` (args derive only from a `validate_run_id`-checked run_id), and `tools/git_io`'s local `git` (args derive only from a `_validate_clone_dest`-checked tree). Nothing else shells out (`tests/tools/test_subprocess_surfaces.py`). The Phase 3b container/sandbox launch is **not** a sixth surface: it is spawned by the MCP `stdio_client` (the same mechanism that launches the local coder-tools server — only `command`/`args` differ), and runtime detection uses `shutil.which`, not a subprocess.
- `mcp_servers/` re-front native tools over MCP: `coder_tools_server` (read/execute-only, delegating to `tools/coder_tools` with the same path validation and no credentials), `github_server` (delegating to `tools/repo_io`, exposing exactly the four factory verbs, no credentials — `repo_io` shells to `gh`'s own auth), and — since Sprint 26 — `issue_io_server` (a **third** native server, delegating to `tools/issue_io`, exposing exactly the two human-escalation verbs `{create_issue, read_issue}`, no credentials — `issue_io` shells to `gh`'s own auth, the same already-sanctioned surface). Tool execution runs in the server subprocess, out of the orchestrator process entirely — the boundary is moved, not relaxed. Since Phase 6 (sprint 27) this is the **only** coder-tool path: `LOOP_ENGINE_TOOLS` and the in-process `CODER_TOOLS`/`_execute_tool` dispatch are deleted, so the model's tools are always sandboxable and there is no unsandboxed fallback to refuse. `tools/mcp` is the client side (discovery + dispatch) and imports no keyring/writes no files. Server discovery is config-driven and consumer-scoped: `tools/mcp/config.py` reads a repo-root **`loop_engine.mcp.json`** (distinct from Claude Code's own `.mcp.json`; committed, declaring the `github` and — since Sprint 26 — `issue` servers) into logical-name → launch-spec, and `build_provider_for(names, ...)` builds a provider for **only** the named servers, so a consumer only ever sees the tools of the server(s) it asked for. The coder-tools server exposes exactly `{read_file, list_files, grep, run_tests, run_lint}` (Sprint 29 adds `run_lint`), the github server exposes exactly `{create_repository, clone_repo, create_branch, open_pr}`, and the issue server exposes exactly `{create_issue, read_issue}` — the three sets are asserted **pairwise disjoint** (`tests/tools/test_mcp_provider.py`). The github and issue verbs are **orchestrator-invoked only**, reached solely through `build_github_provider()`/`build_issue_provider()` — they never enter the model's coder tool loop. Sprint 26 also threads an injectable `issue_filer` write seam (`core/engine.py`'s `execute_stage`/`_pause_for_issue`, forwarded by `run_graph_loop`) and an injectable reader seam (`cli.py`'s `resume --from-issue`) — both default to the classic direct `issue_io` calls; the MCP route is capability-only here, **not** the runtime default, and no new feature flag governs it (mirrors 22b's github posture — see `docs/migration_roadmap.md` Phase 6).
- Any change touching `State` must keep `schema_version` accurate (bump it and extend `migrate_state_payload` for breaking shape changes) and keep `extra="forbid"` intact.
- `trigger/` (Phase 5 piece 2) is a new top-level **orchestrator-level caller**, a sibling of `cli.py` — it may import `core`/the default loop/`State`/`LLMClient`/`worktree` (via the shared `runner.py`), but is not a `tools/` module and not an MCP server. Its boundary posture, asserted by `tests/trigger/test_boundaries.py`: imports no `keyring`, writes no files directly, and adds **no subprocess surface** — dispatch (`trigger/dispatch.py`'s `InProcessDispatcher`) runs the loop in-process on a worker thread. The webhook's HMAC secret comes from `LOOP_ENGINE_WEBHOOK_SECRET`, an **env var**, not the keyring — it authenticates an inbound request, not an outbound LLM call, so it is a distinct credential class from the keyring-only Anthropic key.
- `flows/` (Phase 5 piece 3) is another new top-level **orchestrator-level caller**, a sibling of `cli.py`/`trigger/`. `flows/maintenance` chains `repo_io.clone_repo` → `git_io.checkout_branch` → `runner.run_in_tree` (the default loop, cwd pinned to the clone, **not** `worktree_run` — the clone is its own isolation boundary) → a **completion** guard (the inner run must end `COMPLETED`; a `FAILED_STAGE`/`BUDGET_EXCEEDED`/`AWAITING_ISSUE` run short-circuits to `run_incomplete` so a human-paused tree is never shipped) → a **no-change** guard (`git_io.has_changes`; a no-op run short-circuits to `no_changes`) → a green gate (`coder_tools.run_tests` on the clone) → **green-only** `git_io.commit_all`/`push_branch` + `repo_io.open_pr` (base defaults to `develop`); a non-completed run, an empty diff, or a red gate ⇒ no commit/push/PR. `open_pr` stays the terminal GitHub call — no merge verb exists, so auto-merge is impossible here too. Its boundary posture, asserted by `tests/flows/test_boundaries.py`: imports no `keyring`, writes no files directly, and adds **no subprocess surface of its own** — the one new surface, `tools/git_io`'s local `git`, is *called*, not introduced by `flows/`.
- `flows/bootstrap` (Phase 5 piece 4) is a sibling of `flows/maintenance` — the factory verb that brings a new, conventions-conformant repo into *existence*: `repo_io.create_repository` → `repo_io.clone_repo` (empty tree) → `git_io.checkout_branch(main)` → `tools/scaffold.write_skeleton` → `git_io.commit_all`/`push_branch(main)` → `repo_io.create_branch(develop, base=main)` (ordering is load-bearing — `create_branch` reads the base ref's SHA over the API, so it runs only *after* the push). Deliberately **no** inner loop (`run_in_tree`), **no** green gate, and **no** `open_pr` — a brand-new repo has nothing to PR into; auto-merge stays impossible. Same boundary posture as `flows/maintenance`: no `keyring`, no direct file write, no subprocess surface of its own (asserted by `tests/flows/test_boundaries.py`).

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
