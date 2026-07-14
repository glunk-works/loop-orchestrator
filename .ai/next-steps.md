# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — `awaiting_hitl_review`. Tasks 1–3 DONE. PR #73 open, all
checks green except `architect-review` (expected — it's the gate).**
[`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) —
**FD1–FD11 locked; do not re-open them.**

## Just done (Sonnet/Coder session, 2026-07-14)
- **Implemented Tasks 2–3, the sprint's only code**, and opened **PR #73** (`sprint/36-bl21-ruleset`
  → `main`, head `684e03d`):
  - `repo_io.create_ruleset(owner, repo, *, branches, name=...)` — a fifth `repo_io` verb (never a
    fifth MCP verb, FD6) shelling `gh api repos/{o}/{r}/rulesets --input -` with an explicit JSON
    body (nested arrays don't survive `-f` flags). Ships `deletion` + `non_fast_forward` +
    `pull_request`, explicitly **no** `required_status_checks` (FD4, its own named test).
  - Wired into `flows/bootstrap.run_bootstrap` as the **last** chain step, strictly after
    `create_branch(develop, base=main)` (FD7), targeting **both** `main` and `develop` (FD5).
  - `BootstrapRequest.private` now defaults to **`False`** (FD3). `private=True` stays reachable as
    an explicit opt-in that **skips `create_ruleset` outright** — never attempts a call already known
    to 403 — and `BootstrapResult` gained `ruleset_installed: bool` so `CREATED` is never mistaken
    for protected (the decision the plan left open: refuse/skip cleanly, not catch-and-warn).
- 561/561 tests pass, `lint`/`format` clean, no new dependency (no `sbom` regen needed). All 8
  automated PR checks green except `architect-review`, which is expected to fail until posted.

## Next
1. **Fresh Opus session**: `/resume` → `/code-review` on PR #73 → post with
   `gh pr review --comment` (never `--approve`) against the **current head commit** (`684e03d` as of
   this writing — re-check `gh pr view 73` for drift before posting). This is a genuinely new
   session, not `/model opus` mid-session (CLAUDE.md's HITL-review note — a mid-session switch
   proofreads its own reasoning instead of re-deriving it).
2. **Merge PR #73** once `architect-review` + the other 7 checks are green.
3. **Then Tasks 4–7** — the sprint's real payload. **Real, irreversible side effects on GitHub** (live
   `github_server` verbs, a real bootstrapped repo, a real maintained repo) **and real LLM spend**
   ($5.00 budget for Task 6's inner loop). Re-read FD1–FD11 before starting; **FD11** (explicit
   `owner/repo` on every destructive call, especially the Task 7 teardown's `gh repo delete`) and
   **FD9** (prove the ruleset *rejects* a push — observed, not inferred from its existence) matter most.

## Gotchas worth remembering
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED`/`UNKNOWN` with *nothing failing* is
  GitHub lag — **the checks are the truth.** Do not close+reopen to "fix" it.
- **PR title regex has no room for commas in the scope** — `[a-z0-9._/-]+` only. A first-cut title
  `feat(repo-io,bootstrap): ...` failed `pr-title`; pick **one** boundary-derived scope.
- **A green on a Dependabot PR means nothing unless the run's actor is `dependabot[bot]`** (BL-20).
  Refresh with **`gh run rerun`**.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor owns the same agent
  socket; a signing **`Timeout` means answer the host pinentry prompt** and retry the commit.
- **Rebase a stale branch by merging `main` INTO it** — force-pushing a pushed branch is forbidden.
- Dead refs on the remote (squash-merged, never push): `sprint/34-bl14-dependabot-gap`,
  `sprint/35-tasks-3-4`, `sprint/36-archive-35`, `sprint/36-plan`, `sprint/36-bl25`, `sprint/36-handoff`.
- **`.ai/state.json` is gitignored** — the machine cursor is local-only. **`next-steps.md` is what
  travels.** If you pick this up on another host, this file is all you get.

## Open, outside the sprint
- **[BL-27] needs one lookup**: `var.github_organization` in `global-bootstrap` has **no default** —
  settle it against the live tofu backend before it's forgotten once Tasks 4–7 get busy.
- **At Task 7, decide deliberately whether to REVOKE `administration=write`.**
- **[BL-2] (Slack bot control plane) gets its planning pass immediately after sprint 36** (owner's call).

## Pointers
- [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — **the plan. FD1–FD11 locked.**
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — **§5/§7/§8 are Tasks 4–6's protocols**, the register of record; the plan does not duplicate them. Task 7 retires them (**without renumbering**) and corrects FD1's stale premise.
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, BL-15, BL-16, BL-18, BL-20, **BL-21 (Task 7 closes it)**, BL-22, BL-23, BL-24, BL-25, BL-26, BL-27. Resolved: BL-13, BL-17. Declined: BL-19.
- PR #73 (`sprint/36-bl21-ruleset` → `main`) — Tasks 2–3, awaiting fresh-session `architect-review`.
- Ruleset healthy 2026-07-14: 4 rule types, 8 required checks, targeting exactly `refs/heads/main`.
