# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 0, sprint 44 (`tools/inventory_db` + the §4 Postgres schema).
`sprint_status: awaiting_architect_review`, assigned Opus/architect.** Task 1 (the
hermetic core, driver-free) is implemented and pushed on `sprint/44-inventory-db`, PR
[#159](https://github.com/glunk-works/loop-orchestrator/pull/159) open against `main`.
CI is green on every required check except `architect-review`, which is next. Sprint 43
(BL-5 model routing) is complete and archived. The second loop (`loops/bounty/`) is the
active initiative; the dev loop (`loops/default`) stays paused.

## Just done (2026-07-19) — sprint 44 Task 1 (Sonnet/coder)
- **Implemented `tools/inventory_db`'s hermetic core** on `sprint/44-inventory-db` (cut
  from `main`, which already carried the sprint-44 plan via merged PR #158):
  `inventory.sql` (the §4 schema, idempotent `CREATE ... IF NOT EXISTS`, UUID PKs,
  the three natural-key UNIQUE constraints, `findings.run_id` as a no-FK soft ref,
  `validation_status TEXT + CHECK` per P0-D10), `extra="forbid"` Pydantic domain models
  + `NewType` ID types, the write-only `InventoryRepository` Protocol, and the
  `InMemoryInventory` fake. No `psycopg` import, no dependency change (T2's job). 19
  hermetic tests; full suite 815 passed; confirmed `inventory.sql` lands in a built wheel.
- **Opened PR #159**, title `feat(inventory-db): add T1 hermetic core, models, fake repo`
  (fixed once for the Conventional-Commits lower-case-start rule — `pr-title` failed on
  the first attempt). All CI-chain checks green: `lint`, `format-check`, `test`,
  `secrets-scan`, `dependency-audit`, `sbom`, `pr-title`. `architect-review` red as
  expected — not yet reviewed.
- **Ran `/critic-gate`** (human confirmed both `architect` + `security-critic`,
  `guard-adversary` correctly judged not-yet-applicable — the psycopg boundary test it
  would guard doesn't exist until T2). `security-critic`: clean, no findings.
  `architect`: found `test_all_statements_are_idempotent_creates` silently checked only
  3 of 4 tables (`targets`' statement got dropped — it shares a chunk with the leading
  file-comment when the test split naively on `;`). Fixed by stripping comment lines
  globally before splitting, plus an explicit `len(statements) == 4` assertion. Also
  added a guard test (prompted by both critics) pinning the SQL `CHECK` constraint's
  allowed `validation_status` values against the Pydantic `Literal`'s allowed values, so
  the two can't silently drift apart. Two lower-severity architect notes — the fake's
  upsert "full-replace" semantics being under-specified, and inconsistent
  `ValidationError→InventoryError` wrapping across the three upsert methods — are T2
  design questions, not T1 defects; left as forward notes, not spec-creep fixes. Pushed
  (`d9967da`); full gate + all CI checks re-confirmed green.

## Next — post the Architect Review (Opus/architect, FRESH session)
In a **new session** (not `/clear` — the fresh-session attestation is an integrity
property, not just context hygiene): `/model opus` → `/resume` → `/code-review` the
diff on `sprint/44-inventory-db` (PR #159) → post the Architect Review with the
**verbatim** two-line header + attestation block from `.ai/context/workflow.md` against
the PR's current head commit (`d9967da`). Watch the **BL-35 stale-red** trap
(`architect-review` fires on both `pull_request` and `pull_request_review`; BLOCKED +
rollup FAILURE ⇒ `gh run rerun` the OLD run).

After the owner merges T1, continue with **Task 2** (Sonnet/coder): `PsycopgInventory` +
`bootstrap()` + `build_inventory_from_env()` (env-var DSN, fail-closed) + the
`psycopg[binary]` dep pin + `sbom` regen + the sole-importer boundary test (modeled on
`tests/tools/test_keyring_boundary.py`, guard-adversary-verified) + the
skip-when-no-DSN integration test — on its own fresh branch/PR per
`sprints/44_inventory_db/sprint_plan.md`.

**Next HITL Gate:** none open. The planning micro-gates are closed; the next Gate is the
sprint-44 **completion** Gate (the owner's merges of the T1/T2/T3 PRs). PR #159 still
needs the fresh-session `architect-review` CI gate (not itself a HITL micro-gate) before
it's mergeable.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **`tools/inventory_db` is a new enforced module boundary** — the sole `psycopg` importer
  (T2); pin it with an AST test modeled on `tests/tools/test_keyring_boundary.py`, landed
  in the **same PR (T2)** as the psycopg import it guards, and have guard-adversary confirm
  it goes RED under a planted violation (BL-15).
- **Parameterized SQL only** — the SQL-sink analog of fixed-argv/`shell=False`; T1's DDL
  has zero interpolation (security-critic-confirmed) — keep it that way through T2, before
  sprint 45's untrusted scanner-output ingestion flows through these write methods.
- **The integration test must SKIP (not ERROR) with no DSN set** (T2) — verify `hatch run
  test -k inventory` shows it skipped in a no-DSN run before pushing.
- **T2 adds `psycopg[binary]`** ⇒ regen `sbom.json` (`hatch run sbom`) + clean `hatch run
  audit`, both CI gates.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first; the
  Conventional-Commits regex also rejects an upper-case subject start (bit T1 on the
  first `gh pr create`). **Never commit to `main`, merge, or force-push.** **Full local
  gate (lint→format→test) before push** (memory: #141).

## Pointers
- [PR #159](https://github.com/glunk-works/loop-orchestrator/pull/159) — sprint-44 Task 1, awaiting `architect-review`.
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record (§4 persistence + schema, §8 roadmap, §9 decisions log P0-D1..D10). **Read first.**
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the sprint-44 plan (T1/T2/T3, P0-D7..D10, PR structure, security invariants).
- [`docs/backlog.md`](../docs/backlog.md) — paused dev-loop items behind the bounty pivot.
