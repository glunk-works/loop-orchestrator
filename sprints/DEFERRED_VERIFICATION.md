# Deferred verification: real-key smoke runs (Sprints 09–14)

The token-efficiency sprints (09–14) are implemented and verified against the mocked
test suite (`hatch run test`: unit + integration, exact transport call counts, lint,
format, pip-audit, SBOM). Two smoke checks require a real Anthropic API key and were
deliberately deferred — run them in the devcontainer before relying on the new
behavior in anger:

## 1. Caching + USD budget smoke (validates Sprints 10–12)

```bash
hatch run loop-engine run --input <small requirements doc> --budget 0.50
hatch run loop-engine cost-summary --run-id <run_id>
```

Expected observations:

- `cost-summary` shows nonzero, plausible `Cost (USD)` per stage (rate table live,
  no longer the 0.0 placeholder).
- With a spec large enough that the Architect/Coder prefix exceeds Sonnet 5's
  ~2048-token minimum cacheable size, `Cache R` is nonzero on Coder rows (sprints
  2..N) and on any gate-revision retry.
- **If every `Cache R` is 0**, a silent cache invalidator crept in: diff the system
  blocks between two calls — they must be byte-identical (state-derived content
  only; findings/sprint plans belong in the user turn).
- Note: recorded cost uses standard Sonnet 5 rates ($3/$15 per MTok); through
  2026-08-31 real spend is at introductory rates ($2/$10), so `cost_usd` slightly
  overstates the bill until then (see `tools/llm/pricing.py`).

## 2. Agentic Coder end-to-end (validates Sprints 13–14)

A full run in the devcontainer (sandbox assumption for `run_tests` — generated code
executes with the invoking user's privileges):

```bash
hatch run loop-engine run --input <small requirements doc> --budget 5.00
```

Expected observations:

- The Coder trace shows tool_use rounds (`read_file`/`list_files`/`grep`/`run_tests`)
  rather than single-shot responses.
- Files land under `src/` via applied `### FILEPATH:`/SEARCH-REPLACE blocks; the
  Coder stage only ACCEPTs after the gate's own pytest run is green (exit 5 — no
  tests collected — forces a REVISE).
- `cost-summary` shows heavy `Cache R` on the Coder stage: the cached prefix is
  re-read on every tool-loop iteration.

## 3. Ralph-loop Coder convergence + cost (validates Sprint 19, `LOOP_ENGINE_CODER=ralph`)

The Ralph loop's *mechanism* is verified against the mocked suite (incremental
task selection, coverage-aware gate, dependency ordering, `.agent/` checklist +
memory, cross-engine parity). What a mocked LLM cannot show is whether a real
Ralph run **actually converges** — finishes a multi-sprint project one task at a
time — and at what cost. That needs a real key and, for a real security boundary,
a container runtime (absent in this devcontainer). Run on a daemon-bearing host:

```bash
LOOP_ENGINE_CODER=ralph hatch run loop-engine run --input <small requirements doc> --budget 5.00
hatch run loop-engine cost-summary --run-id <run_id>
```

Expected observations:

- The Sprint Breakdown emits a `task_manifest` artifact; the Coder advances **one
  task per iteration** (each with a fresh tool-loop context), checking tasks off
  in `.agent/STATE.md` and appending a lesson to `.agent/MEMORY.md` per increment.
- The run reaches `completed` only when **every** manifest task is checked off and
  the gate's pytest is green — a green-but-incomplete tree keeps looping (REVISE),
  it does not ACCEPT early.
- Termination is bounded: a non-converging run stops at the iteration cap
  (`LOOP_ENGINE_RALPH_MAX_ITERS`, default 30) with a `FAILED_STAGE` snapshot, at
  the USD budget (`BUDGET_EXCEEDED`), or escalates on repeated identical failing
  findings (no-progress guard) — it never spins unbounded.
- **Self-healing (Phase 4a, `sprints/19a_ralph_hardening/`):** if a later task
  regresses an earlier task's test, the run does **not** dead-end — once every
  task is checked off but the suite is red, the gate emits a regression finding
  and the Coder runs a **repair increment** until green (bounded by the same cap
  + budget). What a mocked LLM cannot show is whether a real repair increment
  actually diagnoses and fixes a genuine regression at acceptable cost — verify
  this on the host run (introduce a deliberate cross-task regression and confirm
  the loop recovers rather than escalating to a human issue).
- **Sandboxing — CLOSED by sprint 28.** Both Coder gates' verification pytest now
  routes through the MCP container sandbox via `tools/mcp.run_gate_pytest`, the
  same mechanism the `run_tests` *tool* already used (Phase 3b); `_raise_if_sandboxed`
  is deleted. This was finding **F-GATE-SANDBOX** below. The remaining obligation is
  *host* re-verification — a real container-sandboxed gate run reaching ACCEPT →
  `COMPLETED` — carried by sprint 27's V1(complete)/V2, not a code gap.
- **Per-task test selection — still OPEN.** The gate still gates on the whole
  `src/` suite going green, not the single task's tests. Unaffected by sprint 28;
  remains a future improvement.

## 4. Declarative personas parity + cost (validates Sprint 20, `LOOP_ENGINE_PERSONAS=declarative`)

The `GeneratorNode` ports of PM / Architecture / Sprint Breakdown are verified
against the mocked suite: byte-parity of the produced `architecture_definition`,
`sprint_plans`, and `task_manifest` classic-vs-declarative for identical fake
responses; PM clean-path `project_spec` equality; identical `system_blocks` and
three-turn revision messages; the `untrusted` wrapper bytes; `CriticGate`
REVISE/ACCEPT decisions and the key_merge fill; and cross-engine equivalence
(`run_loop` vs LangGraph). What a mocked LLM cannot show is whether a **real**
run stays parity in practice and at what cost. Run on a real key:

```bash
LOOP_ENGINE_PERSONAS=declarative hatch run loop-engine run --input <small requirements doc> --budget 5.00
hatch run loop-engine cost-summary --run-id <run_id>
```

