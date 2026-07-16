---
name: resume
description: Rehydrate a fresh dev session from .ai/ externalized state — read the cursor, adopt the assigned persona/model, and state the exact pick-up point. Run this at the START of a session working on this repo. Distinct from the `loop-engine resume` CLI subcommand.
---

# /resume — rehydrate a fresh session from externalized state

Goal: start a new (lean) session already knowing exactly where the last one left off,
without re-reading the whole repo. This is the counterpart to `/handoff`.

## Steps

1. **Read the cursor** (in this order, stop reading once you have enough):
   - `.ai/state.json` — the machine cursor (`current_phase`, `current_sprint_id`, `sprint_status`, `assigned_model`, `assigned_persona`, `last_commit`, `next_action`, `pointers`). If it is missing, fall back to `.ai/next-steps.md` alone.
   - `.ai/next-steps.md` — the human ledger: what was just done, what's next, which model to use, HITL-gate status.
   - The `pointers.sprint_plan` file (the active `sprints/NN_*/sprint_plan.md`) — the task list for the current sprint.
   - `docs/migration_roadmap.md` — read only the **Status table** + the **NEXT ACTION** line, not the whole file, unless the next action needs the decisions log.

2. **Check reality vs. the cursor.** Run `git log --oneline -5` and `git status --short`. Confirm `last_commit` matches HEAD (or note the drift). If the tree is dirty, surface that — a previous session may not have finished a `/handoff`.

3. **Prune squash-merged local branches** (standard practice — this repo is squash-only, and `git branch --merged main` **cannot** see a squash-merged branch because the squash makes a new commit the branch never became an ancestor of; so ask GitHub which PRs merged). One read-only `gh` call, then a safe `-D` on **only** the branches whose PR GitHub reports `merged` — never an unmerged or PR-less branch, never `main`, never the current branch:
   ```bash
   merged=$(gh pr list --state merged --limit 300 --json headRefName -q '.[].headRefName')
   cur=$(git branch --show-current)
   for b in $(git for-each-ref --format='%(refname:short)' refs/heads/); do
     case "$b" in main|"$cur") continue;; esac
     printf '%s\n' "$merged" | grep -qxF "$b" && git branch -D "$b" && echo "pruned $b"
   done
   ```
   Report the result in the pick-up summary in **at most one line** (e.g. `Pruned 6 squash-merged local branches.` or `No stale branches to prune.`). This is hygiene, not a gate — never block the session on it; if the `gh` call fails, skip pruning and say so.

4. **Check the branch-protection ruleset for drift** (BL-11 / sprint 34, FD1+FD2 — the cron in `ruleset-drift.yml` catches drift between sessions; this catches it at the moment work resumes, which in a solo repo is when nearly every change begins). One read-only call, no new PAT scope (FD1):
   ```
   gh api repos/OWNER/REPO/rules/branches/main
   ```
   (resolve `OWNER/REPO` via `gh repo view --json nameWithOwner -q .nameWithOwner` if unknown). Confirm the response includes all four rule types (`deletion`, `non_fast_forward`, `pull_request`, `required_status_checks`) and that the `required_status_checks` rule's contexts cover all eight: `lint`, `format-check`, `test`, `secrets-scan`, `dependency-audit`, `sbom`, `pr-title`, `architect-review`. Report in the pick-up summary, **at most one line**:
   - Healthy → one line, e.g. `Ruleset check: healthy (4 rule types, 8 required checks).`
   - Weakened or missing → impossible to miss; name what's absent.
   - The call itself failed (network/auth) → report **inconclusive**, never healthy — a preflight that can't tell "healthy" from "couldn't look" is the BL-11 defect in miniature.

   This is a report, not a gate — never block or fail the session on its result.

5. **Adopt the assigned persona/model.** If `assigned_model` does not match the model you are running as, say so explicitly and recommend the user `/model` switch before continuing (Architect=Opus for planning/review, Coder=Sonnet for implementation — see `.ai/context/workflow.md`).

6. **State the pick-up point** in 3–6 lines: current phase/sprint, sprint_status, the single next action, any open HITL gate, the ruleset check result, and the branch-prune result. Then wait for the user (do not silently start large work — especially if a HITL gate is open).

   > **If the next action is posting the Architect HITL review:** the review body must
   > **open with the verbatim two-line header + attestation block** from
   > `.ai/context/workflow.md` (`**Opus/Architect HITL review (automated)**` then
   > `*Fresh-session review: this session did not author the diff.*`). The
   > `architect-review` check matches both lines by literal `contains()` — **paste them,
   > do not paraphrase**; a reworded attestation ("Fresh-session attestation: …") fails
   > the gate ~4s after posting even though it reads identically.

## Load-on-demand
Only read `.ai/context/modules.md` / `conventions.md` if the next action actually needs
them. The point of `/resume` is a cheap, targeted rehydrate — not reloading everything.
