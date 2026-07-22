# Bounty Loop — architecture & roadmap (reference of record)

> **Status: PROPOSED. Nothing under `loops/bounty/` is built yet.** This is the design
> authority's reference-of-record for the second loop, the analog of
> [`migration_roadmap.md`](migration_roadmap.md) for the migration. Read it before
> extending the bounty pipeline. Decisions and their rationale are logged here (§9);
> the phased build status is the table in §8. Where this doc and the source disagree,
> the source wins and this doc is the bug — file it.

## 1. What this is

The **bounty loop** is loop-orchestrator's *second* loop: an AI-augmented bug-bounty /
vulnerability-detection → reporting pipeline, a sibling of the PM→Architect→Sprint→Coder
**default loop**. It runs the same machinery — a named sequence of decoupled persona
`Stage`s against a single explicit versioned `State`, each stage gated
(accept / revise / escalate), questions escalating a resolver ladder, aggressive actions
pausing to a human, and a snapshot persisted on every accepted stage and every exit path.

It does **not** re-implement scanning. The org already has the muscle:

- **`bounty-infra`** (separate repo, built) — an AWS Fargate, zero-ingress, Infisical-OIDC
  scanner: `subfinder`/`httpx`/`nuclei` → one-pass triage → KMS-encrypted S3. This is the
  **batch scan substrate**.
- **`global-bootstrap`** — the shared OpenTofu state backend + OIDC/IAM foundation both
  loops' AWS surfaces sit on.
- **`appsec-triage-agent`** — an empty stub today; superseded by this loop's Triage stage,
  not a foundation.

The division of labor: **loop-orchestrator is the brain; `bounty-infra` is the hands.** The
loop drives the substrate, ingests its findings into a durable inventory, and runs the
staged Triage → Deep-Inspection → Validate → Report pipeline the framework was built to host.

## 2. Provenance — the Gemini sketch is guidelines, not rules

The initiative began from a six-document Gemini sketch (CTEM framing; the MCP-security
blueprint; a secure-MCP-tool code example; a 5-phase build order; a Postgres schema; a
LangGraph-Postgres checkpointing recipe). The owner deputized this as **guidelines the
project architecture overrides**. §9 records every point where our architecture trumps the
sketch and why. The most load-bearing override: **execution state stays on our JSON `State`
snapshots, not LangGraph-native Postgres checkpointing** — the sketch built its loop from
zero; we already have resume/escalation/budget on snapshots, and a second checkpoint engine
is two sources of truth for "where is this run."

## 3. The pipeline as `Stage`s over `State`

The sketch's 5-phase order (recon → mapping → baseline-scan+triage → deep-inspection →
validate+report) maps 1:1 onto a `Loop`:

```
Recon/Inventory → Surface-Mapping → Scan+Triage → Deep-Inspection → Validate+Report
   [batch]           [batch]          [gated]        [Ralph, gated]     [gated, HITL]
        \_________ bounty-infra Fargate → S3 _________/   \__ local scope-validated MCP __/
```

| # | Stage (persona) | Gate | Resolvers | Autonomy |
|---|---|---|---|---|
| 1 | **Recon/Inventory** — dispatch `bounty-infra` recon, IDP-normalize raw output → typed `assets`/`endpoints` | `ArtifactGate("asset_inventory")` | — | autonomous (passive) |
| 2 | **Surface-Mapping** — resolve live hosts, index routes/tech-stack, flag auth (IAM) boundaries | `ArtifactGate("surface_map")` | recon | autonomous (passive) |
| 3 | **Scan+Triage** — dispatch `nuclei`; Triage persona (Haiku) dedups / FP-filters / severity-scores against inventory | `ArtifactGate("triage_report")`, `max_revisions` for a re-triage cycle | mapping | autonomous (passive) |
| 4 | **Deep-Inspection** — Ralph-style agentic persona over scope-validated security MCP tools (IDOR / privesc / secret-hunt) | a coverage-style gate on validated findings | mapping | **passive autonomous; active exploitation ESCALATES** |
| 5 | **Validate+Report** — validate the chain, scope-recheck vs program rules, emit CVSS + Markdown repro | `ArtifactGate("finding_report")` + a mandatory **human** review gate | inspection | **HITL — always human-gated (MVP terminus)** |

