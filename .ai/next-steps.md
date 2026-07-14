# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`sprints/36_live_factory_verification/sprint_plan.md`, `docs/backlog.md`) — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — `implementing`. BL-21's code fix is LANDED on `main`.**
PR **#73** merged (squash `91adf5c`, 2026-07-14 23:01Z). Tasks 1–3 done; **Tasks 4–7 (the live
verification + teardown) are untouched.** FD1–FD11 are locked; do not re-open them.

## Just done (this session — Opus/Architect)
- **Untangled PR #73's conflict-and-CI mess.** Merged the advanced `main` (`c63445c`) into
  `sprint/36-bl21-ruleset`, resolved the one `.ai/next-steps.md` conflict by reconciling both
  sides. The PR had been `CONFLICTING` → **running zero CI silently**; the merge cleared it and CI
  actually ran. Suite green on the merged tree (**565/565**), pushed (`0afed6d`).
- **Posted the third fresh-session Opus HITL review** against `0afed6d` (`gh pr review --comment`).
  Verdict: **clear to merge** — R1/R2/R3 (the round-1/2 blockers) genuinely closed; the full
  `pull_request` body and the `input=` channel are now both actually asserted. `architect-review`
  went green (`failure`@22:45 → `success`@22:56 — the latest run counts).
- **PR #73 merged** by the human — `91adf5c` on `main`. Local `main` fast-forwarded to it.

## Next — pick a track, then start it (**Opus/Architect to plan; Sonnet/Coder for Track A code**)
Two tracks remain on the sprint. **Recommendation: Track A first**, so the code Track B exercises
live is the hardened code.

- **Track A — S4–S9 hardening** (Sonnet, fresh `sprint/36-*` branch, PR based on `main`). Six
  non-blocking findings from the round-3 review, ranked. **S5 first — it has an irreversible
  consequence:** the bare `except Exception` in [`flow.py:175`](../src/loop_engine/flows/bootstrap/flow.py#L175)
  also catches `create_ruleset`'s own `json.loads(output)["id"]` parse
  ([`github.py:231`](../src/loop_engine/tools/repo_io/github.py#L231)), so a ruleset that *was*
  created but returned an unparseable body reports `RULESET_FAILED` → an operator tears down a
  **protected** repo (inverse of BL-16). Fix: narrow to `subprocess.SubprocessError`. Full text of
  S4–S9 in `.ai/state.json` → `pointers.open_findings` and in the review comment on PR #73.
- **Track B — Tasks 4–7, the sprint's real payload.** Run `flows/bootstrap` + `flows/maintenance`
  against a **real scratch repo** in `glunk-works`, **prove the ruleset REJECTS a push** (FD9 —
  observed, not inferred from the ruleset's existence), then teardown (FD11) and decide whether to
  revoke `administration=write` (Task 7, which closes BL-21). **Real, irreversible GitHub side
  effects and real LLM spend** ($5.00 budget at Task 6). **Re-read FD1–FD11 first**, especially
  **FD11** (explicit `owner/repo` on every destructive call; NEVER point a flow at `loop-engine`)
  and **FD9**.

## Gotchas worth remembering
- **A `CONFLICTING` PR runs ZERO CI** — an empty check rollup is "nothing ran", not "all green".
  Resolve it (merge `main` INTO the branch) and let CI actually run before reading it. (Hit this session.)
- **A check rollup shows BOTH the stale `FAILURE` and the fresh `SUCCESS` for one check name.** The
  latest run is what counts (`architect-review`: `failure`@22:45, `success`@22:56 this session).
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED`/`UNKNOWN` with *nothing failing* is
  GitHub lag — **the checks are the truth.** Do not close+reopen to "fix" it.
- **PR title regex has no room for commas in the scope** — `[a-z0-9._/-]+` only. Pick **one** scope.
- **⚠️ The PAT carries `administration=write` on the org — it can DELETE ANY REPO, `loop-engine` included.**
  Hard-code the scratch repo name and read it back before every destructive call (FD11). `gh repo
  delete` takes no explicit target and resolves from the CWD — finding R8 with an irreversible verb.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** Cursor owns the same agent socket;
  the script breaks signing and the key *appears* to vanish (`No secret key`). Recovery: reload the
  window. A signing **`Timeout` means answer the host pinentry prompt** and retry the commit.
- **Rebase a stale branch by merging `main` INTO it** — force-pushing a pushed branch is forbidden.
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Open, outside the sprint
- **[BL-27] needs one lookup**: `var.github_organization` in `global-bootstrap` has **no default**.
- **At Task 7, decide deliberately whether to REVOKE `administration=write`** (it can delete *any*
  repo in the org, loop-engine included).
- **[BL-2] (Slack bot control plane) gets its planning pass immediately after sprint 36.**

## Pointers
- [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — **the plan. FD1–FD11 locked.** Tasks 1–3 done; Tasks 4–7 untouched.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — **§5/§7/§8 are this sprint's protocols** and the register of record. Task 7 retires them (**without renumbering**).
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, BL-15, BL-16, BL-18, BL-20, BL-22..BL-27. **BL-21: code fix landed (PR #73); Task 7 closes it once the live run proves it.** Resolved: BL-13, BL-17. Declined: BL-19.
- Ruleset on loop-engine's own `main` healthy 2026-07-14: 4 rule types, 8 required checks, targeting exactly `refs/heads/main`.
