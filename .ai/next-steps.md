# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is fully closed** (Phases 1–6). Work is now **backlog-driven** from
[`docs/backlog.md`](../docs/backlog.md) — that file, not the roadmap, is the source of the
next unit.

**Next unit: sprint `34_ci_supply_chain_hardening` — status `planning`.** The id and the scope
are **provisional**; no `sprint_plan.md` exists yet. The next move is an **Opus planning pass**
(one question at a time, HITL gates), starting on a **fresh branch cut from the updated
`feat/mcp-langgraph-migration`**.

## Just done — sprint 33 archived
Sprint `33_ci_title_starvation` (BL-10) is **complete, merged, and archived**. PR #43 merged as
squash **`88c0dc4`** onto `feat/mcp-langgraph-migration` — **the merge was the approval.** Final
cursor snapshotted to `.ai/archive/33_ci_title_starvation-next-steps.md`.

It shipped two things, one of which was not in the plan:

- **BL-10 closed by a split, not a rewiring.** `pr-title` moved to its own workflow with its own
  trigger list and concurrency group; `ci.yml` lost the `edited` trigger and `lint` lost both
  `needs: pr-title` and its `if:`. **No job in `ci.yml` carries an `if:`**, so none can ever
  report `skipped` — the invariant is pinned structurally by test rather than by re-asserting the
  new wiring. Verified live: with a deliberately bad 111-char title, `pr-title` went red and the
  heavy chain **ran anyway, all six jobs green on the same commit**.
- **BL-11 found and closed** — see below. This was the bigger find.

## BL-11 — the checks were never actually required
Confirming FD5 revealed the repo had **no branch protection and no rulesets at all**. All eight
checks were computed, reported, and **enforcing nothing**: a red PR was mergeable and base
branches were directly pushable. `mergeStateStatus: CLEAN` corroborated nothing — with no rules
configured, nothing can be violated. **Never read `CLEAN` as evidence of enforcement again.**

Closed **by configuration, not code** (temporary `Administration: write` PAT scope, since revoked).
Ruleset **`protected-integration-branches`** (id `18847725`, `active`, `bypass_actors: []`) on
`main` + `feat/**`: **all eight checks required**, PR required to merge, no force-push, no
deletion. Secret scanning + push protection enabled. `sprint/**` stays unruled (must remain
freely pushable). **FD5 is now load-bearing for real** — required checks match by **check-run
name** = job id, so a `name:` override on any of those jobs strands the requirement; `4b61fd1`
pins this by test.

## Next — Opus planning pass
The proposed sprint-34 scope is the three items **BL-11 left open deliberately**, all of which are
about making the enforcement sprint 33 finally switched on *actually hold*:

1. **Actions supply chain.** `allowed_actions: "all"`, `sha_pinning_required: false`, floating tags
   (`actions/checkout@v4`). Enabling SHA pinning fails every workflow until the tags become commit
   SHAs — a **code** change, and the only one of the three with real implementation weight.
2. **Squash-only merges.** `allow_merge_commit` / `allow_rebase_merge` are still `true` while the
   convention is squash-only. `squash_merge_commit_title: PR_TITLE` applies *only* to squash, so
   merge-committing a PR **silently drops the enforced title** and breaks the commit taxonomy. A
   settings toggle — human-only.
3. **Drift detection.** Nothing in the repo asserts the ruleset still exists or still requires the
   eight checks — precisely how its *total absence* went unnoticed for the life of the CI config.
   An `Administration: **read**` scope would let a test or a `/resume` preflight fail loudly if
   enforcement is weakened, **without** granting the power to weaken it. *A gate the governed party
   can remove is not a gate* — write access stays human-only.

Scope is the human's call: (1) is a sprint on its own; (2) and (3) are small but need a human in
the loop for the settings side.

## Standing obligations (not sprint-34 tasks; all still real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8) **never run**. Don't delete it.
- **Two unfixed findings from PR #39** — `publish_artifacts` reads every artifact off disk on every
  stage while both docstrings claim it *"does no I/O"*; that read-back uses `Path.read_text()` with
  no explicit encoding. Still open, still unscheduled. They touch `src/`, so any PR fixing them needs
  a **fresh-session** `architect-review` — now an actually-enforced required check, not a courtesy.
- **Human:** `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6) is still live — delete it in
  the UI, then trim the PAT's repo list. Pending across several sprints.

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — **the source of work.** BL-10 and BL-11 both resolved by
  sprint 33; **BL-11's "Left open, deliberately" section is the sprint-34 candidate list.**
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed. No longer the
  source of work.
- `sprints/34_ci_supply_chain_hardening/sprint_plan.md` — **to be written** by the planning pass.
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.

## Working tree
- **No active sprint branch.** `sprint/33-ci-title-starvation` was squash-merged and is **dead**
  (already deleted on the remote) — **never reuse a squash-merged branch.** Cut a fresh
  `sprint/34-*` from the updated `feat/mcp-langgraph-migration`.
- PR base is always **`feat/mcp-langgraph-migration`**, never `main`.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is tracked.**
