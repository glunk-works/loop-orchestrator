# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`, `docs/backlog.md`) + the active sprint file — it does not
copy them. Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**The migration is fully closed** (Phases 1–6). Nothing here is migration work.

**Current unit: sprint `33_ci_title_starvation` (BL-10) — status `implementing`.**
The plan is **written and HITL-approved**. **Sonnet/Coder** implements Tasks 1–4.
Work on the **existing** branch `sprint/33-ci-title-starvation` — **don't cut a new one**
(it's based on `docs/handoff-sprint-33`, so the orphaned handoff commit `da1c6eb` rides
along in this PR instead of needing one of its own).

## Just done (Opus/Architect planning session, 2026-07-12)
- **Planned sprint 33** — [`sprints/33_ci_title_starvation/sprint_plan.md`](../sprints/33_ci_title_starvation/sprint_plan.md), commit `4500d68`. Five locked decisions, five tasks. **Owner read and approved it.**
- **Chose the fix shape: split the workflows** (not BL-10's minimal option). `ci.yml` makes one
  workflow serve a cheap prose check that *must* re-run on `edited` and a heavy code chain that
  *must not*; every guard in the file is scar tissue from that conflict. Two files → all three
  guards delete themselves.
- **Found a second starvation path BL-10 missed (FD2)** — `concurrency`'s group is identical for
  `opened` and `edited`, so a title edit *mid-run* cancels the suite and the replacement run skips
  it. Fires even on PRs whose title was **never invalid**. BL-10's preferred fix wouldn't close it.
- **Found that a green test asserts the defect (FD3)** — `test_lint_job_gates_on_pr_title_to_fail_fast`.
- **Scoped the PR to touch no `src/`** so `hitl-review.yml`'s `^src/` filter exempts it and it lands
  fast — every open PR is exposed to BL-10 until it does.

## Next — Sonnet implements Tasks 1–4 (four commits, in order)
Read the plan; **FD3 and FD5 before touching anything.**

1. **New `.github/workflows/pr-title.yml`** — the job moved **verbatim** out of `ci.yml`.
2. **`ci.yml`** — delete the `pr-title` job, `edited` from the trigger types, and **both**
   `needs: pr-title` *and* the whole `if:` block on `lint`. Concurrency block **stays**.
3. **`tests/test_ci_config.py`** — delete the test that pins the bug; assert the real invariant.
4. **Docs** — `CLAUDE.md` L86 is now false; close BL-10 in `docs/backlog.md`.

> **Task 2 leaves the suite RED on purpose (FD3).** `test_lint_job_gates_on_pr_title_to_fail_fast`
> asserts `needs: pr-title` — it was written to hold this exact structure in place. **A failing test
> there is the sprint working.** Task 3 makes it green. **Do not "fix" the red by reverting Task 2.**

> **FD5 — the job id `pr-title` is FROZEN.** Branch protection matches required checks by check-run
> name, and that name is the **job id**, not the workflow file. Rename it and every future PR hangs
> forever on a check that never arrives. Claude **cannot** verify this (403 on branch protection —
> the PAT has no `Administration` scope by design).

> **YAML trap for Task 3:** a bare `on:` key parses as the **boolean `True`** — `cfg["on"]` raises
> `KeyError`. Use `cfg.get("on") or cfg[True]`, and `yaml.safe_load`, never `yaml.load`.

Then push, open a PR (**base `feat/mcp-langgraph-migration`**), and **stop**.

## HITL gate
**Planning gate PASSED** (owner approved the plan). **None open right now.**
A new one opens when the PR is up: **Task 5** — live verification against GitHub, which is
**Opus/human work, not Sonnet's**. Open the PR with a deliberately **>72-char** valid title and
watch `pr-title` go red while the **whole heavy chain runs green anyway** — the state that is
unreachable today. Then fix the title and confirm no `ci.yml` run fires at all. A fresh-session
Opus review should still be posted even though CI exempts this PR — the diff's subject *is* the
gate machinery.

## Standing obligations (not sprint-33 tasks; all still real)
- **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8) **never run**. Don't delete it.
- **Two unfixed findings from PR #39** — `publish_artifacts` reads every artifact off disk on every
  stage while both docstrings claim it *"does no I/O"*; that read-back uses `Path.read_text()` with
  no explicit encoding. **Deliberately out of sprint 33's scope** (they touch `src/`).
- **Human:** delete the now-redundant `docs/handoff-sprint-33` branch after the sprint PR merges;
  `glunk-works/loop-engine-v3-scratch` (private, issues #1–#6) is still live and needs deleting in
  the UI, then trimming from the PAT's repo list.

## Pointers
- [`sprints/33_ci_title_starvation/sprint_plan.md`](../sprints/33_ci_title_starvation/sprint_plan.md) — **the sprint.** FD1–FD5 + Tasks 1–5.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-10** (this sprint; its diagnosis is right but *incomplete* — it misses FD2) + BL-1…BL-9.
- `.github/workflows/ci.yml` — the target. `pr-title` (L28), `lint` (L64, `needs:` L65, `if:` L66–68), the `edited` trigger (L11), `concurrency` (L20–22, **stays**).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — every phase closed. Sprint 33 is **not** a phase; **don't add a row.**
- `.ai/context/workflow.md` — PR-gated integration + the fresh-session review rule.

## Working tree
- `sprint/33-ci-title-starvation` (at `4500d68`) is the active branch, based on
  `docs/handoff-sprint-33` = `feat/mcp-langgraph-migration` + `da1c6eb`. PR base is
  **`feat/mcp-langgraph-migration`**. Branches squash-merge — **a squash-merged branch is dead;
  never reuse one.**
- `.ai/state.json` + `.ai/archive/` are git-ignored (local mirrors); **`.ai/next-steps.md` is tracked.**
