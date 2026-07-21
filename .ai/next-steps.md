# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 47 (recon data path): PLANNING COMPLETE, ready to implement.**
`sprint_status: implementing`, next model **Sonnet/coder**. The plan
(`sprints/47_bounty_recon_data_path/sprint_plan.md`) is written and owner-approved across
11 HITL micro-gates + the cross-repo wrap+harden posture. Start with **Task 1**.

## Just done (2026-07-21) — sprint 47 planning pass (Opus/architect)
- **Wrote `sprints/47_bounty_recon_data_path/sprint_plan.md`** — the recon data path
  (`gh workflow_dispatch` → S3 → parse → scope-filter/sanitize → `inventory_db`, its first
  consumer), fully hermetic behind three injected seams, one authorized V-run vs
  `scanme.nmap.org` that also discharges the OWED §10 PG smoke. **12 decisions (S47-D1..D12).**
- **Ruthless self-review folded in** — 5 blocking fixes (producer lives in `tools/recon` not
  `personas/bounty` or a live boundary test fails; UUID→str artifact; anchored scanme RoE;
  import-safe `build_bounty_loop(recon_producer=…)`; `get_target` → T3) + quality fixes
  (`is_in_scope` predicate, `ingest.normalize`, boto3 `Stubber` test, behavioral assertions).
- **4 execution-contract gates resolved (S47-D8..D11)** — correlation-token dispatch,
  bounded-poll block, scope-validated `--seed`, artifact=asset-id-strings + endpoints-under-
  in-scope-assets.
- **Cross-repo hardening filed against `bounty-infra`** (wrap+**harden**, not wrap-only):
  **#18** (the S47-D8 dispatch contract, built on #6's injection fix), wrap+harden comments
  on **#7**/**#13**, and **#19** (adopt the loop-orchestrator working method + branch
  protection; closes #8/#9). Recorded as **S47-D12**.

## Next — implement Task 1 (Sonnet/coder)
**T1 (dispatch half, one `src/` PR):** `tools/s3_io` (sole `boto3` importer + pin + `sbom`/
`audit` + `Stubber` test), `tools/recon` input model + `validate_target`-raise boundary +
`ReconDispatcher` (real `gh` impl owning the S47-D8 token correlation + S47-D9 bounded poll,
+ fake), and the subprocess-surface test learning the **3rd `gh` consumer** (count stays
five). Then T2 (ingest/untrusted path) → T3 (producer swap + CLI) → T4 (docs). See the plan's
Tasks + PR-structure notes.

**HITL Gate: NONE OPEN.** Planning is signed off; `/resume` may auto-start T1. The next gate
is the **fresh-session `architect-review`** on T1's PR (it touches `src/` — do **not** review
in the authoring session; `/handoff` → new window → `/resume` → `/code-review` → post the
verbatim header).

## Gotchas worth remembering
- **The producer lives in `tools/recon`, injected via `loops/bounty` — never in
  `personas/bounty`** (`test_bounty_personas_import_nothing_from_tools` is live). `personas/
  bounty` stays tools-free; the shell is byte-identical to S46 (swap only the collaborator).
- **`build_bounty_loop(recon_producer=fixture_asset_inventory)` default keeps `BOUNTY_LOOP`
  import-safe** — no `boto3`/`psycopg` client at import.
- **`bounty-infra#18` (dispatch contract) is a V-run precondition, blocked on #6.** T1–T3
  merge hermetically without it; the V-run + §10 discharge re-defer if it's not ready. Do
  **not** stamp `DEFERRED_VERIFICATION.md` §10 until the V-run runs.
- **New dep `boto3`** ⇒ `hatch run sbom` regen + `audit` green (T1). **PR title ≤72 bytes.**
  **Never commit to `main`, merge, or force-push.** Full local gate (lint→format→test) before push.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.

## Pointers
- [`sprints/47_bounty_recon_data_path/sprint_plan.md`](../sprints/47_bounty_recon_data_path/sprint_plan.md) — the S47 plan (12 decisions, 4 tasks, PR structure).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — reference-of-record; §9 (decisions log — T4 folds in S47-D1..D12), §10 (threat delta — T4 corrects to wrap+harden).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 OWED sprint-44 PG smoke; discharges in S47's V-run.
- `bounty-infra` #18 (dispatch contract), #7/#13 (harden), #19 (working method) — cross-repo, tracked there, not S47 code.