`impact_reentry` for the bounty loop (blast-radius rework): a `"scope"`-impact question
re-enters Recon (index 0 — the scope changed, re-inventory); a `"surface"`-impact question
re-enters Mapping (index 1). (The default loop's `"architecture"`/`"plan"` impacts are its
own; each loop declares its own re-entry map.)

## 4. Persistence — two stores, one boundary discipline

Two data classes with opposite lifecycles; conflating them is the anti-pattern.

- **Per-run execution state → our JSON `State` snapshots** (`tools/state_io`, `schema_version`
  ≥ 6 — see below). Ephemeral, single-writer, replay/resume/budget/escalation-pause. Already
  built; reused unchanged.
- **Cross-run asset inventory + findings → Postgres/JSONB**, owned by a **new single
  DB-owning module `tools/inventory_db`** (the only module that opens a Postgres connection —
  same posture as `state_io`/`scaffold` being the only file-writers). Long-lived,
  *multi-writer* (recon upserts continuously), needs querying / dedup / referential joins.

**Boundary discipline:** the run's `State` references inventory rows **by ID**
(`target_id`/`asset_id`/`finding_id`) and records gate outcomes + pointers; it **never
embeds** the inventory. Postgres is the system-of-record for assets/findings; snapshots are
the system-of-record for run execution. (This is the sketch's own doc-06 "link by thread_id"
advice — our thread_id is `run_id`, our checkpoint store is snapshots.)

### Inventory schema (Postgres + JSONB)

Derived from the sketch's doc-05, adapted to our invariants. `targets` is the **rules of
engagement** and the root of scope enforcement (§5):

- **`targets`** — `id`, `program_name`, `in_scope_regex[]`, `out_of_scope_regex[]`,
  `banned_actions[]`. The source of truth for what may be touched.
- **`assets`** — `id`, `target_id→targets`, `asset_identifier`, `asset_type`, `open_ports[]`,
  `raw_scan_data JSONB`.
- **`endpoints`** — `id`, `asset_id→assets`, `url_path`, `http_methods[]`, `tech_stack JSONB`,
  `requires_auth`.
- **`findings`** — `id`, `endpoint_id→endpoints`, `run_id` (links to the snapshot that
  produced it), `finding_type`, `severity`, `reproduction_steps`,
  `validation_status ∈ {unverified, ai_verified, human_verified}`.

LangGraph's own checkpoint tables are **not** used — we do not adopt `AsyncPostgresSaver`
(§9-D1).

## 5. Scope enforcement is a structural invariant (non-negotiable)

The single most important safety property. The `targets` in/out-scope regex + `banned_actions`
become a **boundary validator on every scanning MCP tool** — the direct analog of
`repo_io._validate_clone_dest`, the "implicit-repo = the R8 bug" fix, and the "no merge verb"
rule. **The model cannot emit an out-of-scope target, because the tool rejects it at the
Pydantic boundary before any subprocess runs** — exactly the sketch's doc-03 pattern
(`ipaddress` validation, subnet allowlist, banned ports, fixed argv, `shell=False`). Scope is
enforced in code, never delegated to the LLM. A tool call whose target fails scope validation
raises, is never executed, and is surfaced as a gate/escalation signal — it never silently
no-ops.

## 6. Aggressive actions gate through the existing escalation ladder

Passive recon, mapping, and baseline scanning run autonomously. Anything that **actively
exploits** (IDOR exploitation, privilege-escalation attempts, heavy/DoS-adjacent fuzzing —
i.e. a `targets.banned_actions` neighbor) does **not** get a new mechanism: it raises a
`Question` and pauses via the `EscalationFiler` seam
(`build_escalation_filer_from_env()` → `AWAITING_ISSUE`/`AWAITING_SLACK` with
`pending_issue`/`pending_slack`), resuming on the human's answer. Active exploitation is
therefore *always* a human-gated step, which is what keeps the whole loop inside
authorized-testing bounds. The Validate+Report stage's human review gate (§3, stage 5) is the
MVP's terminal HITL point — no finding leaves the system without a human.

## 7. Security-tool MCP servers & compute topology

New MCP servers under `mcp_servers/`, declared in `loop_orchestrator.mcp.json`, each
delegating to a scope-validated `tools/` module with **no credentials of its own** and the
five-sanctioned-subprocess-surface posture (atomic Pydantic-validated verbs — never
`run_terminal_command`; fixed argv; `shell=False`; aggressive output filtering to conserve
context). These are **orchestrator-invoked**, scope-guarded, and pairwise-disjoint from the
existing coder/github/issue tool sets.

