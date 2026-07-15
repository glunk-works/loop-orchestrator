# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`sprints/36_live_factory_verification/sprint_plan.md`, `docs/backlog.md`) — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — Track A DONE; Track B (Tasks 4–7) is all that
remains.** Both hardening PRs are **merged into `main`**: #76 → squash `e551a43`, and #77 →
squash `08e9d2c` (2026-07-15). FD1–FD11 are locked; do not re-open them. **No HITL gate is
open.** The next move is a **deliberate, human-gated GO decision on Track B** (real irreversible
GitHub side effects + real LLM spend) — it does not auto-start.

## Just done (this session — Opus/Architect)
- **Posted the fresh-session HITL review on #77** (`/resume` → `/code-review` → post against head
  `bc7ebaf`). Verdict: **accept, no blockers.** Verified finding 1 (stderr rides through to
  `BootstrapResult.ruleset_error` via `flow.py:232`) and finding 2 (`SubprocessError`'s only two
  subclasses are `CalledProcessError`/`TimeoutExpired`, so narrowing lets the timeout propagate with
  nothing else swallowed). Flagged the raw-`TimeoutExpired`-out-of-`run_bootstrap` as an accepted
  posture, not a defect; one optional nit (double `.strip()`). Body carried both gate strings
  verbatim → `architect-review` went green on the **first** post (no paraphrase re-run this time).
- **The human merged #77** (`08e9d2c`). Its branch `sprint/36-ruleset-error-detail` is now **DEAD**
  (squash trap — never push to it again). Track A (S4–S9 + round-4 findings 1–2) is fully complete.

## Next — Track B, Tasks 4–7 (**Opus/Architect, FRESH SESSION; real side effects + $ spend**)
The sprint's real payload, and the only work left. **The human has chosen a handoff → fresh
session for it, but Track B still needs an explicit GO before any destructive/paid call runs** —
`/resume` should state the plan and wait, not auto-launch it. **First** get onto an up-to-date
`main` (this handoff's branch `sprint/36-ruleset-error-detail` is DEAD — checkout `main`, pull
`08e9d2c`, cut a fresh `sprint/NN-slug` if Task 7 produces a code/docs diff). **Then re-read
FD1–FD11**, especially **FD11** (explicit `owner/repo` on every destructive call; NEVER point a
flow at `loop-engine`) and **FD9**. The work:
- Run `flows/bootstrap` + `flows/maintenance` against a **real scratch repo** in `glunk-works`.
- **Prove the ruleset REJECTS a push** — FD9, *observed* not inferred; this exercises the code #76/#77 hardened.
- Teardown the scratch repo (FD11).
- Decide **deliberately** whether to revoke `administration=write` (Task 7 — closes BL-21).
**Real, irreversible GitHub side effects and real LLM spend** (~$5.00 budget at Task 6).

## Gotchas worth remembering
- **The `architect-review` gate matches the review body by EXACT substring** on both the header and
  the attestation line. Paraphrase = red. Copy both from `.github/workflows/hitl-review.yml`; a
  corrected re-post flips it green (latest run per name wins).
- **⚠️ The PAT carries `administration=write` on the org — it can DELETE ANY REPO, `loop-engine`
  included.** Hard-code the scratch repo name and read it back before every destructive call (FD11).
- **A `CONFLICTING` PR runs ZERO CI** — an empty check rollup is "nothing ran", not "all green".
- **A check rollup shows BOTH the stale `FAILURE` and the fresh `SUCCESS` for one check name.** The
  latest run is what counts.
- **`gh pr view` serves a stale `mergeStateStatus`.** `BLOCKED`/`UNKNOWN` with *nothing failing* is
  GitHub lag — **the checks are the truth.** Do not close+reopen to "fix" it.
- **PR title regex has no room for commas in the scope** — `[a-z0-9._/-]+` only. Pick **one** scope.
- **A squash-merged branch is dead** — `sprint/36-s4-s9-hardening` (#76) is now history; never push to it.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** It breaks signing; the key
  *appears* to vanish (`No secret key`). Recovery: reload the window. A `Timeout` means answer the
  host pinentry prompt and retry.
- **Rebase a stale branch by merging `main` INTO it** — force-pushing a pushed branch is forbidden.
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Open, outside the sprint
- **[BL-27] needs one lookup**: `var.github_organization` in `global-bootstrap` has **no default**.
- **At Task 7, decide deliberately whether to REVOKE `administration=write`** (it can delete *any*
  repo in the org, loop-engine included).
- **[BL-2] (Slack bot control plane) gets its planning pass immediately after sprint 36.**

## Pointers
- [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — **the plan. FD1–FD11 locked.** Tasks 1–3 done; Track A merged (#76 + #77); Tasks 4–7 untouched (Track B).
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — **§5/§7/§8 are this sprint's protocols** and the register of record. Task 7 retires them (**without renumbering**).
- [`docs/backlog.md`](../docs/backlog.md) — open: BL-1..BL-5, BL-15, BL-16, BL-18, BL-20, BL-22..BL-27. **BL-21: code fix landed (#73), hardened by #76 + #77; Task 7 closes it once the live run proves it.** Resolved: BL-13, BL-17. Declined: BL-19.
- Ruleset on loop-engine's own `main` healthy 2026-07-15: 4 rule types, 8 required checks.
