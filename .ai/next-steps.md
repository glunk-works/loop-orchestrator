# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 reviewed fresh at head `e22b359` — verdict REVISE.**
F1's own scope claim ("pinned every write/read to utf-8 at the single-writer boundary")
does not hold: two live gaps of the identical bug class remain (F8, F9 below). Review
deliberately **not posted to GitHub** — same call as the prior REVISE (`e7bdd7f`):
architect-review binds to the exact head commit, and F8/F9's fix is a required follow-up
commit that moves the head, so a review posted against `e22b359` would be stale the
instant the fix lands and would need re-doing anyway. **Next session is Sonnet/Coder.**

## Just done (Opus/Architect review session, 2026-07-13)
Fresh session, no memory of authoring PR #57. Ran an 8-angle finder pass (line-by-line,
removed-behavior, cross-file tracer, reuse, simplification, efficiency, altitude,
CLAUDE.md conventions) plus 1-vote verification on every surviving candidate against the
diff at head `e22b359`. Confirmed F4's docstring correction and F5/F6's docs window
markers read accurately, and F2's parametrized test is a real regression guard *today*.
But F1 is only partially resolved:

- **F8 (CONFIRMED, blocking).** `src/loop_engine/tools/scaffold/writer.py` lines 77
  (`target.write_text(content)`), 92 (`entry.read_text()`), 99
  (`(_templates_root() / _CONVENTIONS_TEMPLATE).read_text()`) are still unpinned.
  CLAUDE.md's own "Enforced module boundaries" section names `tools/scaffold` as the
  **second** file-write-owning module, sibling to `state_io` — the exact boundary F1
  claimed to close. Confirmed the bundled `templates/CLAUDE.md` this module writes into
  every newly bootstrapped repo contains real non-ASCII content (19 em-dashes, via
  `grep -c '—'`) — not hypothetical, the identical live bug F1/F2 just fixed elsewhere,
  in the one sibling module the sweep never visited.
- **F9 (CONFIRMED, blocking).** `src/loop_engine/cli.py:119` —
  `human_input = input.read_text() if input is not None else ""` (the `run()` command's
  `--input` entry point) is still unpinned, in the *same file* where two sibling reads
  (`_load_state`, `cost_summary`) were fixed three lines apart in this very diff. A
  non-ASCII `requirements.md` on a non-UTF-8-locale host crashes `loop-engine run` before
  the loop even starts.
- **F10 (PLAUSIBLE, non-blocking, note only).** The newly-strict `encoding="utf-8"` reads
  (`cli.py`, `agent_state/store.py`) could raise `UnicodeDecodeError` reading a state/
  `.agent` file *written before this fix* on a non-UTF-8-locale host, where the old code
  round-tripped (consistently, if wrongly) on the same locale default at both ends.
  Checked this repo's only documented runtime (devcontainer, `python:3.12-slim`,
  `LANG=C.UTF-8`, PEP 538 coercion) — unlikely to bite in practice. Logging it, not
  blocking on it.
- **F11 (PLAUSIBLE, non-blocking, note only).** The new regression test's
  `locale.setlocale(LC_CTYPE, "C")` mechanism to force a non-UTF-8 default stops working
  once PEP 686 makes UTF-8 mode CPython's default (proposed 3.15+) — `pyproject.toml` has
  no upper Python bound, though `ci.yml` pins exactly `"3.12"` today, so this is dormant,
  not active. Worth a comment noting the assumption someday; not blocking this PR.

## Prior (Sonnet/Coder session, 2026-07-13)
Fixed the 7 findings from the previous Opus review, in two commits on `sprint/35-tasks-1-2`:

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

## Next — Sonnet/Coder
**Fresh session.** `/resume` → on the live `sprint/35-tasks-1-2` branch (PR #57 is open, not
dead — do not cut a new branch), fix:
1. **F8** — pin all three call sites in `src/loop_engine/tools/scaffold/writer.py`:
   `target.write_text(content, encoding="utf-8")` (line 77), and
   `read_text(encoding="utf-8")` at both line 92 and line 99. Extend
   `tests/test_scaffold.py` with a non-ASCII regression test mirroring F2's shape (a
   template or rendered body containing non-ASCII, run under both the default locale and
   `LC_CTYPE=C`) so this boundary gets the same live-verified guard `artifact_store` got.
2. **F9** — pin `src/loop_engine/cli.py:119`:
   `input.read_text(encoding="utf-8") if input is not None else ""`.
3. F10/F11 are notes for awareness, not required fixes — do not scope-creep into them
   unless it's a one-line touch already in the diff.

Green gate (`hatch run lint`/`format`/`test`), commit, push to `sprint/35-tasks-1-2`,
`/handoff` back to Opus for a **fresh** re-review — the new head invalidates this one too.

Then (Opus/human, after a clean review): Task 3 pre-merge preflight → Task 4 open the
migration PR → **Task 5 the merge + settings sequence (HUMAN-ONLY)** → Task 6 sequence the
follow-on work. **PR #55 approved the plan, not Tasks 3–5's execution — that HITL gate is
still open.**

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
- PR #57 — Tasks 1–2, head `e22b359` reviewed **REVISE** (F8, F9 blocking; F10, F11 notes) —
  review not posted to GitHub, see *Just done* above. `architect-review` still fails until
  a clean review posts against the fix commit's head.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design** (closes in
  Task 5); BL-12/BL-14's topology gap closes with the merge itself.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to push any further revisions
  to.** Clean at `e22b359`; F8/F9 fixes land on top of this.
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
