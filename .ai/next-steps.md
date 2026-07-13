# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, Tasks 1–2 revised and pushed to PR #57 — awaiting a fresh
Opus re-review.** Head advanced `d2c3797` → `f124f22`; the prior REVISE verdict does not
carry over (architect-review binds to the head commit). **Next session is Opus/Architect.**

## Just done (Sonnet/Coder session, 2026-07-13)
Fixed the 7 findings from the Opus review, in two commits on `sprint/35-tasks-1-2`:

- **`bf473cd` — F1, F2, F3, F4, F7.**
  - **F1:** pinned every `state_io` writer to `encoding="utf-8"`: `write_state_snapshot`,
    `write_artifact`, `write_agent_scratchpad`, `append_agent_memory` (read + write). Per
    the repo owner's F3 scope call, this landed at the single-writer boundary, not just
    `write_artifact` — a half-pinned policy is what produced the original bug. Follow-through
    surfaces also pinned: the snapshot read-backs in `cli.py` (`_load_state`, `cost_summary`),
    and the `.agent/` reads in `agent_state/store.py` (`read_scratchpad`, `read_memory`,
    `append_memory`).
  - **F2/F7:** `test_publish_is_idempotent_for_unchanged_non_ascii_body` is now
    `@pytest.mark.parametrize("ctype_locale", [None, "C"])` instead of copy-pasted — the
    `"C"` case forces `LC_CTYPE=C` at runtime, which flips the process's *default* text
    encoding to ASCII, so a bare (unpinned) `write_text` raises `UnicodeEncodeError` on the
    café/日本語/😀 body. **Verified live**: reverted `writer.py`'s pin, reran the test — `[C]`
    failed with exactly that error, `[None]` still passed; restored the fix, reran — both
    pass. This is the actual regression signal F2 said was missing.
  - **F4:** corrected `publish_artifacts`' docstrings — no read happens on first publish
    (`path.exists()` short-circuits it), so "every artifact on every stage" was wrong.
- **`f124f22` — F5, F6.** Added a one-line window marker to `CLAUDE.md` and
  `.ai/context/workflow.md` noting the "cut from `main`" / "base is `main`" rules and the
  historical merge-commit note describe the state *after* Task 5 runs, not now — PR #57 is
  still cut from and based on `feat/mcp-langgraph-migration`. Also corrected workflow.md's
  CI-trigger claim (`ci.yml` triggers on push to `main` **and** `feat/**`, not `main` only)
  and noted the `feat/**` strip as Task 5 cleanup.
- Green gate: `hatch run lint` clean, `hatch run format` clean (158 files unchanged),
  `hatch run test` — **544 passed**.
- Pushed to the live `sprint/35-tasks-1-2` branch; PR #57 confirmed `MERGEABLE`, head now
  `f124f22`.

## Next — Opus/Architect
**Fresh session.** `/resume` → `/code-review` PR #57 at head `f124f22` (a new head since the
last review — needs a full review, not a reread) → if clean, post via
`gh pr review 57 --comment` with the `**Opus/Architect HITL review (automated)**` header and
fresh-session attestation (**never `--approve`**). Specifically confirm:
1. F1 actually resolves both sides of every write/read pair now pinned to `utf-8`.
2. F2's parametrized test is a real regression guard (see the live-revert verification above
   if you want to re-check it yourself rather than take it on faith).
3. F4's docstring correction and F5/F6's docs window markers read accurately.

Then (Opus/human): Task 3 pre-merge preflight → Task 4 open the migration PR → **Task 5 the
merge + settings sequence (HUMAN-ONLY)** → Task 6 sequence the follow-on work.
**PR #55 approved the plan, not Tasks 3–5's execution — that HITL gate is still open.**

## Human actions
- **DO NOT disable `allow_merge_commit`** before the migration merge (BL-13). Last verified
  live 2026-07-13: `allow_squash_merge=true`, `allow_merge_commit=true`,
  `allow_rebase_merge=false`, `squash_merge_commit_title=PR_TITLE`,
  `delete_branch_on_merge=true`. Ordinary sprint PRs (including #57) are **SQUASH** — the
  merge-commit button exists only for the one migration PR.
- **Dependabot PRs #50–53 must NOT merge before the migration PR** (FD5) — four **major**
  action bumps that rewrite the exact `ci.yml` `uses:` SHA lines the clean merge depends on
  being identical. They get real review in Task 6, *after* the merge.
- **Carried:** delete `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6); trim the
  PAT's repo list.

## Pointers
- [`sprints/35_migration_merge/sprint_plan.md`](../sprints/35_migration_merge/sprint_plan.md) —
  the approved plan. FD1–FD7 locked.
- PR #57 — Tasks 1–2, head `f124f22`, **no review posted against this head yet**.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design** (closes in
  Task 5); BL-12/BL-14's topology gap closes with the merge itself.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to push any further revisions
  to.** Clean at `f124f22`.
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
