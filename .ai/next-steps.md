# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — the Opus review at head `18042c6` came back
REVISE.** Next session is **Sonnet/Coder**: close F18–F23, then hand back for re-review.

> ⚠️ **A green `architect-review` on `18042c6` is NOT an ACCEPT.** Posting the review
> turned the check green even though the verdict is REVISE — it matches on
> header + attestation + head SHA and never reads the verdict (by design; the human's
> merge is the approval). The F18/F19 fix commit moves the head, so the check goes red
> again on its own and a genuinely fresh review is required. Do not merge on that green.

## Just done (Opus/Architect review session, 2026-07-13)
Fresh-session `/code-review` of PR #57 at head `18042c6` (code diff unchanged since
`8f2afb5`), posted to GitHub with `gh pr review --comment`. **Verdict: REVISE.**

The F1/F3/F5/F6 round landed correctly — but **the F1 sweep missed a fifth call site,
and this PR's own new test is what proves it.**

## Next — Sonnet/Coder

1. **F18 (required).** [`tools/scaffold/writer.py:77`](../src/loop_engine/tools/scaffold/writer.py)
   — `_write_rendered` still calls `write_text(content, encoding="utf-8")` with no
   `newline="\n"`. `scaffold` is the **second** file-write-owning module, so F1's rationale
   applies verbatim. The new [`scaffold/test_writer.py:105`](../tests/tools/scaffold/test_writer.py)
   asserts `read_bytes() == bundled_bytes`, which **fails on any host where
   `os.linesep != "\n"`** — Linux-only CI hides it. **One line.**
2. **F19 (strongly recommended).** Extend
   [`test_encoding_boundary.py`](../tests/tools/test_encoding_boundary.py) to also require
   `newline="\n"` on `write_text` inside the write-owning modules. This is the *root cause*:
   F12 was closed structurally, F1 by hand at four sites, so the fifth sailed through. Run it
   against the branch as-is and it fails on `scaffold/writer.py:77` — that is F18's test.
3. **F20.** Same guard exempts unencoded text-mode `open()` **reads** while flagging
   unencoded `read_text()`. Same locale hazard, opposite outcome — scope reads consistently.
4. **F21.** `_open_mode` misses `"r+"` (write-capable, no `w`/`a`/`x` char) and any
   non-literal mode, silently treating them as reads.
5. **F22.** [`state_io/writer.py:150`](../src/loop_engine/tools/state_io/writer.py) —
   `append_agent_memory` reads with newline translation while its write is byte-exact, so the
   append-only prefix check cannot see the whole-file CRLF→LF rewrite it authorizes. Pin
   `newline=""` on the read.
6. **F23 (optional).** The `skipif`+`parametrize`+`setlocale` block is copy-pasted across
   `test_artifact_store.py` and `scaffold/test_writer.py` → a shared `ctype_locale` fixture
   in a `tests/conftest.py` (none exists yet). Do it last, if it falls out of F19 naturally.

Then: green gate (`lint`, `format`, `test`), push to `sprint/35-tasks-1-2`, `/handoff` →
**fresh Opus session** → re-review at the new head. After that ACCEPT: **Task 3** (pre-merge
preflight) → **Task 4** (open the migration PR) → **Task 5** (merge + settings, **HUMAN-ONLY**)
→ **Task 6**. **PR #55 approved the plan, not Tasks 3–5's execution — that gate is still open.**

## Notes only — do NOT fix in this round (→ backlog)
- **F2.** `artifact_store`'s byte compare hard-codes `state_io`'s serialization contract across
  the enforced single-writer boundary — **now load-bearing for F18**. Deeper fix: a compare
  helper in `state_io`.
- **F4.** ~20 unencoded `read_text()` calls under `tests/` (incl. `test_ci_config.py:154`
  reading `CLAUDE.md`, and the AST boundary tests parsing `src/*.py` — both contain em-dashes).
  The `src/`-scoped guard will never flag them.
- **F14 / F17** — carried, unchanged.
- **New:** `architect-review` cannot distinguish "was reviewed" from "was approved". Harmless
  while a human merges; load-bearing the moment anything automated keys off that check.

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
- PR #57 — Tasks 1–2, third fix round (F18–F23). Full review text is on the PR at `18042c6`.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never
  run. **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 through `18042c6`, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to fix/review/merge.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