Expected observations:

- The produced `docs/architecture_definition.md` / `sprints/*/sprint_plan.md` are
  indistinguishable from a `classic` run over the same input (same prompts, same
  adapters/merge), and PM's clean-path `project_spec` matches.
- `Cache R` on the Architecture/Sprint rows is nonzero on any revision retry —
  the declarative node builds `system_blocks` from immutable config + state only,
  so the cached prefix must stay byte-stable across attempts (same guard as §1).
- **PM escalation-shape (documented behavior change, NOT parity-claimed):** a
  non-converging PM files **one combined** human-issue question naming every
  blank/vague field (via `execute_stage`'s no-progress→escalate), not N per-field
  questions; the declarative multi-cycle path carries **no** `revision_history`
  trail (empty on the happy path in both modes). Confirm the combined question is
  answerable and `fold_answers` on resume still folds the free-text answer.
- `declarative` × `ralph` compose: run with both flags set and confirm the
  pipeline reaches the Ralph Coder with byte-identical upstream artifacts.

## 5. `github_server` live launch + factory verbs (validates Sprint 22b)

The `mcp_servers/github_server` re-front is verified hermetically: real-server
discovery (`list_tools`, offline — no `gh`/network) asserts exactly
`{create_repository, clone_repo, create_branch, open_pr}`; the `tools/repo_io`
delegate's argv-building and stdout parsing are verified with `_run_gh` mocked;
and the bidirectional coder⟂github consumer-scope guard
(`tests/tools/test_mcp_provider.py`) is proven with the real committed
`loop_engine.mcp.json`. What none of that exercises is a **real, authenticated
`gh`** round-trip — this devcontainer has no `gh` auth and no network. Run on a
daemon-bearing host with `gh auth status` green:

```bash
python -m loop_engine.mcp_servers.github_server &  # or launch via build_github_provider()
```

Exercise each of the four verbs against a disposable scratch repo/org:

- `create_repository` — creates a real (private) repo; confirm the returned
  `RepoRef.url` resolves.
- `clone_repo` — clones it to a validated `dest`; confirm the working tree lands
  and a traversal/symlink-escaping `dest` is still rejected pre-`gh`-call.
- `create_branch` — creates a remote ref off the repo's default branch (no
  `base` given) and off an explicit `base`; confirm both via `gh api
  repos/{owner}/{repo}/branches`.
- `open_pr` — push a commit to the new branch (out of scope for `repo_io` itself
  — do this with plain `git`/`gh` in the test harness), then `open_pr` and
  confirm the returned `PullRef.url` resolves and **no merge verb exists** to
  auto-merge it.

Clean up the scratch repo afterward — this check has real side effects on
GitHub, unlike every other check in this file.

## 6. Trigger surface live webhook → real run (validates Sprint 23)

Sprint 23's coverage is entirely hermetic: `TestClient` deliveries against
`create_app(dispatcher=fake)` prove HMAC verify → parse → dispatch end to end,
but `InProcessDispatcher` is only ever exercised with `runner.run_new` patched
(no real loop ever runs in CI), and no port is bound. What none of that shows
is a real GitHub delivery reaching a real, listening server and driving a real
default-loop run. Run on a daemon-bearing host (this devcontainer cannot bind
a port reachable from GitHub):

- **Stand up the server.** No `uvicorn` pin shipped in 23 (deferred with
  hosting) — install it ad hoc for this check (`pip install uvicorn`) and run:
  ```bash
  LOOP_ENGINE_WEBHOOK_SECRET=<real random secret> \
    uvicorn loop_engine.trigger.app:app --host 0.0.0.0 --port 8000
  ```
- **Register a real webhook** on a disposable scratch repo pointed at the
  host's reachable address (tunnel it — e.g. `ngrok` — if the host has no
  public IP), content type `application/json`, secret matching
  `LOOP_ENGINE_WEBHOOK_SECRET`, subscribed to the `issues` and
  `issue_comment` events.
- **Deliver a real signed `agent-action` label event** — label an issue
  `agent-action` — and confirm: GitHub's webhook UI shows a `202` response;
  the server log shows `run starting for <repo>#<issue>`; a `state/<run_id>/`
  directory appears with the run's snapshots; the run actually executes the
  default loop against the issue's title+body as `human_input`.
- **Deliver a real `/agent-run` comment** on a second issue and confirm the
  same, plus that a redelivery (GitHub's "Redeliver" button) while the first
  run is still active is dropped (no second run), per the in-memory dedupe.
- Tear down the tunnel/server and delete the scratch webhook afterward.
- **(23a) Also confirm the bad-body path**: a delivery whose content type is
  misconfigured as `application/x-www-form-urlencoded` (so the raw body is
  not valid JSON) but still correctly signed should observe a `400` response
  in GitHub's webhook UI, not a `500`.

## 7. Maintenance flow live clone → run → gate → push → PR (validates Sprint 24)

Sprint 24's coverage is entirely hermetic: `tests/flows/maintenance/test_flow.py`
fakes every collaborator to prove call order/gating, and
`test_integration.py` exercises real `tools/git_io` against a `tmp_path` repo
+ a local bare remote — but `repo_io.clone_repo`/`open_pr` and the loop run
are always faked; no real `gh repo clone`, no real default-loop run with
`gh` auth + network, and no real push/PR happen in CI. Run on a daemon-bearing
host with `gh` authenticated and network access:

- **Clone a real disposable scratch repo** via
  `flows.maintenance.run_maintenance` with all collaborators at their real
  defaults (`repo_io`, `git_io`, `runner.run_in_tree`, `coder_tools.run_pytest`)
  — confirm the clone lands at the request's `dest` and `git_io.checkout_branch`
  actually cuts the branch in that real tree.
- **Confirm the inner run absorbs the target's own `CLAUDE.md` +
  `.agent/STATE.md`** — seed the scratch repo with both before the run and
  confirm the default loop's personas see them (cwd is the clone, per
  `run_in_tree`).
