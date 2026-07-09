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
- **Deferred with the sprint-18 host work:** routing the Ralph gate's pytest and
  the `run_tests` tool through a sandbox under `LOOP_ENGINE_ISOLATION=container`
  (until then the gate raises `IsolationUnavailableError` rather than run model
  code in-process), and per-task test selection (v1 gates on global green, not the
  single task's tests).

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

Delete this file once the checks have been performed and any findings are fixed.
