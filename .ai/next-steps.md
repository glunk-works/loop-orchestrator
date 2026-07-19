# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Between sprints — Sprint 42 (`loop-engine` → `loop-orchestrator` package rename) is
MERGED.** `sprint_status: done`. PR [#143](https://github.com/glunk-works/loop-orchestrator/pull/143)
merged as `be92d6c`; local `main` fast-forwarded; the `sprint/42` branch is pruned.
Awaiting the owner's next backlog pick. Next session: **Opus/architect** for planning.

## Just done (Opus/architect review session, 2026-07-19)
- **Posted the fresh-session Architect Review on #143** against head `54b55d6` (this session
  authored none of the diff — the attestation is truthful). Cold `/code-review` re-derivation:
  clean mechanical rename, **no correctness bugs**. Independently verified: `src/loop_engine/`
  gone; **zero** raw `os.environ` reads in `src/` (every env consumer routes through the new
  `getenv_compat` `LOOP_ENGINE_*`→`LOOP_ORCHESTRATOR_*` fallback); keyring `loop-engine`→
  `loop-orchestrator` service fallback safe; pyproject/mcp-config/sbom self-name all consistent.
- **Handled the BL-35 stale-red**: after posting, the superseded `pull_request` architect-review
  run stayed red on the same SHA (rollup FAILURE, not lag). Re-ran the old failed run
  (`gh run rerun 29691229015`, **not** a push) → both runs green, `mergeStateStatus: CLEAN`.
- **All 8 required checks green**; the owner **merged** #143 (the approval). One non-blocking
  note recorded: `sbom.json` regenerated without `mutmut`, dropping 5 dev-only transitive
  components — the `sbom` CI job regenerates+uploads and never `git diff`s, so it can't fail.

## Next — the owner picks the next backlog item, then Opus plans it (NEW session)
This is a **human-decision point** — `/resume` states the pick-up and **waits** (`sprint_status`
is `done`, not `implementing`). Open candidates the owner flagged: **BL-1** (in-loop Architect/QA
code-review stage), **BL-3** (prompt-caching correctness review — read the `claude-api` skill
first), **BL-4** (Ralph loop watcher — progress/liveness vs. blunt iteration cap), **BL-5**
(per-persona model routing Architect→Opus; needs `claude-opus-4-8` in pricing RATES first +
resolution `max_tokens` 2048 review). Also open: BL-24 (webhook live smoke), BL-32/33/36/37.
No open HITL Gate; the next gate is the planning Gate on whatever is picked.

## Gotchas worth remembering
- **`.ai/state.json` is git-ignored** — **this file is what travels.**
- **The rename left the `LOOP_ENGINE_*` env + `loop-engine` keyring fallbacks in place on
  purpose** — a one-release back-compat bridge for live deployments still on the old names. A
  *future* sprint drops them once every deployment sets the new names; that's the owner's call.
- **The rename also intentionally left `.agent/` runtime state, historical sprint plans, and
  external-store IDs (Infisical path / secret names) on the old name** — do not "finish" those.
- **Before pushing code, run the FULL local gate** (lint → format → test), not just tests — or
  use `/ship`. **PR title ≤72 bytes** — `wc -c` first.
- **Never commit to `main`, never merge, never force-push.**
- **GPG:** never run `.devcontainer/gpg-forward.sh` in a Cursor session. Signing Timeout =
  answer the host pinentry and retry.

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — the open-item register for the owner's next pick.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — migration long done; the rename was post-migration hygiene, now landed.
- [PR #143](https://github.com/glunk-works/loop-orchestrator/pull/143) — the merged rename (`be92d6c`).
