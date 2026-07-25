# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PR) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 47. Task 1 (dispatch half) is MERGED to `main`.
`sprint_status: implementing`, next up is Task 2, assigned Sonnet/coder.**
[PR #190](https://github.com/glunk-works/loop-orchestrator/pull/190) merged as `cad4db1`
with a green fresh-session Architect Review. The next unit is **Task 2 — the ingest
(untrusted-input) half** — a normal coding session.

## Just done (2026-07-25, Opus/architect — review session)
- **Posted the fresh-session Architect Review of PR #190** (`c1ef1dc`, authored none of
  the diff) with `gh pr review --comment` + the verbatim header/attestation. **Approve, no
  blocking findings.** Independently re-derived the diff and re-ran the load-bearing tests
  green: sole-`boto3`-importer boundary, the third-`gh`-consumer/count-stays-five
  subprocess guard, the B5 scope-raise input boundary, and the full `tools/recon` +
  `tools/s3_io` suites (22 passed). Confirmed the installed `scope_core` API matches,
  `hatch run audit` clean, `boto3` in a regenerated `sbom.json`, and no live caller wires
  the dispatcher yet (no reachable trust boundary).
- **Cleared the BL-35 stale-red** on `architect-review` (two runs on one SHA; the
  `pull_request` run fails before a review exists and never self-clears) — confirmed the
  signature and `gh run rerun`'d the old failed run (no push, no SHA change). PR went
  `CLEAN`, all 8 checks green.
- **Human merged PR #190** (`cad4db1`); pruned the merged `sprint/47-recon-data-path`
  branch.
- **Two non-blocking notes** left on the review for the record: the token-correlation
  substring match risks a prefix collision (settle against `bounty-infra#18`'s real
  contract), and a `completed`+non-`success` conclusion raises immediately (fail-closed by
  intent).

## Next — implement Task 2, the ingest half (Sonnet/coder)
Cut a fresh `sprint/47-recon-data-path` branch off current `main` and implement **Task 2**
per [`sprints/47_bounty_recon_data_path/sprint_plan.md`](../sprints/47_bounty_recon_data_path/sprint_plan.md):
parse the recon JSONL payload `tools/s3_io` fetches, apply `scope_core`
`is_in_scope`/`normalize` + `sanitize` (**P1-D6 output half** — filter+sanitize, the
deliberate counterpart to T1's input scope-raise), and upsert assets/endpoints into
`tools/inventory_db`. Work behind the hermetic `FakeReconDispatcher`/`InMemoryS3Fetcher`/
`InMemoryInventory` fakes T1 landed; **do not** wire the CLI/integration (that's T3). Run
the full green gate (`lint → format → test`) before pushing, open a PR based on `main`,
then run **`/critic-gate`** before `/handoff`. The Architect Review that follows must be a
**fresh session**, not the authoring one.

**HITL Gate: NONE OPEN.** Sprint 47 planning is fully signed off (11 micro-gates); the
4-task sprint is a defined spec. `sprint_status: implementing` + gate NONE OPEN + a defined
T2 spec ⇒ a Sonnet `/resume` **may auto-start** Task 2.

## Gotchas worth remembering
- **Verify `scope_core`'s `is_in_scope`/`normalize`/`sanitize` installed signatures**
  before relying on them (the same check T1 did for `validate_target`) — the package is an
  external SHA-pinned dep.
- **The dangerous sink is cross-repo.** T1's input boundary only scope-*raises*; the seed's
  real execution lives in `bounty-infra`'s recon workflow. T2 owns the *output* sanitize of
  whatever that workflow writes back — treat the fetched JSONL as fully untrusted input.
- **`bounty-infra#18` (dispatch contract) is a V-run precondition, blocked on #6.** T1–T3
  merge hermetically without it; the V-run + §10 discharge re-defer if it's not ready. Do
  **not** stamp the deferred Postgres smoke (§10) verified until the V-run runs.
- **The producer lives in `tools/recon`, injected via `loops/bounty` — never in
  `personas/bounty`** (`test_bounty_personas_import_nothing_from_tools` is live). That
  wiring is T3, not T2; noted so T2 doesn't regress it.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.

## Pointers
- [PR #190](https://github.com/glunk-works/loop-orchestrator/pull/190) — T1 dispatch half, **MERGED** (`cad4db1`).
- [`sprints/47_bounty_recon_data_path/sprint_plan.md`](../sprints/47_bounty_recon_data_path/sprint_plan.md) — the S47 plan (12 decisions, 4 tasks; T1 done, **T2 now**).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — reference-of-record; §9 (decisions log), §10 (threat delta), §11 (2026-07-25 redirection).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 OWED sprint-44 PG smoke; discharges in S47's V-run.
- **Backlog candidate, not yet filed:** `_DISALLOWED_OS_CALLS` in `tests/tools/test_subprocess_surfaces.py` misses `os.popen`/`os.posix_spawn`/`os.spawn*` (pre-existing, PR-190-unrelated). Consider filing to `docs/backlog.md`.
