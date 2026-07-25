# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PR) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 47 Task 1 (dispatch half) is IMPLEMENTED.
`sprint_status: awaiting_architect_review`, assigned Opus/architect.**
[PR #190](https://github.com/glunk-works/loop-orchestrator/pull/190) is open against
`main` (branch `sprint/47-recon-data-path`, head `c1ef1dc`). `/critic-gate` has run
(three critics, owner-confirmed) and its findings are already resolved in the pushed
diff. The next unit is the **fresh-session Architect Review** — a genuinely new session,
not this one.

## Just done (2026-07-25, Sonnet/coder)
- **Verified the scope-core drift flagged by the previous session doesn't diverge.**
  `scope_core`'s installed API (`validate_target(rules, seed) -> None` raising
  `ScopeViolation`; `ScopeRules` frozen/`extra="forbid"`) matches the plan's assumptions
  exactly — no escalation to Opus was needed.
- **Implemented Task 1** per `sprints/47_bounty_recon_data_path/sprint_plan.md`:
  `tools/s3_io` (`S3Fetcher` protocol, `Boto3S3Fetcher` real impl — sole `boto3` importer,
  pinned by a boundary test — `InMemoryS3Fetcher` fake, a `botocore.stub.Stubber`
  request-shape test), `tools/recon` (`ReconRequest` + `build_recon_request`'s
  `validate_target`-raise input boundary — rules passed as a parameter, B5 — the
  `ReconDispatcher` protocol, `GhReconDispatcher` real impl owning the S47-D8
  token-correlation + S47-D9 bounded-poll logic against `gh run list`, `FakeReconDispatcher`).
  `tests/tools/test_subprocess_surfaces.py` learned `tools/recon/dispatch.py` as a
  **3rd `gh` consumer** (surface count stays five, pinned by a dedicated test).
- New `boto3==1.43.56` runtime pin ⇒ `sbom.json` regenerated, `hatch run audit` green.
- Pushed and opened **PR #190** (commit `23cf8e9`).
- Ran **`/critic-gate`**: proposed `security-critic` + `architect` + `guard-adversary`
  (all three owner-confirmed) against the diff, in parallel.
  - **security-critic:** no reachable trust-boundary issue in this diff (no live caller
    wires `dispatch` yet). Two forward-looking notes, both accepted as documented
    judgment calls rather than fixed: (1) `ReconRequest` is directly constructible
    without going through `build_recon_request`'s scope check — matches this codebase's
    existing non-type-enforced domain-model convention (`Target`/`Asset`/`Endpoint` are
    equally directly constructible); (2) the seed isn't shape-sanitized before reaching
    the `gh workflow_dispatch` input — already a locked, deliberate P1-D6 split (input =
    scope-raise only, output = filter+sanitize in T2), and the actual dangerous sink is
    in `bounty-infra`'s workflow, cross-repo.
  - **architect:** three LOW findings, all fixed in commit `c1ef1dc`: the `gh run list`
    poll argv was never asserted by a test (only dispatch's argv was); no test proved
    the token-correlation poll skips a run carrying a *different* token; the
    fail-closed-on-transient-`gh`-failure behavior in `await_completion` was undocumented.
    Added two tests + a clarifying docstring. Everything else (module placement, the B5
    boundary, the "3rd `gh` consumer/count-stays-five" claim, Protocol design) verified clean.
  - **guard-adversary:** confirmed this PR's own guard edit (the third `gh` consumer,
    count-stays-five) holds under adversarial probing — the dict entry is load-bearing,
    aliased-import indirection doesn't slip past the AST walker, a mutated surface-name
    regression is caught. **Also found**, pre-existing and unrelated to this PR:
    `_DISALLOWED_OS_CALLS` misses `os.popen`/`os.posix_spawn`/`os.spawn*` — a genuine
    shell-out the guard's stated intent ("nothing else shells out") should catch but
    doesn't. Not filed as a BL-NN yet (see Pointers) — didn't bundle an uninvited fix
    into this PR.
- Full local gate green throughout: `hatch run lint && format && test` — 856 passed,
  4 skipped (psycopg live-integration tests, no DSN in this environment), no lint/format
  deltas after the critic-gate fix commit.

## Next — post the Architect Review (Opus/architect, FRESH session)
Run `/code-review` against PR #190, then post with `gh pr review --comment` opening
with the verbatim two-line header + attestation from `.ai/context/workflow.md`. This
must be a session that authored none of this diff — not a `/model` switch mid-session.
After a clean/approved review, the human merges; the next coder session starts **Task 2**
(the ingest half — untrusted-input parsing, `is_in_scope`/`normalize`, `sanitize`,
`inventory_db` upsert; see the plan's Task 2).

**HITL Gate: NONE OPEN.** The next required check is the `architect-review` CI gate on
PR #190. `sprint_status: awaiting_architect_review` (not `implementing`), so `/resume`
will state the pick-up point and wait rather than auto-start — correct, since posting a
review needs an explicit `/code-review` trigger, not silent auto-start.

## Gotchas worth remembering
- **`main` advanced during this session** (dependency bumps `#186`/`#187` + the previous
  session's own cursor-sync `#189`) — local `main` was fast-forwarded to `e7c090e` before
  this handoff. PR #190 was cut from the older `3d03d30`; no conflict expected (unrelated
  files) but worth a glance if the review session sees anything unexpected.
- **The producer lives in `tools/recon`, injected via `loops/bounty` — never in
  `personas/bounty`** (`test_bounty_personas_import_nothing_from_tools` is live). Not
  touched by T1 (that's T3); noted so T2/T3 don't regress it.
- **`bounty-infra#18` (dispatch contract) is a V-run precondition, blocked on #6.** T1–T3
  merge hermetically without it; the V-run + §10 discharge re-defer if it's not ready.
- **New dep `boto3`** ⇒ `sbom.json` regenerated + `audit` green (done, this PR).
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.

## Pointers
- [PR #190](https://github.com/glunk-works/loop-orchestrator/pull/190) — T1 dispatch half, awaiting the Architect Review.
- [`sprints/47_bounty_recon_data_path/sprint_plan.md`](../sprints/47_bounty_recon_data_path/sprint_plan.md) — the S47 plan (12 decisions, 4 tasks, PR structure).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — reference-of-record; §9 (decisions log), §10 (threat delta).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §10 OWED sprint-44 PG smoke; discharges in S47's V-run.
- `bounty-infra` #18 (dispatch contract), #7/#13 (harden), #19 (working method) — cross-repo, tracked there, not S47 code.
- **Backlog candidate, not yet filed:** guard-adversary's finding that `tests/tools/test_subprocess_surfaces.py`'s `_DISALLOWED_OS_CALLS` misses `os.popen`/`os.posix_spawn`/`os.spawn*` — pre-existing, PR-190-unrelated. Consider filing to `docs/backlog.md` during the review session.