**Compute topology (design call):**
- **Coarse batch recon/scan → `bounty-infra` Fargate.** Heavy, parallel, zero-ingress,
  long-running. Dispatched at the Recon (§3-1) and Scan (§3-3) phase boundaries via a
  programmatic `workflow_dispatch` trigger (a Phase-1 integration seam on `bounty-infra`),
  results landing in S3 and ingested into Postgres. Not per-tool-call in a tight loop.
- **Fine-grained deep-inspection → local scope-validated MCP tools** under our
  `LOOP_ORCHESTRATOR_ISOLATION=container` posture. Targeted requests inside the interactive
  agent loop, where a Fargate round-trip per call would be intolerable.

## 8. Roadmap & status

| Phase | Scope | Status |
|---|---|---|
| **0 — Enablers** | Land **BL-5** per-persona model routing (Opus deep-inspection/report, Haiku triage; needs Haiku in pricing RATES). Stand up `tools/inventory_db` + the Postgres schema (§4) + the **scope validator** (§5) + an **ingestion-sanitization seam** for scanner output first. These two seams are the concrete fixes for validated gaps in `bounty-infra`'s current scanner — no structural scope check (`bounty-infra#7`) and target-derived fields fed straight into the triage LLM (`bounty-infra#13`) — built once here and shared. **Decomposed into three sprints (P0-D1): 43 (BL-5 routing) → 44 (`inventory_db` + §4 schema) → 45 (scope validator §5 + ingestion seam §10).** The `State.schema_version` → 6 bump is **deferred to Phase 1** (P0-D2) — it ships with the first bounty `State` field, not with pure non-`State` infra. | **✅ complete (all three sprints merged + archived) — sprint 43 (BL-5 routing) T1–T4 merged; sprint 44 (`inventory_db` + §4 schema) complete (T1 PR #159, T2 PR #162, remainder F1 JSONB-adapter fix + T3 docs PR #165 all merged) — hermetically verified, live Postgres round-trip smoke deferred → `sprints/DEFERRED_VERIFICATION.md` §10 (destination Phase 1); sprint 45 (scope validator §5 + ingestion seam §10) T1 PR #168 + T2 docs PR #170 merged — both invariants built as pure leaf primitives (`tools/scope_validator` + `tools/ingest`), no live consumer per P0-D11, fully hermetic (no live surface of their own). Phase 1 (Recon) is next.** |
| **1 — Recon + Surface-Mapping** | `workflow_dispatch` seam on `bounty-infra`; wrap recon as scope-validated MCP tools; IDP parser → typed `assets`/`endpoints`. Stages 1–2. **Decomposed into three sprints (P1-D1): 46 (loop skeleton + `State` 5→6 bump) → 47 (recon data path) → 48 (Surface-Mapping stage).** | **✅ sprint 46 complete (skeleton + `State` v6 bump + this decisions write-up) — T1 PR #173 merged (fresh-session `architect-review` APPROVE on the review-fixed HEAD), T2 docs PR #177 merged. Hermetic only — no live surface exists yet; the OWED sprint-44 live Postgres smoke stays deferred to S47 (`DEFERRED_VERIFICATION.md` §10).** Sprints 47–48 not started. |
| **2 — Scan + Triage** | `nuclei` MCP tool; Triage persona (Haiku) dedup/FP-filter/severity vs inventory, gated. Absorbs + upgrades `bounty-infra`'s one-pass Gemini triage. Stage 3. | not started |
| **3 — Deep-Inspection** | Ralph-style agentic persona; secure security-tool MCP servers; passive autonomous, active gated (§6). Stage 4. | not started |
| **4 — Validate + Report (MVP terminus)** | Validate chain, scope-recheck vs program rules, CVSS + Markdown repro → `findings` (pending human-verify) + S3 report; human review gate. **Stop here.** Stage 5. | not started |
| **Deferred (post-MVP)** | The **Submit** stage (bounty-platform API — dedup/program-policy/rate rules, a platform credential); **graph-DB** attack-path / blast-radius modeling (Neo4j/Neptune); **continuous-recon** cron/DB-trigger auto-spawn. | out of MVP scope |

## 9. Decisions log

Owner-confirmed forks (2026-07-19):

- **D1 — Loop home:** `loops/bounty/` in this repo (why `loops/` is plural), not a new repo,
  not grown inside `bounty-infra`. Reuses engine/gates/escalation/State directly.