- **Green path:** seed the scratch repo so its `src/` test suite passes,
  confirm the flow pushes the branch to the real remote (`git ls-remote
  --heads` against the real GitHub remote) and opens a real PR against
  `develop` (confirm `PullRef.url` resolves) — and that no merge verb is ever
  reachable (`repo_io` exposes none).
- **Red path:** seed the scratch repo so its test suite fails, confirm
  **nothing** is pushed and no PR is opened.
- **Confirm `run_in_tree` never opens `worktree_run`** even with
  `LOOP_ENGINE_ISOLATION=worktree` set on the host — the loop's artifacts
  should land in the clone, not `.worktrees/<run_id>`.
- Clean up the scratch repo (and any opened PR/branch) afterward — this check
  has real side effects on GitHub, unlike every other check in this file.

## 8. Bootstrap flow live create → clone → scaffold → push `main` → create `develop` (validates Sprint 25)

Sprint 25's coverage is entirely hermetic: `tests/tools/scaffold/test_writer.py`
proves `write_skeleton` against a `tmp_path` tree (incl. the `pkg_name`
sanitization/traversal negative tests and the `CLAUDE.md` byte-identity guard),
`tests/flows/bootstrap/test_flow.py` fakes every collaborator to prove the
chain's call order, and `tests/flows/bootstrap/test_integration.py` exercises
real `tools/scaffold` + real `tools/git_io` against a `tmp_path` repo + a local
bare remote — but `repo_io.create_repository`/`clone_repo`/`create_branch` are
always faked; no real `gh repo create`, no real clone, no real push, and no
real `develop` branch creation happen in CI. Run on a daemon-bearing host with
`gh` authenticated and network access, and with resolved org access to
`glunk-works` (still an open hosting question — the org may not exist yet;
confirm access or substitute a disposable scratch org before running this
check):

- **Run `flows.bootstrap.run_bootstrap`** with all collaborators at their real
  defaults (`repo_io`, `git_io`, `tools/scaffold`) against a disposable scratch
  repo name — confirm `create_repository` actually creates a private repo,
  `clone_repo` lands a real empty working tree, and the returned `RepoRef.url`
  resolves.
- **Confirm the skeleton is really there.** In the real clone, confirm
  `pyproject.toml`, `src/<pkg_name>/__init__.py`, `tests/test_smoke.py`,
  `README.md`, `.gitignore`, and `CLAUDE.md` all exist with the repo/package
  name substituted, and that a real `pytest`/`ruff check`/`ruff format --check`
  pass against the scaffolded skeleton on its own (proving the bundled
  templates are actually coherent, not just individually unit-tested).
