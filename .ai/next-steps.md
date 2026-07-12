# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is fully closed** (Phases 1–6 complete; sprint 32 discharged the last
dangling task). No roadmap phase is open, and nothing here is migration work.

**Current unit: sprint `33_ci_title_starvation` (BL-10) — status `planning`.**
No `sprint_plan.md` exists yet. **Writing it is the next action.** Opus/Architect.

## Just done (Opus/Architect review session, 2026-07-12)
- **Sprint 32 (`artifact_refs` strip) merged and approved** — PR #39, squash `3db3237`.
  HITL review posted in a fresh session; 8 findings, none blocking. Both of the plan's
  sharp questions held (the 8 reader modules came out **byte-identical**; a *populated*
  `artifact_refs` v3 snapshot really does still load across the 3→4 bump).
- **Found BL-10 and logged it** — PR #40, `46458af`.
- **Archived sprint 32** — PR #41, `6a9c77a`. Roadmap reconciled; all three sprint
  branches squash-merged and pruned.

## Next — sprint 33 planning pass (BL-10)
**Read [`docs/backlog.md`](../docs/backlog.md) BL-10 first.** It is the sprint's whole
subject and already carries the diagnosis, the recovery, and three candidate fixes.

**This is a live defect, not a backlog idea.** In `.github/workflows/ci.yml`: `pr-title`
enforces a 72-char limit; `lint` is gated on it (`needs: pr-title`); and `format-check` →
`test` → `secrets-scan`/`dependency-audit` → `sbom` all reach `lint` through `needs:`.
**One over-long title skips all six jobs.** And fixing the title *cannot* recover it — a
title edit fires `edited`, and `lint` carries `if: github.event.action != 'edited'`, so the
suite is never re-run. `pr-title` flips green while `test` stays `skipped` forever.

**`skipped` is not `failure`**, and GitHub treats a skipped required check as satisfied —
so the PR merges, untested, with a fully green checks page. **Sprint 32's own PR #39 hit
exactly this and came within one click of merging with its suite never having run.** It
will happen again to the next long-titled PR.

Leading candidate: **drop the `needs: pr-title` fail-fast gate entirely** — the few runner
minutes it saves on a bad title is a poor trade for a silently-untested merge. Weigh it
against (a) letting `edited` re-run the chain when the prior conclusion for that SHA was
`skipped`, and (c) making `pr-title` a standalone required check that gates nothing.

> **Read the rationale comments on *both* guards before changing either.** Each is there
> for a real reason (fail fast on a bad title; don't re-run the suite for a prose edit).
> It is their **interaction** that is wrong, not either one alone.

Then: `/handoff` → Sonnet implements → fresh-session Opus review → PR.

## HITL gate
**NONE OPEN.** Sprint 33 hasn't started; it needs a planning pass before a gate exists.

## Standing obligations (not sprint-33 tasks; both still real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8) that have
  **never been run**. A green `hatch run test` says nothing about them. **Do not delete it.**
- **Two unfixed findings from PR #39's review** — `publish_artifacts` does a full disk read
  of every artifact on every stage while both its docstrings claim it *"does no I/O"*, and
  that read-back uses `Path.read_text()` with no explicit encoding. Fold in before that code
  is load-bearing. `gh pr view 39 --comments`.

## Pointers
- `docs/backlog.md` — **BL-10** (this sprint) + BL-1…BL-9.
- `.github/workflows/ci.yml` — the target. `pr-title` (L28, limit at L43), `lint` (L64, the
  `needs:` + `!= 'edited'` clause at L66), the `edited` trigger (L11).
- `sprints/33_ci_title_starvation/sprint_plan.md` — **to be written.**
- `docs/migration_roadmap.md` — every phase closed. Sprint 33 is **not** a phase; don't add a row.
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.

## Live external state — needs cleanup (HUMAN ACTION)
- **`glunk-works/loop-engine-v3-scratch`** (private) is still live, holding issues **#1–#6**.
  Delete it in the GitHub UI, then remove it from the fine-grained PAT's repo list (the PAT
  has no `Administration` permission by design, so it cannot delete repos — that stays a
  human checkpoint on the one irreversible action; it also carries an unexpected
  `Contents: Write` worth trimming while you're there).

## Working tree
- `main` ← `feat/mcp-langgraph-migration` is the integration branch (now at `6a9c77a`);
  sprint work lands via `sprint/NN-slug` PRs based on it. Branches squash-merge, so only the
  tip ships — **a squash-merged branch is dead; never reuse one.**
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is
  tracked**.