- **D2 — MVP terminus:** human-reviewed findings report; **no external submission** in v1.
- **D3 — Persistence:** JSON snapshots for run state **+** Postgres/JSONB inventory
  (`tools/inventory_db`). **Rejected** LangGraph-native `AsyncPostgresSaver` checkpointing
  (**D1-rationale:** two sources of truth for run execution) and snapshots-only-no-DB
  (database-in-files anti-pattern for a mutating, queryable, multi-writer inventory).
- **D4 — Models:** Claude-only — Opus (deep-inspection/report), Haiku (bulk triage) — which
  lands **BL-5** per-persona routing. Not multi-provider; `bounty-infra`'s in-substrate Gemini
  triage is superseded by the Haiku Triage stage.

Phase-0 planning-pass decisions (2026-07-19, owner-confirmed via HITL micro-gates; **locked** —
a future pass must not re-open them):

- **P0-D1 — Phase 0 splits into three sprints**, smallest reviewable PRs, one concern each:
  **43** (BL-5 per-persona model routing — the enabler; also benefits the paused dev loop) →
  **44** (`tools/inventory_db` + the §4 Postgres schema — the sole DB-connection owner) →
  **45** (the two security invariants: the structural scope validator §5 + the ingestion-
  sanitization seam §10). Sequencing is load-bearing: 43 is independent; 45 needs 44's
  `targets` rules-of-engagement.
- **P0-D2 — `State.schema_version` 5→6 bump deferred to Phase 1.** Phase 0 is pure non-`State`
  infra (routing, DB module, validators); no bounty `Stage` reads a new `State` field until
  Phase 1's Recon stage. Bumping now would ship an empty-schema version with an empty
  `migrate_state_payload` branch — churn. The bump lands in Phase 1 with the field it exists
  for. (Sprints 44/45 each get their own `sprint_plan.md`; P0-D3..D6 are recorded in
  `sprints/43_bl5_model_routing/sprint_plan.md` for those passes.)
- **Sprint 44 T2 Architect Review finding F1 (fixed in the sprint-44 remainder):**
  `PsycopgInventory` bound the `raw_scan_data`/`tech_stack` JSONB columns as bare `dict`
  values, but psycopg 3 has no `dict` dumper — every non-`None` write raised
  `ProgrammingError`→`InventoryError`. Fixed by wrapping non-`None` dict binds in
  `psycopg.types.json.Jsonb(...)` in both the INSERT and UPDATE paths of
  `upsert_asset`/`upsert_endpoint` (`None` stays `None`, never `Jsonb(None)`, which would
  write JSON `null` instead of SQL `NULL`). F2 (upsert TOCTOU race), F3 (held connection
  never closed), F4 (single connection not thread-safe), and F5 (SQL-param guard narrower
  than its docstring) remain open as Phase-1 notes.

Phase-0 sprint-45 planning-pass decisions (2026-07-20, owner-confirmed via HITL micro-gates
1–6; **locked** — a future pass must not re-open them):

