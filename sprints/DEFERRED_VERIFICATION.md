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

Delete this file once both checks have been performed and any findings are fixed.
