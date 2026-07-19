# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the PR) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 42 — package rename `loop-engine` → `loop-orchestrator` — code done, on PR #143,
awaiting the fresh-session Architect Review.** `sprint_status: awaiting_architect_review`,
assigned **Opus/architect**. Branch `sprint/42-rename-loop-orchestrator`, **head now `b40b559`**
(the lint fix — see below; supersedes `bd52975`).

> **A genuinely fresh session must post the review.** The 2026-07-19 review session authored
> `bd52975` AND ran `/code-review` AND dispatched the coder that authored `b40b559`, so it is a
> diff-author and cannot make the "*did not author the diff*" attestation. New window → `/model
> opus` → `/resume` → `/code-review #143` → post against `b40b559`. **Confirm CI green first**
> (`/pr-checks`) — the CI re-run had not been scheduled by GitHub at handoff (queue lag).

## Just done (Opus/architect session, 2026-07-18/19)
- **Resumed onto drift:** the cursor said "between sprints, await backlog pick," but reality
  was a `sprint/42` rename branch one commit ahead of main with **open PR
  [#143](https://github.com/glunk-works/loop-orchestrator/pull/143)** the cursor never knew about.
- **Ran `/code-review` (high effort) on #143.** Verdict: clean mechanical rename — full suite
  **787 passed**; the two behavioral seams are correct (the `env_compat` `LOOP_ENGINE_*` →
  `LOOP_ORCHESTRATOR_*` fallback wired into *every* consumer; the keyring `loop-engine` →
  `loop-orchestrator` service-name fallback in `_resolve_api_key`); pyproject, the
  `loop_orchestrator.mcp.json` config + module paths, README, and the SBOM self-component all
  updated. **No correctness bugs** — only stale-reference findings.
- **Fixed 2 of those findings** (commit `bd52975`, signed valid, pushed to the sprint/42 branch):
  the stale `.claude/` runbooks — `live-verify.md`'s `hatch run loop-engine run` (a **dead
  console script** post-rename) → `loop-orchestrator`, and `ship/SKILL.md`'s `loop-engine/*`
  machine-label namespace → `loop-orchestrator/*` (the emitter now writes
  `loop-orchestrator/needs-human`). All 9 `.claude/` files clean.
- **Did NOT post the Architect Review** — deliberately. This session authored `bd52975` (now
  part of the PR diff) *and* ran the review, so posting the "*this session did not author the
  diff*" attestation would be a **knowing false statement** (`workflow.md`). The gate must come
  from a genuinely fresh session.

## Then — fresh review session (2026-07-19) caught a RED PR, fixed it, did not post
- **Cold `/code-review #143` re-derivation** confirmed the rename clean (see findings) **but**
  surfaced a **blocking CI-lint failure** the prior session missed: 2× E501 in
  `test_slack_io_inbound.py` (the rename pushed two lines 100→106 chars). CI `lint` was **red**,
  cascading every other job to `skipped`. Verified against the live CI log + byte counts — not a
  local-only artifact.
- **Dispatched the `coder` subagent** (user's call) to fix it: `hatch run format` wrapped the two
  lines (minimal 2-line diff), **full** local gate green (lint + format-check + 787 tests), signed
  commit `b40b559` pushed to `sprint/42-rename-loop-orchestrator`. PR head is now `b40b559`.
- **Still did NOT post the review** — this session is now itself a diff-author (it dispatched the
  fix), so the fresh-session attestation still has to come from a *new* session, now targeting
  `b40b559`. GitHub had not scheduled the CI re-run at handoff (queue lag) — confirm green first.

## Review findings (2026-07-19 cold re-derivation — re-derive again, don't just copy)
0. **BLOCKING → FIXED in `b40b559`** — the rename lengthened two string literals
   (`"loop-engine"` → `"loop-orchestrator"`, +6 chars) in `tests/tools/test_slack_io_inbound.py`
   lines 212/218 from exactly 100 → **106 chars**, tripping **ruff E501**. `hatch run lint` went
   red on CI, cascading `test`/`format-check`/`sbom`/`secrets-scan`/`dependency-audit` into
   **skipping** (`needs: lint` failed) — the PR was **not mergeable**. The prior "787 passed" was
   a local *test* run that skipped `hatch run lint` (the recurring "run the FULL gate" miss).
   Fixed via `hatch run format` (auto-wrapped the two calls), full local gate re-run green
   (lint + format-check + **787** tests). *This is why the review must target `b40b559`, not `bd52975`.*
1. **FIXED in `bd52975`** — `.claude/agents/live-verify.md` executable command + `ship/SKILL.md`
   label namespace.
2. **Confirmed NON-issue** — `containers/keyring_backend/cryptfile_backend.py`'s **hard cut** to
   `LOOP_ORCHESTRATOR_KEYRING_FILE` / `..._PASSPHRASE_FILE` (no env_compat fallback — the
   standalone backend can't import the shim) is safe: its **only** setter, `.devcontainer/
   devcontainer.json:30-31`, was renamed to the new names in the **same PR**, and code + env
   travel together in the image build. No legacy value can strand. (Cold re-check upgraded this
   from the prior "low confidence" to a non-issue.)
3. *(minor, not fixed)* — `sbom.json` regenerated in an env missing `mutmut`, dropping 5 real
   transitive components (`glob2`, `junit-xml`, `parso`, `pony`, `toml`). Non-blocking: the
   `sbom` CI job regenerates + uploads, never `git diff`s; direction is arguably more-correct.
4. **Explicitly NOT findings** — the ~40 `loop-engine` refs in `sprints/*/sprint_plan.md`,
   `docs/project_spec.json`, `requirements.md` are legitimately **historical**; and the Infisical
   `--path=/loop-engine` + secret name `LOOP_ENGINE_KEYRING_PASSPHRASE` are external-store
   identifiers deliberately preserved (with comments added in the PR). Every project-side env
   reader routes through `getenv_compat` (verified by grep); `mcp/config.py`'s `_CONFIG_FILENAME`
   tracks the renamed `loop_orchestrator.mcp.json`; no stale operational refs remain in
   `.github/` / containers / devcontainer.

## Next — post the fresh-session Architect Review on #143 (Opus, NEW session)
`new window → /model opus → /resume → /code-review #143 → post`. Body must OPEN with the
verbatim two-line header + attestation (paste, do not reword — literal `contains()` match).
`gh pr review --comment` only, never `--approve`. After posting, watch the **BL-35 stale-red**
(two `architect-review` runs on one SHA; `BLOCKED` + rollup FAILURE ⇒ `gh run rerun <old id>`).
The human's **merge** of #143 is the approval — Claude never merges.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **The rename left `.agent/` runtime state, historical sprint plans, and external-store IDs
  (Infisical path / secret names) intentionally on the old name** — do not "finish" those.
- **Before pushing code, run the FULL local gate** (lint → format → test), not just tests —
  or use `/ship`. **PR title ≤72 bytes** — `wc -c` first.
- **Never commit to `main`, never merge, never force-push.**
- **GPG:** never run `.devcontainer/gpg-forward.sh` in a Cursor session. Signing Timeout =
  answer the host pinentry and retry (hit once this session; retry succeeded).

## Pointers
- [PR #143](https://github.com/glunk-works/loop-orchestrator/pull/143) — the rename, head `bd52975`, awaiting the Architect Review.
- [`docs/backlog.md`](../docs/backlog.md) — open items for the post-#143 owner pick (BL-1/3/4/5, BL-24/35, BL-32/33/36/37).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — migration long done; this rename is post-migration hygiene.
