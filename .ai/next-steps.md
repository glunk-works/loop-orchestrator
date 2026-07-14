# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — `planning`. Opus/Architect.**
No `sprint_plan.md` exists yet; **the planning pass writes it.**

**The migration is landed and the roadmap is history.** `main` = `eeccc05`. Sprint branches are cut
from `main`, PRs are based on `main`, the repo is squash-only. No open PRs, no live sprint branches,
**no outstanding human actions.**

## Just done
**Sprint 35 (`35_migration_merge`) is COMPLETE and archived** (`eeccc05`). It landed
`feat/mcp-langgraph-migration` on `main` as merge commit **`d2135e7`** (two parents, 113 commits
preserved, never squashed — the merged tree came out byte-for-byte the tree the preflight predicted),
retired the branch (**BL-17**), merged the four Dependabot Node-24 majors, and gave every deferred
check a named owner. Full detail in `docs/migration_roadmap.md` (the **▣ THE LANDING** row) and
`docs/backlog.md`.

## Next — plan sprint 36: live factory verification
Scope was **agreed in sprint 35's Task 6** — `sprints/DEFERRED_VERIFICATION.md` **§5** (`github_server`
live factory verbs), **§7** (maintenance flow: live clone → run → gate → push → PR), **§8** (bootstrap
flow: live create → clone → scaffold → push `main` → create `develop`).

One **daemon-bearing host** with authenticated `gh`, network, and **one** disposable scratch-repo
lifecycle — they share that setup, and they are the **only** checks with real side effects on GitHub.
**Together they decide whether the *factory* actually works — the product's central claim, and still
unverified against real GitHub after 25 sprints.** Every other guarantee in this repo is hermetic and
says nothing about it. That makes this the highest-value work outstanding.

> ### ⚠️ Read BL-21 before writing the plan — do not inherit this silently
> **`flows/bootstrap` ships repos with an unprotected `main`.** A brand-new repo accepts direct
> pushes, force-pushes and deletion — while the factory's whole thesis is that integration branches
> are PR-gated. That is a defect **in the very flow §8 exists to verify.** Verifying it as-built
> would confirm it *works*, which is **not** the same as confirming it is *right*.
> **Sprint 36 should almost certainly fix BL-21 and then verify.** Decide it deliberately.
>
> The org-level ruleset (the fix that needs no code) is a **GitHub Team** feature and the org is on
> Free — the endpoint 403s. So it must be installed **per repo, by the thing that creates the repo**:
> likely a new `repo_io` verb called from `flows/bootstrap` *after* `push_branch(main)`. **Note it
> would widen the github MCP server's pinned four-verb set to five if exposed there** — it probably
> should not be (orchestrator-invoked only, like its siblings); the "four verbs, pairwise disjoint"
> assertion in `tests/tools/test_mcp_provider.py` is load-bearing.

**Don't duplicate the protocols** into the sprint plan — §5/§7/§8 in `DEFERRED_VERIFICATION.md` are
the register of record. (§8's old "the `glunk-works` org may not exist" caveat is **closed** — it does.)

No HITL gate is open.

## Gotchas worth remembering
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED` with *nothing failing* is GitHub lag —
  re-read via GraphQL and **wait**. **Do not close+reopen to "fix" it.**
- **A green on a Dependabot PR means nothing unless the run's actor is `dependabot[bot]`** (BL-20).
  Dependabot runs read a *different* secret store, and a close+reopen makes **you** the actor.
  Refresh with **`gh run rerun`** — the PAT now has `actions: write` (verified).
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor owns the same agent socket;
  the script breaks signing and the key *appears* to vanish (`No secret key`). Recovery: reload the
  Cursor window. A signing **`Timeout` means answer the host pinentry prompt** and retry the commit.
- **Rebase a stale branch by merging `main` INTO it** — force-pushing a pushed branch is forbidden.
  Two branches appending to `docs/backlog.md` is **two additions, not a disagreement**: keep **both**.
- Dead refs on the remote (squash-merged, never push): `sprint/34-bl14-dependabot-gap`,
  `sprint/35-tasks-3-4`. Their content is on `main`.

## Pointers
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — **§5/§7/§8 are sprint 36's scope**; every open section now has a named owner.
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, **BL-15**, **BL-16**, **BL-18**, **BL-20**, **BL-21** (read it), **BL-22**, **BL-23**, **BL-24**. Resolved: BL-13, BL-17. Declined: BL-19.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — **history, not a plan.** The **▣ THE LANDING** row records the merge.
- `sprints/36_live_factory_verification/sprint_plan.md` — **to be written by the planning pass.**
- Ruleset healthy 2026-07-14: 4 rule types, 8 required checks, targeting exactly `refs/heads/main`.
