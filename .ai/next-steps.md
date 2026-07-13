# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is fully closed** (Phases 1–6). Nothing here is migration work.

**Current unit: sprint `33_ci_title_starvation` (BL-10) — status `awaiting_hitl_review`.**
**All five tasks are done.** [PR #43](https://github.com/glunk-works/loop-engine/pull/43) is
`CLEAN`, all eight checks green on head `4b61fd1`. **Nothing is left for Claude but the
archive** — the next move is the human's.

## Just done (Opus/Architect session, 2026-07-12)
- **Unblocked the PR.** It was `CONFLICTING`/`DIRTY` with an **empty check rollup** — *zero CI
  had ever run on it, silently*. Merged the base in (`4ca13e9`, a merge commit — **not** a
  rebase; the branch was already pushed), keeping this branch's `.ai/next-steps.md`. Net tree
  diff vs. the pre-merge head: **empty**, confirming the base's `476ce8d` was byte-identical
  content under a different SHA.
- **Task 5 — BL-10 closed by live observation, not assertion.** Set a 111-char (but otherwise
  valid) title, then close+reopen to fire `ci.yml` with the bad title live. `pr-title` went
  **red** and the heavy chain **ran anyway, all six jobs green on the same commit — zero
  `skipped`**. That state was unreachable before this sprint.
- **FD2 closed.** Editing the title back re-ran `pr-title` alone (green, via `edited`), fired
  **no** `ci.yml` run, and left the prior chain at `success` — not `cancelled`. A prose edit can
  no longer reach the code chain.
- **Fresh-session Opus HITL review posted** (`--comment`, never `--approve`). One non-blocking
  finding, **already applied in `4b61fd1`**: the FD5 test pinned the *job id*, but branch
  protection matches the *check-run name* — which is `jobs.<id>.name` when present and falls
  back to the id only when absent. An innocuous `name:` override would have renamed the check,
  stranded the required check, and kept the old test green. Now asserted away. Suite: **541
  passed**, lint/format clean.

## 🔴 FD5 came back with a much bigger answer — new **BL-11**
Checking FD5 in the GitHub UI revealed the repo has **no branch protection and no rulesets at
all**. Rulesets `[]`; the *effective* rules endpoint for the base branch `[]`; no required
reviews. **So no check is required.** `lint`/`test`/`pr-title`/`architect-review` are all
computed and reported — and **enforce nothing**. A red PR can be merged; the base branch can be
pushed to directly.

- **FD5 is moot today, load-bearing tomorrow.** There is no required check to strand. The `4b61fd1`
  fix is still right — it protects the moment protection is added.
- **`mergeStateStatus: CLEAN` proved nothing.** With no rules configured, nothing can be violated.
  Don't read `CLEAN` as evidence of enforcement again.
- **The real casualty is `architect-review`.** `CLAUDE.md` called it "a CI gate, not a courtesy."
  It fails correctly — and blocks nothing. The gate built *because* a convention got skipped
  (sprint 27 Task 8) is itself, today, only a convention. **Logged as BL-11; `CLAUDE.md` corrected.**

## Next — the human, then Opus
1. **Human (BL-11, the real one):** add a repository ruleset on `main` + `feat/**` requiring the
   eight checks (`lint`, `format-check`, `test`, `secrets-scan`, `dependency-audit`, `sbom`,
   `pr-title`, `architect-review`) and a PR before merging. Claude is **403** here and cannot do
   or verify it. Until then every "must pass" in `CLAUDE.md` / `GLOBAL_DEFINITION_OF_DONE.md` /
   `workflow.md` is **aspirational**.
2. **Human:** merge PR #43. **The merge is the approval; Claude never merges.**
3. **Opus, after the merge:** run **`/archive-sprint`** to retire sprint 33, then plan the next
   unit — **BL-11 is the obvious candidate**, and it is mostly a settings change plus a doc
   reconciliation, not code. **Do not start new work on this branch** — a squash-merged branch is
   dead; cut a fresh one from the updated `feat/mcp-langgraph-migration`.

> ⚠ Pushing `4b61fd1` moved the head SHA. That would normally invalidate a commit-pinned
> `architect-review`; only `hitl-review.yml`'s `^src/` exemption (this PR touches no `src/`)
> made it harmless. **If a future commit on this branch touches `src/`, a fresh-session review
> against the new head is required.**

## Standing obligations (not sprint-33 tasks; all still real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8) **never run**. Don't delete it.
- **Two unfixed findings from PR #39** — `publish_artifacts` reads every artifact off disk on every
  stage while both docstrings claim it *"does no I/O"*; that read-back uses `Path.read_text()` with
  no explicit encoding. Out of sprint 33's scope (they touch `src/`); still open.
- **Human, carried across sprints:** after PR #43 merges, delete `docs/handoff-sprint-33` (now
  redundant twice over). `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6) is still
  live — delete it in the UI, then trim the PAT's repo list. Neither done yet.

## Pointers
- [`sprints/33_ci_title_starvation/sprint_plan.md`](../sprints/33_ci_title_starvation/sprint_plan.md) — the sprint. FD1–FD5, Tasks 1–5, **all complete**.
- [PR #43](https://github.com/glunk-works/loop-engine/pull/43) — head `4b61fd1`, base `feat/mcp-langgraph-migration`. Task 5's observations and the HITL review are both posted there.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-10 resolved**, FD2/FD3 recorded. **BL-11 is new and unresolved.**
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed, untouched by sprint 33.
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.

## Working tree
- `sprint/33-ci-title-starvation` (at `4b61fd1`, pushed, clean) is the active branch. PR base is
  **`feat/mcp-langgraph-migration`**. Branches squash-merge — **a squash-merged branch is dead;
  never reuse one.**
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is tracked.**
