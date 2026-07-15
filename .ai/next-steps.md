# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `37_test_suite_velocity` — IMPLEMENTING (Coder/Sonnet).** The BL-22 planning pass is
done: `sprints/37_test_suite_velocity/sprint_plan.md` is **written, committed (`c83a7c8`), and
HITL-approved**. Branch `sprint/37-test-velocity` is cut from `main` and holds the plan commit.
**No HITL gate is open.** Tasks are **sequential, one PR each**.

## Just done (this planning session, Opus/Architect)
- **Measured the real cost** (not the backlog's estimate): 570 tests, 278s local / ~380s CI; a
  single MCP server spawn costs a **fixed ~5s import-bound cold-start**; ~20 spawning tests ≈ **40%
  of the suite**. Two backlog assumptions were wrong — the `test_ralph_coder` slowness is an
  *unmocked provider inside the persona*, not a fixture; and the aggregator fix would force
  weakening the BL-10 guard.
- **Wrote the sprint plan** (`c83a7c8`): T1 mock the provider in `test_ralph_coder`, T2 session-scope
  the four direct-spawner test files, T3 docs-only pytest short-circuit (in-job Option A), T4 measure
  `pytest-xdist`. Locked findings FD1–FD5.
- **Filed BL-31** — reduce the per-spawn ~5s cost itself (helps every real coder session); deferred
  out of 37 as its own `src/`-touching unit.
- **Housekeeping:** pulled `main` to `b301cd2` (#81 archive merged), deleted dead `sprint/37-archive-36`.

## Next — implement Sprint 37 Task 1 (Coder/Sonnet)
**T1:** in `tests/personas/test_ralph_coder.py`, mock
`loop_engine.personas.coder_iac.shared.build_coder_tool_provider` (the pattern
`tests/personas/test_coder_tool_backend.py:35` already uses) so `_CoderToolBackend.resolve()`
returns a stub `(tools, execute)` **without spawning a real ~5s MCP server**. Preserve every existing
assertion — the mock only changes *how the tools list is obtained*. **Do not** touch
`tests/tools/test_mcp_provider.py`'s real-server coverage (FD5). Acceptance: no ralph test spawns a
server (file `--durations` drops from ~75s toward single digits), full suite green, lint/format clean.
Then open a PR **based on `main`**; T1 touches only `tests/` → **architect-review-exempt**, but still
needs the full green suite + `pr-title`.

Then **T2 → T3 → T4** in order (see the plan). **T3 is the dangerous one** — read FD3/FD4 in the plan
before touching `ci.yml`: it is **not** the aggregator (that weakens the BL-10 guard); it is a
step-level `if:` on `hatch run test`, using `gh api .../files` + the SIGPIPE-safe capture-then-match
from `hitl-review.yml:70-74`, failing safe (run pytest unless *every* changed file is docs).

## Gotchas worth remembering
- **PR title ≤ 72 chars**, `^(feat|fix|docs|…)(\(scope\))?!?: [a-z].*[^.]$`; avoid non-ASCII (byte-count).
- **`architect-review` is exempt on PRs with no `src/` change** (docs-, tests-, workflow-only). T1–T3
  are all `src/`-free → exempt, but each still needs the full green suite.
- **`gh pr view` serves a stale `mergeStateStatus`** — BLOCKED with nothing failing is GitHub lag; the
  checks are the truth, don't close+reopen. A conflicting PR runs **zero** CI silently.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** A signing `Timeout` = answer the
  host pinentry and retry.
- **`administration=write` is LIVE on the token** (can delete any org repo). Sprint 37 doesn't need it.
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Pointers
- [`sprints/37_test_suite_velocity/sprint_plan.md`](../sprints/37_test_suite_velocity/sprint_plan.md) —
  **the T1–T4 specs + locked findings FD1–FD5.** Read before implementing.
- [`docs/backlog.md`](../docs/backlog.md) — Sprint 37 = BL-22; then BL-23 → BL-2. BL-31 filed (deferred).
  Open: BL-1..BL-5, BL-15/16/18/20, BL-22..BL-31. BL-28/29/30 (sprint 36 findings) still open.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — migration DONE (sprint 35); post-migration
  work is backlog-driven.
