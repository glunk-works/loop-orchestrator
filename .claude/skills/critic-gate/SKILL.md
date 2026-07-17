---
name: critic-gate
description: Run the QA-critic pass on a coding diff — after the Sonnet green gate, before /handoff to the Architect Review. PROPOSES which read-only critic subagents apply by what the diff touches (security-critic / architect on src/, guard-adversary on guard surfaces, mutation-triage / docs-consistency for their sprint types) and waits for the human to confirm or trim before spawning any — it never auto-fans-out. Aggregates findings for the coder to fix, iterates to clean. Defense-in-depth that runs EARLIER — it is explicitly NOT the architect-review CI gate and never satisfies it.
---

# /critic-gate — the QA-critic pass (Coder-side, before the Architect Review)

Goal: catch the cheap, mechanical, boundary-shaped defects **Sonnet-side**, so the
expensive fresh-session Opus Architect Review spends its attention on judgment — and so nothing
ships green with no critic having looked (the sprint 27 Task 8 failure that created the
`architect-review` gate). This runs in the **implementation session** after the green gate
and before `/handoff`.

> **This is NOT the `architect-review` CI gate and must never be presented as satisfying
> it.** That gate wants a *fresh-session*, human-triggered review with an attestation
> (`.github/workflows/hitl-review.yml`; `.ai/context/workflow.md`). This pass is
> defense-in-depth that runs *earlier*. The fresh-session Architect Review still happens
> after `/handoff`, unchanged.

## Preconditions
- The green gate passes: `hatch run lint && hatch run format && hatch run test`. A red gate
  is fixed first — don't spend critics on a diff that doesn't build.
- There is a diff to review: `git diff main...HEAD` (branch) or the staged/working tree.

## Steps

1. **Scope the diff.** `git diff --stat main...HEAD` (and `git diff main...HEAD` for content).
   Note which trees it touches — `src/`, a static-guard surface, tests, docs.

2. **Propose the applicable critics — spawn NOTHING yet.** This gate does not auto-fan-out.
   Use the diff to work out which critics *apply* and **present that list to the human with a
   one-line reason each**, then wait. Each critic is real spend (mostly Opus subagents), so
   the human confirms or trims the list before any spawn.

   | Diff touches… | propose |
   |---|---|
   | any `src/` | **`security-critic`** (taint / trust-boundary) and/or **`architect`** (correctness pre-review) |
   | a guard surface — a new `subprocess`/`Popen`, an `open()`/`write_*`, a `core/`↔persona import, an MCP verb | **`guard-adversary`** (`isolation: "worktree"`) |
   | a test-validity sprint (BL-23) touching `tests/` under audit | **`mutation-triage`** (sharded, N in parallel) |
   | load-bearing docs / roadmap / CLAUDE.md | **`docs-consistency`** |

   If the caller named critics explicitly (`/critic-gate security-critic architect`), skip the
   proposal and run exactly those. If the diff touches nothing a critic covers, say so and stop
   — don't manufacture a reason to spawn one. Note the `architect`/`security-critic` overlap so
   the human can pick one rather than both when a light look is enough.

3. **On confirmation, spawn only the approved critics.** Each as a **separate read-only
   subagent** via the Agent tool (fresh context — never `/model`-switch and self-review). Give
   each the commit range or PR and its angle; run independent spawns in parallel.

4. **Aggregate the findings.** Collect each critic's ranked findings into one list, deduped,
   most-severe/most-reachable first. Tag each with its source critic and confidence. Drop
   nothing silently; a low-confidence finding is reported as low-confidence.

5. **Fix and re-gate (find/fix separation).** The critics are read-only — **the coder
   applies the fixes** (directly or via the `coder` subagent), then re-runs the green gate.
   If a fix touched a critic's area, re-spawn that critic (again on confirmation) on the new
   diff. Iterate until the critics are clean or the only remainders are consciously-accepted,
   documented judgment calls.

6. **Report and stop — do not cross into the CI gate.** Summarize: which critics ran, what
   they found, what was fixed, what was accepted-with-reason. Then `/handoff` → fresh Opus
   session → `/code-review` → post the Architect Review comment. `/critic-gate` never
   posts a review, never `--approve`s, never merges.

## Why propose instead of auto-spawning
Every critic is real cost (mostly Opus subagents) and noise, and `architect`/`security-critic`
overlap. Auto-fanning-out 2–3 of them on every sprint spends and distracts without the human
choosing to. Proposing keeps the routing's smarts — *which* critics a diff warrants — while
leaving the spawn decision (and the spend) with the human. A light `src/` change may only want
one critic; a trust-boundary change may want the full set. The gate advises; the human picks.
