# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — `implementing` (review rework). Tasks 1–3 done, PR #73
reviewed. `architect-review` is GREEN — but the review recommends *against* merging as-is.**
[`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) —
**FD1–FD11 locked; do not re-open them.**

> **A green `architect-review` means the review *happened*, not that it *approved*.** Do not
> merge PR #73 until R1–R3 below land. That distinction is the whole point of the gate.

## Just done (Opus/Architect session, 2026-07-14)
- **Posted the fresh-session HITL review on PR #73** against head `684e03d`
  (`gh pr review --comment`, never `--approve`). The gate flipped green on the
  `pull_request_review: submitted` trigger.
- **Verdict: the design is sound.** `create_ruleset` is in the right module, orchestrator-only is
  the right posture (it follows `resolve_repo_slug`'s precedent instead of becoming a fifth MCP
  verb), running it strictly last is correctly reasoned *and* tested, FD4's `required_status_checks`
  trap is avoided **and** named in its own test, and `private=True` → skip-outright is the right
  call on BL-16 grounds. No design objection.
- **8 findings at `high` effort. Three of them fire on Task 4's first live call** — see below.
- Ruleset preflight: healthy (4 rule types, all 8 required checks on `main`).

## Next — fix R1–R3 on `sprint/36-bl21-ruleset` (**Sonnet/Coder**)
1. **R1 — the `pull_request` rule body is probably incomplete** (`tools/repo_io/github.py:210`). It
   ships only `required_approving_review_count`; GitHub's schema also wants
   `dismiss_stale_reviews_on_push`, `require_code_owner_review`, `require_last_push_approval`,
   `required_review_thread_resolution`. loop-engine's *own* live ruleset round-trips all seven. A
   partial body likely **422s** — and it would do so *after* the repo is created and pushed.
2. **R2 — a failed `create_ruleset` loses the `RepoRef`** (`flows/bootstrap/flow.py:141`).
   `run_bootstrap` propagates and never returns a `BootstrapResult`, so the caller is left with a
   real, public, already-pushed repo and **no slug to tear it down by** — FD11's teardown discipline
   has nothing to consume. Catch it and return `ruleset_installed=False` with a distinct status, or
   attach the `RepoRef` to the raised error.
3. **R3 — the new `input=input_data` plumbing is never exercised** (`tools/repo_io/github.py:52`).
   Every test patches `_run_gh` *itself*, so a dropped/misspelled `input=` would ship **green**. Add
   one test that patches `subprocess.run` and asserts `kwargs["input"]` carries the body. R1 and R3
   compound: an unverified body sent through an unverified channel.

**Optional, same pass or filed:** **R4** — FD3's public-and-protected invariant lives *only* in
`flows/bootstrap`; `repo_io.create_repository` **and** the MCP `github_server.create_repository`
verb still default `private=True` and silently make an unprotected repo. **R5** — `CLAUDE.md:99`
(four-verb `repo_io`), `CLAUDE.md:107` (chain still ends at `create_branch`), and
`.ai/context/modules.md:65` (`private=True`, pre-ruleset chain/result) are **stale**. **R6** —
`test_flow.py:105`'s `len(calls) - 2` is brittle positional coupling; `test_flow.py:34`'s fakes drop
the `name` arg, so nothing pins the ruleset name.

## Then
4. **Pushing the fix turns `architect-review` RED again** — by design; it binds the review to the
   head SHA. So: fresh **Opus** session → `/resume` → `/code-review` → post against the **new** head.
   **Sonnet must not self-review.** Then merge #73.
5. **Then Tasks 4–7** — the sprint's real payload. **Real, irreversible GitHub side effects** and
   **real LLM spend** ($5.00 budget for Task 6). Re-read FD1–FD11 first, especially **FD11**
   (explicit `owner/repo` on every destructive call) and **FD9** (prove the ruleset *rejects* a
   push — observed, not inferred from its existence).

## Gotchas worth remembering
- **A check rollup can show a stale `FAILURE` *and* a fresh `SUCCESS` for the same check.** Seen
  twice this sprint (`pr-title`, `architect-review`). **The latest run is what counts.**
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED`/`UNKNOWN` with *nothing failing* is
  GitHub lag — **the checks are the truth.** Do not close+reopen to "fix" it.
- **PR title regex has no room for commas in the scope** — `[a-z0-9._/-]+` only. Pick **one**
  boundary-derived scope.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** A signing **`Timeout` means
  answer the host pinentry prompt** and retry the commit.
- **Rebase a stale branch by merging `main` INTO it** — force-pushing a pushed branch is forbidden.
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Open, outside the sprint
- **[BL-27] needs one lookup**: `var.github_organization` in `global-bootstrap` has **no default**.
- **At Task 7, decide deliberately whether to REVOKE `administration=write`** (it can delete *any*
  repo in the org, loop-engine included).
- **[BL-2] (Slack bot control plane) gets its planning pass immediately after sprint 36.**

## Pointers
- [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — **the plan. FD1–FD11 locked.**
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — **§5/§7/§8 are Tasks 4–6's protocols**, the register of record. Task 7 retires them (**without renumbering**).
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, BL-15, BL-16, BL-18, BL-20, **BL-21 (Task 7 closes it)**, BL-22..BL-27. Resolved: BL-13, BL-17. Declined: BL-19.
- **PR #73** (`sprint/36-bl21-ruleset` → `main`, head `684e03d`) — reviewed, green, **hold the merge**.
- **PR #74** (`sprint/36-tasks2-3-handoff` → `main`) — docs-only, carries this cursor.
