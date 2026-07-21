# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1 (Recon + Surface-Mapping). `sprint_status: planning`, assigned
Opus/architect.** Phase 0 (Enablers) is **complete and archived** — all three sprints (43
BL-5 routing, 44 `inventory_db` + §4 schema, 45 scope validator §5 + ingestion seam §10)
merged. The next unit is the **Phase 1 planning pass**: decompose Recon into sprints and
write the first `sprints/NN_*/sprint_plan.md`. No sprint plan exists yet — writing it is the
first deliverable. **Planning is one question at a time (HITL micro-gates); wait for the
owner, don't auto-start.**

## Just done (2026-07-21) — sprint 45 closed, Phase 0 complete
- **T1** (Sonnet/coder, prior session): built `tools/scope_validator` (fail-closed `ScopeRules`
  allowlist + `from_target` structural adapter with no runtime `inventory_db` edge +
  `validate_target` + `is_action_banned` + `ScopeViolation`) and `tools/ingest.sanitize`
  (structural `Cf`-sweep normalizer), full hermetic suites + a hardened no-runtime-edge
  boundary guard. `/critic-gate` clean (architect + security-critic + guard-adversary).
  Merged as **PR #168**.
- **T1 architect-review** (Opus/architect, this session, fresh): re-derived all three
  critic-gate fix areas from the code, ran the full gate green (862 passed), posted the
  verbatim-header review with `gh pr review --comment`, cleared the **BL-35 stale-red** trap
  (`gh run rerun` the old `pull_request` run). Human merged #168.
- **T2** (Opus/architect, this session, docs-only): `CLAUDE.md` boundary bullet for the two
  new leaf modules + `docs/bounty_loop_architecture.md` §8 status / §9 **P0-D11..D16** / §10
  built-seam note. Merged as **PR #170**.
- **`/archive-sprint`**: flipped §8 to **Phase 0 ✅ complete**, snapshotted the sprint-45
  cursor to `.ai/archive/`, advanced `.ai/state.json` to Phase 1 planning.

## Next — plan Phase 1 (Recon), Opus/architect, one question at a time
Decompose **Phase 1 (Recon + Surface-Mapping)** into sprints and write the first
`sprint_plan.md`. Fold in, from the roadmap:
- **Mount the Phase-0 primitives at their first live consumer** — the scanning MCP tools'
  Pydantic boundary gets `scope_validator.validate_target` (reject out-of-scope before any
  subprocess, §5) and `ingest.sanitize` (scrub scanner/target text before the triage LLM,
  §10). This is exactly the P0-D11 deferral coming due.
- **The `schema_version` 5→6 bump lands here** (P0-D2) — with the first bounty `State` field
  (the Recon stage's typed output). Keep `migrate_state_payload` + `extra="forbid"` correct.
- **Discharge the OWED sprint-44 live Postgres round-trip smoke** (`DEFERRED_VERIFICATION.md`
  §10) — when the first `inventory_db` consumer + a real/dev PG land. Do not lose it.
- **The `workflow_dispatch` integration seam on `bounty-infra`** (coarse batch recon on
  Fargate; results → S3 → Postgres), per §7's compute topology.

## Gotchas worth remembering
- **Phase 1 is where `State` finally changes** — after all of Phase 0 was pure non-`State`
  infra. First `State`-touching PR ⇒ `schema_version` bump + migrate branch + fresh-session
  `architect-review`.
- **`scope_validator` matches via unanchored `re.search`** (locked P0-D13) — a Phase-1
  consumer writing `in_scope_regex` rules-of-engagement that must match a whole host exactly
  should anchor them (`^host$`).
- **The sprint-44 live Postgres smoke is genuinely OWED** — the `Jsonb(...)` adapter fix and
  the round-trip assertion have never run against a real Postgres (`LOOP_ORCHESTRATOR_INVENTORY_DSN`
  is unset per P0-D4). Discharge it in Phase 1, don't stamp it "verified."
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.
- **GPG signing** may time out in a Cursor session — answer the host pinentry and retry (hit
  this on the T2 commit this session; retry cleared it). Never run `gpg-forward.sh` in Cursor.
- **PR title ≤72 bytes, lower-case after `type(scope): `** — `wc -c` first. **Never commit
  to `main`, merge, or force-push.** **Full local gate (lint→format→test) before push.**

## Pointers
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — bounty loop reference-of-record (§3 stages, §5 scope validator [built], §6 escalation, §7 MCP servers + compute topology, §8 roadmap [Phase 0 complete], §9 decisions P0-D1..D16, §10 ingestion seam [built]).
- [`sprints/45_scope_validator_ingestion/sprint_plan.md`](../sprints/45_scope_validator_ingestion/sprint_plan.md) — the just-closed sprint's plan (template/precedent for the Phase-1 plan).
- [`sprints/44_inventory_db/sprint_plan.md`](../sprints/44_inventory_db/sprint_plan.md) — the `inventory_db` sprint's plan (the persistence layer recon writes into).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 = the OWED sprint-44 live Postgres smoke; discharge in Phase 1.
- `.ai/archive/45_scope_validator_ingestion-next-steps.md` — the archived sprint-45 final cursor.
