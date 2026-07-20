# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 45 (scope validator §5 + ingestion-sanitization seam §10).
`sprint_status: implementing`, assigned Sonnet/coder.** The sprint-45 plan is **written and
HITL-approved** ([`sprints/45_scope_validator_ingestion/sprint_plan.md`](../sprints/45_scope_validator_ingestion/sprint_plan.md)).
Sprint 45 is Phase 0's **final** sprint — build the two security invariants as pure leaf
primitives with **no live consumer** (the scanning MCP tools that mount them are Phase 1).
After sprint 45, Phase 1 (Recon) begins. Second loop (`loops/bounty/`) is the active
initiative; the dev loop (`loops/default`) stays paused.

## Just done (2026-07-20) — sprint-45 planning pass (Opus/architect)
- **Ran the six-micro-gate planning pass** and wrote `sprints/45_scope_validator_ingestion/sprint_plan.md`.
  Locked decisions **P0-D11..D16** (owner-confirmed; recorded in the plan, to be added to
  `bounty_loop_architecture.md` §9 in Task 2):
  - **D11** deliverable = the two primitives **only, no consumer** (scanning MCP tools = Phase 1).
  - **D12** a **standalone `ScopeRules` value object** + `from_target` structural adapter — **no
    runtime edge** onto `inventory_db` (`Target` is `TYPE_CHECKING`-only).
  - **D13** scope = **fail-closed allowlist**: ≥1 in-scope AND 0 out-of-scope; deny wins; empty
    in-scope denies all; raises `ScopeViolation`.
  - **D14** `is_action_banned` = pure classifier now; reject-vs-escalate **policy deferred** to the
    Phase-3 consumer (§6).
  - **D15** sanitizer = **structural/mechanical** only (control/ANSI/zero-width strip, NFKC,
    collapse, length cap); **no** phrase blocklist.
  - **D16** PR structure = **one combined `src/` PR** (both primitives) + a docs PR → one
    fresh-session `architect-review` cycle.
- **Planning Gate: approved** by the owner.

## Next — implement Task 1 (Sonnet/coder)
**Task 1 (one `src/` PR):** build `tools/scope_validator/` (`ScopeRules` + `from_target` +
`validate_target` + `is_action_banned` + `ScopeViolation`) and `tools/ingest/` (`sanitize`),
each with full hermetic tests and the boundary/no-runtime-edge guards. **No new dependency**,
no `.sql`, no `State` touch, no `sbom`/`audit` delta. Then `/handoff` → fresh session → the
Opus fresh-session `architect-review` on the T1 PR. Task 2 is docs-only (exempt).

**Next HITL Gate:** none open. The next Gate is the **T1 `architect-review`** (fresh Opus
session, after implementation) and then the sprint-45 completion Gate (merged PRs).

## Gotchas worth remembering
- **`schema_version` 5→6 stays DEFERRED to Phase 1** (P0-D2) — sprint 45 is pure non-`State`
  infra; no `State` field, no `migrate_state_payload` branch.
- **`scope_validator` must have NO runtime import edge onto `inventory_db`** (P0-D12) — the
  `Target` reference is `TYPE_CHECKING`-only; pin it with the import-graph assertion.
- **Fail-*open* is the bug to avoid** — empty `in_scope_regex` must DENY, and an out-of-scope
  match must veto even when an in-scope also matches. Pin both edges with explicit tests.
- **No new subprocess surface / no new dependency** — the five sanctioned subprocess surfaces
  and the keyring/psycopg boundaries stay unchanged; both new modules are pure leaves.
- **`DEFERRED_VERIFICATION.md` §10 still owed** — the sprint-44 live Postgres round-trip;
  discharge in Phase 1 when the first inventory consumer + a real PG exist.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first. **Never commit
  to `main`, merge, or force-push.** **Full local gate (lint→format→test) before push.**
- **The T1 `src/` PR needs a FRESH-session architect-review** — watch the BL-35 stale-red trap
  (`architect-review` fires on both `pull_request` and `pull_request_review`; BLOCKED + rollup
  FAILURE ⇒ `gh run rerun` the OLD run).

## Pointers
- [`sprints/45_scope_validator_ingestion/sprint_plan.md`](../sprints/45_scope_validator_ingestion/sprint_plan.md) — **the approved sprint-45 plan** (tasks, P0-D11..D16, acceptance criteria). Read first.
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — bounty loop reference-of-record (§5 scope validator, §6 escalation, §10 ingestion/threat-model, §8 roadmap, §9 decisions P0-D1..D16).
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the just-completed sprint's plan (the template/precedent) — `tools/inventory_db/models.py::Target` is what `ScopeRules.from_target` reads.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = the owed sprint-44 live Postgres smoke.
- [PR #167](https://github.com/glunk-works/loop-orchestrator/pull/167) — the open sprint-45-setup docs PR (archive sprint 44 + advance cursor + this plan).
