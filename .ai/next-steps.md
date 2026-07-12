# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is over** (Phases 1–6 complete; one path, four flags deleted, classic
recoverable at `pre-phase6-classic`).

**Current unit: sprint `32_artifact_refs_strip` — status `planning` (plan written, not yet
implemented). The plan is `sprints/32_artifact_refs_strip/sprint_plan.md`.**

## Just done (Opus/Architect, 2026-07-12)
- **Cleaned up the branch state.** `chore/27-archive` was already squash-merged (PR #38);
  local was stale. Fast-forwarded to `d41ffb7` and pruned 8 dead squash-merged locals.
- **Planned sprint 32 — and INVERTED it.** The planning pass found roadmap decision **FD3**
  had the direction backwards. FD3 was right that the strip is a refactor, not a deletion —
  but the field with no readers is **`artifact_refs`**, not `artifacts`:
  - `get_artifact` (the only function that loads a body from disk) has **zero** production
    callers, and nothing in `src/` reads `docs/artifacts/` back. `artifact_refs` is a
    **write-only mirror**.
  - `State.artifacts` has ~14 read sites across **8** persona/gate modules, and those bodies
    are fed **straight into the prompt-cache prefix** (`declarative/node.py:72-78` →
    system blocks; `llm/client.py:88-89` stamps `cache_control` on the last block).
  - The strip **saves zero tokens** either way — `State` is orchestrator-side and never
    enters a prompt. FD3's direction would have put a `write_text`→`read_text` round-trip
    *inside the cache prefix*, risking silent cache misses, for no gain.
  - A snapshot's **self-containment** is load-bearing: bodies follow the chdir into the
    worktree/clone, snapshots stay pinned to the main checkout. Stripping the inline bodies
    turns a snapshot into dangling pointers after a prune / a foreign clone / a cross-CWD
    resume (finding **R10**).

## Next
**Implement sprint 32, Tasks 1–4 (Sonnet/Coder).** Read the plan's locked decisions
**FD1–FD4** before touching code. Branch `sprint/32-artifact-refs-strip` off
`feat/mcp-langgraph-migration`; each task its own green commit, in order.

Three things that will bite:
1. **Task 3 is the sharp edge.** `State` is `extra="forbid"`, so removing `artifact_refs`
   is a **breaking** schema change (3 → 4). `migrate_state_payload` must **pop** the key or
   every existing v3 snapshot fails to load. Test it with a **populated** `artifact_refs`
   fixture — an empty `{}` would pass a broken pop-less migration.
2. **Do NOT touch the 8 artifact-reader modules.** They must come out byte-identical; a diff
   there means the sprint drifted back into FD3's direction.
3. **Do NOT delete the disk write.** It is **publication**, not externalization:
   `docs/artifacts/` is not gitignored and `flows/maintenance` runs `commit_all`, so the
   bodies ship as documentation in the **managed repo's PR**. `mirror_to_disk` is *renamed*
   `publish_artifacts` and demoted to a side effect — the write survives.

## HITL gate
None open yet. The PR touches `src/`, so `hitl-review.yml` is live: an **Opus HITL review in
a FRESH session** gates the merge (`/handoff` → new session → `/resume` → `/code-review`).

## Standing obligations (neither is a sprint-32 task; both are real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks that have **never been run** (§1, §5,
  §6, §7, §8): they need a real key, a real authenticated `gh`, or a daemon-bearing host.
  A green `hatch run test` says nothing about them. Sprint 32 adds no entry and does not
  touch this file. **Do not delete it.**
- **BL-3 (prompt-caching review)** — where real token savings actually live. Sprint 32 saves
  **zero** tokens by design; do not justify it on token grounds, and do not fold BL-3 into it.

## Pointers
- `sprints/32_artifact_refs_strip/sprint_plan.md` — the active plan (FD1–FD4 + 4 tasks).
- `docs/migration_roadmap.md` — **FD3 still reads as the old direction**; sprint 32 Task 4
  marks it *superseded* (preserving its text — the deferral reasoning was right, only the
  assumed direction was wrong) and flips the NEXT ACTION line.
- `docs/backlog.md` — BL-3, BL-8, BL-9.
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
