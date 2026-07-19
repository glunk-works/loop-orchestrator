# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the PR) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint 42 — package rename `loop-engine` → `loop-orchestrator` — code done, on PR #143,
awaiting the fresh-session Architect Review.** `sprint_status: awaiting_architect_review`,
assigned **Opus/architect**. Branch `sprint/42-rename-loop-orchestrator`, head `bd52975`.

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

## Review findings (for the fresh reviewer — re-derive, don't just copy)
1. **FIXED in bd52975** — `.claude/agents/live-verify.md` executable command + `ship/SKILL.md`
   label namespace (above).
2. *(low confidence, not fixed)* — `containers/keyring_backend/cryptfile_backend.py` reads
   `LOOP_ORCHESTRATOR_KEYRING_FILE` / `..._PASSPHRASE_FILE` with a **hard cut** (no env_compat
   fallback — the standalone backend can't import the shim). Only risk: a live container that
   overrides these via the legacy `LOOP_ENGINE_*` names → falls through to the `/run/secrets/…`
   default. No tracked config sets the legacy name (dev sets the new one; prod uses defaults).
3. *(minor, not fixed)* — `sbom.json` regenerated in an env missing `mutmut`, dropping 5 real
   transitive components (`glob2`, `junit-xml`, `parso`, `pony`, `toml`). Non-blocking: the
   `sbom` CI job regenerates + uploads, never `git diff`s; direction is arguably more-correct.
4. **Explicitly NOT findings** — the ~40 `loop-engine` refs in `sprints/*/sprint_plan.md`,
   `docs/project_spec.json`, `requirements.md` are legitimately **historical**; and the Infisical
   `--path=/loop-engine` + secret name `LOOP_ENGINE_KEYRING_PASSPHRASE` are external-store
   identifiers deliberately preserved (with comments added in the PR).

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