- **Confirm the empty-clone branch mechanics.** Verify the fresh clone's
  initial branch name (whatever the host's `init.defaultBranch` is) and that
  `checkout_branch(tree, "main")` still succeeds and produces a `main` branch
  regardless of that starting name.
- **Confirm the push + `develop` ordering against the real remote.** After the
  run, confirm (via `gh api repos/{owner}/{repo}/branches`) that both `main`
  (with the scaffold as its first commit, and set as the repo's default
  branch) and `develop` (based on `main`'s pushed SHA) exist, and that
  `develop` could only have been created after the push (confirm by timestamp
  or by re-running against a repo where the push is deliberately blocked and
  observing `create_branch` fails against a nonexistent base ref).
- **Confirm no PR is opened and no merge verb is reachable** — `repo_io`
  exposes none, and bootstrap never calls `open_pr`.
- ~~Confirm the wheel actually ships the templates~~ — already verified in the
  25 implementation session (no `gh`/network needed for this one): `hatch
  build -t wheel` + inspecting the archive confirms
  `loop_engine/tools/scaffold/templates/` (including the non-`.py` `CLAUDE.md`
  and `.tmpl` files) ships via hatchling's **default** `packages` file
  selection — no `force-include` needed (an explicit `force-include` entry
  was tried first and **conflicts** with the default inclusion, raising
  hatchling's duplicate-path build error; removed).
- Clean up the scratch repo afterward — this check has real side effects on
  GitHub, unlike every other check in this file.

## 9. Issue-server live `create_issue`/`read_issue` round-trip (validates Sprint 26)

Sprint 26's coverage is entirely hermetic: `tests/tools/test_issue_io.py` proves
the `render_question_issue`/`create_issue`/`parse_issue_answers` pure/`gh`
split is behavior-preserving with `_run_gh` monkeypatched; `tests/tools/
test_issue_io_server.py` launches the real `issue_io_server` stdio subprocess
for discovery/schema only (no `gh` call — a live `gh` call at import time
would hang or fail in this network-off sandbox) and separately exercises the
`@mcp.tool()`-decorated verbs in-process with `tools/issue_io.create_issue`/
`read_issue` monkeypatched; `tests/tools/test_issue_provider.py` and
`tests/core/test_engine.py`/`test_graph_engine.py`'s injected-filer tests use
a fake in-process provider. **No test in this sprint shells a real `gh` through
the `issue` MCP server subprocess.** Run on a daemon-bearing host with `gh`
authenticated against a disposable scratch repo:

- **Real `create_issue` through the server.** Enter `build_issue_provider()`
  for real, dispatch `create_issue` with a throwaway title/body/label, and
  confirm a real GitHub Issue is created (check its URL/number) and carries
  the `loop-engine/needs-human` label.
- **Real `read_issue` through the server.** Post a `` ```answers `` comment on
  that issue, dispatch `read_issue` through the same provider, and confirm the
  returned JSON's `state`/`body`/`comments` match what `gh issue view` reports
  directly (i.e. the server round-trips `gh`'s JSON faithfully, not just the
  monkeypatched shape the unit tests assert).
- **Confirm `mcp_issue_filer`/`mcp_read_issue` round-trip against the real
  server** (not just a fake provider): file via `mcp_issue_filer(provider)`,
  read the answers back via `mcp_read_issue(provider, n)`, and confirm the
  `IssueRef`/answers map match what the classic `file_question_issue`/
  `read_issue_answers` would have produced against the same issue.
- **This check gates together with the still-pending host-gated Phase 6
  block** (the four flag deletions + `artifacts` strip + `loop.py` collapse) —
  specifically the issue-path **default-flip** (making the MCP filer/reader
  the runtime default) and the **classic-path deletion**, per LD3 in
  `docs/migration_roadmap.md`'s "Phase 6 planning pass". Neither should happen
  until this live check has passed.
- **Sprint 26 HITL review (Opus, 2026-07-10) routed findings R1–R7 into this
  flip** — see `docs/migration_roadmap.md` "Sprint 26 … HITL review". Before
  flipping the reader default, fix **R1** (make `mcp_read_issue` a
  provider-binding `mcp_issue_reader(provider)` factory + correct the
  `mcp_client.py` docstring), **R2** (thread the `issue_filer` write seam
  through `cli.resume`), **R3** (unify read/write seams on one injection
  mechanism), and **R4** (injected-filer test coverage at all three
  `_pause_for_issue` sites). Also resolve **R7** here (the `python` vs
  `sys.executable` launch nit in `loop_engine.mcp.json`). **R5/R6** (the
  pre-existing `resume` abort-path crash + first-block-only answer parse) are
  independent of the flip and can be fixed any time.
- Clean up the scratch issue/repo afterward — this check has real side
  effects on GitHub, unlike every other check in this file.

---

# Phase 6 flip-block host-run results (V1 / V2 / V3)

Host session 2026-07-10 (Opus/Architect), devcontainer with DinD + `gh` auth +
`loop-engine-dev:latest`, config `LOOP_ENGINE_ENGINE=langgraph
LOOP_ENGINE_TOOLS=mcp LOOP_ENGINE_PERSONAS=declarative
LOOP_ENGINE_ISOLATION=container`.

## V1 — ENGINE + TOOLS + PERSONAS big factory run — **PASS (qualified)**

Four real end-to-end runs (`hatch`-env `loop-engine run` from a throwaway
checkout so the git-worktree-of-self is a clean tree). **All three target
paths verified functional and at parity across every run:**

- **`ENGINE=langgraph`** — drove `PM → Architecture → Sprint Breakdown → Coder`
  plus the gate/accept transitions, the escalation ladder, the pause-for-issue
  path, and per-stage snapshots. Upstream accept→persist transitions all fired
  under the graph engine.
- **`PERSONAS=declarative`** — `PMGenerator`/`ArchitectureGenerator`/
  `SprintBreakdownGenerator` produced correct `project_spec`,
  `architecture_definition`, `sprint_plans`, and `task_manifest` (the generated
  `converter.py` in run 2 was a genuinely correct strict-validation impl).
  Cost ~$0.38/run for the three generator stages (Cache R 0 on clean first-pass
  accepts — expected; no revision retries). Acceptable.
- **`TOOLS=mcp`** — serviced the Coder tool loop (25–33 `CallToolRequest`s/run:
  `read_file`/`list_files`/`grep`/`run_tests`) inside the hardened container
  (`--network none --cap-drop ALL --read-only --security-opt no-new-privileges`,
  single worktree bind). In-process fallback is structurally impossible under
  `container`+`mcp` (`_CoderToolBackend.resolve` raises
  `IsolationUnavailableError` otherwise) — "no in-process fallback" is met by
  construction.

**Qualification — terminal `COMPLETED` not observed under V1.** All four runs
escalated at the **classic `CoderIacPersona`** stage rather than reaching a
Coder-ACCEPT, for reasons **orthogonal to the three flags** and identical on a
fully-classic run: (1) worktree-of-self tree collision → correct refusal to
clobber; (2) the `_ALLOWED_ARTIFACT_ROOTS = (docs, sprints, src)` write allowlist
blocking generated repo-root scaffolding tasks (that is `flows/bootstrap`'s job,
not the Coder's); (3) classic multi-sprint file-application dropped a module;
(4) the classic Coder over-escalated on a trivial pre-stubbed single-file task
(33 tool calls, wrote nothing). None indicated a `langgraph`/`mcp`/`declarative`
defect. Each escalation also *crashed* the run because the throwaway repos had no
GitHub remote (`gh issue create` exit 1) — a harness artifact, not a product bug.

**Decision (2026-07-10, repo owner):** the classic `CoderIacPersona` is being
**fully retired and replaced by Ralph** — do not sink effort into making the
classic Coder reach `COMPLETED`. The one genuinely-unverified transition
(Coder-ACCEPT → terminal `COMPLETED` under the new engine) is **deferred to V2**:
the Ralph run below IS the production Coder and its `COMPLETED` closes this tail.
V1 is therefore recorded **PASS for `ENGINE`/`TOOLS`/`PERSONAS`** (unblocking
deletion Tasks 1–3), with the terminal-`COMPLETED` proof carried by V2.

## V2 — Ralph convergence + cost — **OPEN (unblocked; host `COMPLETED` not yet observed)**

> **Status update (sprint 29, 2026-07-11).** The gate-sandbox blocker below was
> closed in code by **sprint 28** (F-GATE-SANDBOX). A re-attempt host run (#3, the
> tightened-spec run recorded in the sprint 29 plan) then converged **11 tasks**
> across all 6 sprints — the container gate ACCEPTed 11× — but stopped at
> `BUDGET_EXCEEDED` one sprint short of `COMPLETED`, and surfaced two further
> convergence gaps, both now **resolved in code by sprint 29** (see findings
> **F-TOOLLOOP-CAP** and **F-CODER-NO-LINT** below). **V2 nonetheless stays OPEN:**
> a literal container-sandboxed Ralph run reaching terminal `COMPLETED` within
> budget has still **not** been observed. The remaining obligation is that single
> observation, now gated only on (a) sprints 28+29 in code — done — and (b)
> **escalation-free staging** (a real remote or an injected non-crashing
> `issue_filer`, so a stray escalation on a remote-less scratch tree pauses cleanly
> instead of crashing `gh issue create`). Do **not** record V2 PASS until observed.

> **Status update (V2 re-attempt #6, 2026-07-11, Opus/Architect host session).**
> Escalation-free staging was built the injected-`issue_filer` way (the Seuss27 PAT
> is scoped only to `glunk-works/loop-engine`, so no throwaway scratch remote could
> be created; a non-crashing recording filer was injected via `run_graph_loop`'s
> `issue_filer` seam instead). Run under the full production config
> (`langgraph`+`mcp`+`declarative`+`ralph`+`container`, `LOOP_ENGINE_DEV_IMAGE=loop-engine-dev:latest`
> rebuilt to include `ruff` — the F-CODER-NO-LINT host obligation, now closed) against
> the minimal 2-fn `textkit` spec. **Result: staging validated, but still NOT
> `COMPLETED`.** The run reached the container Ralph coder, serviced a full sandboxed
> tool loop, and then **escalated** (`AWAITING_ISSUE`, $3.29 / $5.00) — the injected
> filer recorded the question and paused cleanly (no `gh` crash), so the staging
> approach itself is proven. The escalation is a **new, distinct convergence gap** —
> see **F-RALPH-OVERSPEC-TEST** below. V2 therefore **stays OPEN**, now additionally
> gated on that finding's fix. Do **not** record V2 PASS until a real container run
> reaches terminal `COMPLETED`.

> **Status update (sprint 30, 2026-07-11).** F-RALPH-OVERSPEC-TEST's fix is now
> **resolved-in-code** (`551338a` — the prompt-only test-scope + self-fix-before-escalate
> guardrails). V2's last in-code blocker is closed; the **only** remaining obligation
> is the host observation itself — a fresh V2 re-attempt (reusing the run-#6 staging
> recipe) reaching terminal `COMPLETED`. Do **not** record V2 PASS until that run is
> observed.

> **Status update (V2 re-attempt #7, 2026-07-11, Opus/Architect host session).**
> Reused the run-#6 staging recipe verbatim (fresh `scratchpad/v2_tree`, same
> `v2_requirements_min.md`, same full production config) to verify sprint 30's fix.
> **F-RALPH-OVERSPEC-TEST did not recur** — no self-authored-test escalation this
> run, so the prompt-only guardrail appears to hold. **Result: still NOT
> `COMPLETED`.** The run escalated again, but on a **new, more serious, and
> deterministic (not flaky) defect** — see **F-RALPH-FALSE-COMPLETION** below. V2
> **stays OPEN**, now gated on that finding's fix. Do **not** attempt another V2
> re-run until it is fixed — this defect will reproduce deterministically any time
> a Ralph task's edit block fails to parse, which is not a rare event.

*Historical record of the 2026-07-10 session (blocker since closed):*

Ran the full production config **with `LOOP_ENGINE_CODER=ralph`** against a
scaffolded src-only scratch tree. **Ralph's algorithm engaged correctly:** the
declarative Sprint Breakdown emitted a `task_manifest`, Ralph entered its
self-loop, wrote `.agent/STATE.md`, and checked off the first manifest task
(`01_input_validation_foundation::t01`) via 11 sandboxed container tool calls —
so the manifest/checklist/one-task-per-iteration machinery works live.

**BLOCKER (finding — the real answer to "does Ralph work under container?"):**
the run crashed at the Ralph coder stage with `IsolationUnavailableError`:
*"container isolation is selected; sandboxed gate verification is deferred to the
host-side e2e build."* Root cause: **`core/coder_gate.py::_raise_if_sandboxed`**
(called by BOTH `CoderGate` and `RalphCoderGate`) raises whenever
`sandbox_runtime_mode() is not None`, because the gate runs its verification
pytest **in-process** and that was never routed through the sandbox. This is the
**documented sprint-18 deferral** (§3 above): the coder's `run_tests` *tool* was
sandboxed in Phase 3b (via MCP), but the gate's *own* verification pytest was not.

**Consequence — affects the whole flip block, not just Ralph:** under the target
production config (`LOOP_ENGINE_ISOLATION=container`), **neither** Coder can reach
a green gate → ACCEPT → `COMPLETED`, because the gate refuses to verify. V1's four
runs escalated on content *before* the gate, so they never surfaced this; V2 hit
it directly. **V2 cannot pass under container isolation until the gate's pytest is
routed through the MCP sandbox (the deferred sprint-18 / Phase-3b-completion work
— an implementation task, not a verification run).** Ralph's convergence
*algorithm* remains separately verifiable under `ISOLATION=worktree`/`none` (gate
runs in-process) on a trusted pure-Python task.

## V3 — forced issue-escalation round-trip — NOT STARTED

Not run (budget/side-effect scope not authorized this session). Independent of the
gate-sandbox gap below (V3 forces a *pause*, it does not need a Coder ACCEPT), but
it has real GitHub side effects, so it is left for a future host session.

## Finding F-GATE-SANDBOX — RESOLVED IN CODE by sprint 28

**Status: resolved-in-code (sprint 28, `sprints/28_gate_pytest_sandbox/`).** The
Coder gates (`CoderGate` + `RalphCoderGate`) no longer refuse to run under
`LOOP_ENGINE_ISOLATION=container`/`sandbox`. `core/coder_gate.py::_raise_if_sandboxed`
is deleted; `_run_gate_pytest` now delegates to `tools/mcp.run_gate_pytest`, which
dispatches the gate's verification pytest through the same MCP sandboxed
coder-tools provider the `run_tests` *tool* already used (Phase 3b), instead of
running it in-process. The stale claim below ("no run of any kind can reach a
Coder ACCEPT → `COMPLETED` under container isolation") no longer holds in code —
what remains is the **host** proof.

**Remaining obligation — host re-verification, not a code gap:** a real
container-sandboxed gate run reaching Coder ACCEPT → `COMPLETED` has not yet been
observed on a daemon-bearing host. That observation is sprint 27's
**V1(complete)/V2**, previously blocked by this finding and now unblocked.

**What the gap originally was (history, kept for context):** the gate's
verification pytest executed **in-process**; under `container`/`sandbox` isolation
that would run untrusted model code in the orchestrator, so `_raise_if_sandboxed`
refused rather than do that. Routing it through the sandbox was deferred sprint-18
work (§3). The coder's `run_tests` *tool* was sandboxed in Phase 3b (via MCP); the
gate's *own* pytest was not — until sprint 28.

**Impact on sprint 27 (the flip block) — as originally assessed (now closed):** the
plan treats V1/V2/V3 as runnable to `COMPLETED` on a daemon-bearing host under
`ISOLATION=container`. That assumption was false at the time this finding was
recorded — no run of any kind could reach a Coder ACCEPT → `COMPLETED` under
container isolation, because the gate that must go green refused to execute. This
was a **prerequisite implementation task the flip block did not account for**, not
a defect in any of the four flags being flipped (the gate refusal was
flag-invariant and predated Phase 6). Sprint 28 closes it; sprint 27's V1/V2 now
carry the host-proof obligation.

**Sequencing decision for the planning session (not decided here):**
- **Option A — build the gate-sandbox wiring first.** Route the Coder/Ralph gate's
  verification pytest through the MCP container sandbox (mirror Phase 3b's
  `run_tests` sandboxing) as a new task/sprint that *finishes* Phase 3b, THEN run
  V1(complete)/V2/V3 under container. Makes the container end-state actually
  completable before any deletion.
- **Option B — decouple the deletions from the gate gap.** The three V1-target
  flags (`ENGINE`/`TOOLS`/`PERSONAS`) are already verified functional + parity
  through PM→Arch→Sprint + the in-container MCP coder tool loop + the escalation
  ladder; the gate-sandbox gap is orthogonal to them (flag-invariant, affects
  classic and new paths equally). Consider whether Tasks 1–3 can proceed on that
  decomposed evidence, with the terminal-`COMPLETED`/container-gate proof tracked
  separately as its own gate (and `CODER`/Ralph Task 4 held until both V2 and the
  gate wiring land).

**State of evidence (2026-07-10 host session):**
- Verified live: `ENGINE=langgraph`, `TOOLS=mcp`, `PERSONAS=declarative` functional
  + parity through the full upstream pipeline, the in-container MCP coder tool loop,
  and the escalation/pause/snapshot paths. Ralph's manifest → checklist →
  one-task-per-iteration machinery engages live (task `t01` checked off).
- NOT verified (blocked by F-GATE-SANDBOX): any Coder-ACCEPT → `COMPLETED` under
  container isolation; Ralph full convergence + cost to `COMPLETED`; the V3 issue
  round-trip (not started).
- GitHub side effects cleaned: scratch issue #21 closed; V1 runs 2–4 and V2 had no
  remote (crashed on `gh` at escalation — a harness artifact), so nothing else was
  filed. Scratch repos are local (scratchpad), no remote cleanup needed.

## Finding F-TOOLLOOP-CAP — RESOLVED IN CODE by sprint 29

**Status: resolved-in-code (sprint 29 Task 1, `b0be361`).** The V2 re-attempt run #1
reached the container gate and checked off 3 tasks, then **crashed** with an
**uncaught** `ToolLoopExceededError` when a trivial `truncate` increment blew the
blunt **12**-iteration inner tool-loop cap — a stuck loop aborted the whole run
instead of failing the stage (unlike `BudgetExceededError`/`TruncatedResponseError`,
which exit cleanly). Fix: `RalphCoderPersona._run_increment` now catches
`ToolLoopExceededError` and degrades to the no-output path (task left unchecked →
re-selected with fresh context → the engine's identical-findings guard escalates if
still stuck), preserving Ralph's multi-task resilience; `core/engine.py::execute_stage`
catches it as a safety net for every other persona, finalizing `FAILED_STAGE` +
a persisted snapshot (iteration exhaustion treated as the sibling of dollar
exhaustion, not a crash). `DEFAULT_MAX_TOOL_ITERATIONS` raised **12 → 40**, the USD
budget documented as the primary bound and the cap only a finite backstop against
near-zero-cost spin. (BL-4 — a real Ralph liveness/progress watcher — remains the
follow-on to the blunt cap; backlogged, not this sprint.)

**Remaining obligation:** none in code. The graceful-degradation + generous-cap
behavior is exercised by the mocked suite; the *host* payoff (a run that would have
crashed at the 12-cap now converging instead) is folded into the still-open **V2**
`COMPLETED` observation above — not a separate host check.

## Finding F-CODER-NO-LINT — RESOLVED IN CODE by sprint 29

**Status: resolved-in-code (sprint 29 Task 2, `10f27d3`).** V2 re-attempt run #4
**escalated** structurally — *"my toolset does not expose a way to execute `ruff
check` / `ruff format --check`"* — so a task carrying a "ruff clean" acceptance
criterion could not be self-verified and instead paused for a human (and that
escalation then crashed on the remote-less scratch tree's `gh issue create`). Fix:
new `tools/coder_tools/run_lint.py` gives the agentic Coder a `run_lint(path)` tool
over `ruff check` + `ruff format --check`, mirroring `run_tests.py`'s containment
exactly (fixed argv `sys.executable -m ruff …`, `shell=False`, hard 60s timeout,
`truncate_result`-capped, `resolve_tool_path`-validated); wired in-process
(`CODER_TOOLS` + `_execute_tool`) and over MCP (`@mcp.tool() run_lint`). This is the
**fifth** sanctioned subprocess surface (`ruff`), recorded in
`tests/tools/test_subprocess_surfaces.py` and CLAUDE.md; unlike `run_tests`' pytest,
`ruff` statically parses the target and never executes model-generated code, so it
is strictly lower-risk. HITL-reviewed by Opus and approved (2026-07-11). Gate-enforced
lint stays out of scope — the Coder gets the *tool*, not a new gate.

**Remaining obligation:** none in code. One item to confirm at V2 host-staging:
`ruff` must be present in the container image so `python -m ruff` resolves — absent
it, `run_lint` returns a misleading "lint failure" (module-not-found) rather than a
tooling gap. That confirmation rides the V2 re-attempt, not a separate check.

## Finding F-RALPH-OVERSPEC-TEST — RESOLVED IN CODE by sprint 30 (host V2 re-attempt still owed)

**Status: resolved-in-code (sprint 30 Task 1, `551338a`).** New finding from V2
re-attempt #6 (2026-07-11); `CODER=ralph` (Task 4) stays gated on V2, and V2 stays
gated on a host re-run of this fix (see **Remaining obligation** below).

**Symptom.** On the minimal 2-fn `textkit` spec, the Ralph coder wrote **correct**
product code (`slugify.py`/`word_count.py`/`__init__.py` all meet the spec) but
then **escalated** at `AWAITING_ISSUE` instead of reaching `COMPLETED` — blocked by
a **single self-authored test** it had written *beyond* the spec:
`test_slugify_uses_module_level_compiled_pattern`, which asserts a **private module
internal** (`slugify._NON_ALNUM_RUN`, a compiled regex) via
`import textkit.slugify as slugify_module`. That import form resolves to the
**function**, not the module (because `__init__.py`'s spec-mandated
`from textkit.slugify import slugify` shadows the `textkit.slugify` submodule
attribute), so it fails `AttributeError: 'function' object has no attribute
'_NON_ALNUM_RUN'`. The test's own inline comment claims the import "sidesteps that
rebinding" — it does not.

**Two-part root cause (both Ralph behavior, not a product defect and not a
`langgraph`/`mcp`/`declarative` defect):**
1. **Over-specified test generation.** The spec enumerated exact known/error cases
   and nothing about private internals, signatures, or ReDoS; Ralph nonetheless
   authored a module-internals test, a `inspect.signature` test, and a 10k-char
   ReDoS test. The internals test encodes a Python-import-semantics misunderstanding
   and cannot pass against the (correct) re-export structure.
2. **Rigid task-scoping → escalation instead of self-fix.** Ralph reasoned the fix
   "belongs to Task 2" and paused for a human rather than deleting/correcting a
   one-line unspecified assertion it had itself introduced. A trivial self-fix
   (remove or correct the test) would have gone green.

**Evidence.** `scratch/v2_rerun6.log` (run_id `0d5e3f3c274d414e988ac295a8d4bddb`,
`AWAITING_ISSUE`, $3.29/$5.00); `scratch/v2_escalations.jsonl` (the recorded
question); generated tree under the run's worktree
(`.../v2_tree/.worktrees/0d5e3f3c…/src/textkit/`). Injected-filer staging worked:
clean pause, within budget, no `gh` crash.

**Fix (sprint 30 Task 1, `551338a` — prompt-only, locked FD1/FD2, no gate-guard):**
two additive directives steer Ralph away from the observed failure mode. (1)
**Test-scope guardrail** — `PROMPT_TEMPLATE` (`coder_iac/shared.py`, shared with the
classic Coder) now scopes every test to the task's enumerated `Acceptance Criteria`
and forbids assertions on private/underscore module internals, import mechanics, or
behavior beyond spec. (2) **Self-fix-before-escalate guardrail** — Ralph's
per-increment prompts (`_build_task_prompt`/`_build_repair_prompt`, `ralph.py`) now
require a test the coder itself authored (in this or an earlier increment) to be
fixed or removed in-scope, for every increment, and reserve `## Open Questions` for
genuine spec ambiguities only — never a test of the coder's own authorship. A
gate-level guard (red gate whose only failing tests are self-authored + out-of-spec
→ auto-repair) was considered and explicitly deferred (FD1): classifying "self-authored
and out-of-spec" reliably at the gate is brittle; the prompt-only fix directly targets
the observed, model-initiated escalation and is lower-risk. (BL-4's Ralph
liveness/progress watcher is adjacent but distinct — this is about *what Ralph tests
and when it escalates*, not iteration liveness.)

**Remaining obligation:** none in code. A fresh V2 re-attempt on a daemon-bearing
host, reusing the run-#6 staging recipe (harness `scratch/v2_run_harness.py`, tree
`scratchpad/v2_tree`, `LOOP_ENGINE_DEV_IMAGE=loop-engine-dev:latest`, injected
`issue_filer`, absolute env python), must observe terminal `COMPLETED` within budget
— only that host observation *verifies* this finding (vs. resolved-in-code) and
discharges V2's last blocker. Do **not** flip `CODER=ralph` (Task 4) until that
re-run reaches `COMPLETED`. A re-run that still escalates on a self-authored test
means the prompt-only fix was insufficient — escalate to the deferred gate-guard
(FD1), do not re-open this fix.

**Verified by V2 re-attempt #7 (2026-07-11): this specific escalation mode did
not recur.** The fix holds for its intended failure mode. Re-attempt #7 hit a
different, more serious defect instead — see **F-RALPH-FALSE-COMPLETION** below.

## Finding F-RALPH-FALSE-COMPLETION — OPEN, blocks V2 (host V2 re-attempt #7, 2026-07-11)

**Status: OPEN — a code fix is required, not a prompt tweak.** New finding from
V2 re-attempt #7 (run_id `e7fc2eed24fe41399089151f74754924`, `AWAITING_ISSUE`,
$2.63/$5.00, evidence: `scratch/v2_rerun7.log`,
`scratch/v2_escalations_rerun7.jsonl`, tree
`scratchpad/v2_tree/.worktrees/e7fc2eed24fe41399089151f74754924/`). `CODER=ralph`
(Task 4) stays gated on V2; V2 stays gated on this fix.

**Symptom.** `.agent/STATE.md` recorded `02_core_feature_implementation::t01`
(implement `slugify`), `t02` (implement `word_count`), and `t03` (write
`test_slugify.py`) as **completed**, each with an elaborate, confident
"Definition of Done Verification" narrative in its report. In reality, on disk:
`src/textkit/slugify.py` and `src/textkit/word_count.py` were **still the
original `raise NotImplementedError` stubs**, `src/textkit/tests/test_slugify.py`
**did not exist**, and `src/textkit/tests/test_placeholder_stubs.py` **still
contained both stale stub-assertion tests** the real implementations should have
superseded. None of the three "completed" tasks' file edits had actually landed.
The run eventually escalated to a human via the exhaustion ladder
(`_exhaustion_escalation`) with a message that undersold the true scope: *"Edit
Application Failures recorded in the implementation report; re-emit the
corrected blocks so they apply cleanly"* — implying one file needed
re-emitting, when in fact three tasks' worth of work had never been applied.

**Root cause (confirmed by code reading, `src/loop_engine/personas/coder_iac/ralph.py`
+ `src/loop_engine/core/coder_gate.py`) — two compounding defects, both specific
to the Ralph per-task loop (the classic `CoderIacPersona` does not share either,
per below):**

1. **Task completion is gated on "did the model raise an open question," not on
   "did its edit actually apply."** `RalphCoderPersona._task_increment`
   (`ralph.py:258-304`) calls `_finalize_report` → `apply_file_blocks`, which
   returns a list of failures for any malformed/non-applying edit block — but
   that return value is never consulted when deciding whether to mark the task
   done. The only branch is `if new_questions: ... blocked ... else: ...
   completed_tasks: [*scratch.completed_tasks, task.id]` (`ralph.py:282-300`). A
   task whose edit silently failed to apply (or, as here, whose edit block was
   never even emitted in the required `### FILEPATH:` grammar — `slugify.py`
   and `word_count.py` have **no** recorded failure at all, because
   `apply_file_blocks` can only flag a block it finds malformed, not a block
   that was never attempted) is marked **completed** exactly like a genuinely
   successful one, as long as the model didn't escalate a question.
2. **A stale, unresolved `## Edit Application Failures` marker can become
   permanently uncleared once its owning task is marked done.**
   `_upsert_task_section` (`ralph.py:87-107`) only replaces the section for the
   **exact task id currently being (re-)run**; `select_next_task` (`ralph.py:51-63`)
   never re-selects a task already in `completed_tasks`. Here, `t02`'s edit
   block for `test_placeholder_stubs.py` failed to parse ("no fenced file
   contents or SEARCH/REPLACE edit block found") — but `t02` was still marked
   completed (defect 1), so its report section, `## Edit Application Failures`
   included, is never revisited. `CoderGate`/`RalphCoderGate`'s `edit_findings`
   check (`coder_gate.py:146-151`) scans the **entire concatenated sprint
   report string** for `EDIT_FAILURES_HEADER`, and short-circuits to REVISE
   *before* ever running pytest. Once one task's stale marker is baked in this
   way, **every subsequent increment for that sprint is permanently blocked
   from ever reaching a pytest run** — the loop can only bounce between
   "re-emit corrected blocks" (for a task that will never be re-selected) until
   the revise cap exhausts and escalates. This is deterministic given defect 1,
   not model flakiness: any single malformed/missing edit block on an
   already-completed task wedges the sprint permanently.

**Why the classic `CoderIacPersona` does not share this bug:** it re-runs the
**whole sprint** every revise cycle and does `reports[sprint_path] = report`
(`persona.py:143`) — a full replace, not a per-task append/upsert — so a
corrected report on the next attempt naturally drops any prior
`## Edit Application Failures` marker. The permanent-taint failure mode is
specific to Ralph's per-task, never-revisit-completed-work design.

**Severity.** This is more serious than F-RALPH-OVERSPEC-TEST: it means
`RalphCoderGate`'s ACCEPT precondition ("every manifest task checked off AND a
green pytest run") can be **unsound** — the checklist half of that conjunction
is model-self-reported and is not cross-validated against `apply_file_blocks`
ever having succeeded for that task. In this run, pytest was never even reached
(blocked by defect 2), so the regression-repair path (`RALPH_REGRESSION_PREFIX`)
never got a chance to engage; in a less lucky run (no single detectably-malformed
block at all, just silently-never-attempted edits across every task), the
manifest could reach "all tasks done," pytest would eventually run and go red,
and the repair path would engage late — but the false "completed" status itself
is the real problem, independent of when pytest happens to catch it.

**Not the same finding as F-RALPH-OVERSPEC-TEST.** That finding was about *what*
Ralph tests and *when* it chooses to escalate (a prompting/scope problem,
correctly fixed with a prompt-only guardrail). This finding is about the
engine's own bookkeeping marking work "done" without verifying the write
actually happened — a correctness gap in `core/coder_gate.py` +
`personas/coder_iac/ralph.py`, not fixable by steering the model's prompt alone
(the model has no way to know, or control, that a parse failure on its output
will be permanently unrecoverable).

**Suggested fix shape (for the planning session, not decided here):** (a) don't
mark a task completed if `apply_file_blocks` reported any failure attributable
to it — treat it like the `new_questions`/blocked branch instead, so the *same*
task is re-selected with the specific edit-application failure in its next
fresh-context prompt (mirroring how a genuine escalation currently keeps a task
open); (b) independently, reconsider whether `edit_findings` should scan the
whole concatenated report or only the latest/active task's section, so a
resolved failure cannot stay permanently load-bearing once its task is behind
the loop. Both may be needed — (a) prevents the false-positive "done," (b)
prevents a legitimately-blocked-and-retried task from tainting the gate forever
once it does eventually succeed.

**Remaining obligation:** a fix (own sprint, code change — not prompt-only),
HITL-reviewed, then a fresh V2 re-attempt reaching terminal `COMPLETED`. Do
**not** attempt another V2 re-run before this lands — the defect is
deterministic and will very likely reproduce (any single malformed/unattempted
edit block on a task the model doesn't also escalate a question about wedges
the sprint the same way). Do not flip `CODER=ralph` (Task 4) until fixed and
verified.

---

Delete this file once the checks have been performed and any findings are fixed.
