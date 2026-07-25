# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 47 (recon data path): `sprint_status: blocked`.**
T1 (dispatch half) is merged (`cad4db1`, PR #190). T2 (the untrusted-input ingest half)
is **blocked** on a plan-vs-reality gap in `scope-core` — needs an Opus/architect decision,
not a Sonnet coding call.

## Just done (2026-07-25) — resume→blocked (Sonnet/coder)
- Resumed with cursor clean (T1 merged, gate NONE OPEN) and auto-started T2 per the
  previous session's instruction.
- Read the sprint plan's Task 2 spec, then verified `scope-core`'s actual installed
  surface before wiring anything (as the prior cursor's drift note required) — found the
  gap below and **stopped before writing any code**. `git diff main...HEAD` is empty this
  session; no `/critic-gate` pass needed.
- Ruleset check: healthy (4 rule types, 8 required checks). Branch prune: none stale.

## The blocking finding — scope-core is missing `is_in_scope` / `normalize`
`sprints/47_bounty_recon_data_path/sprint_plan.md` Task 2 (written 2026-07-21, before
`#182` extracted scope enforcement to the external `scope-core` package) tells T2 to add:
- `is_in_scope(rules, candidate) -> bool` to `tools/scope_validator` (a pure, non-raising
  predicate the output filter needs), and
- `normalize(text) -> str` to `tools/ingest` (structural-only: NFKC + invisible-char strip,
  **no** truncate).

Both target directories are now **empty** (only stale `__pycache__` — `#182` extracted
their contents to `scope-core`). Confirmed live today: `scope-core`
(`glunk-works/scope-core`, pinned in `pyproject.toml` at `7345de5`, confirmed still its
HEAD via `gh api repos/glunk-works/scope-core/commits`) exports only `validate_target`
(raises `ScopeViolation`, no boolean form), `sanitize` (truncates + collapses whitespace;
its NFKC/invisible-strip logic is a **private** internal, not exported), and
`is_action_banned`. **Neither `is_in_scope` nor a bare structural `normalize` exists
anywhere reachable.**

**Options weighed, not yet decided (owner said: stop and escalate, don't improvise):**
1. Add both to `scope-core`, bump the pin — consistent with BI-D6 ("one definition of
   in-scope" shared with `bounty-infra`); needs a cross-repo PR against `scope-core` first,
   blocking T2 until it lands.
2. Implement both locally in `loop-orchestrator`'s `tools/recon` instead — `is_in_scope` as
   a thin try/except wrapper over `validate_target`; `normalize` as a local reimplementation
   of the NFKC+invisible-strip logic. Unblocks T2 immediately but duplicates `scope-core`'s
   private internals across two repos, diverging from the "one definition" intent.
3. Some other resolution the architect prefers.

## Next — Opus/architect decides, then hand back to Sonnet/coder
**HITL Gate: OPEN.** Decide the `is_in_scope`/`normalize` gap above, record the decision
(a new S47-Dxx or a plan amendment), then the Sonnet coder implements Task 2 against the
resolved design. A `/resume` must **not** auto-start T2 until this gate closes.

## Gotchas worth remembering
- **`tools/scope_validator`/`tools/ingest` are gone** — everything routes through
  `scope_core` now (`from scope_core import ScopeRules, validate_target, sanitize, ...`).
  Don't recreate the old modules without an explicit decision to do so.
- **`scope-core` is commit-pinned, not a local package** — adding a function there means a
  PR against `glunk-works/scope-core`, a new commit SHA, and re-pinning
  `pyproject.toml`'s `scope-core @ https://.../<sha>.tar.gz` line (plus `sbom`/`audit`).
- **`bounty-infra#18` (dispatch contract) is still a V-run precondition, blocked on #6** —
  unrelated to this gate; T1–T3 merge hermetically without it.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.

## Pointers
- [`sprints/47_bounty_recon_data_path/sprint_plan.md`](../sprints/47_bounty_recon_data_path/sprint_plan.md) — the S47 plan (Task 2 is the one blocked).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — reference-of-record; §9 decisions log.
- `glunk-works/scope-core` (pinned `7345de5`) — the external package this gap lives in.
