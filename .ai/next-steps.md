# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — `planned`, Task 1 DONE, code not started.**
Plan: [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — **FD1–FD11 locked; do not re-open them.**
**Next session: Sonnet/Coder, Tasks 2–3.**

## Just done (Opus/Architect planning session, 2026-07-14)
- **Wrote the sprint 36 plan.** Fix **BL-21** first, *then* verify the factory live —
  `DEFERRED_VERIFICATION.md` **§5** (github verbs) → **§8** (bootstrap) → **§7** (maintenance),
  chaining **one disposable public scratch repo**: §8 births it, §7 maintains it.
- **Task 1 (the PAT grant) is DONE and verified.** `administration=write` is live —
  `POST orgs/glunk-works/repos` and `POST repos/{o}/{r}/rulesets` now return **422** (body rejected)
  instead of **403** (permission rejected). **Nothing is blocked.**
- **Filed BL-25, BL-26, BL-27; scheduled BL-2** (PR #71).

## Next
1. **Merge PR #70** (this plan — 8/8 checks green) and **PR #71** (backlog). Both docs-only.
2. **Fresh Sonnet session → Tasks 2–3** — the sprint's *only* code:
   `repo_io.create_ruleset` (a fifth **`repo_io`** verb, **NOT** a fifth MCP verb — FD6), wired into
   `flows/bootstrap` as its **last** step (FD7), and `BootstrapRequest.private` flipped to **`False`** (FD3).
   That PR touches `src/` ⇒ it needs a **fresh-session** `architect-review` (so: a third session after Sonnet's).
3. **Then Opus** for Tasks 4–7 — the live protocols and teardown. **Real side effects on GitHub, real
   LLM spend ($5.00 budget).** This is the payload.

## The four things that will bite the next session
> **FD3 — bootstrap must ship PUBLIC repos.** Repo-level rulesets are free on **public** repos only;
> under the org's Free plan a **private** repo needs GitHub Team — *the same 403 that killed the
> org-level fix*. `BootstrapRequest.private` defaults to `True` today, so the BL-21 fix **cannot work**
> until it flips. **Protection is the invariant; privacy is the opt-in that knowingly forfeits it.**

> **FD4 — the shipped ruleset requires ZERO status checks.** `tools/scaffold/templates/` contains **no
> `.github/workflows/` at all**. Any required check would be permanently pending and the repo could
> **never merge anything**. **Do not template loop-engine's eight checks.** (Adding CI to the scaffold
> is deliberately out of scope — it is **[BL-26]**.)

> **FD9 — a ruleset that EXISTS is not a ruleset that BLOCKS.** Task 5's deliverable is an **observed
> rejection** of a deliberate direct push to `main`, not the ruleset's presence in an API response.
> BL-11 / BL-16 / BL-18 / BL-20 are all *a check that verified the wrong property while reporting
> success*. Do not add a fifth.

> **FD11 — the teardown is the dangerous call, and we have ALREADY made this mistake.** Sprint 36 is
> **not** the factory's first live GitHub run — **V3 was**, and its finding **R8** was escalation issues
> filed on **`loop-engine` itself** because `gh` inherited its destination from the ambient CWD. Every
> `repo_io` verb takes an explicit target now — **but `gh repo delete` does not, and Task 7 uses it.**
> The token carries `administration=write` across the org. **Explicit `owner/repo` on every destructive
> call, asserted against the scratch name immediately before firing. Never `cd` and delete.**

## Open, outside the sprint
- **[BL-27] needs one lookup**: `var.github_organization` in `global-bootstrap` has **no default**, so
  its applied value is unreadable from source — and the two candidates give opposite answers (`Seuss27`
  ⇒ no dangling roles but **no org repo can deploy**; `glunk-works` ⇒ **three IAM roles trust repos that
  do not exist**). Cheap to settle against the live tofu backend; easy to forget once 36 gets busy.
- **At Task 7, decide deliberately whether to REVOKE `administration=write`.** The sprint needs it for
  one window; it can delete any repo in the org.
- **[BL-2] (Slack bot control plane) gets its planning pass immediately after sprint 36** (owner's call).

## Gotchas worth remembering
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED`/`UNKNOWN` with *nothing failing* is
  GitHub lag — **the checks are the truth.** Do not close+reopen to "fix" it.
- **A green on a Dependabot PR means nothing unless the run's actor is `dependabot[bot]`** (BL-20).
  Refresh with **`gh run rerun`**.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor owns the same agent socket.
  A signing **`Timeout` means answer the host pinentry prompt** and retry the commit.
- **Rebase a stale branch by merging `main` INTO it** — force-pushing a pushed branch is forbidden.
  Two branches appending to `docs/backlog.md` is **two additions, not a disagreement**: keep **both**.
- Dead refs on the remote (squash-merged, never push): `sprint/34-bl14-dependabot-gap`,
  `sprint/35-tasks-3-4`, `sprint/36-archive-35`.
- **`.ai/state.json` is gitignored** — the machine cursor is local-only. **`next-steps.md` is what
  travels.** If you pick this up on another host, this file is all you get.

## Pointers
- [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — **the plan. FD1–FD11 locked.**
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — **§5/§7/§8 are the protocols** and the register of record; the plan does **not** duplicate them. Task 7 retires them (**without renumbering**) and corrects the stale "daemon-bearing host / no `gh` auth" premise (**FD1** — this devcontainer *is* the host).
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, BL-15, BL-16, BL-18, BL-20, **BL-21 (this sprint closes it)**, BL-22, BL-23, BL-24, **BL-25**, **BL-26**, **BL-27**. Resolved: BL-13, BL-17. Declined: BL-19.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — **history, not a plan.**
