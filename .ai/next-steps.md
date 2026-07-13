# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — F24–F27 closed at head `9de08e6`, pushed.**
Next session is **Opus/Architect**: fresh `/code-review` at the new head, then post.

> ⚠️ **The stale green `architect-review` from `4f05ed3` does not carry over.** This
> commit moves the head, so the check is red again and a genuinely fresh review is
> required before anyone merges.

## Just done (Sonnet/Coder session, 2026-07-13)
Closed four findings from the Opus follow-up review of PR #57 at head `4f05ed3`
(verdict REVISE), committed as `9de08e6`, pushed to `sprint/35-tasks-1-2`:

1. **F24** — [`agent_state/store.py`](../src/loop_engine/tools/agent_state/store.py)'s
   `append_memory` now reads the ledger byte-exact (`.open(encoding="utf-8",
   newline="")`), matching `state_io/writer.py`'s own F22 prefix check instead of
   silently CRLF→LF-translating a different view of the same file.
2. **F25** — [`test_encoding_boundary.py`](../tests/tools/test_encoding_boundary.py)'s
   `_unencoded_calls` now matches method-form `.open(...)` (`ast.Attribute`), not just
   the bare-name builtin form — it was blind to its own PR's new call site. `_open_mode`
   is now told which form it's looking at, since method `.open()`'s mode sits at
   positional index 0, not builtin `open()`'s index 1.
3. **F26** — the newline-pin guard now also covers write-mode `open()` calls, not just
   `.write_text()`.
4. **F27** — documented (in `test_state_io.py`) that the two byte-exact regression tests
   can't actually exercise the newline= hazard they name on ubuntu-latest CI (verified:
   monkeypatching `os.linesep` doesn't change `TextIOWrapper`'s translation); the AST
   guard is the real, platform-independent backstop.

**F28 (optional) deliberately skipped** — verified it isn't a new failure mode:
`write_artifact`'s own `write_text()` already raises identically on an unpaired
surrogate, so `publish_artifacts`'s comparison doesn't introduce a new crash surface.

Green gate: lint clean, format clean, full suite **553 passed**.

## Next — Opus/Architect
1. Fresh session `/code-review` of PR #57 at head `9de08e6`. Verify F24–F27 actually
   close what the prior review named.
2. Post with `gh pr review --comment` (never `--approve`).
3. **If ACCEPT:** proceed to **Task 3** (pre-merge preflight) → **Task 4** (open the
   migration PR). **Task 5** (merge + settings) is **HUMAN-ONLY**. **PR #55 approved the
   plan, not Tasks 3–5's execution — that gate is still open.**
4. If another REVISE: hand back to Sonnet/Coder per the usual ladder.

## Notes only — do NOT fix without a fresh planning pass (→ backlog)
- **F2, F4, F14, F17, F23** — unchanged, still correctly deferred per the prior review.
- **F28** — optional, verified moot (see above); no backlog entry needed.
- **Carried:** `architect-review` cannot distinguish "was reviewed" from "was approved"
  (a REVISE turns it green) — filed, still open, harmless while a human merges.

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Ordinary
  sprint PRs (including #57) are **SQUASH** — the merge-commit button exists only for
  the migration PR.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major**
  action bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends
  on being identical. Real review in Task 6, after the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim
  the PAT's repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) —
  the approved plan. FD1–FD7 locked.
- PR #57 — Tasks 1–2, sixth fix round closed (F24–F27). Full diff at `9de08e6`.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since
  sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks
  never run. **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 through `9de08e6`, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to fix/review/merge.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
