# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — F18–F22 are closed at head `96cc88e`, pushed.**
Next session is **Opus/Architect**: fresh `/code-review` at the new head, then post.

> ⚠️ **The stale green `architect-review` from `18042c6` does not carry over.** This
> commit moves the head, so the check is red again and a genuinely fresh review is
> required before anyone merges.

## Just done (Sonnet/Coder session, 2026-07-13)
Closed five findings from the Opus review of PR #57 at head `18042c6` (verdict REVISE),
committed as `96cc88e`, pushed to `sprint/35-tasks-1-2`:

1. **F18** — [`tools/scaffold/writer.py:77`](../src/loop_engine/tools/scaffold/writer.py)
   `_write_rendered` now pins `newline="\n"` on its `write_text` call — the fifth call
   site the original F1 sweep missed.
2. **F19** — [`test_encoding_boundary.py`](../tests/tools/test_encoding_boundary.py) gained
   `test_write_owning_modules_pin_newline_on_write_text`, a structural AST guard scoped to
   the two write-owning modules (`state_io`, `scaffold`) requiring `newline="\n"` on every
   `write_text` call — the root-cause fix, so a sixth call site can't slip through by hand.
3. **F20/F21** — the same guard's `open()` check (renamed `_is_unencoded_text_open`) now
   flags any non-binary `open()` call missing `encoding=`, including plain reads, `"r+"`,
   and unresolvable/non-literal modes. The old read-vs-write split and the silent
   treat-as-read gap for `r+`/dynamic modes are gone.
4. **F22** — [`state_io/writer.py`](../src/loop_engine/tools/state_io/writer.py)'s
   `append_agent_memory` now reads the existing ledger via
   `target_path.open(encoding="utf-8", newline="")` — **not** `read_text(newline=...)`,
   which doesn't exist as a kwarg on `Path.read_text()` (only `write_text` gained `newline=`
   in 3.10). A first-draft fix used the nonexistent kwarg; the full suite caught it (4
   `test_ralph_coder.py` + 2 `test_agent_state.py` failures, all a `TypeError`) before commit.

**F23 (optional) deliberately skipped** — the shared `ctype_locale` fixture doesn't
naturally fall out of this round (no new copy-pasted `setlocale` block was added). Still
open, notes-only.

Green gate: lint clean, format clean, full suite **553 passed**.

## Next — Opus/Architect
1. Fresh session `/code-review` of PR #57 at head `96cc88e`. Verify F18–F22 actually close
   what the prior review named — the diff is small (3 files) and self-contained.
2. Post with `gh pr review --comment` (never `--approve`).
3. **If ACCEPT:** proceed to **Task 3** (pre-merge preflight) → **Task 4** (open the
   migration PR). **Task 5** (merge + settings) is **HUMAN-ONLY**. **PR #55 approved the
   plan, not Tasks 3–5's execution — that gate is still open.**
4. If another REVISE: hand back to Sonnet/Coder per the usual ladder.

## Notes only — do NOT fix without a fresh planning pass (→ backlog)
- **F2.** `artifact_store`'s byte compare hard-codes `state_io`'s serialization contract —
  now load-bearing for both F18 and F19.
- **F4.** ~20 unencoded `read_text()` calls under `tests/` (incl. `test_ci_config.py:154`
  reading `CLAUDE.md`, and the AST boundary tests parsing `src/*.py`). The `src/`-scoped
  guard will never flag them.
- **F14 / F17** — carried, unchanged.
- **F23** — shared `ctype_locale` fixture; still open, still optional.
- **Carried:** `architect-review` cannot distinguish "was reviewed" from "was approved" (a
  REVISE turns it green) — harmless while a human merges, load-bearing the moment anything
  automated keys off that check.

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Ordinary sprint
  PRs (including #57) are **SQUASH** — the merge-commit button exists only for the migration PR.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major** action
  bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends on being
  identical. They get real review in Task 6, *after* the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the
  PAT's repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) —
  the approved plan. FD1–FD7 locked.
- PR #57 — Tasks 1–2, fourth fix round (F18–F22 closed, F23 skipped). Full diff at `96cc88e`.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never
  run. **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 through `96cc88e`, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to fix/review/merge.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
