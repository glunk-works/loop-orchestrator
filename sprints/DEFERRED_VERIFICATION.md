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

Delete this file once the checks have been performed and any findings are fixed.
