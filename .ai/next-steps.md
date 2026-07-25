# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 47 (recon data path): `sprint_status: implementing`.**
T1 (dispatch half) is merged (`cad4db1`, PR #190). The T2 block is **resolved** — the
`scope-core` `is_in_scope`/`normalize` gap is decided (S47-D13, owner-confirmed **Option A**:
add both to `scope-core`, bump the pin). Next is execution, starting with a small
**prerequisite `scope-core` PR** (a different repo).

## Just done (2026-07-25) — Opus/architect, gate resolved
- Verified `scope-core` (pinned `7345de5`, still its HEAD) exports only `validate_target`
  (raises) + `sanitize` (full scrub) + `is_action_banned` — **no** `is_in_scope`, **no** bare
  `normalize`; local `tools/scope_validator`/`tools/ingest` are empty (extracted by #182).
- **Decisive evidence (owner's steer):** `bounty-infra`'s scanner — the pilot `scope-core`
  consumer — already hand-rolled the boolean via `try/except validate_target` in a bulk loop
  (the exact Q1 anti-pattern) and scope-checks *un-normalized* hosts. Both primitives have a
  real second consumer ⇒ BI-D6 "one definition of in-scope" wins.
- Recorded **S47-D13** + rewrote Task 2's stale local-module bullets to consume
  `scope_core.{is_in_scope,normalize}`, added the prerequisite blocker (`288a9f4`).
- Filed the `bounty-infra` adopt-it follow-up: **`bounty-infra#86`**.
- Ruleset check: healthy (4 rule types, 8 required checks). Branch prune: none stale.

## Next — Sonnet/coder executes (HITL Gate: NONE OPEN)
The decision is locked; no open decision remains. Execute in order:
1. **Prerequisite `scope-core` PR** (repo `glunk-works/scope-core`): add
   `is_in_scope(rules, candidate) -> bool` = `not any(out.search(c)) and any(in.search(c))`
   (refactor `validate_target` to `if not is_in_scope(...): raise`, keeping its two distinct
   reasons); add `normalize(text) -> str` = the structural prefix of `sanitize` (ANSI + C0/C1
   + invisible-format/variation strip + NFKC, **no** collapse/truncate) and refactor
   `sanitize` to `collapse+truncate ∘ normalize`. Parity + no-truncate tests; export both.
   Follow `scope-core`'s own CI/review.
2. **Re-pin** `pyproject.toml`'s `scope-core @ …/<new-sha>.tar.gz`; `hatch run sbom` + `audit`.
3. **Task 2** (`sprints/47_bounty_recon_data_path/sprint_plan.md`): the untrusted-input
   ingest path in `tools/recon`, consuming `scope_core.{is_in_scope,normalize}`. Fresh-session
   `architect-review` + security-critic (untrusted path + both scope boundaries + gh/DB sinks).

## Gotchas worth remembering
- **`tools/scope_validator`/`tools/ingest` are gone** — everything routes through `scope_core`
  now. Don't recreate the old local modules.
- **`scope-core` is commit-pinned, not a local package** — a function there means a PR against
  `glunk-works/scope-core`, a new SHA, re-pinning `pyproject.toml` (+ `sbom`/`audit`).
- **`bounty-infra#18` (dispatch contract) is still a V-run precondition, blocked on #6** —
  unrelated to this gate; T1–T3 merge hermetically without it.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.

## Pointers
- [`sprints/47_bounty_recon_data_path/sprint_plan.md`](../sprints/47_bounty_recon_data_path/sprint_plan.md) — S47 plan (Task 2 unblocked; S47-D13 recorded).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — reference-of-record; §9 decisions log (S47-D13 folds in at T4).
- `glunk-works/scope-core` (pinned `7345de5`) — the package the two primitives are added to.
- `bounty-infra#86` — the pilot-consumer adopt-it follow-up.
