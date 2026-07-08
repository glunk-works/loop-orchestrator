# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 4 · part 2 review-fixes (sprint `21_declarative_review_fixes`) — `implementing`.**
Sprint 20 (declarative `GeneratorNode` + PM `CriticGate`, `cf48b0c`) is **HITL-reviewed / approved**;
the review's fixes are routed into sprint 21. Next session is **Sonnet / Coder**.

## Just done
- **HITL review of Phase 4 · part 2 (`cf48b0c`)** — parity holds on the accept path; defects found on the escalation/revision path. Sprint-20 gate now **closed (approved)**.
- **Locked decision (Architect):** PM-only `escalate_on_exhaustion` — a stage that churns past its revision budget escalates to a human instead of `StageGateFailedError`, PM stage only, flag-scoped (default off, both engines share `execute_stage`).
- **Drafted `sprints/21_declarative_review_fixes/sprint_plan.md`** — 5 Sonnet tasks: (1) declarative PM `fold_answers` → restores `resume --from-issue`; (2) `Stage.escalate_on_exhaustion` engine flag; (3) PM stage `max_revisions=4` + flag wiring; (4) `utf-8` config reads; (5) cleanups. Review finding #4 (key_merge findings accumulation) **deferred** to an Architect call.

## Next
1. **(Sonnet / Coder) Implement sprint 21 tasks 1–5** per `sprint_plan.md`; run the green gate (`hatch run test`/`lint`/`format`/`audit`). Keep every change flag-scoped so the `classic`/default-off suite passes verbatim (esp. the two existing `StageGateFailedError` tests — do NOT edit them). Hand back for HITL review when green.
2. **(Opus / Architect) Settle review finding #4** (accumulation: re-derive latest-only for `key_merge` vs. document as accepted non-parity) — a small decision before it becomes a task. See the "Deferred" note at the bottom of the sprint plan.
3. After sprint 21 lands + is reviewed → `/archive-sprint` for 20 **and** 21, then plan Phase 5 (FastAPI webhook triggers + multi-repo factory).

## Pointers
- `docs/migration_roadmap.md` — deep status + decisions log (resume point of record).
- `sprints/21_declarative_review_fixes/sprint_plan.md` — the active sprint (review fixes).
- `sprints/20_declarative_generators/sprint_plan.md` — the reviewed/approved sprint the fixes derive from.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

> Uncommitted: `sprints/21_declarative_review_fixes/` is untracked — commit it before switching sessions (a `/resume` expects `last_commit` to match HEAD).
