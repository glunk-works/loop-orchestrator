# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is fully closed** (Phases 1–6). Work is **backlog-driven** from
[`docs/backlog.md`](../docs/backlog.md).

**Current unit: sprint `34_ci_supply_chain_hardening` — status `implementing`.**
The plan is **written and human-approved**. Branch `sprint/34-ci-supply-chain-hardening` is cut
from `feat/mcp-langgraph-migration` and pushed (`24d65bf`, holding the plan).
**Next session is Sonnet/Coder.**

## Just done (Opus/Architect session, 2026-07-13)
- **Sprint 33 archived and merged.** PR #44 landed as `baf80dc` — the merge was the approval.
- **Sprint 34 planned** ([`sprint_plan.md`](../sprints/34_ci_supply_chain_hardening/sprint_plan.md),
  committed as `24d65bf`). Six tasks, six locked findings, a Risks section, a human-actions list.
  It closes the three items **BL-11** left open: SHA-pin the four actions, squash-only merges, and
  ruleset drift detection. The theme is one thing — sprint 33 switched enforcement *on*; this sprint
  makes it **hold**, pairing every control with an assertion that it still exists.

## The three findings that changed the plan's shape
- **FD1 — no new PAT scope is needed, and BL-11's note is wrong to ask for one.** Verified live, with
  the temporary `Administration: write` grant already revoked: the **effective-rules** endpoint
  (`GET /repos/../rules/branches/main`) returns all four rule types **and all eight required check
  names** with no admin scope. BL-11's resolution note recommends granting `Administration: read`;
  **Task 6 deletes that recommendation**, because leaving it standing invites a future session to
  widen scopes for nothing. **Do not widen any scope.**
- **FD2 — a drift check that is a *required* check is circular.** The ruleset is what *makes* a check
  required — so deleting the ruleset also un-requires the check watching it. It goes red and blocks
  nothing, precisely when it matters. Hence a **scheduled workflow + a `/resume` preflight**, never a
  9th required check.
- **FD3 — a cron only fires from the *default* branch (`main`), but our PRs land on `feat/**`.** A
  drift workflow merged to `feat/**` would sit in the tree, correct and reviewed, and **never
  execute** — BL-11's failure mode reproduced by the fix meant to detect it. **Task 4 therefore ships
  in its own PR based on `main`** — the single deliberate exception to the one-base rule.

## Next — Sonnet/Coder
Implement **Tasks 1, 2, 3, 5, 6** on `sprint/34-ci-supply-chain-hardening`, then PR into
`feat/mcp-langgraph-migration`. **Read the plan first** — its Risks section will save a debug cycle.
**Task 4 does NOT go on this branch** (FD3): its PR is based on `main` and carries only the drift
workflow.

Three traps, repeated because each is expensive:
1. **`uses:` needs a COMMIT sha, not a tag-object sha.** Resolve with
   `gh api repos/OWNER/REPO/commits/<tag> --jq .sha` — **not** the `git/ref/tags` endpoint, which
   returns the tag object and breaks every workflow at once.
2. **Never flip `sha_pinning_required` yourself** — human settings action, and it must come *after*
   the pins merge, or every workflow rejects floating tags including the PR carrying the fix.
3. **Task 4's criterion is LIVE OBSERVATION, not assertion (FD6).** `GITHUB_TOKEN` is a different
   principal from the local PAT; its read access to the rules endpoint is **unverified**. A green run
   that silently read nothing is the exact BL-11 defect and **does not pass**.

No `src/` is touched, so `hitl-review.yml`'s `^src/` filter exempts this sprint — `architect-review`
goes green on its own and **no fresh-session Opus review is required to merge.** The human's merge is
the only remaining gate.

## Human actions
- **After Task 1 merges** (ordering is load-bearing — FD5): set **`sha_pinning_required: true`**.
- **Any time:** `allow_merge_commit: false` + `allow_rebase_merge: false`. `squash_merge_commit_title:
  PR_TITLE` applies *only* to squash, so a merge-commit silently drops the enforced title — quietly
  undoing what sprint 33 built.
- **Merge Task 4's PR into `main`**, then confirm the drift workflow appears in the Actions tab.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the PAT's repo list.

## Standing obligations (not sprint-34 tasks; all still real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8) **never run**. Don't delete it.
- **Two unfixed findings from PR #39** — `publish_artifacts` reads every artifact off disk on every
  stage while both docstrings claim it *"does no I/O"*; that read-back uses `Path.read_text()` with no
  explicit encoding. Still open, out of sprint-34 scope. They touch `src/`, so fixing them **would**
  require a fresh-session `architect-review`.

## Pointers
- [`sprints/34_ci_supply_chain_hardening/sprint_plan.md`](../sprints/34_ci_supply_chain_hardening/sprint_plan.md) — **approved.** FD1–FD6, Tasks 1–6, Risks, human actions.
- [`docs/backlog.md`](../docs/backlog.md) — the source of work. **BL-11's "Left open, deliberately" section *is* this sprint.**
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed. Sprint 34 adds no row.
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.

## Working tree
- `sprint/34-ci-supply-chain-hardening` at `24d65bf` (pushed, clean). PR base is
  **`feat/mcp-langgraph-migration`** — **except Task 4, whose base is `main`** (FD3).
- Branches squash-merge — **a squash-merged branch is dead; never reuse one.**
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is tracked.**
