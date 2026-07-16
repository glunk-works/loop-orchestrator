---
name: critic-gate
description: Run the QA-critic pass on a coding diff — after the Sonnet green gate, before /handoff to the Architect review. Routes to the relevant read-only critic subagents by what the diff touches (security-critic + architect on src/, guard-adversary on guard surfaces, mutation-triage / docs-consistency for their sprint types), aggregates their findings for the coder to fix, and iterates to clean. Defense-in-depth that runs EARLIER — it is explicitly NOT the architect-review CI gate and never satisfies it.
---

# /critic-gate — the QA-critic pass (Coder-side, before the Architect review)

Goal: catch the cheap, mechanical, boundary-shaped defects **Sonnet-side**, so the
expensive fresh-session Opus HITL review spends its attention on judgment — and so nothing
ships green with no critic having looked (the sprint 27 Task 8 failure that created the
`architect-review` gate). This runs in the **implementation session** after the green gate
and before `/handoff`.

> **This is NOT the `architect-review` CI gate and must never be presented as satisfying
> it.** That gate wants a *fresh-session*, human-triggered review with an attestation
> (`.github/workflows/hitl-review.yml`; `.ai/context/workflow.md`). This pass is
> defense-in-depth that runs *earlier*. The fresh-session Architect review still happens
> after `/handoff`, unchanged.

## Preconditions
- The green gate passes: `hatch run lint && hatch run format && hatch run test`. A red gate
  is fixed first — don't spend critics on a diff that doesn't build.
- There is a diff to review: `git diff main...HEAD` (branch) or the staged/working tree.

## Steps

1. **Scope the diff.** `git diff --stat main...HEAD` (and `git diff main...HEAD` for content).
   Note which trees it touches — `src/`, a static-guard surface, tests, docs.

2. **Route to critics by what the diff touches.** Spawn each as a **separate read-only
   subagent** via the Agent tool (fresh context — never `/model`-switch and self-review):

   | Diff touches… | spawn |
   |---|---|
   | any `src/` | **`security-critic`** (taint / trust-boundary) **+ `architect`** (correctness pre-review) |
   | a guard surface — a new `subprocess`/`Popen`, an `open()`/`write_*`, a `core/`↔persona import, an MCP verb | **also `guard-adversary`** (spawn with `isolation: "worktree"`) |
   | a test-validity sprint (BL-23) touching `tests/` under audit | **`mutation-triage`** (shard the survivors; spawn N in parallel) |
   | load-bearing docs / roadmap / CLAUDE.md | **`docs-consistency`** |

   A docs/test-only diff with no `src/` may need only `docs-consistency` (or nothing) —
   don't spawn critics that have nothing to look at. Give each subagent the commit range or
   PR and its angle; run independent spawns in parallel.

3. **Aggregate the findings.** Collect each critic's ranked findings into one list, deduped,
   most-severe/most-reachable first. Tag each with its source critic and confidence. Drop
   nothing silently; a low-confidence finding is reported as low-confidence.

4. **Fix and re-gate (find/fix separation).** The critics are read-only — **the coder
   applies the fixes** (directly or via the `coder` subagent), then re-runs the green gate.
   If a fix touched a critic's area, re-spawn that critic on the new diff. Iterate until the
   critics are clean or the only remainders are consciously-accepted, documented judgment
   calls.

5. **Report and stop — do not cross into the CI gate.** Summarize: which critics ran, what
   they found, what was fixed, what was accepted-with-reason. Then `/handoff` → fresh Opus
   session → `/code-review` → post the `architect-review` HITL comment. `/critic-gate` never
   posts a review, never `--approve`s, never merges.

## Why route instead of always-spawn-all-six
Spawning every critic on every sprint is off-altitude and wasteful. Most sprints are a
`src/` change → `security-critic` + `architect`. `guard-adversary`, `mutation-triage`, and
`docs-consistency` are conditional on the diff actually touching their domain.
