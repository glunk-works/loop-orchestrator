# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`sprints/36_live_factory_verification/sprint_plan.md`, `sprints/DEFERRED_VERIFICATION.md`,
`docs/backlog.md`) — it does not copy them. Regenerated on every `/handoff`. (Run `/resume`
to rehydrate a fresh session.)

## Now
**Sprint `36_live_factory_verification` — Track B is DONE; the whole sprint is complete
bar the merge.** All of Tasks 4–7 were executed **live** (2026-07-15). **PR #79**
(`sprint/36-track-b-verification`, **docs-only**, base `main`) is **open and green** —
it discharges `DEFERRED_VERIFICATION.md` §5/§7/§8 and closes BL-21. **No HITL gate is
open** (docs-only ⇒ `architect-review` is exempt and already shows PASS). The human's
**merge of #79 is the approval.**

## Just done (this session — Opus/Architect, live execution)
- **§5 (Task 4) — PASS.** All four `github_server` verbs via `build_github_provider()`
  (first authenticated MCP-fronted `gh` round-trip): create/clone/branch/PR against a
  private scratch repo; traversal + symlink `dest` rejected pre-`gh`; FD6 = exactly 4
  verbs at runtime, no `create_ruleset`, no merge verb.
- **§8 (Task 5) — PASS, and BL-21 proven live (FD9).** `run_bootstrap` → public repo +
  ruleset (id 18965237). Direct/force/delete pushes on `main` **and** `develop` all
  **observed rejected** (`GH013`) — the `administration=write` admin token itself blocked
  (empty `bypass_actors`). `develop` based on `main`'s exact SHA; zero required checks (FD4).
- **§7 (Task 6) — PASS.** Green: a real loop run (COMPLETED, $1.46/$5) opened **PR #2**
  against `develop` (unmerged); `.agent/STATE.md` absorption confirmed; no `.worktrees`
  under `LOOP_ENGINE_ISOLATION=worktree`. Red: the flow's red-gate contract proven
  deterministically (`GATE_FAILED` → no push/PR); a **real-loop** re-run (after the API
  top-up) showed a real loop *converges a red suite to green* — the Coder transparently
  emptied the seeded failing test.
- **Teardown (FD11):** all three scratch repos (`factory-scratch-s5-`, `-boot-`,
  `-boot2-`) deleted with explicit slugs, read-back-asserted, loop-engine-refusal guard;
  `glunk-works/loop-engine` confirmed intact.
- **Docs:** `DEFERRED_VERIFICATION.md` §5/§7/§8 retired in place (not renumbered) + FD1's
  stale "no gh auth / daemon-bearing host" premise corrected; **BL-21 closed**; **BL-28/29/30
  filed** (see below).
- **PAT decision:** `administration=write` was **KEPT** (owner's call, to finish testing;
  account topped up). Revoke when no further live factory testing is planned.

## Next — a FRESH session (no blocking gate)
1. **Merge PR #79** once fully green (docs-only; the merge is the approval).
2. **`/archive-sprint`** to retire sprint 36.
3. **BL-2 (Slack control plane) planning pass** — the agreed next work after sprint 36.

## Findings filed this sprint (all generated-repo territory, all `src/` → own sprints)
- **[BL-28]** — a factory-scaffolded repo **fails its own `ruff check`** (`S101` in
  `tests/`, no `per-file-ignores`). `pytest`/`ruff format` pass; only lint fails.
- **[BL-29]** — maintenance **escalation crashes** on a factory-born repo: `gh issue
  create --label loop-engine/needs-human` fails (bootstrap provisions no such label); the
  run raises after the `AWAITING_ISSUE` snapshot already persisted. Provision the label at
  bootstrap, or make the issue filer tolerant.
- **[BL-30]** — the maintenance green gate runs `pytest src` but the scaffold puts tests
  in `tests/`; a fresh repo would `GATE_FAILED` on 0 collected tests. Make gate & layout agree.

## Gotchas worth remembering
- **`architect-review` is exempt on docs-only PRs** (it showed PASS on #79 with no review).
  A PR touching `src/` still needs the fresh-session review.
- **PR title ≤ 72 chars** and must match `^(feat|fix|docs|…)(\(scope\))?!?: [a-z].*[^.]$`
  (first #79 title failed the length limit; also avoid `§` in the title to dodge byte-count).
- **The factory's own gate suppression works:** a real maintenance loop will *edit
  out-of-scope failing tests to go green* (transparently, in the PR diff, human-reviewed,
  no auto-merge) — so you cannot observe `GATE_FAILED` from a real loop via a *fixable*
  seeded failure; prove the gate contract deterministically instead.
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** A signing `Timeout`
  means answer the host pinentry and retry the commit (seen once on #79's first commit).
- **`administration=write` is LIVE on the token** — it can delete any org repo. FD11 guards
  (explicit slug, read-back, loop-engine refusal) apply to every destructive call.
- **`.ai/state.json` is gitignored** — **`next-steps.md` is what travels.**

## Pointers
- [`sprints/DEFERRED_VERIFICATION.md`](../sprints/DEFERRED_VERIFICATION.md) — §5/§7/§8 now
  carry their PERFORMED (sprint 36) records; **§1 and §6 remain open** (§1 → BL-3, §6 → BL-24).
- [`sprints/36_live_factory_verification/sprint_plan.md`](../sprints/36_live_factory_verification/sprint_plan.md) — the plan; Tasks 1–7 all done.
- [`docs/backlog.md`](../docs/backlog.md) — **BL-21 closed**; open: BL-1..BL-5, BL-15/16/18/20,
  BL-22..BL-30. **Next: BL-2.**
