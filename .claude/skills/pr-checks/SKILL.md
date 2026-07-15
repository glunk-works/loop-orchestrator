---
name: pr-checks
description: Report the status of a PR's required checks and give an explicit merge-ready verdict WITHOUT merging. Run when asked whether a PR is green / ready to merge, or to poll a PR whose checks are still running. Reports ALL required checks (never a subset), decodes the skipped/BLOCKED/conflict traps, and never merges — the human's merge is the approval.
---

# /pr-checks — report required-check status and merge-readiness (never merge)

Goal: answer "is PR #N ready to merge?" with a trustworthy, complete verdict — every
required check named and classified — and stop there. **Never** merge, `--approve`, or
force-push. The human's merge is the approval (see `pr-gated-commits`,
`user_merge_timing_caution`). This is a read-only status skill.

Argument: a PR number (e.g. `/pr-checks 94`). If none is given, resolve it from the
current branch with `gh pr view --json number`.

## The 8 required checks

The `protected-integration-branches` ruleset requires exactly these on `main` + `feat/**`:

`lint` · `format-check` · `test` · `secrets-scan` · `dependency-audit` · `sbom` · `pr-title` · `architect-review`

Report **all eight** by name, every time — a partial "looks green" is exactly the trap
that has caused early merges before. If a required check is *absent* from the results,
that is a finding, not a pass (a required check that never got created still blocks merge).

## Steps

1. **Pull status in one shot.** Run:
   ```bash
   gh pr checks <N>                       # per-check state (pass/fail/pending/skipping)
   gh pr view <N> --json number,title,mergeable,mergeStateStatus,isDraft,headRefName,baseRefName,url
   ```
   `gh pr checks` exits non-zero when any check is failing/pending — that is expected, not
   an error; read its output regardless.

2. **Classify each of the 8.** For every required check, report `green` / `red` /
   `pending` / `missing`. Then decode the ambiguous states — this is where the value is:

   - **`skipped` ≠ `failure`, but also ≠ a free pass.** A job can report `skipped` two ways:
     (a) a *deliberate condition* — on a **docs-only** PR the `test` job's pytest step
     short-circuits, and `architect-review` is **exempt** (docs-only PRs touch no `src/`).
     Those skips are legitimately green-equivalent. (b) a `needs:` dependency **failed** —
     the downstream job then reports `skipped` too. That is a *red*, masquerading. Confirm
     which by checking whether any upstream job actually failed before you call a skip benign.
   - **`mergeStateStatus: BLOCKED` with nothing red or pending** = GitHub re-evaluation
     lag, **not** a problem. Say so and wait — do **not** intervene, re-run, or push.
     (`github-workflow-traps`: BLOCKED-with-nothing-failing is just lag.)
   - **`mergeable: CONFLICTING`** = the PR is out of date / has conflicts and may be
     running **zero** CI silently. A "green" here proves nothing. Flag it and note the
     branch needs a rebase (merge `main` *into* the branch — never force-push; see
     `pr-gated-commits`).
   - **`isDraft: true`** — checks may be intentionally incomplete; surface it.

3. **State a single explicit verdict.** One of:
   - **READY** — all 8 required checks are green (or legitimately docs-only-skipped) **and**
     `mergeable` is not `CONFLICTING`. Tell the user "PR #N is ready to merge — merge it
     yourself; I will not." List the 8 with their states so the readiness is auditable.
   - **NOT READY (red)** — name every failing check and, for each, the one-line reason
     from its job log (`gh run view <run-id> --job <job-id> --log` grep'd to the failure).
   - **PENDING** — name which checks are still running. If invoked from a `/loop` or a
     scheduled run, reschedule another poll; otherwise tell the user it's still running
     and offer to re-check.

4. **Never act on the PR.** No `gh pr merge`, no `gh pr review --approve`, no
   `git push --force`. If the user asks you to merge, confirm the verdict is READY and
   hand it back — the merge click is theirs.

## Report shape

```
PR #94 — "test(core): land all 86 core/ mutation-audit fix verdicts" (sprint/38-t3 → main)

  lint             ✅ pass        secrets-scan       ✅ pass
  format-check     ✅ pass        dependency-audit   ✅ pass
  test             ✅ pass        sbom               ✅ pass
  pr-title         ✅ pass        architect-review   ✅ pass (docs/test-only, exempt)

  mergeable: MERGEABLE   state: CLEAN

Verdict: READY — all 8 required checks green. Merge it yourself when you're ready; I won't.
```
