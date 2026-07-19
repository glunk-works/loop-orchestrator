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
| **0 — Enablers** | Land **BL-5** per-persona model routing (Opus deep-inspection/report, Haiku triage; needs Haiku in pricing RATES). Stand up `tools/inventory_db` + the Postgres schema (§4) + the **scope validator** (§5) + an **ingestion-sanitization seam** for scanner output first. These two seams are the concrete fixes for validated gaps in `bounty-infra`'s current scanner — no structural scope check (`bounty-infra#7`) and target-derived fields fed straight into the triage LLM (`bounty-infra#13`) — built once here and shared. **Decomposed into three sprints (P0-D1): 43 (BL-5 routing) → 44 (`inventory_db` + §4 schema) → 45 (scope validator §5 + ingestion seam §10).** The `State.schema_version` → 6 bump is **deferred to Phase 1** (P0-D2) — it ships with the first bounty `State` field, not with pure non-`State` infra. | **in progress — sprint 43 (BL-5 routing) complete (T1–T4 merged); 44/45 remain** |
| **1 — Recon + Surface-Mapping** | `workflow_dispatch` seam on `bounty-infra`; wrap recon as scope-validated MCP tools; IDP parser → typed `assets`/`endpoints`. Stages 1–2. | not started |
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

## 11. Pointers

- [`docs/architecture_definition.md`](architecture_definition.md) — the framework's
  architecture + threat model this extends.
- [`docs/migration_roadmap.md`](migration_roadmap.md) — the MCP+LangGraph migration that
  produced the machinery this loop reuses.
- [`docs/backlog.md`](backlog.md) — **BL-5** (per-persona routing) is Phase 0's enabler.
- `bounty-infra` (separate repo) — the Fargate scan substrate.
- `loops/default/loop.py` — the reference `Loop`/`Stage` wiring this loop mirrors.
