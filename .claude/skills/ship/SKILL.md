---
name: ship
description: Close out a finished task — commit the working tree with a conventions-correct message, push to a branch cut from main (never main itself), and open a PR based on main with a length-checked title. Stops at the open PR — never merges, never --approve, never force-pushes. Run when work is done and you want it on a PR.
---

# /ship — commit, push, and open the PR (then stop)

Goal: turn a finished working tree into an open PR against `main`, with every repo
convention applied by construction — so the recurring slips (over-length PR title,
committing on `main`, a wrong scope) can't happen. This skill **opens** the PR and
**stops**. It never merges, `--approve`s, or force-pushes — the human's merge is the
approval (`pr-gated-commits`).

## Steps

1. **Preflight the branch.** Run `git rev-parse --abbrev-ref HEAD`.
   - **On `main`?** Cut a branch first — a plain commit/push to `main` is rejected by the
     `protected-integration-branches` ruleset (GH013). Name it for the work:
     `sprint/NN-slug` for sprint tasks, else a typed prefix matching the change
     (`docs/…`, `chore/…`, `fix/…`, `ci/…`). The branch is cut **from `main`**.
   - **Already on a work branch?** Confirm it was cut from `main` and just add to it.
   - Never rebase/force-push a pushed branch. To refresh a stale branch, merge `main`
     **into** it (a `docs/backlog.md` conflict is *two additions* — keep **both** sides).

2. **Review the diff, then compose the commit.** `git status --short` + `git diff --staged`
   (stage with `git add` as needed). Write a Conventional Commit:
   - `type(scope): imperative subject` — lower-case, no trailing period, **≤72 chars**.
   - `type` ∈ `feat|fix|docs|test|refactor|perf|chore|ci|revert` (no `style`).
   - **`scope` reuses an enforced module boundary** (`core`, `personas/ralph`, `tools/mcp`,
     `flows`, `trigger`, …) so commit vocab == architecture vocab.
   - `!` after the scope **only** for a `State` shape break — which also requires a
     `schema_version` bump + `migrate_state_payload` extension **in the same commit**.
   - Trailers where they apply: `Sprint: NN`, `Finding: F-*`, `Closes: #N`, and always
     end with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
   - Commits are GPG-signed via the forwarded agent. A signing *timeout* just means the
     host pinentry is waiting — answer it and re-run the commit (see
     `gpg-signing-forwarded-agent`; never run `gpg-forward.sh` inside Cursor).

3. **Push the branch** (`git push -u origin <branch>`). Push freely to the work branch,
   **never to `main`**. Once asked to push in a session, keep pushing later commits
   without re-confirming (`feedback_always_push`) — but always to the branch.

4. **Length-check the PR title BEFORE creating the PR.** This is the recurring mistake —
   never eyeball it (`feedback_pr_title_length_check`):
   ```bash
   TITLE="type(scope): imperative subject"
   printf '%s' "$TITLE" | wc -c        # must be ≤ 72
   ```
   The squash merge makes the **PR title** the commit subject, so the title — not the
   commit — is what the `pr-title` CI job enforces. If >72, shorten and re-check.

5. **Open the PR against `main`.** `gh pr create --base main --title "$TITLE" --body "…"`.
   Body: a `## What` / `## Why` summary; note the scope (which boundary changed) and, for a
   docs/test/tooling-only PR, that `architect-review` is exempt. End the body with the
   `🤖 Generated with [Claude Code](https://claude.com/claude-code)` line.

6. **Label on the three axes** if labels are being used: type (`bug`/`feature`/`docs`/
   `chore`), `area/*` (mirrors the scope), `status/*`. Machine-emitted labels stay
   namespaced (`loop-engine/*`).

7. **If the diff touches `src/`, flag the review gate — do not satisfy it here.** The
   `architect-review` check stays red until a **fresh-session** Opus/Architect HITL review
   is posted against the PR's current head. `/ship` does **not** post that review (switching
   model mid-session is not a review session). Tell the user the PR needs the
   `/handoff` → new session → `/resume` → `/code-review` → post sequence.

8. **Stop at the open PR.** Report the PR URL and, if you want, hand off to `/pr-checks <N>`
   to watch the required checks. **No `gh pr merge`, no `gh pr review --approve`, no
   `git push --force`** — the merge is the human's.

## Guardrail summary

Branch from `main` · push to the branch never `main` · title ≤72 (measured, not eyeballed)
· base `main` · signed commit with the Co-Authored-By trailer · **never merge / approve /
force-push**.
