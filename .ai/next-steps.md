# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is over, and as of sprint 32 it is fully closed.** Phases 1–6 complete;
one path; four flags deleted; classic recoverable at `pre-phase6-classic`. Sprint 32
discharged Task 5 — the last dangling ⚠ on the board.

**There is no current sprint, and no next one is pre-selected.** For the first time
there is no roadmap phase to advance. Status: `planning` (Opus/Architect).

## Just done (Opus/Architect review session, 2026-07-12)
- **Sprint 32 (`artifact_refs` strip) is merged and approved** — PR
  [#39](https://github.com/glunk-works/loop-engine/pull/39), squash `3db3237`. HITL review
  posted in a fresh session; the owner's merge is the approval. Eight findings, none blocking.
  Both of the plan's sharp questions held: the 8 artifact-reader modules came out
  **byte-identical** to the pre-sprint base (the tell that the FD1 inversion held), and a
  *populated*-`artifact_refs` v3 snapshot really does still load across the 3→4 bump.
- **Found a live CI hole and logged it as BL-10** — PR
  [#40](https://github.com/glunk-works/loop-engine/pull/40), squash `46458af` (docs-only).
  See below; this is the most important thing that came out of the session.
- Sprint 32 archived (`.ai/archive/32_artifact_refs_strip-next-steps.md`); roadmap
  reconciled (NEXT ACTION flipped, merge commit recorded in the Phase 6 row).

## ⚠ BL-10 — a live defect, not a backlog idea
**PR #39's test suite never ran.** Not failed — *never executed*. Its 78-char title failed
`pr-title` (72-char limit), which skipped `lint` via the fail-fast `needs:` gate, which
cascaded through `needs:` to skip `format-check`, `test`, `secrets-scan`,
`dependency-audit` and `sbom`. **And fixing the title cannot recover it:** a title edit
fires `edited`, and `lint` carries `if: github.event.action != 'edited'` so the suite is
not re-run on a prose change. `pr-title` flips green while `test` stays `skipped` forever.

`skipped` is not `failure`, and GitHub treats a skipped required check as satisfied — so
**nothing blocks the merge and the checks page shows no red.** Two individually-correct
guards compose into a PR that looks clean and was never tested. This will happen again to
the next long-titled PR.

- **Recovery, if you hit it:** close + reopen. `reopened` is not `edited`, and unlike a
  push (`synchronize`) it **preserves the head SHA** — so a posted `architect-review`,
  which is pinned to an exact commit, stays green instead of needing a fresh-session
  re-review.
- **Logged, not fixed** — the `ci.yml` change wants its own review. BL-10 sketches three
  options; the cheapest is probably dropping the `needs: pr-title` fail-fast gate outright.

## Next
**Plan the next unit (Opus).** Candidates, most-urgent first:
1. **BL-10** — the CI hole above. The only backlog entry that is a live defect.
2. **PR #39's two actionable findings** — `publish_artifacts` now does a full disk read of
   every artifact on every stage while both its docstrings still claim it *"does no I/O"*;
   and that same read-back uses `Path.read_text()` with no explicit encoding (it is the
   first code in the engine to read these files back, and under `flows/maintenance` they
   can arrive from a git checkout rather than from this process's own write).
   `gh pr view 39 --comments` for the full reasoning.
3. **`sprints/DEFERRED_VERIFICATION.md`** — needs a real key / real `gh` / a daemon host.
4. **BL-1…BL-9** — the product backlog.

## HITL gate
**CLOSED.** No gate is open. Sprint 32 was reviewed by Opus in a fresh session and approved
by the owner's merge of #39.

## Standing obligations (still real, still unmet)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8) that have
  **never been run**. A green `hatch run test` says nothing about them. **Do not delete it.**
- **BL-3 (prompt-caching review)** — where real token savings actually live. Sprint 32 saved
  **zero** tokens by design; do not retroactively justify it on token grounds.

## Pointers
- `docs/migration_roadmap.md` — every phase closed; NEXT ACTION reads "none pre-selected".
- `docs/backlog.md` — BL-1…BL-10.
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.
- `sprints/32_artifact_refs_strip/sprint_plan.md` — the last sprint plan; done.

## Live external state — needs cleanup (HUMAN ACTION)
- **`glunk-works/loop-engine-v3-scratch`** (private) is still live, holding issues **#1–#6**.
  Delete it in the GitHub UI, then remove it from the fine-grained PAT's repo list (the PAT
  has no `Administration` permission by design, so it cannot delete repos — that stays a
  human checkpoint on the one irreversible action; it also carries an unexpected
  `Contents: Write` worth trimming while you're there).

## Working tree
- `main` ← `feat/mcp-langgraph-migration` is the integration branch; sprint work lands via
  `sprint/NN-slug` PRs based on it. Sprint branches squash-merge, so only the tip ships.
- `sprint/32-artifact-refs-strip` and `docs/bl-10-ci-title-starves-suite` are **squash-merged
  and therefore dead** — do not reuse them; cut fresh branches from
  `feat/mcp-langgraph-migration` (now at `46458af`).
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is
  tracked**.
