# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge` is COMPLETE.** All six tasks done, every PR merged, nothing open.
`main` = **`0e50552`**.

**THE MIGRATION IS ON `main`.** PR #58 merged as merge commit **`d2135e7`** — two parents, 113
commits preserved, **not squashed**; `main`'s tree came out byte-for-byte the tree the preflight
predicted. **The two-branch era is over:** cut sprint branches from **`main`**, base PRs on
**`main`**. The one-time merge-commit exception is **spent** — `allow_merge_commit` is back to
`false` and the repo is squash-only.

## Just done (Opus/Architect, 2026-07-14)
- **The migration landed**, reviewed fresh-session per FD7 as an *integration* review (explicitly
  declining to re-review the 113 already-reviewed commits) and merged by the owner.
- **Task 5:** `allow_merge_commit` → `false` (**BL-13 closed**, and BL-11's "three strategies, one
  convention" gap with it). Retiring `feat/**` was deferred → **BL-17**.
- **All four Dependabot majors merged (#50–53).** They were **not four upgrades — one deadline**:
  every one is the Node 20 → Node 24 runtime migration, and GitHub **removes Node 20 on
  2026-09-16**. `secrets-scan` is a *required* check, so `gitleaks-action@v2` dying would have made
  **every PR unmergeable** on a known date. That deadline is now closed.
- **Fixed two structural CI faults they exposed:** `GITLEAKS_LICENSE` was **misnamed** in the org
  **Dependabot** secret store (**BL-20**), and Dependabot's default PR title fails the required
  `pr-title` check by construction (fixed in `dependabot.yml`, PR #62 — pinned by a test that runs
  Dependabot's generated subject through `pr-title.yml`'s *own* regex).
- **Task 6:** the four majors reviewed on their merits, and **every deferred check given a named
  owner** — §5/§7/§8 → sprint 36, §1 → folded into BL-3, §6 → BL-24.
- **Filed:** BL-17, BL-18, BL-20, BL-22, BL-23, BL-24. **Declined:** BL-19 (keep `gitleaks-action`).

## Next — Opus/Architect
1. **`/archive-sprint`** — sprint 35 is complete and merged; retire it.
2. **Plan sprint 36 — live factory verification** (§5 `github_server` verbs + §7 maintenance flow +
   §8 bootstrap flow). One daemon-bearing host, authenticated `gh`, network, one disposable
   scratch-repo lifecycle. **These are the only checks with real side effects on GitHub, and
   together they decide whether the *factory* works — the product's central claim, still unverified
   against real GitHub after 25 sprints.** Everything else here is hermetic and says nothing about it.

> ### ⚠️ Read BL-21 before planning sprint 36
> **`flows/bootstrap` ships repos with an unprotected `main`** (BL-21, from PR #65) — a defect **in
> the very flow §8 exists to verify**. Verifying it as-built would confirm it *works*, which is
> **not** the same as confirming it is *right*. Sprint 36 should almost certainly **fix BL-21 and
> then verify** — not verify, then discover. Decide that deliberately.

No HITL gate is open.

## Gotchas worth remembering
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED` with *nothing failing* is GitHub
  lag — re-read via GraphQL and **wait**. Hit on #58, #62, #64 and #66; all settled `CLEAN` on their
  own. **Do not close+reopen to "fix" it.**
- **A green on a Dependabot PR means nothing unless the run's actor is `dependabot[bot]`** (BL-20).
  Dependabot runs read a *different* secret store, and a close+reopen makes **you** the actor.
  Refresh with **`gh run rerun`** — the PAT now has `actions: write` (verified working).
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor owns the same agent
  socket; the script breaks signing and the key *appears* to vanish (`No secret key`). Recovery:
  reload the Cursor window. A signing **`Timeout` means answer the host pinentry prompt** and retry
  the commit — it is **not** a broken agent.
- **Rebase a stale sprint branch by merging `main` INTO it** — force-pushing a pushed branch is
  forbidden, and the squash-merge collapses it anyway. Two branches appending to `docs/backlog.md`
  is **two additions, not a disagreement**: keep **both** sides.

## Human actions
**None outstanding.**

- ~~**BL-17 — retire `feat/**`**~~ — **DONE 2026-07-14.** The owner dropped `feat/**` from the
  ruleset's targets (it now targets exactly `refs/heads/main`); the branch was proven fully merged
  (`b669482` is an **ancestor of `main`** and is `d2135e7`'s second parent — **zero** unmerged
  commits, so nothing was discarded) and deleted. **`main`'s protection was verified before *and*
  after**, then confirmed **independently** by dispatching `ruleset-drift.yml`, which reported
  `OK: ruleset intact -- 4 rule types, 8 required checks`. A weakened `main` fails **open** — every
  check still runs and reports, and none of them blocks — so the after-check is the item, not
  bookkeeping.
- Loose end, folded into **BL-22** (not lost): `ci.yml` still has `push: branches: [main, 'feat/**']`.
  That glob is now **dead** — it matches nothing, costs nothing. Drop it in the next CI-config pass.

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, **BL-15**, **BL-16**, **BL-17**, **BL-18**, **BL-20**, **BL-21**, **BL-22**, **BL-23**, **BL-24**. Resolved: BL-13 (+ BL-12/BL-14's pattern, closed by the merge). Declined: **BL-19**.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — every open section now has a named owner (Task 6).
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) — FD1–FD7; all six tasks done.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed; the merge closes the topology question too.
- Ruleset checked healthy 2026-07-14: 4 rule types, all 8 required checks on `main`.
