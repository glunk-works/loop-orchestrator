# Next steps — dev-workflow cursor

Thin, live cursor for whoever picks up this repo next. Points into the deep record
(`docs/bounty_loop_architecture.md`, the sprint plan, the PRs) — it does not copy them.
Regenerated on every `/handoff`. (Run `/resume` to rehydrate a fresh session.)

## Now
**Bounty loop — Phase 1, sprint 47 (recon data path): `sprint_status: awaiting_architect_review`.**
T1 is merged (`cad4db1`, PR #190, reviewed). The S47-D13 prerequisite —
`scope-core`'s `is_in_scope`/`normalize` — is merged in that separate repo
([scope-core#2](https://github.com/glunk-works/scope-core/pull/2), SHA `3d251f1`) and
`pyproject.toml` is re-pinned. **Task 2 (the ingest half) is implemented and up as
[PR #193](https://github.com/glunk-works/loop-orchestrator/pull/193)** — a `/critic-gate`
pass ran, its findings are fixed, and all 7 non-review required checks are green. Only
`architect-review` is red, awaiting the fresh-session post.

## Just done (2026-07-25, Sonnet/coder)
- **Prerequisite `scope-core` PR** merged: added `is_in_scope(rules, candidate) -> bool`
  (composes into `validate_target`, preserving its two distinct `ScopeViolation` reasons)
  and `normalize(text) -> str` (structural prefix of `sanitize`, no collapse/truncate;
  `sanitize` now composes `collapse+truncate ∘ normalize`). Parity + no-truncate tests.
- **Re-pinned** `pyproject.toml`'s `scope-core` dependency to the merged SHA; regenerated
  `sbom.json`; `hatch run audit` green.
- **Task 2 implemented** (`tools/recon/{parse,pipeline}.py`): JSONL → whitelisted
  `ReconRecord`s (S43 structured-extraction-and-wrap) → group by normalized host →
  `scope_core.is_in_scope` drop+count (P1-D6 output boundary) → `scope_core.sanitize` the
  free-text survivors → `inventory_db` upsert. Endpoints attributed to their own record's
  host, never the seed's (S47-D11). Five-case fixture matrix + endpoint host-scoping test.
  Opened as PR #193.
- **`/critic-gate` ran** (security-critic + architect, both spawned on the human's
  confirmation). Findings fixed: (1) `http_methods` was the one attacker-influenceable
  free-text field reaching `inventory_db` unsanitized — now sanitized like every other
  field; (2) a crafted JSONL line (pathological nesting, or an integer literal past the
  interpreter's digit limit) raised `RecursionError`/`ValueError` from `json.loads`
  itself, escaping the narrow `except json.JSONDecodeError` and crashing the whole batch —
  now caught and drop+counted like any other malformed line. Both findings had tests added;
  full suite re-green (868 passed) before the fix push.
- **Closed [PR #192](https://github.com/glunk-works/loop-orchestrator/pull/192)** (a stale
  docs-cursor-sync PR) as superseded — it conflicted with #191 (already merged) and its
  content predated this session's scope-core merge + Task 2 work. This `/handoff`
  supersedes it cleanly.
- Ruleset check: healthy (4 rule types, 8 required checks) — confirmed at session start.

## Next — Opus/architect posts the fresh-session review (HITL Gate: NONE OPEN)
In a **new session** (not `/clear` — the review boundary needs a genuinely separate
invocation): `/model opus` → `/resume` → `/code-review` on
[PR #193](https://github.com/glunk-works/loop-orchestrator/pull/193)
(`sprint/47-recon-ingest` → `main`) → post with `gh pr review --comment`, verbatim
two-line header + attestation from `.ai/context/workflow.md`. If clean, tell the human
it's ready for their merge (never merge/`--approve` yourself). After merge: **Task 3**
(`build_recon_producer`, `build_bounty_loop(recon_producer=…)` param, `inventory_db.get_target`,
the `bounty-target add`/`bounty-run` CLI) per
[`sprints/47_bounty_recon_data_path/sprint_plan.md`](../sprints/47_bounty_recon_data_path/sprint_plan.md),
then **Task 4** (docs), then the V-run.

## Gotchas worth remembering
- **`tools/scope_validator`/`tools/ingest` are gone** — everything routes through
  `scope_core` now (external, commit-pinned). A change to `is_in_scope`/`normalize`/
  `sanitize`/`validate_target` means a PR against `glunk-works/scope-core`, a new SHA,
  re-pinning `pyproject.toml` (+ `sbom`/`audit`) — not a local edit here.
- **The one free-text field that's easy to miss:** every attacker-influenceable string on
  a `ReconRecord` needs `scope_core.sanitize` before `inventory_db` — `http_methods` was
  the field that slipped through in the first Task 2 pass; caught by `/critic-gate`, not
  by the original implementation. Worth a second look on any future field addition.
- **`bounty-infra#18` (dispatch contract) is still a V-run precondition, blocked on #6** —
  unrelated to T2/T3; they merge hermetically without it.
- **`.ai/state.json` is git-ignored** — this file (`next-steps.md`) is what travels.

## Pointers
- [PR #193](https://github.com/glunk-works/loop-orchestrator/pull/193) — Task 2, all 7
  non-review checks green, **awaiting fresh-session architect-review**.
- [`sprints/47_bounty_recon_data_path/sprint_plan.md`](../sprints/47_bounty_recon_data_path/sprint_plan.md) — S47 plan (T1 done, T2 up, T3/T4 + V-run remain).
- [`docs/bounty_loop_architecture.md`](../docs/bounty_loop_architecture.md) — reference-of-record; §9 decisions log (S47-D13 folds in at T4).
- [scope-core#2](https://github.com/glunk-works/scope-core/pull/2) — merged (`3d251f1`), adds `is_in_scope`/`normalize`.
- `bounty-infra#86` — the pilot-consumer (`bounty-infra`'s own scanner) adopt-it follow-up, unrelated to this repo's merge bar.
