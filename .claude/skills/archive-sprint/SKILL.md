---
name: archive-sprint
description: Retire a COMPLETED, HITL-approved, committed sprint — snapshot its .ai/next-steps.md into .ai/archive/, advance .ai/state.json to the next sprint, and seed a fresh next-steps.md. Run ONLY on sprint completion; /handoff and /resume never archive.
---

# /archive-sprint — retire a completed sprint and bootstrap the next

Goal: close out a finished sprint cleanly and set up the next one, keeping the live
cursor small and moving completed detail out of routine context. This is the ONLY
command that archives — do not invoke it for ordinary session switches.

## Preconditions (verify ALL before doing anything)

1. The sprint's HITL gate is **approved** by the user (ask if unclear — never assume).
2. The work is **committed** (`git status --short` clean, or only unrelated changes). If dirty, stop and tell the user to commit first.
3. `docs/migration_roadmap.md` reflects the sprint as done (status row + commit hash recorded). If not, do that first (or flag it).

If any precondition fails, STOP and report why — do not archive.

## Steps

1. **Snapshot** the current `.ai/next-steps.md` to `.ai/archive/<current_sprint_id>-next-steps.md` (`.ai/archive/` is git-ignored). This preserves the sprint's final cursor for manual history queries.

2. **Advance `.ai/state.json`** to the next sprint: set `current_sprint_id` / `current_phase` to the next unit from the roadmap, `sprint_status: "planning"`, `assigned_model: "opus"` / `assigned_persona: "architect"` (the next step after completion is always planning/review by Opus), update `last_commit`, and set `next_action` to "plan <next sprint/phase>". Point `pointers.sprint_plan` at the next sprint_plan (or note it does not exist yet).

3. **Seed a fresh `.ai/next-steps.md`** for the next unit: **Now** = next phase/sprint in `planning`; **Just done** = one line noting the prior sprint archived + its commit; **Next** = "plan <next unit> (Opus)"; **Pointers** = roadmap + the next sprint_plan (or "to be written").

4. **Prune squash-merged local branches** (standard practice — a sprint boundary is when the just-merged `sprint/NN-*` branch becomes dead, the "squash trap"). This repo is squash-only, so `git branch --merged main` **cannot** see these branches; ask GitHub which PRs merged and `-D` **only** those — never an unmerged or PR-less branch, never `main`, never the current branch:
   ```bash
   merged=$(gh pr list --state merged --limit 300 --json headRefName -q '.[].headRefName')
   cur=$(git branch --show-current)
   for b in $(git for-each-ref --format='%(refname:short)' refs/heads/); do
     case "$b" in main|"$cur") continue;; esac
     printf '%s\n' "$merged" | grep -qxF "$b" && git branch -D "$b" && echo "pruned $b"
   done
   ```
   Report which branches were pruned (or "none"). Hygiene, not a gate — if the `gh` call fails, skip and say so.

5. **Report** what was archived, the new `current_sprint_id`, the next action, and the branches pruned. Remind the user to commit the archival (the tracked `next-steps.md` change + roadmap) if they want it durable.

## Guardrails
- Never delete the roadmap history or the sprint_plan files — archival only moves the `.ai/` cursor snapshot; the deep record stays in `docs/` and git.
- Never archive an un-approved or uncommitted sprint.
- The branch prune deletes **only** branches whose PR GitHub reports `merged` (via `gh`); it never touches an unmerged branch, a branch with no PR, `main`, or the current branch. `git branch -D` is safe here precisely because merged-ness is confirmed out-of-band (a squash-merged branch looks "unmerged" to git).