- **P0-D11 — Deliverable = the primitives only, no consumer.** Ship the scope validator and
  the ingestion sanitizer as pure library primitives with **no scanning-tool caller**; the
  Pydantic-boundary wiring into real scanning MCP tools lands in Phase 1 with the tools it
  guards (same no-consumer YAGNI posture as sprint 44's P0-D7). **Rejected:** also building
  one reference scanning MCP tool now — pulls the MCP-provider/server surface into a sprint
  with no recon stage to feed it.
- **P0-D12 — A dedicated, standalone `ScopeRules` value object.** `tools/scope_validator`
  owns a frozen `extra="forbid"` `ScopeRules` (`in_scope_regex`/`out_of_scope_regex`/
  `banned_actions`) with a `ScopeRules.from_target(...)` adapter that reads the three rules
  attributes via a **structural protocol** (`Target` under `TYPE_CHECKING` only) — **zero
  runtime import edge** onto `inventory_db`, pinned by a hardened import-graph guard.
  **Rejected:** consuming `inventory_db.models.Target` directly — couples the leaf validator
  to the DB module's schema shape.
- **P0-D13 — Fail-closed allowlist; deny wins.** A candidate is ALLOWED iff it matches **≥ 1**
  `in_scope_regex` **AND 0** `out_of_scope_regex`; an out-of-scope match always vetoes, and an
  **empty `in_scope_regex` denies everything**. A violation **raises `ScopeViolation`**, never
  silently no-ops. Matching is unanchored `re.search` (an operator wanting exact-host scope
  anchors their pattern `^…$`) — documented and pinned. **Rejected:** denylist-primary /
  in_scope-optional — an empty `Target` would fail *open* to the whole internet, the exact
  posture §5 exists to prevent.
- **P0-D14 — `is_action_banned(...)` is a pure predicate; policy deferred.** The validator
  ships `is_action_banned(rules, action) -> bool` as **mechanism**; the reject-vs-**escalate**
  policy (§6) stays with the Phase-3 deep-inspection consumer that issues actions. The
  primitive classifies; the consumer decides. **Rejected:** baking escalate-vs-reject policy
  into a leaf with no caller.
- **P0-D15 — The sanitizer is structural/mechanical.** `sanitize(text, *, max_len)` strips
  C0/C1 control chars + ANSI CSI escapes + invisible format code points (a Unicode `Cf`-
  category sweep covering zero-width/BOM, bidi override/isolate, and the Tags block, plus a
  narrow variation-selector strip), NFKC-normalizes, collapses whitespace, and hard-truncates
  — **no** injection-phrase blocklist; untrusted text stays structurally fenced by the
  (Phase-1) prompt template, mirroring §5's structural-not-heuristic ethos. **Rejected:**
  injection-phrase scrubbing — brittle, false confidence, heuristic creep in a safety
  primitive.
- **P0-D16 — One combined `src/` PR + a docs PR.** Both primitives are small, cohesive
  pure-Python leaves with no dependency surface, so they ship in **one** `src/` PR (T1, one
  fresh-session `architect-review` cycle — PR #168) with docs landing last (T2, exempt).
  **Rejected:** two separate `src/` PRs — an extra full review handoff for a small, cohesive
  diff.

> **P0-D12/D13/D14/D15 still describe the real semantics — they just describe `scope-core`'s
> code now, not `tools/scope_validator`/`tools/ingest` in this repo.** The SC pass (BI-D6,
> 2026-07-22) relocated both primitives to `glunk-works/scope-core`, a shared package this repo
> now depends on instead of implementing locally; see §10 below. Not re-opened, only relocated —
> the fail-closed/deny-wins/unanchored-`re.search`/structural-mechanical-sanitizer decisions
> hold exactly as written.

Phase-1 planning-pass decisions (2026-07-21, owner-confirmed via HITL micro-gates 1–7;
**locked** — a future pass must not re-open them):

- **P1-D1 (micro-gate 1) — Phase 1 is three sprints**, smallest reviewable PRs, one concern
  each: **46** (bounty loop skeleton + the `State` 5→6 bump) → **47** (recon data path:
  `workflow_dispatch` seam on `bounty-infra` + scope-validated recon MCP tool + IDP parser →
  `inventory_db`, its first consumer) → **48** (Surface-Mapping stage). Sequencing is
  load-bearing: the irreversible schema change is isolated in 46 and reviewed before any
  external surface exists; 47 needs 46's `State.bounty`; 48 needs 47's inventory.
  **Rejected:** a 4-sprint split isolating the bump into its own micro-PR — an extra review
  handoff for a change cohesive with the skeleton it exists for; and a 2-sprint split
  bundling the bump with external integration surface — a large PR mixing the one
  irreversible change with live-infra code.
- **P1-D2 (micro-gate 2) — a nested `BountyRunState` sub-model, not flat fields.** The 5→6
  bump adds one optional namespaced sub-model `bounty: BountyRunState | None = None` to the
  shared `State`; the default loop never sets it. Future bounty ID references (`asset_ids`,
  `endpoint_ids`, `finding_ids`, a surface-map ref) go **inside** `BountyRunState`
  **additively — with no further `schema_version` bump** (the same additive-with-default
  posture as `Question.origin_detail` and `StageRecord`'s cache fields). First field:
  `target_id: str` (the `targets` RoE root, §4). **Rejected:** a flat `target_id` on `State`
  — pollutes the shared state the default loop carries and forces a new flat field per
  future ref; and a pre-populated nested model seeding empty asset/finding ref lists now —
  fields with no writer until later stages, the YAGNI tension P0-D7 rejected.
- **P1-D3 (micro-gate 3) — walking skeleton, both stages, stub bodies behind a stable
  seam.** Sprint 46 wires **both** stages with placeholder personas that emit **fixture**
  stub artifacts, so the full loop runs green end-to-end hermetically. S47 replaces the
  Recon persona's **body** (its injected producer collaborator) with the real data path;
  S48 replaces Mapping's. The persona **shell** (reads `State.bounty`, calls the
  collaborator, writes the artifact, returns `State`), the gates, the re-entry map's target
  indices, and the schema shape do **not** churn again. **Rejected:** a Recon-only skeleton
  adding Mapping whole in S48 — leaves the loop incomplete and the `surface:1` re-entry edge
  untested until late; and wiring the *real* persona classes with stubbed tools now —
  front-loads S47's dispatch/parse design into the skeleton sprint.
  > **Fold-in correction (S46 T1 Architect Review, HIGH):** the sprint plan's original text
  > claimed `impact_reentry` is "exercised from day one." It is not — `Question.impact` has
  > no `"scope"`/`"surface"` member, `reentry_index()` only checks `("architecture",
  > "plan")`, and `VALID_IMPACTS` filters both out, so a `"scope"`/`"surface"` resolution can
  > never reach the map today. The map's **target indices** are locked now (so S47/S48 don't
  > re-derive them); making it **live** is three core edits (the three named above),
  > deferred to S47/S48. PR #173's review-fix (commit `7cdf15b`) corrected `loop.py`'s
  > docstring/comment and renamed the shape-only test accordingly — see CLAUDE.md's
  > `loops/bounty/` boundary bullet for the corrected claim.
- **P1-D4 (micro-gate 4) — S47 builds hermetic behind injected seams; live verification is
  one authorized V-run.** S47 is built fully hermetic (a `ReconDispatcher` protocol + a
  fake, `InMemoryInventory`) and stays green in hermetic CI with no creds/spend on the merge
  path. The live `workflow_dispatch` → S3 → **real-Postgres round-trip** discharge together
  in **one** authorized `live-verify` V-run, which **also discharges the OWED sprint-44 §10
  live PG smoke** (the first `inventory_db` consumer + a real/dev PG exist by then — §10's
  own stated destination). **Rejected:** wiring live infra inline as S47 acceptance —
  couples the merge gate to live AWS/GitHub/PG + real Fargate spend; and splitting the PG
  smoke into S47 while deferring the Fargate seam — leaves the recon data path incomplete
  with faked S3 input. (An S47-scoped decision, recorded here for phase completeness; S47
  gets its own planning pass at its boundary.)
- **P1-D5 (micro-gate 5) — S3 fetch is a `boto3` egress, not a subprocess surface.** S47's
  recon dispatch fires `workflow_dispatch` via **`gh`** — a *third* consumer of the
  already-sanctioned `gh` subprocess surface (alongside `issue_io`/`repo_io`), **not** a
  sixth surface — and fetches results from S3 via a **new pinned `boto3` dependency**: a new
  network **egress** under the already-declared AWS/Infisical-OIDC credential class, **not**
  a subprocess surface. The **five** sanctioned subprocess surfaces stay five; S47 carries a
  `boto3` pin + `sbom` regen + `dependency-audit` delta (like sprint 44's `psycopg`).
  **Rejected:** the `aws` CLI as a sixth subprocess surface — a real change to a boundary
  the repo has deliberately held at five, for no dependency saving worth that; and deferring
  the real S3 client past S47 — the V-run then can't discharge, weakening P1-D4. (S47-scoped;
  recorded for phase completeness.)
- **P1-D6 (micro-gate 6) — scope enforcement mounts at BOTH boundaries with distinct
  semantics.** In S47, `tools/scope_validator` goes live two ways: **(input)**
  `validate_target` at the recon MCP tool's Pydantic boundary **raises `ScopeViolation`** on
  any caller/model-supplied target or seed (the canonical §5 guard, satisfying P0-D11's
  "Pydantic boundary"); **(output)** each **discovered** asset from the IDP parser is
  scope-checked and out-of-scope ones are **FILTERED** — dropped + counted, **never
  raised** — because bulk recon naturally surfaces out-of-scope hosts and raising per host
  would halt a normal run. Only in-scope assets reach `inventory_db`; the sanitizer
  (`ingest.sanitize`) scrubs scanner/target-derived text on the same output path before any
  model sees it. This is the fail-closed reading of §5's "never silently no-ops": a *caller
  asserting* an out-of-scope target is an error (raise); a *scanner discovering*
  out-of-scope hosts is expected (filter). **Rejected:** output-filter only — defers the
  canonical input guard P0-D11 named; input-raise only — persists whatever recon returns, so
  an out-of-scope host in scan output slips into inventory unchecked. (S47-scoped; recorded
  for phase completeness.)
- **P1-D7 (micro-gate 7) — sprint 46 is a library loop, engine-test-driven; no CLI
  surface.** Sprint 46 defines `build_bounty_loop()` + `BountyRunState` + the schema bump +
  stub personas, verified by driving the engine over the loop in tests (both fixture
  artifacts produced, both gates pass, the re-entry map's shape asserted). The CLI/runner
  loop-selector is **deferred to S47**, when a real recon path makes hand-invocation
  meaningful. **Rejected:** a `--loop {default,bounty}` selector or a `bounty-run`
  subcommand now — CLI surface + arg handling for a loop that emits only stubs until S47.

Design-authority overrides of the Gemini sketch:

- Scope enforcement is structural code, not an LLM responsibility (§5).
- Active exploitation reuses the existing escalation ladder, not a new "paused_for_auth"
  mechanism (§6).
- Credentials keep our posture: keyring (Anthropic key), Infisical-OIDC (AWS/scan-infra),
  env-vars (transport). No new credential class.
- Graph DB deferred; doc-01's CTEM/portfolio framing treated as capability guidance, not
  product direction.

## 10. Threat-model delta (extends `architecture_definition.md`)

New untrusted inputs cross into the loop: **raw scanner output** and **live target
responses** (both attacker-influenceable — a target can craft banners/JS/HTTP responses to
prompt-inject the triage/inspection personas). New dangerous sinks: the **scanning tool
argv** (must never take a model-controlled flag or an out-of-scope target — §5) and the
**target network itself** (active actions — §6). Mitigations: scope validation at every tool
boundary, aggressive output filtering/normalization before any scanner text reaches a model,
zero-trust-between-stages carried over, and human-gated exploitation + reporting. Full
writeup lands with Phase 0.

These are not hypothetical. The 2026-07-19 `bounty-infra` review confirmed both failure
modes in the existing scanner: it has **no structural scope check** — target selection is
gated only by who can dispatch the workflow (`bounty-infra#7`, H2) — and it **feeds
target-derived fields (`matched-at`) into its Gemini triage prompt** (`bounty-infra#13`, M4).
Phase 0's scope validator (§5) and ingestion-sanitization seam are precisely these two fixes,
lifted into the loop rather than reinvented; the review's other findings (GitHub Actions
script injection, over-broad task-role IAM, unpinned tool/template supply chain,
CI/plan-gate gaps) track as `bounty-infra#6`–`#16`.

**Built (sprint 45, PR #168).** The ingestion-sanitization seam and the scope validator shipped
as pure leaf primitives with **no live consumer yet** (P0-D11): `sanitize` (structural
normalizer — §10/P0-D15) and `ScopeRules`/`validate_target` (fail-closed allowlist +
banned-action classifier — §5/P0-D13/D14). Phase 1 mounts them at the scanning MCP tools'
Pydantic boundary, where the untrusted scanner/target text they defend against actually begins
to flow.

**Moved (SC pass, 2026-07-22 — BI-D6).** Both primitives now live in
[`glunk-works/scope-core`](https://github.com/glunk-works/scope-core), a dedicated shared
package repo, not `tools/scope_validator`/`tools/ingest` in this repo. This corrects an
overclaim: the paragraph above originally read these as "lifted into the loop" as bounty-infra's
`#7`/`#13` fix; they are instead a **shared** definition both repos depend on, so bounty-infra's
scanner and this loop's Phase-1 recon tools can never disagree about what "in scope" means.
`scope-core` is pinned by commit SHA via a PEP 508 direct reference in `pyproject.toml` (not
published to PyPI). See `bounty-infra`'s `sprints/SC_scope_core_extraction/sprint_plan.md`.

## 11. Pointers

- [`docs/architecture_definition.md`](architecture_definition.md) — the framework's
  architecture + threat model this extends.
- [`docs/migration_roadmap.md`](migration_roadmap.md) — the MCP+LangGraph migration that
  produced the machinery this loop reuses.
- [`docs/backlog.md`](backlog.md) — **BL-5** (per-persona routing) is Phase 0's enabler.
- `bounty-infra` (separate repo) — the Fargate scan substrate.
- `loops/default/loop.py` — the reference `Loop`/`Stage` wiring this loop mirrors.
