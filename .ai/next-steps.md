# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — Opus review at head `fb93715`: verdict REVISE.**
Next session is **Sonnet/Coder**: close **F29–F34**, green gate, push.

## Just done (Opus/Architect session, 2026-07-13)
Fresh-session `/code-review` of PR #57 at head `fb93715`, posted with
`gh pr review --comment`. F24–F27 each **do** close what the prior review named, and
F28 is correctly moot — but this round's fixes all live in **structural guards**, and
two of those guards are themselves broken:

- **F29 (HIGH, blocking)** — [`test_state_io_boundary.py:22`](../tests/tools/test_state_io_boundary.py)'s
  `_direct_write_calls` is **blind to method-form `.open()`** (matches `ast.Name` for
  `open`, `ast.Attribute` only for `write_text`/`write_bytes`). Verified: `path.open("w")`
  in **any** module bypasses the single-writer boundary and the test stays green. This is
  the *same* bug F25 just fixed in `test_encoding_boundary.py`, left standing in its twin —
  and this PR adds the repo's first method-form `.open()` calls, one of them in
  `agent_state/store.py`, outside `ALLOWED_DIRS`.
- **F30 (HIGH, blocking)** — [`test_encoding_boundary.py:65`](../tests/tools/test_encoding_boundary.py)'s
  `_open_mode(is_method=True)` **parses the filename as the file mode** for module-level
  openers. `gzip.open('blob.gz','wt')` → mode `'blob.gz'` → contains a `b` → judged binary →
  a real unencoded text write is exempted. Whether the guard fires depends on whether the
  filename happens to contain the letter "b".
- **F31 (med)** — the newline guard's `WRITE_OWNING_DIRS` excludes `agent_state/`, the one
  module this PR gave an `.open()` handle to. With F29, a write there is unguarded twice over.
- **F32 (med)** — the `sys.flags.utf8_mode` skipif drops the **whole** parametrized test,
  including the locale-*independent* `None` case; on Python 3.15 all non-ASCII publish
  coverage silently vanishes.
- **F33 (med-low)** — the append-only prefix check is now tautological for its only caller
  (both sides read the same file byte-identically). May be answered with a docstring.
- **F34 (low)** — `_is_write_capable_mode` inverts the conservatism F21 states 20 lines above.

## Next — Sonnet/Coder
1. Close **F29 + F30** (blocking), then **F31 + F32** (cheap, same round). **F33/F34** are
   judgment calls — F33 may be answered with a docstring rather than a refactor.
2. Green gate: `hatch run lint`, `hatch run format`, `hatch run test`. Commit, push.
3. Hand back to **Opus** for a fresh-session review **at the new head** — moving the head
   turns `architect-review` red again regardless.

## Notes only — do NOT fix without a fresh planning pass (→ backlog)
- **F2, F4, F14, F17, F23** — unchanged, still correctly deferred.
- **F28** — optional, verified moot; no backlog entry needed.
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
  the approved plan. FD1–FD7 locked. **PR #55 approved the plan, not Tasks 3–5's execution.**
- PR #57 — Tasks 1–2, seventh fix round (F29–F34). Full review comment on the PR at `fb93715`.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since
  sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks
  never run. **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 through `fb93715`, pushed, PR #57 open against
  `feat/mcp-langgraph-migration`. **Live — still the branch to fix/review/merge.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
