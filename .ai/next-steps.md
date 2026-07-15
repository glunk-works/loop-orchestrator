# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Sprint `38_test_validity_audit` (BL-23 pass 1) — DONE.** All 3 tasks and both
planning-pass follow-ups are closed. Nothing further to land on this sprint.
**Next session: run `/archive-sprint`, then start the BL-2 (Slack control plane)
planning pass as Architect/Opus.** No HITL gate is open.

## Just done (this session)
- **Task 3 landed** (PR #94, squash `5119b5b`): every one of `audit_report.md`'s 86
  `fix` verdicts implemented as an added/strengthened `tests/core/` test across
  `coder_gate.py`, `engine.py`, `gates.py`, `graph_engine.py`. **No `src/` change was
  needed anywhere** — every row that named a "genuine defect" (the
  `has_artifact(state, None)` masking gap, the token/cost/cache delta
  subtraction-vs-addition bug) turned out on inspection to be mislocated coverage,
  not an actual production bug. Test-only PR, `architect-review` auto-exempt. Full
  suite green (597 passed), lint/format clean.
- **`hatch run mutate` re-run and verified line-by-line against the report**, not
  just by total count: `coder_gate.py` 10/10, `gates.py` 3/3, `graph_engine.py`
  20/20 exact match against the report's named `keep` rows. `engine.py` matched
  except 3 extra survivors, which turned out to be a genuine correction (next bullet).
- **Found and documented 3 mis-triaged verdicts.** Landing the `_prime_resume` fix
  (a real, non-mocked resume integration test, per that row group's own
  recommendation) proved 3 of its 16 originally `fix`-triaged mutants (`mutmut_5`,
  `mutmut_6`, `mutmut_12`) are actually **equivalent** by call-graph analysis — a
  dead pre-loop initial value always overwritten one line later, and a fallback
  default provably `>=` every real value it's ever compared against. Per FD5 ("don't
  contort a test to kill an equivalent mutant"), reclassified to `keep` with the
  proof written inline in `audit_report.md` rather than forcing an artificial
  assertion. No other row was re-triaged. Report's summary counts corrected to 61
  keep / 86 fix (was 58/89); `hatch run mutate`'s residual survivor count (61)
  now matches exactly.
- **Both sprint-plan follow-ups resolved** (owner decisions, this session):
  - **BL-32 filed** (PR #95, docs-only, squash `2ecbbdd`): the adversarial
    invariant-injection audit of the static structural guards (subprocess-surface,
    encoding/write-owner, `core/`↔`personas/` import-boundary, MCP
    verb-disjointness) — mutation testing is the wrong instrument for these (FD1),
    so this generalizes BL-15's proven method instead. Not designed yet; next
    BL-23 planning pass scopes it.
  - **Gate-vs-script: decided "stay on-demand."** Real timings (~35–50s for a full
    `hatch run mutate` run scoped to `core/`) came in far below the sprint plan's
    feared "minutes-to-hours," but the owner chose to keep `hatch run mutate` as
    an on-demand script rather than a required `ci.yml` gate. No CI change made.

## Next — retire the sprint, then plan BL-2
1. Run **`/archive-sprint`** to snapshot this file into `.ai/archive/` and advance
   `.ai/state.json` to the next sprint slot — sprint 38 is COMPLETED and merged
   (the human-approval bar this repo uses), with nothing further to land.
2. Start the **BL-2 (Slack control plane)** planning pass as **Architect/Opus**.
   `docs/backlog.md`'s BL-2 entry carries a `SCHEDULED` note with three open
   questions the planning pass must weigh before drafting a `sprint_plan.md`:
   BL-24's never-verified inbound surface, the Slack credential class (distinct
   from the keyring-only Anthropic key and the env-var webhook secret), and
   whether it's a new top-level orchestrator caller (sibling of `trigger/`/`flows/`)
   or an MCP server.

## Gotchas worth remembering
- **PR title content, not just length.** T3's PR title was accidentally born with
  a stale `(#92)` suffix copy-pasted from a prior commit message — caught and
  amended before push. Always re-read the actual title text, not just `wc -c` it.
- **`architect-review` exempt on no-`src/` PRs** — confirmed again on BOTH T3's
  test-only PR (#94) and BL-32's docs-only PR (#95).
- **A squash-merged branch is dead** — both `sprint/38-t3-land-fixes` and
  `docs/backlog-bl32-adversarial-guard-audit` already pruned locally post-merge.
- **Equivalent-mutant method:** when a targeted test still can't kill a
  plausible-sounding survivor, trace the actual call graph (`mutmut show <name>`
  for the exact diff, then read every consumer of the mutated value) before
  concluding the test is wrong — it might be the mutant that's dead. See
  `.ai/state.json`'s `equivalent_mutant_method` for the two proofs this session.
- **mutmut survivor names are per-function** (`module.x_funcname__mutmut_N`,
  numbering restarts at 1 per function) and stable across re-runs —
  `hatch run mutate-results` + `mutmut show <name>` (via
  `hatch run python -m mutmut show <name>` if the bare script isn't wired) is the
  fast way to inspect one without re-deriving it from prose.
- **`.ai/state.json` is gitignored** — **this file is what travels.**
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** A signing
  Timeout = answer the host pinentry and retry the commit.

## Pointers
- [`sprints/38_test_validity_audit/sprint_plan.md`](../sprints/38_test_validity_audit/sprint_plan.md)
  — COMPLETE: FD1–FD5, T1–T3, and both follow-ups all closed.
- [`sprints/38_test_validity_audit/audit_report.md`](../sprints/38_test_validity_audit/audit_report.md)
  — final state: 61 keep / 86 fix / 0 delete, with the T3-correction note.
- [`docs/backlog.md`](../docs/backlog.md) — BL-23 pass 1 closed; BL-32 filed. Next: BL-2.
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION line still
  says sprint 38/BL-23; update once BL-2 planning starts (or via `/archive-sprint`).
