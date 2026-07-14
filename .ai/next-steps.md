# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — `planned`. Opus/Architect wrote the plan; Sonnet/Coder takes Tasks 2–3.**
[`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) —
**FD1–FD9 are locked; do not re-open them.**

> ## ⛔ ONE HUMAN ACTION BLOCKS THE ENTIRE SPRINT (Task 1)
> On the fine-grained PAT (the token `gh` authenticates as **`Seuss27`**), set
> **Repository access → All repositories** *and* grant
> **Repository permissions → Administration: Read and write**.
> (A scratch repo that does not exist yet cannot be in a "selected repositories" list.)
>
> **Measured, not guessed** — both 403 today, both are the same grant:
> ```
> POST orgs/glunk-works/repos           -> 403  X-Accepted-Github-Permissions: administration=write
> POST repos/glunk-works/<r>/rulesets   -> 403  X-Accepted-Github-Permissions: administration=write
> ```
> **Verify by exercising those two endpoints — a `422` is a PASS** (permission cleared, body rejected).
>
> 🚩 **`GET orgs/glunk-works/rulesets` is NOT a valid signal (FD10).** It returns
> `403 "Upgrade to GitHub Team"` **whatever you grant** — org-level rulesets are a Team feature, which
> is FD3's own premise. The first cut of this plan used it as Task 1's acceptance criterion anyway.
> A check that can never go green is **BL-16 wearing a different hat**. Do not reintroduce it.
>
> ⚠️ This grant can **delete any repo in the org, loop-engine included.** Never point sprint 36's flows
> at `loop-engine`; hard-code the scratch repo's name.

## Just done
**Sprint 35 is COMPLETE and archived**; the migration is landed on `main` (merge commit `d2135e7`) and
the roadmap is **history, not a plan**. `main` = `c8eae78`. No open PRs, no live sprint branches.
Then: **sprint 36's planning pass** (this one) wrote the plan below.

## The plan, in one breath
Prove **the factory actually works** against real GitHub — `DEFERRED_VERIFICATION.md` **§5** (github
verbs), **§8** (bootstrap) and **§7** (maintenance) — but **fix BL-21 first**, because §8 exists to
verify a flow that ships an **unprotected `main`**, and verifying it as-built would confirm it *works*,
not that it is *right*. One disposable **public** scratch repo chains all three: **§8 births it, §7
maintains it.** Tasks 2–3 are code (Sonnet); Tasks 4–6 are **executed protocols** with **real side
effects on GitHub and real LLM spend** ($5.00 budget); Task 7 discharges the sections and tears down.

### Three findings from the planning pass that changed the sprint's shape
- **FD1 — the "daemon-bearing host" was never needed, and it is what deferred these checks for 25 sprints.**
  `DEFERRED_VERIFICATION.md` claims this devcontainer "has no `gh` auth and no network". **False**: `gh` is
  authenticated, the network resolves, and the Anthropic key is in the keyring. §5/§7/§8 need *authenticated
  `gh` + network + a scratch repo* — **no daemon**. That word was inherited from **§6** (bind a port GitHub
  can reach), which is genuinely blocked and is correctly **BL-24**. **This session's container is the host.**
- **FD3 — BL-21's fix is impossible as BL-21 sketches it.** Repo-level rulesets are free on **public** repos
  only; on Free, a **private** repo needs GitHub Team — the *same 403* that killed the org-level fix. And
  `BootstrapRequest.private` defaults to **`True`**. So bootstrap must flip to **`private=False`**:
  **protection becomes the invariant, privacy the opt-in that knowingly forfeits it.** (All five repos in the
  org are already public — none came out of the factory.)
- **FD4 — the shipped ruleset must require ZERO status checks.** The scaffold ships **no `.github/workflows/`
  at all**. Any required check would be permanently pending and the repo could **never merge anything** —
  BL-21's stated trap, and the mirror-image of BL-11. **Do not template loop-engine's eight checks.**

> **FD9 — and the one that matters most: a ruleset that EXISTS is not a ruleset that BLOCKS.**
> Task 5's deliverable is an **observed rejection** of a deliberate direct push to `main`, not the
> ruleset's presence in an API response. This repo's recurring defect (BL-11, **BL-16**, BL-18, BL-20)
> is *a check that verified the wrong property while reporting success.* Do not add a fifth.

## Next
1. **Task 1 — the human PAT grant** (above). Everything is blocked on it. **Do not start Task 2 hoping it
   lands later**: `create_ruleset`'s tests are hermetic and will pass *without* the grant, so a green suite
   would prove nothing about whether the verb can actually run. That is the BL-16 trap, in advance.
2. Then `/handoff` → **Sonnet/Coder** for **Tasks 2–3** (the BL-21 fix: `repo_io.create_ruleset`, wired
   into `flows/bootstrap` as its **last** step, `private` default flipped).
3. Then **Opus** for Tasks 4–6 (the live protocols) and Task 7. The sprint PR touches `src/`, so it needs a
   **fresh-session** `architect-review`.

## Gotchas worth remembering
- **`create_ruleset` is a `repo_io` verb, NOT an MCP verb** (FD6). The github MCP server stays at **four**,
  pairwise-disjoint — `tests/tools/test_mcp_provider.py`'s assertion is load-bearing. Precedent:
  `resolve_repo_slug` is already exactly this shape.
- **Ordering is load-bearing** (FD7): `create_ruleset` runs **last**, after `create_branch(develop)`. Install
  it any earlier and the `pull_request` rule rejects bootstrap's own initial push to `main`.
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED` with *nothing failing* is GitHub lag —
  re-read via GraphQL and **wait**. **Do not close+reopen to "fix" it.**
- **A green on a Dependabot PR means nothing unless the run's actor is `dependabot[bot]`** (BL-20).
  Refresh with **`gh run rerun`** — the PAT has `actions: write`.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor owns the same agent socket; the
  script breaks signing and the key *appears* to vanish (`No secret key`). Recovery: reload the window.
  A signing **`Timeout` means answer the host pinentry prompt** and retry the commit.
- **Rebase a stale branch by merging `main` INTO it** — force-pushing a pushed branch is forbidden.
- Dead refs on the remote (squash-merged, never push): `sprint/34-bl14-dependabot-gap`,
  `sprint/35-tasks-3-4`, `sprint/36-archive-35`.

## Pointers
- [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — **the plan. FD1–FD9 locked.**
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — **§5/§7/§8 are this sprint's protocols** and are the register of record; the plan deliberately does **not** duplicate them. Task 7 retires them (**without renumbering**) and corrects the stale premise FD1 found.
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, BL-15, BL-16, BL-18, BL-20, **BL-21 (this sprint closes it)**, BL-22, BL-23, BL-24. Resolved: BL-13, BL-17. Declined: BL-19.
- Ruleset healthy 2026-07-14: 4 rule types, 8 required checks, targeting exactly `refs/heads/main`.
