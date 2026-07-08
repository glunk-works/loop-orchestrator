# Dev-workflow protocol: model routing + session handoff

This repo is built with two models, split to keep each session lean and single-model
(the fix for hitting session limits — long Opus sessions accumulate huge context).
Work is externalized into `.ai/` so a fresh session can rehydrate cheaply instead of
inheriting a bloated context window.

## The two state layers (do not conflate)

- **`.ai/`** — *this* dev-workflow's state (how Claude Code sessions hand off).
  - `.ai/next-steps.md` (git-tracked) — the human-readable cursor: current phase/sprint, status, next action, which model to use, HITL-gate state. A **thin pointer** into the roadmap + the active sprint file; not a second copy of them.
  - `.ai/state.json` (git-ignored) — the machine cursor (`current_sprint_id`, `sprint_status`, `assigned_model`, `last_commit`, `next_action`, `pointers`).
  - `.ai/context/` (git-tracked) — heavy reference loaded on demand (`modules.md`, `conventions.md`, this file).
  - `.ai/archive/` (git-ignored) — retired sprint snapshots.
- **`.agent/STATE.md` + `.agent/MEMORY.md`** — the loop-engine **product's** runtime Ralph state, written when the engine itself runs. Nothing in the dev workflow writes these.

The deep, authoritative history stays in `docs/migration_roadmap.md`; `.ai/` never
duplicates it, only points at the current cursor within it.

## Model routing

- **Architect = Opus.** Decide *what* to build or *whether* a diff is correct: architecture, design, sprint/phase planning (one question at a time, HITL gates), HITL review of a coding diff, boundary calls, non-trivial debugging, roadmap/memory updates.
- **Coder = Sonnet.** Execute an already-defined spec: implement a sprint task, write/adjust tests, mechanical refactors, run the green gate (`hatch run lint/format/test/audit/sbom`), fix lint.

Phase 1 (now) is **manual, persona-driven** routing — you or the orchestrator pick the
model. Automated routing (a proxy/router) is explicitly out of scope until the
thresholds are proven.

## Switch points across a sprint

```
OPUS (plan)    design/plan the sprint -> write sprint_plan.md + roadmap -> /handoff
   |                                                                          |
   v   (fresh session, /model sonnet)                                         |
SONNET (code)  /resume -> implement tasks + tests -> green gate -> commit -> /handoff
   |                                                                          |
   v   (fresh session, /model opus)                                           |
OPUS (review)  /resume -> /code-review the diff -> HITL gate -> update roadmap
               -> /archive-sprint (on completion) -> plan the next sprint
```

Each box is its own **short, single-model session**. The expensive planning context
never carries into the coding session, and vice-versa — that is the token saving.

- **Primary path: session handoff** (above). Use it at every sprint boundary.
- **Secondary path: in-session subagent.** For a small, well-scoped coding task that
  doesn't warrant a full session switch, an Opus session may dispatch the Sonnet
  **`coder`** subagent (`.claude/agents/coder.md`) via the Agent tool. The subagent's
  result returns into the Opus context, so prefer the handoff path for anything large.

## The three skills

- **`/resume`** — run at the **start** of a session. Reads `.ai/state.json` +
  `.ai/next-steps.md` + the pointed sprint_plan + roadmap NEXT ACTION, states the exact
  pick-up point, and adopts the assigned persona/model. (Distinct from the
  `loop-engine resume` CLI subcommand — different namespace.)
- **`/handoff`** — run **before** switching model/session. Serializes the current cursor
  to `.ai/state.json`, regenerates `.ai/next-steps.md` (what was done, what's next, which
  model next), and reminds you to commit if the tree is dirty. Does **not** archive.
- **`/archive-sprint`** — run **only** when a sprint is HITL-approved **and** committed.
  Moves its `next-steps.md` snapshot into `.ai/archive/`, advances `.ai/state.json` to
  the next sprint, and seeds a fresh `.ai/next-steps.md`.
