# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`sprints/36_live_factory_verification/sprint_plan.md`, `sprints/DEFERRED_VERIFICATION.md`,
`docs/backlog.md`) — it does not copy them. Regenerated on every `/handoff`. (Run `/resume`
to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` is COMPLETE and MERGED.** Track B (Tasks 4–7) was
executed **live** on 2026-07-15 and landed via **PR #79** — squash `212cc56` on `main`
(discharges `DEFERRED_VERIFICATION.md` §5/§7/§8, closes BL-21). Track A (#73/#76/#77) merged
earlier. **No HITL gate is open.** The only bookkeeping left is **`/archive-sprint`** to
retire sprint 36 — then the reprioritized backlog begins.

> **This branch (`sprint/36-close-handoff`) is the handoff-only PR** — it carries this
> cursor update alone. All substantive sprint-36 content is already on `main`.

## What landed (sprint 36 Track B — live, this session)
- **§5 — PASS.** All four `github_server` verbs via `build_github_provider()` (first
  authenticated MCP-fronted `gh` round-trip); traversal + symlink `dest` rejected pre-`gh`;
  FD6 = exactly 4 verbs at runtime, no `create_ruleset`, no merge verb.
- **§8 — PASS, BL-21 proven live (FD9).** `run_bootstrap` → public repo + ruleset. Direct/
  force/delete pushes on `main` **and** `develop` all **observed rejected** (`GH013`) — the
  `administration=write` admin token itself blocked (empty `bypass_actors`); `develop` off
  `main`'s exact SHA; zero required checks (FD4).
- **§7 — PASS.** Green: a real loop run (COMPLETED, $1.46) opened **PR #2** against `develop`;
  `.agent/STATE.md` absorption confirmed; no `.worktrees` under `LOOP_ENGINE_ISOLATION=worktree`.
  Red: gate contract proven deterministically, and a real-loop re-run showed a real loop
  *converges a red suite to green* (the Coder transparently emptied the seeded failing test).
- **Teardown (FD11):** all three scratch repos (`-s5-`, `-boot-`, `-boot2-`) deleted with
  explicit slugs, read-back-asserted; `loop-engine` confirmed intact.
- **PAT:** `administration=write` **KEPT** (owner's call, account topped up). Revoke when no
  further live factory testing is planned.

## Next — a FRESH session
1. **`/archive-sprint`** to retire sprint 36 (it is merged; this is the last bookkeeping).
2. **Test-review block jumps AHEAD of BL-2 (owner decision 2026-07-15) — BL-22, then BL-23,
   then BL-2.** Rationale: test/CI cost compounds across every future sprint, so front-load
   it before feature work. Start with a **BL-22 Architect planning pass**:
   - **BL-22 (CI/runner-time velocity).** Highest-value/lowest-risk lever: **session-scope the
     MCP-subprocess fixtures** (faster suite *everywhere*, incl. local TDD; touches no CI
     trigger logic — land it first). The docs-PR CI-exemption half is **dangerous**:
     `paths-ignore` on required checks is exactly what caused **BL-10/BL-12**, so it needs the
     deliberate **aggregator-job** design (`if: always()`, inspect `needs.*.result`), not a
     casual path filter. (Sprint 36 proved the waste: PR #79 was markdown-only and still ran
     the full ~380 s `test` job.)
   - **BL-23 (test-validity audit)** next — trust, not speed: mutation-test the boundary guards
     + `core/`, hunt orphan/vestige tests and guards weaker than their docstring.
   - **BL-2 (Slack control plane)** after the test-review block.

## Findings filed sprint 36 (all generated-repo territory, all `src/` → own sprints)
- **[BL-28]** — a factory-scaffolded repo **fails its own `ruff check`** (`S101` in `tests/`,
  no `per-file-ignores`). `pytest`/`ruff format` pass; only lint fails.
- **[BL-29]** — maintenance **escalation crashes** on a factory-born repo: `gh issue create
  --label loop-engine/needs-human` fails (bootstrap provisions no such label); the run raises
  *after* the `AWAITING_ISSUE` snapshot already persisted. Provision the label at bootstrap,
  or make the issue filer tolerant.
- **[BL-30]** — the maintenance green gate runs `pytest src` but the scaffold puts tests in
  `tests/`; a fresh repo would `GATE_FAILED` on 0 collected tests. Make gate & layout agree.

## Gotchas worth remembering
- **`architect-review` is exempt on docs-only PRs** (it showed PASS on #79 with no review).
  A PR touching `src/` still needs the fresh-session review.
- **PR title ≤ 72 chars** and must match `^(feat|fix|docs|…)(\(scope\))?!?: [a-z].*[^.]$`
  (first #79 title failed the length limit; also avoid `§` in the title to dodge byte-count).
- **A real maintenance loop will *edit out-of-scope failing tests to go green*** (transparently,
  in the PR diff, human-reviewed, no auto-merge) — so you cannot observe `GATE_FAILED` from a
  real loop via a *fixable* seeded failure; prove the gate contract deterministically instead.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** A signing `Timeout` means
  answer the host pinentry and retry the commit (seen on #79's first commit).
- **`administration=write` is LIVE on the token** — it can delete any org repo. FD11 guards
  (explicit slug, read-back, loop-engine refusal) apply to every destructive call.
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Pointers
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §5/§7/§8 now carry
  their PERFORMED (sprint 36) records; **§1 and §6 remain open** (§1 → BL-3, §6 → BL-24).
- [`docs/backlog.md`](../docs/backlog.md) — **BL-21 closed**; open: BL-1..BL-5, BL-15/16/18/20,
  BL-22..BL-30. **Next: BL-22 → BL-23 → BL-2** (test-review block front-loaded, owner decision 2026-07-15).
