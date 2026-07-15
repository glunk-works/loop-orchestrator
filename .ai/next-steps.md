# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/backlog.md`, `docs/migration_roadmap.md`) — it does not copy them. Regenerated on
every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**BL-2 (Slack control plane) — PLANNING.** No sprint directory exists yet. Sprint 38
(BL-23 pass 1, `core/` mutation testing) is archived — see
`.ai/archive/38_test_validity_audit-next-steps.md` for its final cursor if you need
the history. **Next session: Architect/Opus plans BL-2.** No HITL gate is open.

## Just done (previous session)
- **Sprint 38 archived** (`/archive-sprint`) after landing in full: T1/T2/T3
  (PRs #90/#92/#94), BL-32 filed (PR #95), handoff doc (PR #96), and a roadmap
  close-out commit (`02c48d0`, local as of this handoff — not yet pushed/PR'd).
  Final tally: 61 keep / 86 fix / 0 delete, `hatch run mutate` residual survivor
  count verified to match exactly, per-file, against `audit_report.md`.

## Next — plan BL-2 (Architect/Opus)
Read `docs/backlog.md`'s **BL-2** entry in full, including its `SCHEDULED` sub-note
(added 2026-07-14) — it names three open questions the planning pass must weigh
**before** drafting a `sprint_plan.md`:
1. **BL-24's inbound trigger surface has never received a real webhook.** BL-2's
   inbound-trigger candidate inherits that unverified foundation — decide whether
   BL-2 depends on discharging BL-24 first, or can proceed independently of it.
2. **Slack credential class.** A bot token is distinct from the keyring-only
   Anthropic key and the env-var `LOOP_ENGINE_WEBHOOK_SECRET` (per the `trigger/`
   precedent) — decide storage/threading before scoping the rest.
3. **Architecture shape.** A new top-level orchestrator-level caller (sibling of
   `trigger/`/`flows/`) vs. a new MCP server — decide against the module-boundary
   conventions in `CLAUDE.md` before committing to file layout.

No sprint directory exists yet — create `sprints/NN_bl2_slack/` (NN = next
sequential number after 38) once the planning pass actually starts drafting.

## Outstanding from before (not blocking BL-2)
- **`02c48d0`** (the sprint-38 roadmap close-out) is committed on local `main` but
  not yet pushed or PR'd — cut a branch and open a PR for it whenever asked.
- **BL-32** (adversarial static-guard audit, filed PR #95) has no sprint plan yet —
  it's BL-23's next pass, not a BL-2 blocker, and not urgent.

## Gotchas worth remembering
- **Local `main` vs. `origin/main` after a squash merge:** this repo squash-merges
  every PR, so a locally-committed change and its later squash-merged counterpart
  are DIFFERENT commit objects with IDENTICAL content — `git merge --ff-only`
  will fail with "diverging branches." Verify via `git diff origin/main main`
  (expect empty), then `git reset --hard origin/main` to resync local `main`
  safely (nothing is lost — the content already landed via the squash commit).
- **PR title:** `wc -c` the byte count AND re-read the actual text before
  `gh pr create/edit --title` — a stale copy-pasted `(#NN)` suffix from a prior
  commit message slipped through once this cycle.
- **A squash-merged branch is dead** — prune via `gh pr list --state merged` +
  `git branch -D`, never bare `git branch --merged main` (invisible to squash merges).
- **`.ai/state.json` is gitignored** — **this file is what travels.**
- **Never run `.devcontainer/gpg-forward.sh` in a Cursor session.** A signing
  Timeout = answer the host pinentry and retry the commit.

## Pointers
- [`docs/backlog.md`](../docs/backlog.md) — **BL-2** (this unit, with its `SCHEDULED`
  sub-note), BL-24 (the dependency question), BL-32 (filed, no plan yet).
- [`docs/migration_roadmap.md`](../docs/migration_roadmap.md) — NEXT ACTION line
  points at BL-2 planning; sprint 38's full closing paragraph is the historical
  record of BL-23 pass 1.
- [`sprints/38_test_validity_audit/`](../sprints/38_test_validity_audit/) — archived
  sprint's full record (`sprint_plan.md`, `mutation_baseline.md`, `audit_report.md`).
- `.ai/archive/38_test_validity_audit-next-steps.md` — sprint 38's final live cursor,
  preserved for manual history queries (git-ignored, local only).
