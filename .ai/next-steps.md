# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/migration_roadmap.md`) + the active sprint file — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Phase 5 — Sprint 25 (`bootstrap_flow`, piece 4) — `implementing`.**
Plan is written and **HITL-approved**. The next session is a **Sonnet/Coder**
implementation pass over `sprints/25_bootstrap_flow/sprint_plan.md` (tasks 1–6 in order).

## Just done (Sprint 25 — planning pass, Opus/Architect)
- Wrote + got HITL approval for `sprints/25_bootstrap_flow/sprint_plan.md` (the
  bootstrap flow — Phase 5 piece 4). Five decisions locked in the planning pass:
  1. **Skeleton only, no inner loop** — bootstrap makes a ready-to-work repo *exist*;
     maintenance/trigger does the feature work. No `run_in_tree`, no green gate, no LLM run.
  2. **New `tools/scaffold` = the 2nd sanctioned FILE-WRITE surface** (not a 5th
     subprocess surface) — writes bundled templates via `write_text`, tree validated
     via `repo_io._validate_clone_dest`. Mirrors 24's `git_io` carve-out. **No `hatch new`.**
  3. **Templates bundled as package data; injected `CLAUDE.md` byte-identical to
     `.ai/context/conventions.md`**, enforced by a sync-guard test.
  4. **Python-only skeleton, `kind`-parametrized** — IaC/OpenTofu set deferred behind the seam.
  5. **Push `main` (first commit) → create `develop` → no PR** — nothing to PR into on a
     brand-new repo; leaves the repo conformant + maintenance-ready.
- Net boundary delta: file-write owners **1→2**; subprocess surfaces **unchanged (four)**;
  no new dependency (SBOM unchanged); no credential into process; no `open_pr`/merge.

## Next
1. **(Sonnet/Coder) Implement Sprint 25** per the sprint_plan, tasks 1–6:
   `tools/scaffold` + bundled templates → boundary invariants (widen
   `test_state_io_boundary.py` to `{state_io, scaffold}`, keep subprocess at four,
   conventions sync-guard) → `flows/bootstrap` chain → `flows/` boundary coverage →
   hermetic e2e proof (real scaffold + real `git_io` to a bare remote, faked `repo_io`) →
   docs/roadmap/deferred-verification.
2. Run the green gate (`hatch run test` / `lint` / `format` / `audit`; SBOM unchanged).
3. `/handoff` back to Opus for HITL review of the diff once green.

## HITL gate
NONE open right now — the plan is approved, cleared to implement. The next gate opens
**after** implementation: Opus HITL review of the coding diff.

## Carry-forward
- **Sprint-24 review nit (still open):** no unit test over
  `flows/maintenance.flow._default_run_tests`. Orthogonal to bootstrap.
- **22b nit (still open):** bare `python` vs `sys.executable` in the committed
  `loop_engine.mcp.json` github stanza. Orthogonal — not touched in 25.

## Pointers
- `sprints/25_bootstrap_flow/sprint_plan.md` — the approved plan to implement.
- `docs/migration_roadmap.md` — Phase 5 status; ▶ NEXT ACTION → Sprint 25.
- `.ai/context/workflow.md` — the Opus↔Sonnet handoff protocol + switch points.

## Working tree
- Plan committed? **Not yet** — `sprints/25_bootstrap_flow/` is untracked at HEAD
  `add275d`. Commit the plan before switching sessions so `/resume`'s `last_commit`
  matches HEAD.
