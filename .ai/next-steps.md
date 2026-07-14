# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`sprints/36_live_factory_verification/sprint_plan.md`, `docs/backlog.md`) — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — `implementing`. S1–S3 landed; awaiting a THIRD review round.**
PR **#73** (`sprint/36-bl21-ruleset` → `main`) — pushing the S1–S3 fix commit re-reds `architect-review`
**by design**; it must NOT be merged until a fresh Opus session posts a new review against the new head.
FD1–FD11 are locked; do not re-open them.

> ## ⚠️ A GREEN `architect-review` MEANS THE REVIEW *HAPPENED*, NOT THAT IT *APPROVED*
> Once the third review is posted, verify what it actually says before merging — a green check proves a
> fresh-session review exists for that head SHA, nothing more. Merging on the strength of the green check
> alone is BL-16's exact shape, on our own process.

## Just done (this session — Sonnet, S1–S3 landed on top of `75e8d42`)
- **S1 fixed** — `tests/tools/test_repo_io.py::test_create_ruleset_pull_request_rule_declares_full_parameters`
  now asserts the full `pull_request` rule `parameters` dict, not just rule *type* strings.
- **S2 fixed** — `test_create_ruleset_body_carries_the_required_name_field` asserts `body["name"]` under both
  the default and an explicit override. Both `_FakeRepoIO.create_ruleset` fakes
  (`tests/flows/bootstrap/test_flow.py`, `tests/flows/bootstrap/test_integration.py`) now record `name` in
  their call tuples instead of silently discarding it, closing the flow-level assertion gap too.
- **S3 fixed** — `CLAUDE.md:99` now says `repo_io` is five verbs (adds `create_ruleset`, notes it's
  orchestrator-only, never an MCP verb); `CLAUDE.md:107` and `.ai/context/modules.md:65` now describe the
  full bootstrap chain through `create_ruleset`, `private=False` default, and the `RULESET_FAILED` /
  `ruleset_installed` result shape.
- **565/565 tests pass** (563 + 2 new), lint clean, format clean. S4–S9 were left open (not required to
  unblock the third review; see `.ai/state.json` → `pointers.open_findings` if picked up later).

## Next — push, then a THIRD fresh Opus review
**Model: Opus/Architect, fresh session.** Push `sprint/36-bl21-ruleset`, then `/resume` → `/code-review` →
post against the **new head** with `gh pr review 73 --comment`. **Sonnet must not self-review.** If the
third review is clean, the human merge is next; if it finds anything, land it same as this round.

**S4–S9 are still open and undone** (deliberately deferred — not blocking): `ruleset_installed` doesn't carry
the discarded ruleset id (S4); the bare `except Exception` in `flow.py` can swallow a successful create's
response parse and report `RULESET_FAILED` on a protected repo (S5); `RULESET_FAILED` carries no 403-vs-422
error detail (S6); `branches=[]` is unguarded (S7); `create_repository` still defaults `private=True` in
`repo_io` and the MCP verb even though `flows/bootstrap` overrides it to `False` (S8, = R4); a brittle
positional assert in `test_flow.py` was never deleted now that a position-independent test covers it (S9, =
R6 first half). Full text in `.ai/state.json` → `pointers.open_findings`.

## Gotchas worth remembering
- **A check rollup shows BOTH the stale `FAILURE` and the fresh `SUCCESS` for one check name.** Seen
  repeatedly this sprint (`pr-title`, `architect-review`; `FAILURE`@21:07, `SUCCESS`@21:46). **The latest run is what counts.**
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED`/`UNKNOWN` with *nothing failing* is GitHub lag — wait.
  **The checks are the truth. Do not close+reopen to "fix" it.**
- **A `CONFLICTING` PR runs ZERO CI** — an empty check rollup on #73 is not "all green", it is "nothing ran".
  Resolve the conflict (merge `main` INTO the branch) and let CI actually run before reading it.
- **PR title regex has no room for commas in the scope** — `[a-z0-9._/-]+` only. Pick **one** boundary-derived scope.
- **⚠️ The PAT carries `administration=write` on the org — it can DELETE ANY REPO, `loop-engine` included.**
  Never point sprint 36's flows at `loop-engine`; hard-code the scratch repo name and read it back before every
  destructive call (FD11). `gh repo delete` takes no explicit target and resolves from the CWD — that is finding
  R8 with an irreversible verb on the other end.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor owns the same agent socket; the script
  breaks signing and the key *appears* to vanish (`No secret key`). Recovery: reload the window. A signing
  **`Timeout` means answer the host pinentry prompt** and retry the commit.
- **Rebase a stale branch by merging `main` INTO it** — force-pushing a pushed branch is forbidden.
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Open, outside the sprint
- **[BL-27] needs one lookup**: `var.github_organization` in `global-bootstrap` has **no default**.
- **At Task 7, decide deliberately whether to REVOKE `administration=write`** (it can delete *any*
  repo in the org, loop-engine included).
- **[BL-2] (Slack bot control plane) gets its planning pass immediately after sprint 36.**

## Pointers
- [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — **the plan. FD1–FD11 locked.** Tasks 4–7 (the live protocols + teardown) are untouched.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — **§5/§7/§8 are this sprint's protocols** and the register of record. Task 7 retires them (**without renumbering**).
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, BL-15, BL-16, BL-18, BL-20, **BL-21 (this sprint closes it)**, BL-22..BL-27. Resolved: BL-13, BL-17. Declined: BL-19.
- **PR #73** (`sprint/36-bl21-ruleset` → `main`) — S1–S3 landed; **awaiting the third review round against the new head** — hold the merge.
- Ruleset on loop-engine's own `main` healthy 2026-07-14: 4 rule types, 8 required checks, targeting exactly `refs/heads/main`.
