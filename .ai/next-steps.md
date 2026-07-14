# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**THE MIGRATION IS ON `main`.** PR #58 merged as merge commit **`d2135e7`** — two parents, 113
commits preserved, **not squashed**. `main`'s tree is `4aad78e`, byte-for-byte the tree the Task 3
preflight predicted. The two-branch era is over: cut sprint branches from **`main`**, base PRs on
**`main`**. Sprint `35_migration_merge` — **Task 6 (planning) is all that's left.**

## Just done (Opus/Architect session, 2026-07-14)
- **Posted PR #58's `architect-review`** from a genuinely fresh session, bound to head `b669482`,
  scoped per **FD7** as an *integration* review (does the merge produce the predicted workflow set;
  is `ci.yml` post-sprint-33; do the four workflows co-exist) and **explicitly declining** to
  re-review the 113 already-reviewed commits. Owner merged. **Task 4 done.**
- **Task 5 done bar one step.** `allow_merge_commit` held across the merge, merge-commit button
  used, then set back to **`false`** — repo is now squash-only, closing **BL-13** and BL-11's
  "three strategies, one convention" gap. Retiring `feat/**` was **deferred by the owner → BL-17**.
- **Unblocked all four Dependabot PRs (#50–53).** They were never conflicted (FD5 vindicated), but
  were blocked by **two** structural faults: `GITLEAKS_LICENSE` lived in the org **Actions** secret
  store while Dependabot-triggered runs can read only the org **Dependabot** store (owner fixed);
  and Dependabot's default title `Bump X from A to B` fails the required `pr-title` check. Retitled
  all four by hand — **all now `CLEAN`, 8/8**.
- **PR #61** (docs: Task 5 close-out, BL-17/18/19) and **PR #62** (`dependabot.yml` Conventional
  Commits prefix + a test that runs Dependabot's generated subject through `pr-title.yml`'s *own*
  regex). Both **CLEAN**, both docs/CI-config only so `architect-review` is exempt.

## Task 6 — DONE (the planning; the merges are the human's)

### (a) Dependabot #50–53 — reviewed on their merits. **Verdict: merge all four.**
**They are not four upgrades. They are one deadline.** Every one is, at root, the **Node 20 → Node
24 runtime migration** — not features. GitHub flipped the runner default to Node 24 on **2026-06-02**
(already past — our logs show `actions target Node.js 20 but are being forced to run on Node.js 24`)
and **removes Node 20 entirely on 2026-09-16**. `secrets-scan` is a **required** check: when
`gitleaks-action@v2` stops working, **every PR in this repo becomes unmergeable**, on a known date.

Each verdict was checked against how we *actually* use the action, not just the changelog:
- **#50 `gitleaks-action` 2.3.9→3.0.0 — merge first.** Release notes: *"No changes to inputs,
  outputs, or behavior."* Pure runtime. **This is the one with the deadline.**
- **#53 `checkout` 4.3.1→7.0.0.** The only genuinely behavioral change in the whole set is v7
  **blocking fork-PR checkout for `pull_request_target` / `workflow_run`** — and we have **neither
  trigger anywhere**; only `ci.yml` checks out, and CI never pushes. v6's "persist creds to a
  separate file" likewise cannot reach us. v7's change is a security *hardening*.
- **#51 `setup-python` 5.6.0→6.3.0.** v6's break is Node 24 + runner floor; its other changes are all
  cache-related and **we pass no `cache:` input**, only `python-version`.
- **#52 `upload-artifact` 4.6.2→7.0.1.** v7's `archive:` param is **additive and opt-in** (its
  multi-file-glob failure applies only with `archive: false`, which we don't set). Single
  `sbom.json`, default settings, behavior unchanged.
- The **`v2.327.1` minimum-runner** requirement is a non-issue: all six jobs are `ubuntu-latest`
  (GitHub-hosted). It would only bite self-hosted runners; we have none.

**Merging (human):** one at a time — all four edit `ci.yml`'s `uses:` lines, so each merge staleness
the rest and Dependabot rebases them (same conflict logic as FD5). **And check the actor before
trusting any green** — `gh api repos/glunk-works/loop-engine/actions/runs/<id> --jq .actor.login`
must say `dependabot[bot]`; a human close+reopen reads the *other* secret store (**BL-20**).

### (b) The five never-run checks now each have a scheduled owner (agreed 2026-07-14)
| Section | Home |
| --- | --- |
| **§5** `github_server` verbs, **§7** maintenance flow, **§8** bootstrap flow | **Sprint 36 — live factory verification** (one daemon-bearing host, authenticated `gh`, one scratch-repo lifecycle) |
| **§1** caching + USD smoke | **folded into BL-3** — it *is* BL-3's evidence-gathering step |
| **§6** live webhook | **BL-24** — lowest priority (needs a tunnel; nothing depends on the surface) |

**§8's org blocker is closed:** `glunk-works` exists (verified live) — no substitute org needed.

## Next — Opus/Architect
**Plan sprint 36 — live factory verification (§5 + §7 + §8).** These are the only checks with real
side effects on GitHub, and together they decide whether **the factory actually works** — the
product's central claim, still unverified against real GitHub after 25 sprints. Everything else in
this repo is hermetic and says nothing about it.

No HITL gate is open.

## Gotchas worth remembering
- **`gh pr view` serves stale `mergeStateStatus`.** `BLOCKED` with *nothing failing* is usually
  GitHub not having recomputed — re-read via GraphQL before intervening (hit on #58 *and* #62; both
  were actually `CLEAN`). Do **not** close+reopen to "fix" it.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor does its own GPG agent
  forwarding and owns `~/.gnupg/S.gpg-agent`; the script fights it for the same path and breaks
  signing (the key then appears to vanish: `No secret key`). A signing **`Timeout` means answer the
  host pinentry prompt**, not repair the agent. Recovery: reload the Cursor window.

## Human actions
- **Merge #50–53** — one at a time, letting Dependabot rebase between (Task 6(a) above has the
  verdicts and the reasoning). **#50 first — it carries the 2026-09-16 deadline.**
- **BL-17:** retire `feat/**` — it still exists at `b669482`, having survived the merge *by design*
  (FD6: the ruleset's `deletion` rule beat `delete_branch_on_merge`).
- **Grant the PAT `actions: write`** — its absence forced the close+reopen that produced BL-20's
  false pass. `gh run rerun` is the correct way to refresh a Dependabot PR's checks, and it needs
  this. (Secrets **read** was granted 2026-07-14 and is what finally diagnosed the gitleaks bug.)
- ~~delete `glunk-works/loop-engine-v3-scratch`~~ — **done**; the repo no longer exists (verified
  against the org's repo list, 2026-07-14).

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) — FD1–FD7; only Task 6 remains.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-13 resolved**; BL-12/BL-14's topology pattern **closed by the merge**; **BL-19 DECLINED** (keep `gitleaks-action`); **new: BL-17, BL-18, BL-20**; BL-15/BL-16 open.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed; the merge closes the topology question too.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — the five never-run checks (Task 6 homes them).
- Ruleset checked healthy 2026-07-14: 4 rule types, all 8 required checks on `main`.
