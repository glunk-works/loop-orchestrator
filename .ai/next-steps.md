# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 45 (scope validator §5 + ingestion-sanitization seam §10).
`sprint_status: awaiting_architect_review`, assigned Opus/architect.** Task 1 is
implemented, `/critic-gate` ran and is clean, and the combined `src/` PR is open:
[PR #168](https://github.com/glunk-works/loop-orchestrator/pull/168). Sprint 45 is Phase 0's
**final** sprint. After the T1 architect-review + Task 2 (docs) + merge, Phase 0 is complete
and Phase 1 (Recon) begins.

## Just done (2026-07-20) — sprint-45 Task 1 (Sonnet/coder)
- Cut `sprint/45-scope-validator-ingestion` from up-to-date `main` (per the prior session's
  instruction — implementation never lands on a docs branch).
- Built `tools/scope_validator/` (`ScopeRules` frozen value object + `from_target` structural
  adapter with **no runtime `inventory_db` edge** + `validate_target` fail-closed allowlist +
  `is_action_banned` classifier + `ScopeViolation`) and `tools/ingest/sanitize.py` (structural
  normalizer), each with full hermetic test suites and boundary guards, per
  `sprints/45_scope_validator_ingestion/sprint_plan.md` (P0-D11..D16).
- Ran the full local gate (lint → format → test) green, then `/critic-gate` with the human
  confirming `architect` + `security-critic` + `guard-adversary`, all in parallel:
  - **architect**: clean, no blocking findings — verified the fail-closed edges, the
    frozen+`PrivateAttr` compiled-regex pattern, and the zero-runtime-edge claim directly.
  - **security-critic**: found the sanitizer's original 5-codepoint zero-width strip missed
    the Unicode **Tags block** (invisible-instruction smuggling) and **bidi
    override/isolate** characters (Trojan-Source-class display spoofing) — fixed by
    generalizing to a Unicode **`Cf`-category sweep** + an explicit variation-selector
    strip (still structural, not a phrase blocklist — P0-D15 intact). Also flagged
    `validate_target`'s unanchored `re.search` (an unanchored `in_scope_regex` matches a
    superstring host) — this is the **locked P0-D13 semantics, not a bug**; added a
    docstring note + a pinning test instead of re-litigating it.
  - **guard-adversary** (BL-32, worktree): found the new no-runtime-edge boundary guard
    (`test_boundary.py`) stayed **GREEN** under three genuine runtime-edge shapes — a
    **relative import**, a **locally-shadowed `TYPE_CHECKING`**, and a **dynamic
    `importlib.import_module`/`__import__`** call. Hardened the guard to resolve relative
    imports to their absolute target, verify `TYPE_CHECKING` is actually bound from
    `typing` (not shadowed), and flag dynamic imports; added a regression test per finding.
  - All fixes landed in the same PR; re-ran the full local gate green (862 passed, 4
    pre-existing skips) before pushing.
- `/ship`: committed (`0cbd101`), pushed `sprint/45-scope-validator-ingestion`, opened
  [PR #168](https://github.com/glunk-works/loop-orchestrator/pull/168) against `main`.
  **Not merged** — needs the fresh-session `architect-review`.

## Next — the T1 architect-review (Opus/architect, FRESH session)
**Next HITL Gate: the T1 `architect-review` on PR #168** — required before merge (the
`architect-review` CI check). Read the diff, confirm the critic-gate fixes above are sound
(don't just re-trust the summary — verify), then post with `gh pr review --comment` (never
`--approve`) carrying the **verbatim** two-line header + attestation block from
`.ai/context/workflow.md`. Watch the **BL-35 stale-red trap** (`architect-review` fires on
both `pull_request` and `pull_request_review`; BLOCKED + rollup FAILURE ⇒ `gh run rerun`
the OLD run).

After the review posts and a human merges PR #168: **Task 2** (docs-only,
`architect-review`-exempt) — a `CLAUDE.md` "Enforced module boundaries" bullet for the two
new leaf modules, and `docs/bounty_loop_architecture.md` §8 status + §9 `P0-D11..D16` +
a §10 note. Then the **sprint-45 completion Gate** (`/archive-sprint`, Phase 0 → done).

## Gotchas worth remembering
- **`schema_version` 5→6 stays DEFERRED to Phase 1** (P0-D2) — sprint 45 is pure non-`State`
  infra; no `State` field, no `migrate_state_payload` branch. PR #168 confirms this holds.
- **`scope_validator` has NO runtime import edge onto `inventory_db`** (P0-D12) — verified
  directly by `architect`, and the boundary guard is now hardened against relative-import /
  shadowed-`TYPE_CHECKING` / dynamic-import evasion (BL-32 findings, all fixed).
- **The sanitizer's invisible-character strip is now a `Cf`-category sweep**, not an
  enumerated codepoint list — still structural (P0-D15), just complete. Variation selectors
  (Mn category) get a narrow explicit range alongside it; ordinary combining marks are
  untouched.
- **`validate_target` matches via unanchored `re.search`** — documented and pinned by a
  test, not changed. A future Phase-1 consumer writing `in_scope_regex` patterns should
  anchor them (`^host$`) for exact-host matching.
- **`DEFERRED_VERIFICATION.md` §10 still owed** — the sprint-44 live Postgres round-trip;
  discharge in Phase 1 when the first inventory consumer + a real PG exist.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first. **Never commit
  to `main`, merge, or force-push.** **Full local gate (lint→format→test) before push.**

## Pointers
- [PR #168](https://github.com/glunk-works/loop-orchestrator/pull/168) — the open sprint-45 Task 1 `src/` PR (`sprint/45-scope-validator-ingestion`, commit `0cbd101`). Needs the fresh-session `architect-review`.
- [`sprints/45_scope_validator_ingestion/sprint_plan.md`](../sprints/45_scope_validator_ingestion/sprint_plan.md) — the approved sprint-45 plan (tasks, P0-D11..D16, acceptance criteria).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — bounty loop reference-of-record (§5 scope validator, §6 escalation, §10 ingestion/threat-model, §8 roadmap, §9 decisions P0-D1..D16).
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the prior sprint's plan (the template/precedent).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = the owed sprint-44 live Postgres smoke.
