# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `35_migration_merge`, PR #57 — reviewed and ACCEPTed at head `fb3d719`; the
`architect-review` check is GREEN.** One required follow-up fix (F1) plus three cheap
guard-hardening findings remain before the merge. **Next session is Sonnet/Coder.**

## Just done (Opus/Architect session, 2026-07-13)
Fresh-session `/code-review` of PR #57 at head `fb3d719`, **verdict ACCEPT**, posted to
GitHub headed `**Opus/Architect HITL review (automated)**`. The `architect-review` check
flipped to **pass** at that head (it re-runs on `pull_request_review: submitted`).

Confirmed closed: **F12** (the AST guard genuinely bites and carries its own
detector spot-check), **F13** (`artifact_store.py:39` compares bytes, so a corrupt
non-UTF-8 artifact can no longer raise `UnicodeDecodeError`), **F16** (docstring dedup).
No bare `open()` remains in `src/`; every `read_text`/`write_text` there pins `encoding=`.

Six new findings, none wrong on Linux — hence ACCEPT rather than a fifth handback round.
Full text and disposition are in the posted review on PR #57.

## Next — Sonnet/Coder, on the live `sprint/35-tasks-1-2` branch

**F1 — REQUIRED.** [`state_io/writer.py:101`](../src/loop_engine/tools/state_io/writer.py#L101):
add `newline="\n"` to the `write_text` calls. `Path.write_text` defaults to `newline=None`,
which translates `\n` → `os.linesep` on write — so `write_artifact` does **not** emit the raw
UTF-8 bytes that [`artifact_store.py:39`](../src/loop_engine/tools/artifact_store.py#L39)'s new
`read_bytes() == body.encode("utf-8")` compare assumes. On Windows every artifact body (all
markdown, all contain newlines) compares unequal forever, so the idempotence skip is
**permanently dead**; CI is ubuntu-only and cannot see it. This is a regression *this PR
introduced*, unlike F14/F15/F17. Add a regression test asserting the on-disk bytes equal
`body.encode("utf-8")` exactly.

**F3/F5/F6 — cheap hardening of the guards this PR is about.** Fold into the same round.
- **F3** [`test_encoding_boundary.py`](../tests/tools/test_encoding_boundary.py) — the guard
  matches only `read_text`/`write_text`, but `open` is the **third** sanctioned write primitive
  (`test_state_io_boundary.py:11`'s `DISALLOWED_WRITE_CALLS` names all three) and is *legal*
  inside `state_io`/`scaffold` — i.e. legal in exactly the two modules this PR fixed. Extend it.
- **F5** same file — it passes **vacuously** if `SRC_DIR` fails to resolve (`rglob` yields
  nothing, `offenders` stays empty, green). Assert a nonzero scanned-file count.
- **F6** [`test_artifact_store.py:60`](../tests/tools/test_artifact_store.py#L60) +
  [`scaffold/test_writer.py:95`](../tests/tools/scaffold/test_writer.py#L95) — add
  `pytest.mark.skipif(sys.flags.utf8_mode)` so the locale parametrization's coverage loss under
  PEP 686 (default in 3.15; `requires-python` is `>=3.12`, no upper bound) is loud, not silent.

Then green gate, push. **The review check is head-pinned** — pushing F1 moves the head and
re-reds `architect-review`, so the new head needs one more fresh-session Opus review before
the merge. That is a formality on a known-ACCEPT diff, not a fifth substantive round.

Then: Task 3 (pre-merge preflight) → Task 4 (open the migration PR) →
**Task 5 (the merge + settings sequence, HUMAN-ONLY)** → Task 6 (sequence the follow-on work).
**PR #55 approved the plan, not Tasks 3–5's execution — that HITL gate is still open.**

## Notes only — do NOT fix in this PR (→ backlog)
- **F2.** `artifact_store`'s byte compare hard-codes `state_io`'s serialization contract
  (exact UTF-8, no newline translation, no trailing newline) across the enforced single-writer
  boundary. F1 is the one-line symptom fix; the deeper fix is a compare helper in `state_io`.
- **F4.** ~20 unencoded `read_text()` calls remain under `tests/` — incl. `test_ci_config.py:154`
  reading `CLAUDE.md`, and the AST boundary tests parsing `src/*.py`. Both now contain em-dashes,
  so on the C-locale host F8 exists to defend against, the suite dies before it can prove
  anything. The new guard scopes to `src/` and will never flag them.
- **F14 / F17** — carried, unchanged (subprocess `text=True` locale decoding; `append_memory`
  double-read).

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
- PR #57 — Tasks 1–2, head `fb3d719`, **reviewed ACCEPT**, `architect-review` green. The posted
  review carries F1–F6 and their disposition.
- [`docs/backlog.md`](../docs/backlog.md) — BL-11 resolved; **BL-13 open by design**.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed since sprint 32.
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — five checks never run.
  **FD4: none blocks the merge**, but Task 6 gives each a scheduled home.
- Ruleset checked healthy 2026-07-13: 4 rule types, all 8 required checks on `main`.

## Working tree
- `sprint/35-tasks-1-2` carries Tasks 1–2 plus the F8/F9/F12/F13/F16 fixes, pushed, PR #57
  open against `feat/mcp-langgraph-migration`. **Live — still the branch for the F1 fix.**
- `sprint/35-migration-merge` and `sprint/35-archive-34` remain **dead** (squash-merged as
  #55/#56) — never push to either again.
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); `.ai/next-steps.md` is
  tracked.
