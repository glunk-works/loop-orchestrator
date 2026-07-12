# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is over** (Phases 1–6 complete; one path, four flags deleted, classic
recoverable at `pre-phase6-classic`).

**Current unit: sprint `32_artifact_refs_strip` — status `awaiting_hitl_review`.
Tasks 1–4 are implemented and committed on `sprint/32-artifact-refs-strip`. PR is open:
[#39](https://github.com/glunk-works/loop-engine/pull/39) (base `feat/mcp-langgraph-migration`).**

## Just done (Sonnet/Coder, 2026-07-12)
Implemented sprint 32's Tasks 1–4 per the locked decisions FD1–FD4, each its own green
commit (full suite green + lint/format clean before every commit):
- **Task 1** (`1d712d0`) — repointed the read path off `artifact_refs`: deleted
  `get_artifact` (zero production callers), `has_artifact` now checks `state.artifacts`
  directly.
- **Task 2** (`6d85b91`) — demoted `mirror_to_disk` → `publish_artifacts` (`State -> None`),
  a pure side effect. Publication into `docs/artifacts/<run_id>/` is kept (FD3 —
  `flows/maintenance` ships these as documentation in the managed repo's PR); only the
  state-mutating half died. Both `engine.py` call sites became bare statements.
- **Task 3** (`af61273`) — the sharp edge. Deleted `artifact_refs`/`ArtifactRef`/
  `artifact_digest` from `State`; `CURRENT_SCHEMA_VERSION` 3 → 4; `migrate_state_payload`
  now pops the retired key from any v1/v2/v3 payload. Tested against a **populated**
  `artifact_refs` fixture (an empty `{}` would have passed a broken pop-less migration).
  `default_artifact_path` kept — publication still needs it.
- **Task 4** (`0f94945`) — reconciled `docs/migration_roadmap.md` (FD3 marked
  *superseded by sprint 32's FD1*, original text preserved, not rewritten) and
  `CLAUDE.md`; flipped the NEXT ACTION line; discharged Phase 6's dangling Task-5 ⚠
  as "inverted, not executed as written."

**Verified invariant:** `git diff --stat` of the 8 artifact-reader modules
(`personas/{pm/persona,pm/critic_gate,architecture/persona,agile_sprint_breakdown/manifest,coder_iac/ralph,declarative/node,declarative/services}.py`,
`core/{gates,coder_gate}.py`) against the pre-sprint base shows **zero changes** — the
tell that the sprint stayed in the correct (inverted) direction.

**Opened PR #39** — title `refactor(state)!: strip artifact_refs, keep State.artifacts
as source of truth` (the `!` marks the `schema_version` 3→4 breaking bump), branch
pushed with `-u origin`.

## Next
**Get the Opus HITL review in a FRESH session, then post it on PR #39.** Sequence:
this `/handoff` (done) → **new session** → `/resume` → `/code-review` → post with
`gh pr review --comment` (never `--approve` — the human's merge is the approval).
`hitl-review.yml` is live (the PR touches `src/`).

The reviewer's sharpest questions (per the sprint plan):
1. **Did the 8 reader modules come out byte-identical?** (Verified above — confirm it
   still holds against PR #39's actual head, not just this session's local check.)
2. **Does a populated-`artifact_refs` v3 snapshot really still load?** See
   `tests/core/test_state.py::test_migrate_v3_payload_pops_populated_artifact_refs`.

## HITL gate
**OPEN.** PR #39 touches `src/`, so `hitl-review.yml` gates the merge. Needs a review
headed `**Opus/Architect HITL review (automated)**` with the fresh-session attestation,
posted against the PR's current head commit (`0f94945`).

## Standing obligations (neither is a sprint-32 task; both are real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks that have **never been run** (§1, §5,
  §6, §7, §8): they need a real key, a real authenticated `gh`, or a daemon-bearing host.
  A green `hatch run test` says nothing about them. Sprint 32 added no entry and did not
  touch this file. **Do not delete it.**
- **BL-3 (prompt-caching review)** — where real token savings actually live. Sprint 32
  saved **zero** tokens by design; do not retroactively justify it on token grounds.

## Pointers
- **PR #39** — https://github.com/glunk-works/loop-engine/pull/39
- `sprints/32_artifact_refs_strip/sprint_plan.md` — the plan (FD1–FD4 + 4 tasks, all done).
- `docs/migration_roadmap.md` — reconciled by Task 4: FD3 now reads *superseded (sprint 32,
  FD1 — direction inverted)*, NEXT ACTION line flipped off the artifacts strip.
- `docs/backlog.md` — unaffected by sprint 32.
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.

## Live external state — needs cleanup (HUMAN ACTION)
- **`glunk-works/loop-engine-v3-scratch`** (private) is still live, holding issues **#1–#6**.
  Delete it in the GitHub UI, then remove it from the fine-grained PAT's repo list (the PAT
  has no `Administration` permission by design, so it cannot delete repos — that stays a
  human checkpoint on the one irreversible action; it also carries an unexpected
  `Contents: Write` worth trimming while you're there).

## Working tree
- `main` ← `feat/mcp-langgraph-migration` is the integration branch; sprint work lands via
  `sprint/NN-slug` PRs based on it. Sprint branches squash-merge, so only the tip ships.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is
  tracked**.
- Branch `sprint/32-artifact-refs-strip` is clean, pushed with `-u origin`, HEAD `0f94945`
  matches PR #39's head.
