# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — Opus reviewed head `aa155d7`: verdict ACCEPT,
F8/F9 confirmed closed.** Two hardening items handed back rather than posted.
**Next session is Sonnet/Coder.**

## Just done (Opus/Architect review session, 2026-07-13)
Fresh-session `/code-review` of PR #57 at head `aa155d7`. **No commits** — review only.

- **F8/F9 verified closed, live** (not just read): grepped `src/` independently — zero
  unpinned `read_text`/`write_text`, zero bare `open(`, zero `read_bytes`/`write_bytes`
  remain. F1's original "single-writer boundary" claim now actually holds.
- **The new tests genuinely bite** — Python is 3.12.13 and no UTF-8 mode is set anywhere
  in the repo, so the `LC_CTYPE=C` parametrization really does force an ASCII default.
  This is no longer the F2 tautology.
- **The docs half checks out** — its one falsifiable claim (that `ci.yml` triggers on
  `push` to `main` *and* `feat/**`) verified against the actual workflow. Correct.
- **Ruleset healthy** — 4 rule types, all 8 required checks present on `main`.
- **Review NOT posted** (third round running). The user chose to fix the two actionable
  findings first; those move the head, so a review posted against `aa155d7` would go
  stale on contact — the same reasoning that withheld the `e7bdd7f` and `e22b359` reviews.

## Next — Sonnet/Coder
**Fresh session.** Fix two findings on `sprint/35-tasks-1-2`. Both are **hardening, not
defects** — the diff as it stands is correct.

- **F12 (the important one, altitude).** Add a structural **AST guard** test: every
  `read_text`/`write_text` call in `src/` must carry an `encoding` kwarg. The fix pinned
  ten call sites across five files but ships tests for only two — revert
  [`cli.py:119`](../src/loop_engine/cli.py#L119) today and the suite stays green. That
  absence is *why* this needed two review rounds. Follow the existing idiom in
  [`tests/tools/test_state_io_boundary.py`](../tests/tools/test_state_io_boundary.py) /
  [`test_subprocess_surfaces.py`](../tests/tools/test_subprocess_surfaces.py) /
  [`test_keyring_boundary.py`](../tests/test_keyring_boundary.py).
- **F13 (correctness).** [`artifact_store.py:37`](../src/loop_engine/tools/artifact_store.py#L37) —
  the skip-check `path.read_text(encoding="utf-8") == body` raises `UnicodeDecodeError` on
  a corrupt on-disk artifact, crashing `publish_artifacts` on a file it was about to
  overwrite anyway. Use `path.read_bytes() == body.encode("utf-8")` — equivalent, cannot
  raise, and already exactly what the new test asserts. Fold in **F16** while there: the
  F1 docstring correction was applied twice (module docstring *and* function docstring
  state the same read-compare nuance); keep one authoritative copy on the function.

Then green gate → push (this moves PR #57's head) → **fresh Opus session** to re-review.
Then Task 3 (pre-merge preflight) → Task 4 (open the migration PR) →
**Task 5 (merge + settings sequence, HUMAN-ONLY)** → Task 6.
**PR #55 approved the plan, not Tasks 3–5's execution — that HITL gate is still open.**

## Notes only — do NOT fix in this PR
- **F14 → backlog.** All six sanctioned subprocess surfaces pass `text=True` with no
  `encoding=`, so they still decode child output with the **locale default** — the same
  bug class, pre-existing. `issue_io/github.py:31` reading a human-authored issue body
  with an em-dash is the realistic failure.
- **F15 (optional, cheap).** Both new regression tests silently become tautologies under
  Python UTF-8 mode (PEP 686 default in 3.15; `requires-python` is `>=3.12`, no upper
  bound). A `pytest.mark.skipif(sys.flags.utf8_mode)` makes the coverage loss loud.
- **F17 → backlog.** `agent_state/store.py:152` `append_memory` double-reads `MEMORY.md`
  (`append_agent_memory` re-reads it to validate the prefix) — wasted I/O + a TOCTOU window.

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
- PR #57 — Tasks 1–2, head `aa155d7`, **reviewed ACCEPT but unposted** (F12/F13 handback).
  Prior heads `e7bdd7f` and `e22b359` were REVISE and also never posted.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 plus the F8/F9 fix, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to push F12/F13 to.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
