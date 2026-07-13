# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — F1/F3/F5/F6 landed at head `8f2afb5`, awaiting a
fresh Opus/Architect review of that new head.** Next session is **Opus/Architect**.

> **`architect-review` on #57 is red again, correctly this time.** Unlike the previous
> handoff's docs-only head move, `8f2afb5` is a real `src/`+`tests/` diff that has not
> been reviewed yet. Do not treat the prior ACCEPT (posted at `fb3d719`) as covering it.

## Just done (Sonnet/Coder session, 2026-07-13)
Closed all four findings from the fb3d719 review in one round, committed as `8f2afb5`:
- **F1 (required).** [`state_io/writer.py`](../src/loop_engine/tools/state_io/writer.py) —
  added `newline="\n"` to all four `write_text` calls (`write_state_snapshot`,
  `write_artifact`, `write_agent_scratchpad`, `append_agent_memory`) so writes are
  byte-exact UTF-8 on every platform, not just ones where `os.linesep == "\n"`. Added
  regression tests in `test_state_io.py` asserting on-disk bytes equal
  `body.encode("utf-8")` exactly for both `write_artifact` and `write_state_snapshot`.
- **F3.** [`test_encoding_boundary.py`](../tests/tools/test_encoding_boundary.py) — the
  guard now also flags a bare `open(path, "w"/"a"/...)` text-mode call missing
  `encoding=` (binary modes and reads are out of scope), with detector spot-checks.
- **F5.** Same file — added `assert scanned > 0` so a misresolved `SRC_DIR` (empty
  `rglob`) can no longer pass vacuously.
- **F6.** [`test_artifact_store.py`](../tests/tools/test_artifact_store.py) +
  [`scaffold/test_writer.py`](../tests/tools/scaffold/test_writer.py) — added
  `pytest.mark.skipif(sys.flags.utf8_mode)` to the locale-parametrized "C"-locale
  cases, so PEP 686 UTF-8 mode (default in 3.15) makes the coverage loss loud, not
  silent.

Green gate ran clean before push: `lint` (ruff, incl. S/B), `format` (unchanged),
`test` — 551 passed. Pushed to `sprint/35-tasks-1-2`, PR #57 head now `8f2afb5`.

## Next — Opus/Architect, fresh session

1. `/resume` to confirm the cursor, then run `/code-review` against PR #57's **current
   head `8f2afb5`** — a genuinely fresh session, not a mid-session `/model opus` switch.
2. Expect this to confirm the known-ACCEPT diff rather than surface new substantive
   findings: the four changes above are narrowly scoped fixes to exactly what the prior
   review named. F2 and F4 (below) are intentionally **not** addressed in this round.
3. Post the review to GitHub headed `**Opus/Architect HITL review (automated)**` via
   `gh pr review --comment` (never `--approve` — merge is the human's approval).
4. Once `architect-review` flips green at `8f2afb5`: **Task 3** (pre-merge preflight) →
   **Task 4** (open the migration PR) → **Task 5** (merge + settings, **HUMAN-ONLY**) →
   **Task 6** (sequence the follow-on work). **PR #55 approved the plan, not Tasks 3–5's
   execution — that HITL gate is still open.**

## Notes only — do NOT fix as part of this review round (→ backlog)
- **F2.** `artifact_store`'s byte compare hard-codes `state_io`'s serialization contract
  (exact UTF-8, no newline translation, no trailing newline) across the enforced
  single-writer boundary. F1 was the one-line symptom fix (now landed); the deeper fix
  is a compare helper in `state_io`.
- **F4.** ~20 unencoded `read_text()` calls remain under `tests/` — incl.
  `test_ci_config.py:154` reading `CLAUDE.md`, and the AST boundary tests parsing
  `src/*.py`. Both now contain em-dashes, so on a C-locale host the suite dies before it
  can prove anything. The new guard scopes to `src/` and will never flag these.
- **F14 / F17** — carried, unchanged (subprocess `text=True` locale decoding;
  `append_memory` double-read).

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Ordinary
  sprint PRs (including #57) are **SQUASH** — the merge-commit button exists only for the
  one migration PR.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major**
  action bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends on
  being identical. They get real review in Task 6, *after* the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the
  PAT's repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) —
  the approved plan. FD1–FD7 locked.
- PR #57 — Tasks 1–2 implementation complete through the F1/F3/F5/F6 round at `8f2afb5`;
  needs a fresh review at this head (see **Now**/**Next** above).
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 plus all fixes through `8f2afb5`, pushed, PR #57
  open against `feat/mcp-langgraph-migration`. **Live — still the branch to review/merge.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
