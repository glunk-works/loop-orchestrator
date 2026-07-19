---
name: resume
description: Rehydrate a fresh dev session from .ai/ externalized state — read the cursor, adopt the assigned persona/model, and state the exact pick-up point. Then start the next_action unattended IF the cursor is clean and unambiguous (hitl_gate NONE OPEN, sprint_status implementing, model matches, no drift); otherwise state the pick-up point and wait. Fails closed — an open, missing, or unreadable gate always waits. Run this at the START of a session working on this repo. Distinct from the `loop-orchestrator resume` CLI subcommand.
---

# /resume — rehydrate a fresh session from externalized state

Goal: start a new (lean) session already knowing exactly where the last one left off,
without re-reading the whole repo. This is the counterpart to `/handoff`.

## Steps

1. **Read the cursor** (in this order, stop reading once you have enough):
   - `.ai/state.json` — the machine cursor (`current_phase`, `current_sprint_id`, `sprint_status`, `assigned_model`, `assigned_persona`, `last_commit`, `next_action`, `hitl_gate`, `pointers`). If it is missing, fall back to `.ai/next-steps.md` alone — and note that a `/resume` running on `next-steps.md` alone can never auto-start (step 6): no cursor, no unattended work.
   - `.ai/next-steps.md` — the human ledger: what was just done, what's next, which model to use, HITL Gate status.
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

6. **State the pick-up point** in 3–6 lines: current phase/sprint, sprint_status, the single next action, any open HITL Gate, the ruleset check result, and the branch-prune result.

   Then **either start the next action or wait**, per the rule below.

   **Auto-start** — begin the `next_action` immediately, no "go" needed, only when **all** hold:
   - `hitl_gate` is present and reads `NONE OPEN`;
   - `sprint_status` is `implementing`;
   - the running model matches `assigned_model` (step 5);
   - step 2 found no drift — `last_commit` matches HEAD **and** the tree is clean.

   Otherwise **state the pick-up point and wait.** In particular: always wait on
   `planning` (the planning pass is one question at a time — that dialogue *is* the
   work), on any open or unreadable gate, on a model mismatch, and on any drift.

   > **Fail closed.** A missing, empty, or unparseable `hitl_gate`, a `state.json` that
   > won't parse, or a `sprint_status` you can't classify all mean **wait** — never
   > proceed. "I couldn't tell whether a gate was open" is not "no gate is open"; that
   > conflation is the BL-11 defect in miniature, same as the ruleset check in step 4.

   Say which branch you took and why in one line (`Auto-starting: gate NONE OPEN,
   status implementing, cursor clean.` / `Waiting: HITL Gate open on the sprint 41 plan.`)
   so the choice is visible and you can stop it.

   **Why auto-start is not a lost approval:** the `next_action` was written by the
   previous session's `/handoff` — which the human reviewed and approved *then*.
   Re-approving it at the start of the next session approves the same decision twice, and
   in practice that second approval was a content-free "go" 10 times out of 13 sessions in
   a single day. The approval that carries real signal is the **`hitl_gate`**, and it is
   still absolutely enforced. Auto-start removes a rubber stamp, not a gate. It also never
   crosses a merge or review boundary: `/critic-gate` still proposes and the human still
   picks, the human still merges, and nothing here posts an Architect Review.

   > **If the next action is posting the Architect Review:** the review body must
   > **open with the verbatim two-line header + attestation block** from
   > `.ai/context/workflow.md` (`**Opus/Architect HITL review (automated)**` then
   > `*Fresh-session review: this session did not author the diff.*`). The
   > `architect-review` check matches both lines by literal `contains()` — **paste them,
   > do not paraphrase**; a reworded attestation ("Fresh-session attestation: …") fails
   > the gate ~4s after posting even though it reads identically. That header still says
   > "HITL review" on purpose — it is a frozen wire string, **not** an escaped rename.

## Load-on-demand
Only read `.ai/context/modules.md` / `conventions.md` if the next action actually needs
them. The point of `/resume` is a cheap, targeted rehydrate — not reloading everything.
