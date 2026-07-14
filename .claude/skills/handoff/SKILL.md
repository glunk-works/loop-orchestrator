---
name: handoff
description: Serialize the current dev-session state into .ai/ before switching model or session — update .ai/state.json, regenerate .ai/next-steps.md, and remind to commit. Run this at the END of a session (e.g. Opus planning -> Sonnet coding, or coding -> Opus review). Does NOT archive a sprint.
---

# /handoff — externalize state before switching model/session

Goal: leave a clean, self-contained cursor so the next (fresh, lean) session can
`/resume` without inheriting this session's bloated context. This is the token-saving
handoff point. It does **not** archive — that is `/archive-sprint`, only on completion.

## Steps

1. **Determine the new cursor** from what this session did:
   - `current_phase`, `current_sprint_id`, and `sprint_status` — one of `planning` | `implementing` | `awaiting_hitl_review` | `blocked` | `done`.
   - `assigned_model` / `assigned_persona` for the **next** session (Architect=Opus for planning/review, Coder=Sonnet for implementation — see `.ai/context/workflow.md`).
   - `last_commit` = current `git rev-parse --short HEAD`.
   - `next_action` = the single most important next step, phrased as an imperative.
   - `pointers` = `{ "roadmap": "docs/migration_roadmap.md", "sprint_plan": "<active sprint_plan.md>" }`.

2. **Write `.ai/state.json`** (this file is git-ignored — it's a local convenience mirror). Keep `schema_version: 1`. Overwrite it wholesale with the new cursor.

3. **Regenerate `.ai/next-steps.md`** (git-tracked — this is the durable human ledger). Keep it to ~20–40 lines, in this shape:
   - **Now:** current phase/sprint + status (one line).
   - **Just done:** 2–5 bullets of what this session accomplished (+ commit hashes).
   - **Next:** the imperative next action + which model should do it + any open HITL gate.
   - **Pointers:** the roadmap + active sprint_plan paths (do not copy their content — link to them).
   Regenerate the whole file (it is a cursor, not an append log — history lives in git + the roadmap).

4. **Commit reminder.** Run `git status --short`. If the tree is dirty, tell the user what's uncommitted and recommend committing before switching sessions (a `/resume` expects `last_commit` to match HEAD). Do NOT auto-commit unless the user asked.

5. **Report** the new `sprint_status`, the `next_action`, and the recommended next model in 2–3 lines.

## Guardrails
- Never write secrets into `.ai/next-steps.md` or `.ai/state.json`.
- `.ai/next-steps.md` points into the roadmap/sprint files; it must not become a second copy of them.
