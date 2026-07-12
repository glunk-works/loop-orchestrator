# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 6 is CLOSED.** The migration is collapsed to one path — LangGraph engine + MCP
tool dispatch + declarative `GeneratorNode` personas / PM `CriticGate` + Ralph Coder.
Four flags deleted; classic recoverable at the **`pre-phase6-classic`** tag;
`LOOP_ENGINE_ISOLATION` survives as genuine runtime config. V1/V2/V3 all PASS.

Sprint `27_phase6_flip_block` is complete pending this PR's merge, then `/archive-sprint`.

## Just done (Opus/Architect, 2026-07-12)
- **PR #34 (Task 8's R8 repair + Task 10's F1–F7) reviewed in a fresh Opus session and
  approved; merged as `796610a`.** The review is on the PR. Headline: F1/F2 were closed by
  *correcting the finding* — given only an issue number and a CWD there is **no oracle** for
  which of two same-numbered issues a human meant, so `resume --snapshot` was made
  authoritative (repo + number from the snapshot's own `pending_issue.url`) and
  `--from-issue` echoes its resolved destination. F3/F6: `_ORIGIN_CWD`/`_STATE_ROOT` are
  `ContextVar`s + an `InProcessDispatcher` lock. F4: `_pause_for_issue` persists before filing.
- **Task 9 — and it did NOT go as specced.** Its premise ("delete
  `sprints/DEFERRED_VERIFICATION.md`; its closing line says to") was **false**, the same way
  Task 5's was. The closing line's condition is *"once the checks have been performed"* —
  **five had never been run**: §1 (caching + USD smoke), §5 (`github_server` live launch),
  §6 (trigger webhook), §7 (maintenance flow live), §8 (bootstrap flow live). BL-3 depends on
  §1. Deleting would have destroyed the only record that these were never verified against a
  real host. **So the file was pruned, not deleted** (1007 → 210 lines) and retitled: it is now
  the standing register of unmet proof obligations and **outlives the migration**. The spent
  parts (§2 moot; §3/§4/§9 superseded by V1–V3; the V-run results; the resolved findings) are
  folded into the roadmap's Phase 6 row. **Section numbers were not renumbered** on purpose.
- **BL-9 filed** — PR #34's five non-blocking review notes.

## Next
1. **Merge this docs-only PR** (`architect-review` skips it — no `src/` changes), then
   **`/archive-sprint`** for `27_phase6_flip_block`.
2. **Plan the `State.artifacts` strip (decision FD3) as its own sprint — Opus.** This is the
   roadmap's NEXT ACTION. It is a **behavior-changing refactor, not a deletion**: the
   `artifacts` readers were always the personas and gates, never `run_loop`, which is why it
   was cut from Phase 6.

**Model: Opus/Architect** to plan FD3. Sonnet/Coder once that sprint's tasks are defined.

## Standing obligations that survive Phase 6 (neither is a migration task; both are real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks that have **never been run** (§1, §5,
  §6, §7, §8). They need a real Anthropic key, a real authenticated `gh`, or a daemon-bearing
  host that can bind a port. **A green `hatch run test` says nothing about any of them.**
- **FD3** — the deferred `State.artifacts` strip (above).

## HITL gate
None open. PR #34 is reviewed, approved, and merged. This docs-only PR needs no Architect
review (the gate exempts PRs with no `src/` changes) — but the owner's merge is still the
approval. Claude never merges or force-pushes.

## Pointers
- `docs/migration_roadmap.md` — Phase 6 row (🟩 Done, with V1–V3's results folded in) +
  the NEXT ACTION line + the decisions log (FD1/FD2/**FD3**).
- `sprints/27_phase6_flip_block/sprint_plan.md` — Tasks 0–4/6/7/8/9/10 DONE, Task 5 deferred
  (FD3). Task 9's entry records *why its premise was false* — read it before anyone tries to
  "finish the job" by deleting `DEFERRED_VERIFICATION.md`.
- `docs/backlog.md` — **BL-8** (stop using process CWD as an isolation mechanism) and
  **BL-9** (retire the implicit-CWD destination from the issue path's remaining surfaces;
  item 1 — `resume --from-issue` still guesses from CWD — is the one worth doing).
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.
- `.github/workflows/hitl-review.yml` — the gate: binds a review to an exact head SHA,
  exempts PRs with no `^src/` file.

## Live external state — needs cleanup (HUMAN ACTION)
- **`glunk-works/loop-engine-v3-scratch`** (private) is still live, holding issues **#1–#6**.
  Delete it in the GitHub UI, then remove it from the fine-grained PAT's repo list (the PAT has
  no `Administration` permission by design, so it cannot delete repos — that stays a human
  checkpoint on the one irreversible action; it also carries an unexpected `Contents: Write`
  worth trimming while you're there).

## Working tree
- Work is on **`sprint/27-task9-decommission`** (cut fresh from `feat/mcp-langgraph-migration`
  at `796610a`, after #34 squash-merged). Sprint branches squash-merge, so only the tip ships.
- `.ai/state.json` is git-ignored (local mirror); **`.ai/next-steps.md` is tracked**.
