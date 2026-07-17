---
name: handoff
description: Serialize the current dev-session state into .ai/ before switching model or session — check the /critic-gate pass ran on any src/ diff, update .ai/state.json (including hitl_gate, always), regenerate .ai/next-steps.md, and remind to commit. Run this at the END of a session (e.g. Opus planning -> Sonnet coding, or coding -> Opus review). Does NOT archive a sprint.
---

# /handoff — externalize state before switching model/session

Goal: leave a clean, self-contained cursor so the next (fresh, lean) session can
`/resume` without inheriting this session's bloated context. This is the token-saving
handoff point. It does **not** archive — that is `/archive-sprint`, only on completion.

## Steps

1. **Check the QA-critic pass ran** (skip if this session wrote no code — a planning
   session has no diff to critique). Run `git diff main...HEAD --stat`. If it touches
   `src/` and **no `/critic-gate` pass ran on that diff in this session**, say so plainly
   and offer to run it before handing off. The critic pass belongs to the implementation
   session — once you `/handoff`, the diff moves on to the Architect Review with no critic
   having looked, which is the sprint 27 Task 8 failure (`.ai/context/workflow.md`).

   This is a **prompt, not a block**: the human may decline and hand off anyway (say
   "handing off without a critic pass" in the report so the choice is on the record). It
   exists because nothing else in the pipeline points at `/critic-gate` — the skill said
   "before `/handoff`" while `/handoff` never mentioned it, so the human was the only
   trigger. The gate still **proposes and the human still picks** which critics run; this
   step only stops the pass from being forgotten.

2. **Determine the new cursor** from what this session did:
   - `current_phase`, `current_sprint_id`, and `sprint_status` — one of `planning` | `implementing` | `awaiting_architect_review` | `blocked` | `done`.
   - `assigned_model` / `assigned_persona` for the **next** session (Architect=Opus for planning/review, Coder=Sonnet for implementation — see `.ai/context/workflow.md`).
   - `last_commit` = current `git rev-parse --short HEAD`.
   - `next_action` = the single most important next step, phrased as an imperative.
   - `hitl_gate` — **always write this field**, even when nothing is open (`"NONE OPEN"` + what the next gate will be). It is load-bearing: `/resume` reads it to decide whether it may start the next action unattended, and treats a missing or unparseable value as an open gate. Dropping it doesn't fail loudly — it silently costs the next session its auto-start.
   - `pointers` = `{ "roadmap": "docs/migration_roadmap.md", "sprint_plan": "<active sprint_plan.md>" }`.

3. **Write `.ai/state.json`** (this file is git-ignored — it's a local convenience mirror). Keep `schema_version: 1`. Overwrite it wholesale with the new cursor — "wholesale" means every field above, `hitl_gate` included; an overwrite that drops a field is how a cursor loses one.

4. **Regenerate `.ai/next-steps.md`** (git-tracked — this is the durable human ledger). Keep it to ~20–40 lines, in this shape:
   - **Now:** current phase/sprint + status (one line).
   - **Just done:** 2–5 bullets of what this session accomplished (+ commit hashes).
   - **Next:** the imperative next action + which model should do it + any open HITL Gate.
   - **Pointers:** the roadmap + active sprint_plan paths (do not copy their content — link to them).
   Regenerate the whole file (it is a cursor, not an append log — history lives in git + the roadmap).

5. **Commit reminder.** Run `git status --short`. If the tree is dirty, tell the user what's uncommitted and recommend committing before switching sessions (a `/resume` expects `last_commit` to match HEAD). Do NOT auto-commit unless the user asked. A dirty tree also costs the next session its auto-start — `/resume` treats cursor/HEAD drift as a reason to stop and ask.

6. **Report** the new `sprint_status`, the `next_action`, and the recommended next model in 2–3 lines. If the critic pass was skipped by choice (step 1), say so here.

## Guardrails
- Never write secrets into `.ai/next-steps.md` or `.ai/state.json`.
- `.ai/next-steps.md` points into the roadmap/sprint files; it must not become a second copy of them.
- `/handoff` writes the `next_action` that `/resume` may execute **without a further prompt** (see `/resume` step 6). Phrase it as a precise, bounded imperative that you would be content to see carried out unattended — not a vague direction that needs a human to interpret it. If the next step genuinely needs a decision, that is what `hitl_gate` is for: open one.
