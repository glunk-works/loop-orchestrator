# Phase 3 — Execution Isolation (detailed plan)

Detailed planning pass for the roadmap's Phase 3 sketch
(`docs/migration_roadmap.md`). Read the roadmap first for context and the
locked decisions log; this file is the buildable spec.

Phase 3 splits into **3a (worktree isolation — build now)** and **3b
(container/sandbox isolation — spec the seam, defer the build)**. The split is
forced by an environmental fact and confirmed with the user (see Decisions).

## Decisions locked for Phase 3

| # | Decision | Rationale |
|---|---|---|
| D1 | **Root the run at the worktree by `chdir`**, via a per-run context manager — not by threading an explicit `root: Path` through the write/read APIs. | Everything already keys off `Path.cwd()` (state_io, coder_tools, artifact_store, the MCP server's `cwd` param). chdir needs ~zero signature changes, converges the MCP and in-process tool paths, and **auto-tightens the existing traversal/symlink checks to the worktree for free**. One run per process is already true (`cli.py`), so process-global cwd is fine. |
| D2 | **State snapshots stay in the orchestrator's main checkout**; only the produced artifact tree (`src/`, `docs/`, `sprints/`, `.agent/`) lives in the worktree. | Snapshots are orchestrator bookkeeping (already git-ignored). Keeping them out of the worktree means resume/cost-summary survive worktree cleanup and snapshots never land on a feature branch. The artifact tree *is* the run's product and belongs in the worktree (→ Phase 5 PR-per-run). |
| D3 | **No DinD, no DooD in this devcontainer.** 3b targets a daemon-bearing host (the Phase 5 factory), or a daemon-free rootless sandbox (`bwrap`/`nsjail`). Build 3a now; ship 3b as spec + a flag stub. | The devcontainer has no `docker`/`podman` and is itself an unprivileged container. DinD needs `--privileged`; DooD mounts the host socket (host-root-equivalent) into a process that *already runs untrusted model code in-process* — that **enlarges** the surface we're trying to shrink, and hits the bind-mount host-path footgun. |

**Honest scoping note.** 3a is **blast-radius / organizational isolation**, not
a security sandbox: on the default (in-process) tools path, model-generated
code still executes in the orchestrator process with the user's privileges —
chdir only confines *where files land*. The actual security boundary (untrusted
execution out of the orchestrator process) is **3b**. Nobody should over-trust
3a.

---

## Phase 3a — Worktree isolation (build now)

**Goal.** Every run executes against its own git worktree on a per-run ref; the
model-facing artifact tree is confined to that worktree via chdir; State
snapshots remain in the main checkout; worktrees are retained where a run may
resume and prunable otherwise. Gated by a new flag, default off, so the phase
boundary stays checkout-able (consistent with `LOOP_ENGINE_ENGINE` /
`LOOP_ENGINE_TOOLS`).

**Flag.** `LOOP_ENGINE_ISOLATION` — enum `none` (default) | `worktree`.
(3b later extends this with `container` | `sandbox`.)

### New module: `tools/worktree/manager.py`

A new **sanctioned subprocess surface** (`git worktree`), joining `gh`
(issue_io) and `pytest` (coder_tools) — fixed argv, `shell=False`, `run_id`
validated with the existing `_validate_safe_name` before it reaches git.

API:

- `worktree_path(run_id) -> Path` — `<worktree_root>/<run_id>`, where
  `worktree_root` defaults to `.worktrees/` under the main checkout and is
  overridable via `LOOP_ENGINE_WORKTREE_ROOT`.
- `create(run_id) -> Path` — `git worktree add <path> -b loop/<run_id> HEAD`
  (idempotent: if the path already exists and is a registered worktree, reuse
  it; this is what resume relies on).
- `cleanup(run_id)` — `git worktree remove --force <path>` + delete the branch.
- `@contextmanager worktree_run(run_id, *, reuse: bool)` — the single
  integration seam. On enter: capture the orchestrator home (original cwd),
  `create` (or reuse) the worktree, `os.chdir(worktree)`. On exit: `os.chdir`
  back **in a `finally`** (must restore even on exception), then apply the
  retention policy. When `LOOP_ENGINE_ISOLATION != worktree` it is a no-op
  passthrough (no chdir, no worktree) so the default path is byte-identical to
  today.

**Retention policy** (tunable; stated so review can veto):
- `awaiting_issue` → **retain** (the run resumes here; artifacts must survive).
- `completed` → **retain** (Phase 5 opens a PR from it).
- `failed_stage` / `budget_exceeded` → **retain** for inspection; prunable via a
  new `loop-engine prune-worktrees [--older-than] [--status]` command.

Rationale for retain-by-default: a worktree is cheap (shared object store) and
losing a resumable/inspectable run is expensive. Pruning is explicit.

### Snapshot anchoring (D2)

`write_state_snapshot` must not follow the chdir. Minimal change that keeps the
single-writer boundary intact: state_io grows a module-level **state root**
(`set_state_root()` / `state_root()`, defaulting to `Path.cwd()` at import).
`worktree_run` sets it to the captured orchestrator home on enter and restores
on exit; `write_state_snapshot` builds `state_root() / "state" / run_id`
instead of `Path("state") / run_id`. When isolation is off, `state_root()` ==
cwd → identical behavior. This touches exactly one writer function, not the
~80-site artifact surface.

`mirror_to_disk` → `write_artifact` is deliberately left chdir-following, so
`docs/artifacts/<run_id>/…` lands **in the worktree** (correct: artifacts are
the product).

**Invariant to document:** artifact refs in a snapshot are *relative*
(`docs/artifacts/<run_id>/…`), resolved against cwd at read time. So
`artifact_store.get_artifact` reads are only valid **inside the worktree
context**. Resume re-enters that context (below); `cost-summary` doesn't read
artifacts, so it's unaffected. This dependency matters for the deferred inline-
artifacts strip (cross-cutting follow-up #1) — note it there.

### Tool paths: no change needed (the payoff of D1)

- **MCP path:** the Coder already launches the server with `cwd=Path.cwd()`
  (`persona.py:65` → `coder_tools_server_params`). Under chdir that *is* the
  worktree. Zero change.
- **In-process path:** `resolve_tool_path` compares against `Path.cwd()`
  (`coder_tools/__init__.py:82`). Under chdir that confines reads/writes to the
  worktree automatically.

Both tool paths tighten to the worktree with no code change — this is why D1
was chosen over root-threading.

### Integration point

`cli.py` `run` and `resume` wrap `_select_engine()(...)` in
`worktree_run(run_id, reuse=<resuming?>)`. Because the wrapper sits above engine
selection, **both** the classic and LangGraph engines inherit the worktree with
no engine code change. `run_id` is known before the call (freshly minted for a
new run; read from the loaded snapshot on resume).

### Resume semantics

- `resume --from-issue N` / `run --resume-from <path>`: load snapshot → `run_id`
  → `worktree_run(run_id, reuse=True)` re-chdirs into the existing worktree so
  relative artifact refs resolve.
- Worktree missing on resume (e.g. pruned): hard error with a clear message —
  the artifact tree is gone and cannot be reconstructed from the (thin)
  snapshot. This is why `awaiting_issue` retains (above).

### Files touched (3a)

- **new** `tools/worktree/manager.py` — the manager + context manager.
- **new** `tools/worktree/__init__.py` — public surface (`worktree_run`,
  `create`, `cleanup`, `worktree_path`).
- `tools/state_io/writer.py` — add `set_state_root`/`state_root`; anchor
  `write_state_snapshot`.
- `cli.py` — wrap `run`/`resume` in `worktree_run`; add `prune-worktrees`.
- `.gitignore` — add `.worktrees/`.
- `CLAUDE.md` — add `tools/worktree/` to the module map and list `git worktree`
  as a sanctioned subprocess surface in "Enforced module boundaries".
- `docs/migration_roadmap.md` — flip Phase 3a status, record decisions.

### Tests (3a)

- `tests/tools/test_worktree.py` (real git in a `tmp_path` repo):
  create → path under root; reuse is idempotent; `cleanup` removes worktree +
  branch; **cwd restored after an exception inside the context**; `run_id`
  traversal/invalid-name rejected (negative-input test for the new boundary).
- `tests/tools/test_state_root.py`: under a worktree context, `write_artifact`
  lands in the worktree while `write_state_snapshot` lands in the orchestrator
  home; with isolation off, both land in cwd (parity).
- Extend the subprocess-boundary test to allow `git` in `tools/worktree` only.
- Parity: rerun the engine-parity harness with `LOOP_ENGINE_ISOLATION=worktree`
  for **both** engines — outcomes identical to isolation-off.
- `tests/test_cli.py`: `run` under the flag creates a worktree and writes the
  snapshot to the main checkout; `resume` reuses the worktree; resume against a
  missing worktree errors clearly; `prune-worktrees` removes the right ones.

### 3a Definition of Done

Green `hatch run lint`/`format`/`test`/`audit`/`sbom`; new boundary
(`run_id` → git) has a negative-input test; no unjustified `# noqa`; docs +
CLAUDE.md updated; flag defaults off; **hard stop for HITL review** before 3b.

---

## Phase 3b — Container / sandbox isolation (spec the seam, defer the build)

> **Detailed buildable spec:** `sprints/18_execution_isolation_container/sprint_plan.md`
> (house sprint format, model-executable). This section is the design record;
> the sprint is the task-by-task build. **Resolved with the user (2026-07-08):**
> - **Primary substrate = docker/podman on a daemon-bearing host** (the Phase 5
>   factory host), reusing the `dev` Dockerfile stage. `bwrap`/`nsjail` is the
>   secondary daemon-free path.
> - **Build scope on this branch = the inert seam:** the argv builders
>   (`container_server_params`, `sandbox_server_params`), the runtime preflight,
>   provider selection, and honest-failure guards — all argv-shape unit-tested,
>   **nothing untrusted executed**. The real `docker run` end-to-end path + its
>   parity test are **deferred to a daemon-bearing host** (they cannot run in
>   this devcontainer: no runtime, and `unshare -Ur` → EPERM, so even `bwrap`
>   has no unprivileged userns here).

**Goal (when a runtime exists).** Untrusted execution (`run_tests`, and any
future code-exec tool) runs in a throwaway sandbox mounting **only** the active
worktree — no repo root, no keyring, no host paths — so the orchestrator process
never runs untrusted code in-process. The coder-tools MCP server becomes the
in-sandbox entrypoint.

**Two untrusted-execution surfaces, not one.** The boundary is a lie unless
*both* are moved out of process: (1) the Coder's `run_tests` MCP tool, and
(2) the **Coder gate's own deterministic pytest** (`core/coder_gate.py:69`,
`run_tests_tool.run_pytest`). The inert-seam sprint sandboxes (1)'s launch
params and **hard-guards (2)** — under `container`/`sandbox` the gate refuses to
run pytest in-process and raises, because routing the gate's pytest through the
sandbox is part of the deferred host-side build. A `container`-mode run that let
the gate execute model tests in-process would defeat the entire phase.

**Never silently degrade.** Selecting `container`/`sandbox` when no runtime is
present, or without `LOOP_ENGINE_TOOLS=mcp` (there is no server to sandbox on the
in-process tool path), raises `IsolationUnavailableError` — it must never fall
back to running untrusted code in-process.

**The seam we preserve in 3a so 3b is a drop-in.** All LLM-facing tool execution
already flows through the MCP provider abstraction
(`build_coder_tool_provider(cwd=…)` → `StdioServerParameters`). Discovery is
dynamic (`list_tools`) and dispatch is transport-agnostic, so the orchestrator
side needs **no change** for 3b — only the server *launch parameters* change:

```text
3a (now):     command=sys.executable, args=["-m", "...coder_tools_server"], cwd=worktree
3b container: command="docker"/"podman",
              args=["run","--rm","--network","none","--read-only",
                    "-v", f"{worktree}:{worktree}:rw", "-w", worktree,
                    "--cap-drop","ALL","--user","<nonroot>",
                    LOOP_ENGINE_DEV_IMAGE, "python","-m","...coder_tools_server"]
3b sandbox:   command="bwrap", args=["--unshare-all","--die-with-parent",
                    "--ro-bind","/usr","/usr", "--bind", worktree, worktree,
                    "--chdir", worktree, "python","-m","...coder_tools_server"]
```

Concretely 3b adds a `sandbox_server_params(worktree)` alongside
`coder_tools_server_params`, selected by `LOOP_ENGINE_ISOLATION`.

**Substrate.** The image is the **`dev` stage of the root `Dockerfile`** (already
carries hatch + pytest). For the container path, target a host with a **native**
daemon (the Phase 5 factory host) so the `-v worktree:worktree` bind uses a real
host path — this sidesteps the DooD host-path-translation footgun that makes the
current nested devcontainer the wrong place to run it.

**Daemon-free alternative** (`LOOP_ENGINE_ISOLATION=sandbox`): `bwrap`/`nsjail`
give process isolation without a daemon and work inside an unprivileged
container **if** unprivileged user namespaces are permitted. Verify
availability (`bwrap --version`; `unshare -Ur true`) before committing to build
it — noted as the first 3b task, not assumed.

**Explicitly out of scope now:** DinD, DooD-from-devcontainer, host-socket
mounts. See D3.

**Deferred to a daemon-bearing host** (out of scope for the inert-seam sprint):
- The real `docker run` end-to-end path + a live parity test (outcomes identical
  to isolation-off). Exercises the `-i`/no-`-t` stdio-framing requirement and the
  bind-mount ownership hazard (`--user {uid}:{gid}`) that can't be tested here.
- **Routing the Coder gate's pytest through the sandbox** — replaces the inert
  sprint's Task-4 guard; this is untrusted-exec surface (2) above.
- Network policy per tool (`run_tests` → `--network none`; a future dependency-
  install step would need egress — separate policy).
- Confirm gate evidence (pytest exit code) crosses the sandbox boundary back as
  MCP tool output with parity.
- `bwrap`/`sandbox` substrate: verify unprivileged userns on the target host
  (`unshare -Ur true`) before committing to build it — denied in this devcontainer.

---

## Sequencing & phase gate

1. Build 3a as its own green commit (per `branch-isolation-phase-gates`). ✅ `951e377`
2. **Hard stop for HITL review.** ✅
3. Build 3b's **inert seam** as its own green commit — the argv builders,
   runtime preflight, provider selection, and honest-failure guards (both
   untrusted-exec surfaces), argv-shape tested; **no sandbox/container code
   executes** (guarded to raise). ✅ done —
   `sprints/18_execution_isolation_container/sprint_plan.md`.
4. **Hard stop for HITL review.**
5. On a daemon-bearing host: replace the guards with the real `docker run` path +
   sandboxed gate pytest + a live parity test (the "Deferred" list above). No
   sandbox/container code executes until a runtime is chosen and verified.
