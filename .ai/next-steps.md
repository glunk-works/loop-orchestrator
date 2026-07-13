# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — F12/F13/F16 fixed and pushed, head `069ac69`,
awaiting a fresh Opus re-review.** The prior review (head `aa155d7`) was ACCEPT but
unposted — two hardening findings were handed back instead. **Next session is
Opus/Architect.**

## Just done (Sonnet/Coder session, 2026-07-13)
Fixed F12, F13, and F16 from the Opus review of PR #57 at head `aa155d7`, one commit:

- **`069ac69` — F12, F13, F16.**
  - **F12:** added [`tests/tools/test_encoding_boundary.py`](../tests/tools/test_encoding_boundary.py) —
    a structural AST guard asserting every `read_text`/`write_text` call in `src/` carries
    an `encoding` kwarg, following the `test_state_io_boundary.py` / `test_subprocess_surfaces.py` /
    `tests/tools/test_keyring_boundary.py` idiom. **Live-verified**: reverted
    [`cli.py:119`](../src/loop_engine/cli.py#L119), reran, the guard failed with the exact
    unencoded call flagged; restored the fix, reran — clean.
  - **F13:** [`artifact_store.py:37`](../src/loop_engine/tools/artifact_store.py#L37) —
    replaced the idempotence check `path.read_text(encoding="utf-8") == body` (raises
    `UnicodeDecodeError` on a corrupt/non-UTF-8 on-disk artifact) with
    `path.read_bytes() == body.encode("utf-8")` (cannot raise). Added
    `test_publish_overwrites_a_corrupt_non_utf8_artifact_without_raising` to
    `tests/tools/test_artifact_store.py` — **live-verified**: reverted the fix, reran,
    got `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff...`; restored, reran — passes.
  - **F16:** deduplicated the read-compare nuance in `artifact_store.py` — the module
    docstring now just points at the function docstring, which carries the one
    authoritative (and now byte-comparison-accurate) explanation.
- Green gate: `hatch run lint` clean, `hatch run format` clean (159 files unchanged),
  `hatch run test` — **549 passed** (546 + the AST guard's 2 tests + the new F13 regression).
- Pushed to the live `sprint/35-tasks-1-2` branch; PR #57 confirmed `mergeable=MERGEABLE`,
  head now `069ac69` (`mergeStateStatus=BLOCKED` — expected, pending the required review/checks).

## Next — Opus/Architect
**Fresh session.** `/resume` → `/code-review` PR #57 at head `069ac69` on
`sprint/35-tasks-1-2`. Specifically re-verify F12 and F13 are closed (see commit `069ac69`
above) and that no new gap of the same bug class was introduced. F14/F15/F17 are notes
only, not required fixes. If clean: **post** the review to GitHub headed
`**Opus/Architect HITL review (automated)**` against head `069ac69` — this is the first
review in this round with no known blocking finding going in, so it should actually land
rather than go stale.

Then: Task 3 (pre-merge preflight) → Task 4 (open the migration PR) →
**Task 5 (the merge + settings sequence, HUMAN-ONLY)** → Task 6 (sequence the follow-on
work). **PR #55 approved the plan, not Tasks 3–5's execution — that HITL gate is still open.**

## Notes only — do NOT fix in this PR
- **F14 → backlog.** All six sanctioned subprocess surfaces pass `text=True` with no
  `encoding=`, so they still decode child output with the **locale default** — the same
  bug class, pre-existing. `issue_io/github.py:31` reading a human-authored issue body
  with an em-dash is the realistic failure.
- **F15 (optional, cheap).** Both regression tests (F1/F8/F9 shape) silently become
  tautologies under Python UTF-8 mode (PEP 686 default in 3.15; `requires-python` is
  `>=3.12`, no upper bound). A `pytest.mark.skipif(sys.flags.utf8_mode)` makes the coverage
  loss loud.
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
- PR #57 — Tasks 1–2, head `069ac69`, **unreviewed at this head** (F12/F13/F16 just landed).
  Prior heads `e7bdd7f`, `e22b359`, `aa155d7` were reviewed (REVISE, REVISE, ACCEPT) but
  never posted — each moved before posting made sense. This is the fourth round.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 plus the F8/F9/F12/F13/F16 fixes, pushed, PR #57
  open against `feat/mcp-langgraph-migration`. **Live — still the branch for any further fixes.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
