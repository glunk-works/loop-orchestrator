# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, `docs/backlog.md`, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**PIVOTED — building the SECOND loop.** The autonomous dev loop (`loops/default`) is paused.
Active initiative: **`loops/bounty/`** — an AI bug-bounty / vuln-detection → reporting
pipeline that drives the **`bounty-infra`** repo as its scan substrate. Architecture is set
and **merged** ([`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md),
PR #146). `sprint_status: planning`, assigned **Opus/architect**. **Next: the Phase 0 planning
pass.** HEAD `335ba56`, tree clean.

## Just done (Opus/architect session, 2026-07-19)
- **Closed out sprint 42** — posted the fresh-session Architect Review on #143 (rename), cleared
  the BL-35 stale-red, owner merged; cursor synced (#145).
- **Pivoted to the bounty loop.** Ingested the owner's six-doc Gemini sketch (guidelines, not
  rules), located the substrate (`bounty-infra` built; `appsec-triage-agent` an empty stub),
  and locked **four decisions** with the owner: `loops/bounty/` in-repo · report-only MVP ·
  JSON snapshots + Postgres inventory · Claude Opus/Haiku (lands BL-5).
- **Authored + merged `docs/bounty_loop_architecture.md`** (#146) — the reference-of-record:
  staged-persona pipeline over `State`, the two-store split + inventory schema, the structural
  scope-validation and exploitation-gating invariants, compute topology (§7, owner-accepted
  for now), phased roadmap, threat-model delta.
- **Reviewed `bounty-infra`** (security / IaC / best-practices) — filed **issues #6–#16**
  (4 High / 7 Medium) on that repo, rendered an
  [artifact](https://claude.ai/code/artifact/35f7f616-166e-499c-b532-b4269698dee9), and folded
  H2 (#7, no scope check) + M4 (#13, triage prompt-injection) into Phase 0 as the shared fixes.

## Next — run the Phase 0 planning pass (Opus/architect, WAIT-then-dialogue)
`/resume` **waits** here (planning is a one-question-at-a-time dialogue — that *is* the work;
never auto-start). **Read `docs/bounty_loop_architecture.md` first** (§8 = the roadmap). Break
**Phase 0** into a `sprints/NN_*/sprint_plan.md`:
1. Land **BL-5** per-persona routing (Opus deep-inspection/report, Haiku bulk triage; needs
   Haiku in pricing RATES) — also benefits the dev loop.
2. Stand up **`tools/inventory_db`** (sole Postgres-owning module) + the §4 schema
   (`targets`/`assets`/`endpoints`/`findings` + run linkage).
3. Build the **structural scope validator** (§5) — out-of-scope target rejected at the tool
   boundary, analog of `_validate_clone_dest`.
4. Build the **ingestion-sanitization seam** for scanner output (§10 prompt-injection defense).
5. Bump `State.schema_version` 5 → 6 + extend `migrate_state_payload`.

The next HITL Gate is the human's approval of that Phase 0 sprint plan.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **This is a context-refresh handoff, not a model switch** — Phase 0 planning stays
  Opus/architect, so `/clear` → `/model opus` → `/resume` in place is fine (no new window
  needed; that's only for the review-integrity boundary).
- The bounty loop's **invariants are non-negotiable**: scope validation is structural code
  (never the LLM's job); active exploitation gates through the existing escalation ladder.
- **Two paused dev-loop docs PRs are already merged** (#145, #146). Backlog items behind the
  pivot: BL-1/3/4, BL-24/32/33/36/37.
- **Before pushing code, run the FULL local gate** (lint → format → test) or `/ship`. **PR
  title ≤72 bytes** — `wc -c` first. **Never commit to `main`, merge, or force-push.**
- **GPG:** never run `.devcontainer/gpg-forward.sh` in a Cursor session; Timeout = answer the
  host pinentry and retry.

## Pointers
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — the bounty loop's reference-of-record. **Read first.**
- `glunk-works/bounty-infra` — the scan substrate; review issues #6–#16.
- [`docs/backlog.md`](../docs/backlog.md) — BL-5 is Phase 0's enabler; paused dev-loop items behind it.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — the migration (done); unrelated to this initiative.
