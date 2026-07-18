# loop-engine — Backlog

Post-migration / out-of-band ideas that are **not** part of the current
`docs/migration_roadmap.md` phases. Captured here so they aren't lost; each is a
candidate to promote into a phase/sprint plan later. Nothing here is scheduled or
committed to a design yet.

> Scope note: `docs/migration_roadmap.md` remains the authoritative record for the
> in-flight MCP + LangGraph + isolation migration. This file is for *product*
> ideas beyond it.

## Index

Navigation for a long file — jump to an item rather than scanning. Titles are the
headers verbatim; **each item's own body is authoritative for its status** (resolved and
declined items are retained inline, not deleted — several carry live lessons or reference
material). Keep this list in sync: one line per `### BL-N` header.

- **BL-1** — In-loop code review of the Coder's output (Architect / QA persona + gate)
- **BL-2** — Slack integration · **COMPLETE** (all 3 passes; hermetic — live smoke deferred, BL-37)
- **BL-3** — Review the prompt-caching implementation (correctness + improvement)
- **BL-4** — Ralph loop watcher: progress/liveness detection for runaway inner tool loops
- **BL-5** — Per-persona model routing + resolution token budget review
- **BL-6** — Give Claude its own GitHub identity (machine user / GitHub App)
- **BL-7** — The PM stage has no channel to ask a human a question
- **BL-8** — Stop using process CWD as an isolation mechanism
- **BL-9** — Retire the implicit-CWD destination from the issue path's remaining surfaces
- **BL-10** — A bad PR title permanently starves the heavy CI chain · _resolved (sprint 33)_
- **BL-11** — None of the "required" checks are actually required · _resolved (sprint 33); holds the canonical ruleset spec_
- **BL-12** — `main` behind and cannot pass its own ruleset · _resolved (sprint 34)_
- **BL-13** — Squash-only settings vs. the one-time merge-commit landing · _resolved (sprint 35)_
- **BL-14** — SHA pins / Dependabot inert off the default branch · _resolved; retained as a live lesson_
- **BL-15** — AST write/encoding guards classify `open()` by name (alias defeats them)
- **BL-16** — CI gates verified *required*, never *functional* — a gate can fail open
- **BL-17** — _RESOLVED:_ `feat/**` is retired
- **BL-18** — "No `if:`, so nothing can be `skipped`" is the wrong invariant (a failed `needs:` skips too)
- **BL-19** — _DECLINED:_ keep `gitleaks-action`; do not move to the CLI binary
- **BL-20** — Dependabot reads a different secret store; missing → empty; re-trigger flips the actor
- **BL-21** — _RESOLVED:_ `flows/bootstrap` installs a per-repo ruleset, proven live
- **BL-22** — Review what *triggers* the full test suite (re-proving the same thing)
- **BL-23** — Audit the tests themselves: still valid, still testing what they claim?
- **BL-24** — §6: the `trigger/` webhook has never received a real request · _open (Slack supersedes, not closes)_
- **BL-25** — Should the backlog / defect register live in GitHub Issues?
- **BL-26** — Factory births repos, but `global-bootstrap` makes a repo *real* — nothing connects them
- **BL-27** — `global-bootstrap`'s registry still points at the personal account
- **BL-28** — A factory-scaffolded repo fails its own `ruff check` out of the box
- **BL-29** — Maintenance escalation against a factory-born repo crashes (missing label)
- **BL-30** — Maintenance green gate runs `pytest src`, but the scaffold puts tests in `tests/`
- **BL-31** — MCP server cold-start is a fixed ~5s import penalty per spawn
- **BL-32** — Static structural guards need an adversarial invariant-injection audit
- **BL-33** — Boundary-guard AST walkers share BL-15's blind spots (remediation list)
- **BL-34** — CI `test` docs-only pre-step fail-safe + skip audit/sbom on docs PRs · _resolved (2026-07-18); skip path not yet live-verified_
- **BL-35** — `architect-review` strands a stale red check-run on every `src/` PR
- **BL-36** — Low-priority cleanups deferred from the BL-2 sprint-41 reviews
- **BL-37** — The Slack inbound surface has never been exercised live

## Open items

### BL-1 — In-loop code review of the Coder's output (Architect / QA persona + gate)
*(added 2026-07-10, from repo owner)*

The default loop is `PM → Architecture → Agile Sprint Breakdown → Coder/IaC`, and
each stage passes a content **gate** (accept / revise / escalate). Today the
Coder's implementation output is gated only by its own `CoderGate` /
`RalphCoderGate` (green-test gate) — there is **no dedicated review of the sprint's
code by an Architect or QA persona** inside the loop. The only architect-level
review is the *dev-workflow* Architect Review (a fresh Opus session reviewing a diff),
which is external to a running loop.

**Idea:** revise the flow so a completed sprint's code is reviewed by an
Architect or a new QA/Reviewer persona before the sprint is accepted — an in-loop
review stage/gate that can `revise` (route rework back to the Coder by blast
radius) or `escalate`, mirroring the existing gate ladder rather than relying
solely on the green-test gate.

**Open design questions (not yet decided):**
- New dedicated `Reviewer`/`QA` persona vs. reusing the Architect persona in a
  review role.
- Where it sits: a post-Coder review **stage** in the default loop, vs. a richer
  **gate** on the Coder stage output.
- What it reviews against: architecture-definition conformance, the Global
  Definition of Done, security invariants, diff quality.
- Interaction with the isolated multi-repo factory (`flows/maintenance` already
  gates on green tests + opens a PR — is the review the PR review, an in-loop
  stage, or both?).
- Cost/latency impact of an extra LLM review stage per sprint.

### BL-2 — Slack integration
*(added 2026-07-10, from repo owner)*

Add Slack integration to loop-engine. Scope intentionally open — candidate
surfaces to define later:
- Notifications: run started / completed / failed / budget-exceeded /
  **awaiting-issue** (the human-escalation pause is the highest-value signal —
  today it only surfaces as a filed GitHub issue).
- A trigger surface (parallel to the existing `trigger/` GitHub webhook): kick off
  a run from a Slack command/message.
- Answering escalations from Slack (route a paused run's questions to a channel
  and fold the reply back), as an alternative to the GitHub-issue round-trip.

**Open design questions:** which direction(s) first (outbound notify vs. inbound
trigger vs. escalation round-trip); credential class (a Slack token is an inbound/
outbound bot credential — distinct from the keyring-only Anthropic key and the
env-var webhook secret, per the `trigger/` precedent); whether it's a new
top-level orchestrator-level caller (sibling of `trigger/`/`flows/`) or an MCP
server.

> ### SCHEDULED: BL-2 gets its planning pass immediately after sprint 36
> *(repo owner, 2026-07-14 — the shape is now known: a **bot control plane**, which is
> effectively all three candidate surfaces above at once. Sprint 36 was already in flight,
> so this waits rather than forking attention.)*
>
> **Three things the planning pass must weigh — none of them obvious from the item above:**
>
> 1. **The existing inbound surface has NEVER received a real request.** That is **[BL-24]**:
>    `trigger/` is proven only against `TestClient` with a faked dispatcher — **no port has ever
>    been bound and no real delivery has ever arrived.** A Slack control plane would be a
>    **second** inbound surface built while the first is still unverified. Decide deliberately
>    whether Slack **supersedes** `trigger/`, **parallels** it, or **waits behind proving it** —
>    "two inbound trigger paths, neither ever run live" is a bad place to land.
> 2. **Slack may DISSOLVE the blocker that parked BL-24.** §6/BL-24 is deferred because it needs
>    a tunnel and a publicly routable address, which neither the devcontainer nor the dev host
>    has. **Slack's Socket Mode needs neither** — the app opens an *outbound* WebSocket, so Slack
>    never has to reach us. That would buy a **live, exercised inbound path without solving the
>    hosting problem at all**, which is strictly better than where the GitHub webhook sits.
>    **Unverified:** a long-lived outbound WebSocket is a connection posture **no existing module
>    holds**, so its fit against the module-boundary and subprocess-surface rules is an open
>    question, not a given. Check it; do not assume it.
> 3. **Third credential class.** A Slack bot/app token is neither the keyring-only Anthropic key
>    nor the env-var webhook secret. `trigger/`'s posture is the precedent to reason *from*
>    (`LOOP_ENGINE_WEBHOOK_SECRET` lives in an env var, **not** the keyring, because it
>    authenticates an *inbound request* rather than an *outbound LLM call*) — but Socket Mode's
>    token is used to *open an outbound connection*, so the precedent may not transfer cleanly.
>
> **Related:** [BL-24] (the unverified inbound surface, and the hosting blocker Socket Mode may
> sidestep), [BL-4] (a Ralph-loop watcher wants somewhere to report *to* — the notify direction
> here is a natural home).

> ### LANDED: pass 1 of 3 — outbound notify (sprint 39, 2026-07-16)
> The planning pass resolved direction-first: **outbound notify shipped first** (FD1), as an
> official `slack_sdk` transport in `tools/slack_io`, **not** an MCP server (FD2). Credentials are
> env vars — `LOOP_ENGINE_SLACK_BOT_TOKEN` / `LOOP_ENGINE_SLACK_CHANNEL` (FD3) — not the keyring,
> confirming the third-credential-class question above. `core/graph_engine.py`'s `run_graph_loop`
> emits through the `core/notify` `Notifier` seam, fail-open at the call site (FD4). Landed across
> T1+T2 (#107), T3 (#112), T4 (this docs pass). **Passes 2–3 — the inbound trigger surface and the
> escalation round-trip — remain open**, and BL-24 (the never-live-verified inbound surface) is
> still unresolved; the planning questions above (supersede/parallel/wait-behind `trigger/`; Socket
> Mode's connection posture against the module-boundary rules) still apply to whichever surface is
> planned next.

> ### LANDED: pass 2 of 3 — inbound trigger (sprint 40, 2026-07-17)
> The Slack **inbound trigger** shipped: `loop-engine slack-listen` runs a Socket Mode daemon that
> turns `/agent-run --budget <n> <requirements>` in `LOOP_ENGINE_SLACK_CHANNEL` into a real run.
> Landed across T1 (listener), T2+T3 (parser + dispatcher, #117), T4+T5 (daemon + CLI, #119), T6
> (this docs pass).
>
> **The three planning questions above are now answered — record, not repeat:**
> 1. **Supersede, not unify (FD1).** Slack **supersedes** `trigger/` as the live inbound path;
>    `trigger/` is **parked**, deliberately not refactored into a shared abstraction, and
>    `slack_control/` shares **no code** with it. We did *not* land "two inbound paths, neither run
>    live" — we landed one live path beside one parked one. See the BL-24 note below.
> 2. **Socket Mode dissolved the hosting blocker, as hoped.** No tunnel, no public address, no bound
>    port — the daemon dials **out**. The connection-posture question (#2's "unverified") **checked
>    out**: the long-lived WebSocket fits the existing rules without relaxing them —
>    `slack_control/` adds **no subprocess surface** (the five sanctioned surfaces are unchanged),
>    writes no files, and imports neither `keyring` nor `slack_sdk`; `tools/slack_io` remains the
>    sole `slack_sdk` importer, function-scoped in both directions.
> 3. **Third credential class confirmed, and it transferred.** `LOOP_ENGINE_SLACK_APP_TOKEN`
>    (`xapp-…`, `connections:write`) joins the pass-1 vars as **env vars, not keyring** (FD3) —
>    despite #3's doubt that the `trigger/` precedent would transfer to a token that opens an
>    *outbound* connection, it did: the discriminator is "not the LLM API call," not the direction.
>
> **Postures worth not re-deriving:** inbound **fails closed** (`build_listener_from_env` /
> `build_daemon_from_env` raise before any socket opens) — the deliberate **inverse** of pass 1's
> inert-by-default notifier; the **FD3 channel guard compares resolved IDs, not names**; `--budget`
> is **required** (fail-closed on the money cap, never `DEFAULT_BUDGET_USD`); dedupe is on
> `envelope_id` (FD6). **Accepted residual risk: channel membership IS the authorization model** —
> anyone who can post in the channel can spend money and run the Coder (threat model, §1).
>
> ### LANDED: pass 3 of 3 — escalation round-trip (sprint 41, 2026-07-18) — **BL-2 COMPLETE**
> The Slack **escalation round-trip** shipped, closing BL-2. With `LOOP_ENGINE_ESCALATION_TRANSPORT=slack`
> a paused run posts its questions to `LOOP_ENGINE_SLACK_CHANNEL`; a human replies in the thread with
> `N: answer` lines (bare text when exactly one question is open); the `slack-listen` daemon folds the
> reply back through the shared `runner.resume_run` seam and posts the outcome to the thread. Landed
> across **T1** (`SlackRef` + `pending_slack` + `RunStatus.AWAITING_SLACK` + schema **v4→v5**, #127),
> **T2** (transport-agnostic `EscalationFiler` seam in `core/engine.py` + `build_escalation_filer_from_env`,
> default=issue, zero behavior change, #128), **T3** (outbound filer + pure `render_question_message`/
> `parse_thread_answers`, #131), **T4** (shared `runner.resume_run` + `cli.resume` refactor + the
> `find_paused_snapshot_by_slack_thread` correlation reader, #133), **T5** (daemon `events_api`
> message-event handling + `dispatch_resume`, #136), and **T6** (this docs pass).
>
> **Postures worth not re-deriving:**
> 1. **Transport selection is env-driven and fail-closed.** `LOOP_ENGINE_ESCALATION_TRANSPORT` defaults
>    to `issue` (byte-for-byte the old GitHub-issue path); `=slack` selects the Slack filer, and
>    `build_escalation_filer_from_env()` **raises at build** if the Slack vars are then unset — a Slack
>    run refuses to start rather than discover at pause time it has nowhere to post (unlike the notifier's
>    cosmetic fail-open, a missing escalation post is load-bearing). Exit code **5** (`AWAITING_SLACK`)
>    joins 0/2/3/4.
> 2. **Correlation is by mtime, not filename.** `find_paused_snapshot_by_slack_thread` takes the
>    latest snapshot *per run dir by mtime* — a snapshot filename's `NN_` prefix is the loop **stage
>    position**, not a write counter, and a blast-radius re-entry can write a lower-numbered file *later*,
>    so a lexicographic "last filename" would resurrect a stale `awaiting_slack` file and double-resume a
>    dead thread (found by the T5 critic-gate; regression test pins the backward-reentry shape).
> 3. **Idempotency on two keys.** `dispatch_resume` dedupes on `envelope_id` (Socket Mode redelivery)
>    **and** `thread_ts` (distinct replies to a still-`awaiting_slack` thread), sharing `dispatch`'s
>    `_run_lock`. **The FD3 channel guard applies to `message` events too, before any state read**, and
>    the bot's own posts are dropped (no self-trigger). No new sink class and no new subprocess surface;
>    `slack_control/` now reads the state tree (only via `tools/state_io`) and resumes via `runner`,
>    still importing no `keyring`/`slack_sdk` and writing no files. Threat model: §1's escalation
>    round-trip boundary.
>
> **BL-2 is done against the sprint plans — all three passes (notify / command / escalation round-trip)
> shipped and are hermetically verified (780 tests, fakes throughout).** They have **not** yet been
> exercised **live** end-to-end: the entire Slack *inbound* surface (pass 2's `/agent-run` command and
> pass 3's round-trip) has only ever run against a fake `WebClient`/listener and synthetic `events_api`
> envelopes — no real Socket Mode session has fired. That deferred live smoke is tracked in **[BL-37]**
> (its analog is **[BL-24]**, the never-run-live `trigger/` webhook, which Slack supersedes but does not
> close). "Complete and hermetically verified" is the honest claim; "proven live" is not yet earned.
> Remaining Slack-adjacent open decision is **[BL-24]**. Low-priority review cleanups from the sprint-41
> passes are collected in **[BL-36]**; the guard-adversary finding from T5 folds into **[BL-33]**.

### BL-3 — Review the prompt-caching implementation (correctness + improvement)
*(added 2026-07-10, from repo owner; **absorbed `DEFERRED_VERIFICATION.md` §1** in sprint 35 Task 6,
2026-07-14, agreed with the repo owner)*

> **§1 (caching + USD budget smoke) is now BL-3's evidence-gathering step, not a separate check.**
> Both need the same scarce thing — a **real Anthropic key and real spend** — and BL-3 cannot
> assess caching without live `Cache R` numbers, which is precisely what §1 produces. Running them
> apart would mean paying for two key-bearing sessions to learn one thing. **Do §1's smoke first
> *within* this item** (it is the measurement); the review below is the interpretation. If every
> `Cache R` is 0, stop and find the invalidator — that finding *is* BL-3's headline, and no further
> review is meaningful until it's resolved.

A focused review of the Anthropic prompt-caching implementation (landed in
`sprints/11_prompt_caching/`, primarily in `tools/llm/client.py` with rate
accounting in `tools/llm/pricing.py`). Two aims:

**a. Confirm correct implementation.** Verify caching actually engages and is not
silently invalidated: the cached system prefix must be **byte-identical across
calls** (state-derived, immutable content only — findings/sprint plans/revision
history belong in the *user* turn, never the cached prefix, per the guard noted in
`sprints/DEFERRED_VERIFICATION.md` §1). Check `cache_control` breakpoint placement,
that the prefix clears Sonnet 5's ~2048-token minimum cacheable size on the
Coder/Architect stages, and that `Cache R` (cache-read) is nonzero on tool-loop
iterations and revision retries rather than always 0 (the tell-tale of a silent
invalidator). Confirm cost accounting attributes cache-read vs. cache-write tokens
at the right rates.

**b. Look for improvement opportunities.** e.g. additional/earlier cache
breakpoints, widening the cached prefix, caching across stages where the prefix is
stable, cache-TTL/ordering considerations, and any cost-model refinements. Nothing
designed yet.

**Notes / where to look:** `tools/llm/client.py` (cache-control assembly + system
blocks), `tools/llm/pricing.py` (rate table, incl. the introductory-rate caveat
through 2026-08-31), `sprints/DEFERRED_VERIFICATION.md` §1 (the caching + USD smoke
and the byte-identity guard). Part of this is a **live** check needing a real key
(the mocked suite pins exact transport call counts but cannot show real cache hits)
— fold it into the same daemon-bearing host session as the other deferred smokes.

### BL-4 — Ralph loop watcher: progress/liveness detection for runaway inner tool loops
*(added 2026-07-10, from repo owner — surfaced by the Phase-6 V2 host run)*

The Coder's inner tool loop (`LLMClient.run_tool_loop`) is bounded only by two
*blunt* limits: the USD budget (the real guardrail — every iteration is a metered
API call that re-checks the ledger) and a finite iteration backstop
(`DEFAULT_MAX_TOOL_ITERATIONS`, raised 12→40 when a legitimately-progressing V2
`truncate` increment was guillotined at 12). Neither can distinguish a loop that is
**making progress but needs more turns** from one that is **stuck** (re-reading the
same files, re-applying the same failing edit, oscillating between two states). The
engine has a progress check at the *outer* gate-cycle level (the identical-findings
guard, `core/engine.py`), but **nothing watches the inner tool loop** — which is
exactly where V2 stalled.

**Idea:** a liveness/progress watcher on the inner loop that detects a *non-progressing*
loop directly and cuts it (fail the increment honestly → Ralph's existing no-output
degradation → re-select/escalate), rather than relying on an iteration count as a
stand-in for "stuck." This targets the actual runaway failure mode while letting
genuine multi-step work run as long as it is still changing something.

**Open design questions (not yet decided):**
- What counts as "progress": working-tree/file deltas between iterations, the set of
  distinct tool calls (repeated identical `read_file`/edit args = no progress),
  test-result deltas, edit-application success/failure, or a combination.
- Oscillation detection (A→B→A→B) vs. simple no-change-for-N-iterations.
- Where it lives: inside `run_tool_loop` (generic, covers every persona) vs. a
  Ralph-specific wrapper (Ralph is the surviving Coder post-Phase-6 Task 4).
- Relationship to the iteration backstop: does the watcher **replace** the cap, or
  do they coexist (watcher as primary, generous cap as a final finite backstop)?
- Avoiding false positives on legitimately slow-but-progressing work (large reads,
  many small correct edits) and on intentionally repeated tool calls.

**Notes / where to look:** `tools/llm/client.py::run_tool_loop` (the inner loop +
the `DEFAULT_MAX_TOOL_ITERATIONS` backstop and its rationale comment),
`personas/coder_iac/ralph.py::_run_increment` (the `ToolLoopExceededError` →
no-output degradation this would feed), `core/engine.py` (the outer identical-findings
progress guard this mirrors at a different level).

### BL-5 — Per-persona model routing + resolution token budget review
*(added 2026-07-11, from repo owner)*

Today **every persona runs `claude-sonnet-5`** — both the classic hardcoded
`DEFAULT_MODEL` constants (`personas/*/persona.py`) and the declarative configs
(`personas/declarative/configs/{pm,architecture,sprint_breakdown}.yaml`, all
`model: claude-sonnet-5`). There is no Opus anywhere in the product. Two related
questions about that per-call configuration:

**a. Route the Architect (and maybe PM / Sprint Breakdown) persona to Opus.** The
dev-workflow layer already runs Architect=Opus / Coder=Sonnet (see CLAUDE.md
"model routing") on the theory that *deciding what to build* wants the stronger
model while *executing a defined spec* does not. The **product's own** loop does
not mirror that — its Architecture stage runs Sonnet. Hypothesis: a stronger
initial architectural design (and sprint breakdown) yields better, more
convergent downstream Coder loops, worth more than its marginal cost. **Unproven
— it may not move the needle;** treat as an experiment with a before/after on
Coder convergence + total run cost, not a foregone change.
- **Cost:** Opus 4.8 (`claude-opus-4-8`) is **$5/$25 per MTok** vs Sonnet 5's
  **$3/$15** — ~**1.67× at list** (up to ~2.5× vs Sonnet's introductory $2/$10
  through 2026-08-31). The Architecture stage is small (~$0.13 in the V2 run-#3
  cost-summary), so Opus-ifying *just* it adds only ~$0.06/run; extending to PM +
  Sprint Breakdown scales that up but all three upstream stages together were
  ~$0.29/run.
- **Hard dependency (do this first):** `tools/llm/pricing.py`'s `RATES` table has
  **only** `claude-sonnet-5`, and `_rates_for` raises `UnknownModelError` on any
  other model. Routing *any* persona to Opus **requires adding `claude-opus-4-8`
  rates ($5/$25 per MTok) to `RATES`** — otherwise the run crashes in cost
  accounting the first time the Opus stage returns. Confirm the introductory-rate
  caveat handling (`pricing.py` already notes Sonnet's intro rates) applies or is
  N/A for Opus.
- **Where to change the model:** the forward-looking (Phase-6) path is the
  declarative `configs/architecture.yaml` `model:` field (and pm/sprint_breakdown
  if extending); the classic `DEFAULT_MODEL` constants are being deleted in
  sprint 27 Task 3–4, so don't invest there.
- **Open questions:** which stages (Architect only, or PM + Sprint Breakdown too);
  per-stage `effort` (`output_config.effort` is not currently threaded — see the
  claude-api skill; Opus/Sonnet 5 both support `low..max`, and `xhigh`/`high` is
  the sweet spot for hard reasoning); how to measure the "better downstream loops"
  payoff objectively.

**b. Revisit `RESOLUTION_MAX_TOKENS = 2048`.** The resolver-ladder answer pass
(a persona resolving an escalated downstream question) is capped at **2048**
output tokens — `personas/architecture/persona.py:13`, `personas/pm/persona.py:16`,
and the declarative `resolution.max_tokens` in `architecture.yaml` / `pm.yaml`.
That is ~**31× smaller** than the **64000** the main generation passes get
(`MAX_TOKENS`), and PM's own extraction pass gets 4096. A substantive
architectural resolution that runs past 2048 tokens hits `max_tokens` →
`TruncatedResponseError` → the stage fails honestly rather than returning a
half-answer. **Unclear whether 2048 is ever the binding constraint in practice**
(short Q→A resolutions may never approach it), but the asymmetry vs the 64000
generation budget is worth a deliberate look — raise it (e.g. to match the
extraction 4096, or higher) if real resolutions are getting truncated. A host
run that forces a real escalation→resolution round-trip (V3 territory) would show
whether resolutions actually approach the cap.

**Notes / where to look:** `personas/declarative/configs/*.yaml` (the live
per-persona `model` + `max_tokens`), `personas/*/persona.py` (`DEFAULT_MODEL`,
`RESOLUTION_MAX_TOKENS`, `EXTRACTION_MAX_TOKENS`, `MAX_TOKENS`),
`tools/llm/pricing.py` (`RATES` — the Opus-rate prerequisite), and the claude-api
skill / `shared/models.md` for current Opus 4.8 vs Sonnet 5 pricing + `effort`.

### BL-6 — Give Claude its own GitHub identity (machine user / GitHub App)

**Why:** the `gh` CLI in this devcontainer authenticates as **`Seuss27`** — the repo
owner's own account. So when Claude opens a PR and posts an Architect Review on
it, GitHub renders it as *the owner reviewing their own PR*. Today this is patched by
convention: every posted review is prefixed `**Opus/Architect HITL review
(automated)**` (a frozen string — see `.ai/context/workflow.md`) so authorship is
unambiguous in the text.
That is a *declared* attribution, not a *real* one.

**Why it eventually matters:** the PR gate exists so that a human merge is the
approval. Shared identity means "who reviewed this" and "who approved this" are not
independently checkable facts — they are conventions Claude is trusted to honor. That
is acceptable while the human reads every PR, but it does not survive contact with
branch protection ("require 1 approving review" is meaningless if the bot and the human
are the same login) or with any future audit of the factory's own change history.

**Shape:** a GitHub App installation token (preferred — scoped, revocable, renders as a
distinct bot author) or a dedicated machine user. Interacts with the GPG signing story:
commits are signed by the owner's forwarded host agent
(`.devcontainer/gpg-forward.sh`), so a separate *review* identity is separable from —
and easier than — a separate *commit* identity. Do the review identity first; the
commit identity is a bigger question.

**Not urgent.** GitHub already refuses self-approval, so the dangerous failure (Claude
approving its own PR) is blocked by the platform, not just by convention. This is about
attribution quality, not a live hole.

### BL-7 — The PM stage has no channel to ask a human a question

**Why:** the PM can *detect* a requirements problem and has no way to *raise* it. Found on
the V3b host run (2026-07-12) as finding **R9**. It was originally recorded in
`sprints/DEFERRED_VERIFICATION.md`; sprint 27's Task 9 retired that file's Phase-6
sections and folded the V-run findings into `docs/migration_roadmap.md`'s Phase 6 row,
which is now the record of point for R9.

Given a deliberately unsatisfiable requirements doc (entries both immutable and erasable;
storage both memory-only and durable across hardware failure), the PM **correctly
identified every contradiction** and wrote them into its `risks_and_assumptions` field — and
the gate **ACCEPTed anyway**, sending the pipeline off to architect a service whose own spec
says the requirements are impossible.

Three things compose to make PM→human escalation unreachable for *semantic* problems:

1. `personas/pm/critic_gate.py::CriticGate` is **purely structural** — `critic.review()` is
   blank/vague-field checks with **no LLM**, and `check_internal_consistency` tests only
   whether `in_scope` string-equals `out_of_scope`.
2. The PM's artifact contract is **JSON** with no `open_questions` key
   (`open_questions_for_architect` was retired in State schema v2).
3. `personas/declarative/configs/pm.yaml` sets **`extract_open_questions: false`**, disabling
   the `ArtifactGate` ESCALATE-on-`## Open Questions` channel that the Architect and Sprint
   Breakdown stages *do* use — in the same V3b run, the Architect raised 6 questions and
   escalated correctly.

So the only reachable PM escalation is `escalate_on_exhaustion` after 4 *structural* REVISE
cycles — "the model kept leaving fields blank", a model-failure trigger, not a
requirements-ambiguity one. The stage whose whole job is to interrogate requirements is the
one stage that cannot ask.

**Shape:** either give the PM an open-questions channel (a spec field the gate reads, or
`extract_open_questions: true` plus a prompt that populates it), or make the PM gate
semantic (an LLM critic that can fail a self-contradictory spec). The first is cheap and
deterministic; the second is the honest fix. Note the PM stage already has `resolvers=[]` +
`escalate_on_exhaustion=True`, so an escalation routes straight to the human — the ladder is
ready, the question just can't get onto it.

**Not urgent, but not cosmetic:** the failure is silent, and it fires precisely when the
requirements are worst.

**Notes / where to look:** `personas/pm/critic.py`, `personas/pm/critic_gate.py`,
`personas/declarative/configs/pm.yaml`, `core/gates.py::extract_open_questions`.

### BL-8 — Stop using process CWD as an isolation mechanism

**Why:** found during Task 10 (sprint `27_phase6_flip_block`), fixing the Opus HITL
review findings on PR #34 (F3/F6). `worktree_run`'s `_ORIGIN_CWD`/`state_io`'s
`_STATE_ROOT` were plain module globals mutated via `os.chdir` bracketing — safe only
because the orchestrator ran one loop at a time. The trigger surface
(`InProcessDispatcher`) breaks that assumption: it dispatches concurrent
`asyncio.to_thread(runner.run_new)` calls, and two different issues' runs sharing one
process CWD is a real hazard, not a theoretical one — the R8 leak (escalation issues
filed on loop-engine instead of the managed repo) returns the moment two runs'
`worktree_run`s are open at once, because `os.chdir` is inherently process-global no
matter what wraps it.

Task 10 fixed the *symptom* two ways: `_ORIGIN_CWD`/`_STATE_ROOT` are now
`contextvars.ContextVar`s (so reads/resets no longer cross between concurrently-running
`asyncio.to_thread` workers — each gets its own copied context), and
`InProcessDispatcher` gained a lock serializing actual loop execution (so the
`os.chdir` race itself is unreachable, not just less likely). Both are honest
mitigations, not the real fix — the review was explicit that `os.chdir` staying
process-global is "pre-existing and concurrency-hostile."

**Shape:** thread the tree path explicitly through the call chain (engine, personas,
tools) instead of relying on `Path.cwd()` to communicate "which run's tree is this."
That likely means every tool that currently reads `Path.cwd()` implicitly (artifact
writes, the coder tools, `resolve_repo_slug`'s default) takes an explicit root/cwd
argument instead. A bigger refactor than Task 10's scope — the dispatcher lock buys
time by making the factory single-loop-at-a-time in practice, at the cost of the
throughput it isn't currently using anyway.

**Not urgent while the dispatcher lock holds**, but it is the load-bearing reason the
lock can never safely come out again until this lands.

**Notes / where to look:** `tools/worktree/manager.py::worktree_run`/`origin_cwd`,
`tools/state_io/writer.py::state_root`, `trigger/dispatch.py::InProcessDispatcher`,
`runner.py::run_in_tree` (the other CWD-dependent entrypoint, used by
`flows/maintenance`).


### BL-9 — Retire the implicit-CWD destination from the issue path's remaining surfaces

**Why:** the five non-blocking notes from the Opus HITL review of PR #34 (2026-07-12,
sprint `27_phase6_flip_block`, approved). Task 8/Task 10 fixed R8 — escalation issues
for managed repos were being filed on loop-engine, because `gh` derived the destination
from an ambient CWD that, inside a run's worktree, resolved to loop-engine itself. The
*write* side is now explicit (`default_issue_filer` resolves `worktree.origin_cwd()` and
refuses to file without a named destination — no `repo=None` fallback anywhere). These
are the surfaces that fix did not reach.

**Items, highest value first:**

1. **`resume --from-issue` still defaults to a CWD-derived destination** and merely
   *echoes* what it guessed (`cli.py`, the `read_repo = repo or resolve_repo_slug(Path.cwd())`
   branch). This is the same class of defect the sprint exists to kill, one surface over:
   an implicit CWD-derived destination that silently does the wrong thing. The review
   established there is genuinely **no oracle** here — given only an issue number and a
   CWD, two same-numbered issues in two repos are indistinguishable, because each is
   internally consistent — so the only real fix is to *refuse to guess*: require an
   explicit `--repo` (or `--snapshot`, which is already authoritative). An echo is a
   defense only when a human is reading, and this CLI runs in scripts.
   `test_cli_resume_from_issue_silently_resumes_a_same_numbered_wrong_repo_issue`
   already documents the hole honestly — it asserts exit 0 and the wrong run resumed.

2. **`IssueDestinationUnresolvedError` escapes as an uncaught traceback → exit 1**, so
   "could not name a destination for the escalation issue" is indistinguishable from a
   crash. Sprint 27 just added exit code **4** on the argument that a distinct outcome
   deserves a distinct code; this is exactly such an outcome. (The run's work is *not*
   lost — `_pause_for_issue` persists the `AWAITING_ISSUE` snapshot before filing, and
   `_start_index_for` resumes a paused run at its paused stage, so `run --resume-from`
   recovers it. Only the exit contract and the traceback are wrong.)

3. **`resolve_repo_slug` catches only `CalledProcessError`** (`tools/repo_io/github.py`).
   `FileNotFoundError` (no `gh` on PATH) and `subprocess.TimeoutExpired` still cross the
   module boundary raw — the precise leak `RepoNotResolvableError` was introduced to
   stop, and the reason `issue_io` can catch it without importing `subprocess`.

4. **`repo_from_issue_url` raises a bare `ValueError`** (`tools/issue_io/github.py`) on a
   non-canonical `pending_issue.url`, surfacing from `cli.resume` as a traceback rather
   than a `typer.BadParameter`.

5. **The trigger surface's escalations land on loop-engine, not the requesting repo.**
   `runner.run_new` opens `worktree_run` in the loop-engine checkout, so `origin_cwd()`
   resolves there, and `RunRequest.repo_full_name` — the managed repo whose webhook
   started the run — never reaches the filer. **Not a regression** (the old implicit path
   landed in the same place) and arguably correct, since `run_new` does not clone the
   managed repo, so loop-engine genuinely *is* the tree it operates on. But `CLAUDE.md`
   now claims **every** entrypoint (`cli`, `runner.run_new`, `run_in_tree`, the trigger
   surface) "is correct without threading a cwd", and for the trigger that holds only in
   that narrow sense. Either qualify the claim or close the gap — do not leave the docs
   stronger than the code.

**Relationship to [BL-8]:** BL-8 is the structural fix (stop using process CWD as an
isolation mechanism at all); items 1 and 5 here are instances of the same root cause and
would largely dissolve if BL-8 lands first. Items 2–4 are independent error-handling
cleanups and can go any time.

**Notes / where to look:** `src/loop_engine/cli.py` (`resume`),
`src/loop_engine/tools/issue_io/mcp_client.py`, `src/loop_engine/tools/issue_io/github.py`,
`src/loop_engine/tools/repo_io/github.py`, `src/loop_engine/trigger/dispatch.py`,
`CLAUDE.md` (the `tools/issue_io` boundary bullet). The full review reasoning is on
PR #34 (`gh pr view 34 --comments`).

### BL-10 — A bad PR title permanently starves the heavy CI chain
*(added 2026-07-12, found during the Opus HITL review of PR #39, sprint 32)*

**Why:** two individually-correct guards in `.github/workflows/ci.yml` compose into a hole
that lets a PR reach an all-green/neutral state **having never run lint or the test suite**.

The sequence, observed live on PR #39:

1. The PR was opened with a 78-character title; `pr-title` enforces a 72-char limit, so it
   **failed**.
2. `lint` is deliberately gated on it (`needs: pr-title`, `if: needs.pr-title.result ==
   'success' || == 'skipped'`) as a **fail-fast** measure — a bad title shouldn't burn
   runner minutes. With `pr-title` failing, `lint` was **skipped**.
3. `format-check` → `test` → `secrets-scan`/`dependency-audit` → `sbom` all reach `lint`
   through `needs:`, so the entire heavy chain skipped with it.
4. **Fixing the title cannot recover this.** A title edit fires `edited`, and `lint` carries
   `if: github.event.action != 'edited'` — equally deliberate, so that editing prose doesn't
   re-run the suite on an unchanged tree. So `pr-title` flips green while `lint`/`test` stay
   `skipped` **forever**.

Net: `test` reports `skipped`, not `failure`. GitHub generally treats a skipped required check
as satisfied, so nothing blocks the merge. The suite never ran, and the PR looks fine.

This is the same species of failure `hitl-review.yml`'s own preamble was written about — "the
suite passed, CI passed, and the check that would have caught it was simply not run" — except
here it's the suite itself that goes missing, and no amount of reviewer diligence surfaces it,
because the checks page shows no red.

**Recovery (what was done for #39):** fire a non-`edited` event. Close + reopen (`reopened`)
is strictly better than pushing a commit (`synchronize`), because it preserves the head SHA
and therefore does not invalidate the `architect-review` binding, which is pinned to an exact
commit.

**Shape:** the `edited`-skip needs to be conditional on the heavy chain having *already run
successfully on this SHA*, rather than assuming it did. Options: (a) let `edited` re-run the
chain when the prior conclusion for the SHA was `skipped`; (b) drop the `needs: pr-title`
fail-fast gate so a bad title never suppresses the suite in the first place (costs a few
runner minutes on a bad title — the fail-fast saving is small and this is what it bought);
(c) make `pr-title` non-blocking for the chain and merely a required check in its own right.
(b) is the cheapest and removes the composition entirely.

**Notes / where to look:** `.github/workflows/ci.yml` — the `pr-title` job, the `lint` job's
`if:` (the `!= 'edited'` clause and the `needs.pr-title.result` allowlist), and the `on:
pull_request: types: [..., edited]` trigger. The rationale comments on both guards are worth
reading before changing either — each is there for a real reason; it's their *interaction*
that's wrong.

**Resolved by sprint 33** (`sprints/33_ci_title_starvation/sprint_plan.md`). This entry's
diagnosis was correct but incomplete in two ways the planning pass found:

- **FD2 — a second, independent starvation path through `concurrency`.** `github.ref` for a
  `pull_request` event is `refs/pull/N/merge`, identical across `opened` and `edited`, and
  `ci.yml`'s `concurrency` group is keyed on it with `cancel-in-progress: true`. Editing the
  title *while the suite is running* — even a title that was **always valid** — cancels the
  in-flight run; the replacement run then hits `if: != 'edited'` and skips the heavy chain.
  This entry's preferred option (b), dropping `needs: pr-title`, does **not** close this path:
  the killer is the shared concurrency group plus the `edited` guard, not the `needs:`.
- **FD3 — a green test was pinning the bug in place.** `test_lint_job_gates_on_pr_title_to_fail_fast`
  asserted the exact `needs`/`if:` wiring that caused the starvation, so any fix had to make it
  fail before replacing it — not soften it into something that passed either way.

The actual fix was a **split**, not a rewiring of `needs:`: `pr-title` moved to its own
workflow, `pr-title.yml`, with its own trigger list and its own concurrency group. `ci.yml`
lost the `edited` trigger entirely (closing FD2) and `lint` lost both `needs: pr-title` and its
`if:` block, so no job in `ci.yml` carries an `if:` and none can ever report `skipped` — the
invariant sprint 33 pins by test, structurally, rather than pinning the new wiring.

---

### BL-11 — None of the "required" checks are actually required; every CI gate is advisory
*(added 2026-07-12, found during the Opus HITL review of PR #43, sprint 33 — while trying to
confirm FD5)*

**Why:** this repo has **no branch protection and no rulesets at all**. Every check the docs
call *required* — `lint`, `format-check`, `test`, `secrets-scan`, `dependency-audit`, `sbom`,
`pr-title`, `architect-review` — is **computed and reported, but enforces nothing**. A red PR
can be merged. `feat/mcp-langgraph-migration` and `main` can be pushed to directly, and
force-pushed.

Evidence (2026-07-12):

- Settings → Branches shows *"Classic branch protections have not been configured."*
- `GET /repos/glunk-works/loop-engine/rulesets` → `[]`
- `GET /repos/glunk-works/loop-engine/rules/branches/feat%2Fmcp-langgraph-migration` → `[]`
  — this is the **effective** rules endpoint, so an org-level ruleset would appear here. None does.
- PR #43's `reviewDecision` is empty: no required reviews either.

**This is the fail-open `mergeStateStatus: CLEAN` hides.** `CLEAN` means "no rule is being
violated," which is trivially true when no rule exists. Sprint 33's Task 5 read `CLEAN` as
corroboration that `pr-title` still resolved as a required check; it corroborated nothing. Any
future reasoning that treats `CLEAN` as evidence of enforcement is making the same mistake.

**The sharp edge is `architect-review`, not `pr-title`.** `CLAUDE.md` asserts in bold that the
Opus review *"is a CI gate, not a courtesy"* — that a PR touching `src/` **fails** until a
review is posted. The workflow really does compute that failure. But a failing check blocks no
merge, so the gate is precisely the thing it was built to replace: **a convention that works
only as long as nobody skips it.** It was introduced *because* a convention got skipped
(sprint 27 Task 8 shipped an R8 fix that covered `cli.py` and left every fresh-run path filing
issues on the wrong repo — the review that would have caught it was skipped and nothing
noticed). Today that gate has the same failure mode it was created to close.

BL-10 reads differently in this light too: "a starved suite merges green and untested" was
true, but the suite was never *blocking* the merge in the first place.

**Shape:** add a repository ruleset on `main` and `feat/**` requiring the eight status checks
above plus a PR before merging. Then FD5 (below) becomes load-bearing for real — a required
check is matched by **check-run name**, so the `pr-title` job id and the absence of a `name:`
override are what make the required check resolvable at all
(`tests/test_ci_config.py::test_pr_title_workflow_defines_the_frozen_job_id` pins both).

**Notes / where to look:** this is a **GitHub settings change, not a code change** — nothing in
this repo can assert it, which is exactly why it went unnoticed for the whole life of the CI
config. Claude is 403 on branch protection and cannot verify or set it; a human must confirm it
in the UI. Until then, treat every "must pass" in `CLAUDE.md`,
`sprints/GLOBAL_DEFINITION_OF_DONE.md`, and `.ai/context/workflow.md` as **aspirational**.

**Resolved 2026-07-12 (sprint 33), by configuration rather than code.** The repo owner granted a
temporary `Administration: write` scope on the fine-grained PAT; the settings below were applied
and the scope was then revoked. Confirmation that the diagnosis was right, not merely inferred
from a screenshot: with the scope live, `GET /repos/.../branches/main/protection` returned **404
"Branch not protected"** — not the earlier 403. There genuinely was nothing there.

**Ruleset `protected-integration-branches`** (id `18847725`), `active`, targeting
`refs/heads/main` + `refs/heads/feat/**`, `bypass_actors: []` (it binds admins too):

- `required_status_checks` — all eight: `lint`, `format-check`, `test`, `secrets-scan`,
  `dependency-audit`, `sbom`, `pr-title`, `architect-review`.
  `strict_required_status_checks_policy: false` — deliberately **not** requiring branches to be
  up to date with base, which would force a merge-of-base plus a full CI re-run on every PR
  whenever base moves (exactly the churn that produced this sprint's silent zero-CI conflict).
- `pull_request` — a PR is required to merge, with `required_approving_review_count: 0`.
  **The zero is deliberate:** GitHub forbids approving your own PR, and this is a solo repo, so
  requiring even one approval would deadlock every PR. The Architect review is enforced by the
  `architect-review` **check**, not by GitHub's review counter.
- `non_fast_forward` + `deletion` — no force-pushes, no branch deletion.

`sprint/**` branches are deliberately **unruled** — they must stay freely pushable.

**Also enabled:** `secret_scanning` and `secret_scanning_push_protection`. The `secrets-scan`
gitleaks job is *post-hoc* — on a **public** repo it reports a leaked key only once it is already
public, when rotation is the sole remedy. Push protection rejects the push. Given this codebase's
central rule is that the Anthropic key lives only in the OS keyring, that is the modeled threat,
and CI was catching it one step too late. (`secret_scanning_validity_checks` and
`secret_scanning_non_provider_patterns` accept the PATCH but do not take — they are gated behind
GitHub Advanced Security, not the free public tier.)

**Already correct, verified, no change:** `allow_auto_merge: false` (matches the no-merge-verb
rule), `delete_branch_on_merge: true`, Actions `default_workflow_permissions: read`,
`can_approve_pull_request_reviews: false`, Dependabot alerts + security updates on. And
`squash_merge_commit_title: PR_TITLE` — **load-bearing for BL-10**: on the default
`COMMIT_OR_PR_TITLE`, a single-commit PR takes its subject from the *commit*, so the enforced PR
title would never reach the branch and `pr-title` would gate nothing that survives.

**Left open, deliberately — candidates for a follow-up sprint. Resolved by sprint 34
(`34_ci_supply_chain_hardening`):**

- **Actions supply chain — resolved.** `ci.yml`'s four actions (`actions/checkout`,
  `actions/setup-python`, `actions/upload-artifact`, `gitleaks/gitleaks-action`) are now pinned
  to commit SHAs with a version comment, `tests/test_ci_config.py` structurally asserts every
  `uses:` in every workflow is a 40-hex SHA (not just today's four), and Dependabot's
  `github-actions` ecosystem (weekly) keeps the pins from going stale. `sha_pinning_required` is
  a human settings toggle applied **after** this merges (ordering is load-bearing — flipping it
  first rejects the very PR carrying the fix).
- **Three merge strategies, one convention — resolved.** `allow_merge_commit: false` +
  `allow_rebase_merge: false` is a human settings action carried by sprint 34's human-actions
  list; no ordering constraint.
- **Drift detection — resolved, without the scope this entry proposed.** `FD1` (sprint 34
  planning, verified live): the **effective-rules** endpoint
  (`GET /repos/.../rules/branches/main` — the same one whose empty `[]` was this entry's original
  evidence of absence) returns all four rule types **and** all eight required check names with
  **no** `Administration` scope at all. The `Administration: read` grant this entry recommended
  is **not needed** and must not be requested — leaving the recommendation standing would invite
  a future session to widen scope for nothing. `FD2`: the drift check is a **scheduled workflow**
  (`.github/workflows/ruleset-drift.yml`) plus a `/resume` preflight, deliberately **not** a 9th
  required check — a required check is only required *because* the ruleset says so, so deleting
  the ruleset would silently un-require the very check watching it, precisely on the failure it
  exists to catch.

---

### BL-12 — `main` is 106 commits behind and cannot currently pass its own ruleset
*(added 2026-07-13, found live while starting sprint 34 Task 4 — the ruleset-drift workflow's
PR is supposed to base off `main` per FD3)*

**Why:** Task 4's PR must base off `main`, not `feat/mcp-langgraph-migration` (FD3 — a scheduled
workflow only ever fires from the default branch). Before opening it, checked `main`'s actual
state rather than assuming it mirrors the integration branch. It doesn't:

- `git log origin/main..origin/feat/mcp-langgraph-migration` → **106 commits**; the reverse is
  **0**. The entire MCP/LangGraph migration — everything since roughly sprint 09 — has never
  merged to `main`.
- `main`'s `.github/workflows/` contains **only `ci.yml`** (6 jobs: `lint`, `format-check`,
  `test`, `secrets-scan`, `dependency-audit`, `sbom`). **`pr-title.yml` and `hitl-review.yml`
  don't exist on `main` at all** — they were introduced by sprints 33/26+ on the integration
  branch and never backported.

**The trap this creates:** the `protected-integration-branches` ruleset requires all **eight**
checks — including `pr-title` and `architect-review` — on `main` too (confirmed live, same call
as FD1). A PR against `main` right now would need those two checks to report, but no workflow on
`main` produces a check-run with either name. GitHub shows a required check with no matching
check-run as **"Expected — waiting"**, indefinitely — not a red X, a silent stall. Any PR based
on `main` (Task 4's included) would be **permanently unmergeable** the moment it's opened, and
nothing would say why unless someone thought to check. This is BL-11's exact failure shape
(*a control that looks present and is inert*) produced by a different mechanism.

**Shape (not yet decided — needs a human call, out of scope for a sprint task to resolve
unilaterally):**
- **(a)** Ship `pr-title.yml` + `hitl-review.yml` to `main` in a small, narrow, mechanical PR so
  `main`'s produced checks match what its own ruleset already demands. Unblocks Task 4 without
  touching the larger migration question.
- **(b)** Decide when/whether to merge `feat/mcp-langgraph-migration` into `main` outright — the
  bigger question this finding surfaces but does not answer. `.ai/context/workflow.md` already
  notes the integration branch merges to `main` as a **merge commit**, never a squash, when that
  happens.

**Status: resolved 2026-07-13.** Shape (a) was taken: PR #46 backported `pr-title.yml` +
`hitl-review.yml` to `main` verbatim (both self-referentially resolved on the PR that introduced
them — live proof, not assumption). Task 4's PR (#47) followed, merged, and its two post-merge
acceptance criteria were live-verified: a manual `workflow_dispatch` run confirmed
`GITHUB_TOKEN` (with only `contents: read` — no scope escalation needed) actually read the
effective-rules endpoint and saw all 8 checks; a second dispatch on a throwaway branch with a
fake 9th check name confirmed the workflow goes red for the right reason, and that branch was
deleted without merging. Shape (b) — the migration merge itself — remains open; see BL-13.

---

### BL-13 — Sprint 34's squash-only settings action conflicts with the documented one-time
merge-commit landing for `main`
*(added 2026-07-13, found by the repo owner while reviewing sprint 34's human-actions list)*

**Why:** sprint 34's human-actions list (`sprints/34_ci_supply_chain_hardening/sprint_plan.md`)
says to set `allow_merge_commit: false` + `allow_rebase_merge: false` repo-wide, to close the
"three merge strategies, one convention" item BL-11 left open. But `.ai/context/workflow.md`
already documents a **one-time exception**: `main` stays untouched until the whole migration
lands as **one final PR**, and that PR merges as a **merge commit**, deliberately never a
squash — squashing it would collapse the entire migration's history into a single commit.
`allow_merge_commit` is a repo-wide GitHub setting; it does not distinguish PR by PR. Flipping
it off now would silently disable the merge-commit button for that future PR too, and nobody
re-checks a repo setting at the moment a plan from months earlier finally executes — the same
failure shape as BL-11/BL-12 (a control quietly contradicting a documented plan), just with the
contradiction pointed the other way (a *tightening* action breaking a *planned exception*
instead of a weakening going unnoticed).

**Shape:** set `allow_rebase_merge: false` now (nothing in this repo uses rebase merges).
**Hold off on `allow_merge_commit: false`** until after `feat/mcp-langgraph-migration` merges to
`main` as its one-time merge commit, then disable it. Simpler than the alternative (flip both
now, remember to re-enable-then-disable around the migration merge) because it has no
"remember to do X later" step to forget.

**Status: resolved 2026-07-14 (sprint 35, Task 5).** The plan held. `allow_merge_commit` stayed
enabled across the migration merge — PR #58 landed on `main` as merge commit `d2135e7`, two
parents, 113 commits of history preserved — and was set to `false` immediately afterwards.
Verified live post-merge: `allow_merge_commit: false`, `allow_rebase_merge: false`,
`allow_squash_merge: true`. That closes both this item and the "three merge strategies, one
convention" gap BL-11 left open: the repo is now squash-only, and the one-time exception is spent
rather than standing. The deferral was the right call precisely because it had no
"remember to re-enable X later" step to forget — the setting was never wrong at any point in the
window.

---

### BL-14 — Task 1/2's SHA pins and Dependabot entry were inert: Dependabot reads config only
from `main`
*(added 2026-07-13, found live while answering a question about how action-version updates
would work going forward)*

**Why:** GitHub Dependabot version updates read `.github/dependabot.yml` **only from the
repository's default branch** (`main`) — never from a feature branch, and `target-branch:`
controls where the resulting PR lands, not where the config is read from. Sprint 34's Task 1
(SHA-pinning `ci.yml`'s actions) and Task 2 (the `github-actions` Dependabot ecosystem entry)
both landed only on `feat/mcp-langgraph-migration` (#45). Checked live rather than assumed: as
of that merge, `main`'s `dependabot.yml` still had only the `pip` entry, and `main`'s `ci.yml`
still had all 13 actions on floating tags. The mechanism Task 2 exists for — keeping the pins
from freezing on a stale, possibly-vulnerable commit — was sitting inert, read by nothing, on
the one branch where active development (`feat/mcp-langgraph-migration` and every `sprint/**`
cut from it) actually happens. Same failure shape as BL-12 (`pr-title.yml`/`hitl-review.yml`
inert on `main`), this time for the control meant to maintain a different control.

**Resolved 2026-07-13, same shape as BL-12 (backport, not a design change).** PR #49 pinned
`main`'s own `ci.yml` `uses:` lines to the identical commit SHAs already verified on
`feat/mcp-langgraph-migration`, editing only `uses:` lines and leaving `main`'s own `on:`/
concurrency block (which already differs from the migration branch's — no `feat/**` push
trigger, no explicit `pull_request.types`, no `concurrency:` block) untouched, matching the
narrow-scope discipline the original Task 1 used. Also added the `github-actions` entry to
`main`'s `dependabot.yml` verbatim. CI on that PR is the live proof the SHAs resolve under
`main`'s own trigger config, not just the migration branch's.

**The underlying pattern — closed 2026-07-14 by the migration merge (sprint 35, Task 5).** The
branch-topology gap behind this (config living on `feat/mcp-langgraph-migration` doesn't take
effect until it reaches `main`) was structural, not a one-time bug: BL-12, BL-13 and BL-14 are
three instances of the same shape, all found in a single week, and each was backported narrowly
as found. **The generator is now gone.** PR #58 merged the migration into `main` (merge commit
`d2135e7`), and `feat/mcp-langgraph-migration` is retired — there is no longer a second
long-lived branch for a default-branch-only control (Dependabot config, scheduled workflows,
branch-protection-adjacent settings) to sit inert on. Development happens on `main`, so a control
committed to the branch you are working on **is** the control that runs.

Retained as a live lesson, because the class outlives this instance: **a control that only
functions on the default branch is inert everywhere else, and nothing tells you.** If a
long-lived branch is ever reintroduced, this failure mode returns with it — and BL-16 is its
sibling (a control that is *present* but *doesn't work*, with every alarm still green).

---

### BL-15 — The AST write/encoding guards classify `open()` receivers by name, so an import alias defeats them
*(added 2026-07-13, found during the fourth Opus HITL review of PR #57, sprint 35 — filed as
findings F41/F42, both non-blocking, and merged unfixed by design)*

**Why:** `tests/tools/_ast_open.py` is the shared classifier behind two of the repo's
**enforced module boundaries** — the write-boundary guard (`test_state_io_boundary.py`, which
asserts only `state_io`/`scaffold` write files) and the encoding/newline guard
(`test_encoding_boundary.py`). It decides where an `open()`-shaped call's mode argument lives by
matching the **receiver's bare module name** against two hardcoded sets. Everything it doesn't
recognize falls through to "method-form `Path.open`, mode at index 0."

That default is right for the common case (`p.open('w')`) and wrong in a way that silently
reintroduces the bug the last three review rounds were spent closing.

**F41 — an import alias reverts the guard to the F35 failure mode.** With `import gzip as gz`,
the receiver `gz` is in neither set, so it's treated as a `Path` and the mode resolves to
`args[0]` — the *filename*. Write-capability is then decided by which letters happen to appear in
the path string. Verified by driving the guards directly:

- `gz.open('out.gz', 'wt')` → **write MISSED** by the write-boundary guard (`"out.gz"` contains no
  `w`/`a`/`x`/`+`).
- `gz.open('data.gz', 'rt')` → a read **FALSE-POSITIVED** as a write (the `a` in `"data"`).
- `from gzip import open as gzopen` → classified `None`, skipped by **both** guards entirely.

**Not live today** — `src/` contains no aliased or `from`-imports of the five index-1 receivers
(checked). This is a latent weakness in a defense-in-depth control, not a shipped bug.

**The pattern is the actual finding.** F30 → F35 → F41 are the same defect wearing different
hats, and it keeps returning because each round's fix *enumerated another name into a set*
rather than removing the assumption underneath. A name-matching classifier cannot be made
correct by adding names.

**Shape:** bind imports instead of guessing. Both guards already parse the whole `ast.Module`, so
walk `ast.Import`/`ast.ImportFrom` first to build an alias → real-module map and pass it into the
classifier. That closes the alias case *and* the `from`-import case together, and is
name-set-independent — the fix stops being a list that needs maintaining.

**F42 — `gzip`/`bz2`/`lzma` default to binary, not text.** `_ast_open.py` describes its index-1
receivers as "the same call shape as the builtin `open()`". True of the mode *position*; false of
the mode *default*. Builtin `open(p)` defaults to text `'r'`, but `gzip.open(p)` / `bz2.open(p)` /
`lzma.open(p)` default to `'rb'`. So a bare `gzip.open('blob.gz')` — a legitimate binary read that
**rejects** `encoding=` with a `TypeError` — is flagged by the encoding guard as an unencoded text
open, and the fix the guard demands would crash at runtime. Only `codecs` and `io` genuinely share
the builtin's text default.

---

### BL-16 — Every CI gate is verified to be *required*, never to be *functional* — a gate can fail open and all four alarms stay green
*(added 2026-07-14, found while driving PR #58 (the migration merge) to green, sprint 35. The
specific bug is FIXED — PRs #59/#60 — but the reason it went undetected is not, and that is
what this item is for.)*

**Why:** `architect-review` — a **required** check on `main`, and the gate this repo built
precisely because a rule living only in prose gets skipped — spent an unknown number of sprints
**exempting itself on large PRs**, and nothing in the repo could have told us.

The mechanism was a shell pipeline (`gh api --paginate | grep -q '^src/'`): `grep -q` exits at
its first match, closing the pipe; the still-paginating `gh` dies of SIGPIPE (141); `set -o
pipefail` promotes 141 to the pipeline's status; and `if !` reads that failure as *"no `src/`
changes"* and takes the exemption branch. Exit 0. Green check. On PR #58 it reported "No src/
changes in this PR" over **66 changed files under `src/`**.

**Three properties made this invisible, and all three generalize beyond this one bug:**

1. **It failed *green*, not `skipped`.** BL-10 taught us `skipped` reads as satisfied; this is
   worse. A green `architect-review` is *affirmative evidence* that a review happened. It
   satisfies the `protected-integration-branches` required-check rule. There is no artifact
   anywhere that distinguishes "the gate ran and found a review" from "the gate ran and excused
   itself" — both are `exit 0`.
2. **Severity was inverted with diff size.** On a small PR, `gh` finishes writing before `grep`
   quits, so no SIGPIPE, and the gate works correctly — that is every sprint PR to date,
   including #57. It only misfires once the file list is long enough to keep `gh` paginating. So
   the gate **silently weakened as the diff grew** and was least trustworthy on the largest,
   least-reviewable PRs. Testing it on ordinary PRs would never have found it.
3. **`ruleset-drift.yml` watches the wrong thing.** It verifies the check is *required* — the
   BL-11 concern. It cannot verify the check *works*. A gate that is required, always-green, and
   structurally inert passes the drift check forever, and passes it *because* it is inert.

**The pattern is the finding.** BL-11 asked "is this gate required?" and answered it. Nobody
asked "does this gate fail closed?" The `architect-review` exemption branch is the sharpest case
because its whole job is to decide whether enforcement applies — a malfunction of its guard
condition is indistinguishable from a legitimate pass.

**Shape (for a planning pass — do not fix piecemeal):**
- **Negative fixtures.** Each gate should be exercised against an input it *must* reject. The
  `src/`-detection deserves a test that feeds it a synthetic 200-file list and asserts it demands
  a review — the structural test added in #59 pins the *shape* of the fix (no pipe into `grep -q`)
  but still cannot observe the gate's runtime behavior.
- **Fail closed, and make the exemption loud.** An early `exit 0` should have to *prove* its
  precondition, not merely fail to disprove it: assert the file list is non-empty (a real PR
  always changes ≥1 file), and echo the count and the branch taken, so an exemption is an
  auditable statement rather than a silent default. (The #59 fix already gets part of this for
  free: `changed=$(gh api …)` under `set -e` now aborts the step if `gh` fails, rather than
  reinterpreting the failure as an answer.)
- **Audit the other three workflows for the same construct** — the class, not the instance. This
  is the F30→F35→F41 lesson from [BL-15] restated at the CI layer: fixing the instance and leaving
  the assumption is how a defect comes back wearing a different hat.

**Related:** [BL-11] (required-ness — necessary, and now demonstrably not sufficient), [BL-10]
(`skipped` reads as satisfied), [BL-6] (a gate cannot tell *who* reviewed; this one could not
tell *whether* it reviewed).

Fails **loud** (a red test), not silent, which is the safe direction for a boundary guard — hence
non-blocking. One-line fix: for `_INDEX1_MODE_RECEIVERS` minus `{codecs, io}`, treat a *missing*
mode argument as binary rather than as the implicit text `"r"`.

**Priority:** low-ish but not cosmetic. Neither defect can bite until someone adds a compression- or
`codecs`-based call to `src/`, but the write-boundary guard is one of the controls `CLAUDE.md`
advertises as "checked by static tests, not just convention" — and a guard defeatable by
`import gzip as gz` is weaker than advertised. Fix F41 and F42 together; they're the same file and
one of them is a one-liner.

**Notes / where to look:** `tests/tools/_ast_open.py` (`open_call_is_method`, `_INDEX1_MODE_RECEIVERS`,
`_NO_MODE_CONCEPT_RECEIVERS`), its two consumers `tests/tools/test_state_io_boundary.py` and
`tests/tools/test_encoding_boundary.py`. Full review reasoning is on PR #57
(`gh pr view 57 --comments`).

---

### BL-17 — RESOLVED: `feat/**` is retired
*(added 2026-07-14, sprint 35 Task 5 — deferred by the repo owner, who was away from a terminal
when the migration merged; **executed and closed the same day**)*

**Status: RESOLVED 2026-07-14.** Executed in the ordered sequence below, which was the whole point
of the item:

1. **The repo owner removed `feat/**` from the `protected-integration-branches` ruleset's targets.**
   It now targets exactly `refs/heads/main` (`include: ["refs/heads/main"]`, `exclude: []`).
2. **`main`'s protection was verified BEFORE the deletion** — 4 rule types, 8 required checks — so
   the ruleset edit was confirmed clean rather than assumed. This is the trap the item warned about:
   the edit that drops `feat/**` is the same edit that could silently un-protect `main`.
3. **The branch was proven fully merged before deletion, not asserted:** `b669482` is an **ancestor
   of `main`** (`git merge-base --is-ancestor` → true) and is literally `d2135e7`'s **second
   parent**, with **zero** commits not in `main`. Deleting the ref discarded nothing — all 113
   commits remain reachable through the merge commit.
4. **`feat/mcp-langgraph-migration` deleted.** No `feat/**` branch remains.
5. **`main` re-verified AFTER the deletion** — still 4 rule types, still 8 required checks — and
   then confirmed **independently** by dispatching `ruleset-drift.yml`, which reported
   `OK: ruleset intact -- 4 rule types, 8 required checks`. That is the backstop the item named,
   doing its job, reporting from something other than the actor who made the change.

**What the check-after-the-fact is for, and why it is not bookkeeping.** Steps 2 and 5 are the item.
A weakened `main` fails **open**: every check still *runs* and still *reports*, and none of them
*blocks* — the same failure shape as BL-11, and indistinguishable from health unless you look. The
independent drift-check run in step 5 is the only evidence here not produced by the party that made
the change.

---

<details>
<summary>Original item (retained for the reasoning, which still applies to any future ruleset edit)</summary>

**Why:** the migration merged (PR #58 → merge commit `d2135e7`), so
`feat/mcp-langgraph-migration` has no remaining purpose: development returns to `main`, and per
`.ai/context/workflow.md` sprint branches are now cut from — and based on — `main`. The branch
still exists. It **survived the merge on purpose**, not by accident: the repo has
`delete_branch_on_merge: true`, but the `protected-integration-branches` ruleset targets
`refs/heads/feat/**` with a **`deletion`** rule, and the rule won (sprint 35, FD6). That collision
was predicted and is benign — but it means the branch cannot simply be deleted, and retiring it is
a deliberate two-step act rather than something the merge did for you.

**Shape (ordered — the order is the whole item):**
1. Remove `feat/**` from the `protected-integration-branches` ruleset's target list (ruleset id
   `18847725`), leaving `refs/heads/main` targeted. This is correct on its own merits once no
   `feat/**` branch exists — the ruleset should not claim to protect a namespace that is empty.
2. Delete `feat/mcp-langgraph-migration` (currently at `b669482`, now an ancestor of `main` — so
   nothing is lost; the merge commit's second parent preserves every one of the 113 commits).
3. **Verify `main` is untouched afterwards** via the read-only
   `gh api repos/glunk-works/loop-engine/rules/branches/main` — all **four** rule types
   (`deletion`, `non_fast_forward`, `pull_request`, `required_status_checks`) and all **eight**
   required checks (`lint`, `format-check`, `test`, `secrets-scan`, `dependency-audit`, `sbom`,
   `pr-title`, `architect-review`) still present. Same endpoint `/resume` and `ruleset-drift.yml`
   already use — **no new PAT scope** (BL-11/FD1).

**The trap to avoid:** step 1 edits the very ruleset that makes all eight checks required on
`main`. A careless edit that drops `refs/heads/main` from the targets, or trims the check list
while trimming the branch list, **silently un-protects the default branch** — every check would
still *run* and still *report*, and none would *block*. That is BL-11's exact failure shape, and
it is why step 3 is not optional bookkeeping. `ruleset-drift.yml`'s daily cron is the backstop and
**will** fail loudly on the next run if `main`'s protection is weakened — which is the drift check
working, not breaking. Do not "fix" a red drift check by relaxing the check.

**Not urgent, and safe to leave.** Nothing is broken while the branch lives: it is frozen, no CI is
wasted on it (nothing will be pushed), and `ci.yml`'s `push: branches: [main, 'feat/**']` trigger
simply matches nothing. The costs are cosmetic — a dead branch inviting someone to branch from it,
and a vestigial `feat/**` in both the ruleset and `ci.yml`'s trigger list. Fold into the next
sprint that touches CI config; drop the now-dead `'feat/**'` from `ci.yml`'s `push:` trigger in the
same pass.

**Blocked on:** nothing. It is a human settings action (ruleset edit + branch delete). Claude was
deliberately not asked to perform it — see sprint 35's Task 5, which reserves the settings sequence
for the repo owner.

</details>

**One loose end this leaves — folded into [BL-22], not lost.** `ci.yml` still carries
`push: branches: [main, 'feat/**']`. With no `feat/**` branch in existence, that glob is now
**dead** — it matches nothing, costs nothing, and breaks nothing. Drop it in the next pass that
touches CI config; BL-22 is that pass.

---

### BL-18 — "No `if:`, so nothing can be `skipped`" is the wrong invariant: a failed `needs:` skips too
*(added 2026-07-14, observed live while unblocking Dependabot PRs #50–53 in sprint 35)*

**Why:** `CLAUDE.md` claimed — and `tests/test_ci_config.py` was read as pinning — that because no
job in `ci.yml` carries an `if:`, **no job can ever report `skipped`**. That is false, and it was
watched being false: with `secrets-scan` red on the Dependabot PRs, `sbom` (which `needs:
secrets-scan`) reported **`skipped`**, and flipped to `success` the instant `secrets-scan` passed.
No `if:` was involved. **A job whose `needs:` dependency fails is skipped by GitHub, full stop.**

The claim and the mechanism don't line up. Removing every `if:` prevents a job being skipped **by a
condition** — which is genuinely what BL-10 was about (a gate keyed on the wrong event reported
`skipped`, satisfied `needs:`, and let an all-green checks page hide a suite that never ran). It
does not, and cannot, prevent a skip caused by an upstream failure.

**Why it isn't currently exploitable — and why that's not a reason to leave it:** a `needs:`-skip
only happens *because* an upstream job failed, and that failure blocks the merge by itself. So the
safety today comes from **the failing job**, not from the absence of `skipped`. The stated
invariant is doing no work; the thing actually protecting `main` is something else. That is exactly
the configuration in which a later, reasonable-looking change — reordering the chain, making a job
non-required, adding `continue-on-error`, or splitting a job out from under `needs:` — quietly
removes the real protection while the documented one still reads as intact. **BL-16's lesson
verbatim:** the alarm is green because it is measuring the wrong thing.

**Shape (not designed yet):**
- Correct the claim wherever it is stated (done for `CLAUDE.md` in this sprint — say what the
  absence of `if:` actually buys, and that a `needs:`-failure skip is possible and safe *because
  the upstream failure blocks*).
- Decide whether `tests/test_ci_config.py` should assert the real invariant rather than the proxy.
  The honest property is closer to *"every required check either succeeds, or something red blocks
  the merge"* — which a static test over `ci.yml` cannot fully express. Worth being explicit that
  this is a limit of the static test, not something to fake.
- Consider whether `skipped` satisfying a *required* check is a live risk for any job **not** behind
  a `needs:` that would independently fail. Today every job in the chain is; a future job added
  outside the chain would not be, and that is the case to watch for.

**Related:** [BL-10] (the original — `skipped` reads as satisfied), [BL-16] (a gate verified
*required*, never *functional*), [BL-11] (required-ness is necessary, not sufficient).

**Notes / where to look:** `.github/workflows/ci.yml` (the `needs:` chain), `CLAUDE.md` (the
corrected sentence), `tests/test_ci_config.py`. Live evidence: PRs #50–53 before the org Dependabot
`GITLEAKS_LICENSE` secret was added — `sbom` = `skipped`, `secrets-scan` = `failure`.

---

### BL-19 — DECLINED: keep `gitleaks-action`; do not move to the gitleaks CLI binary
*(added 2026-07-14, sprint 35 — **decided and closed the same day** by the repo owner)*

**Status: DECLINED. We are staying on `gitleaks/gitleaks-action`.** Recorded so the question is not
re-opened from first principles every time someone notices the licence.

**The correction that mattered more than the decision.** This item was originally filed on a claim
that turned out to be **false**: that the Dependabot `GITLEAKS_LICENSE` secret "has been added and
all four Dependabot PRs pass." It had not been, and they did not. The four PRs were green only
because a human close+reopen had re-triggered their CI, which silently switched which secret store
the run read (see **BL-20** — that is the real, durable finding). The actual defect was a **name
mismatch**: the org Dependabot store held `GITLEAKS_SECRETS` while the workflow reads
`secrets.GITLEAKS_LICENSE`. Renaming it fixed `secrets-scan` on a genuinely `dependabot[bot]`-actored
run, verified 2026-07-14.

**What was considered:** `gitleaks/gitleaks-action` requires a **paid licence** for repositories
under an organization (`[glunk-works] is an organization. License key is required.`), whereas the
gitleaks **CLI binary is free and MIT-licensed** and performs the same scan. Swapping would have
removed a paid dependency and one third-party action from the supply chain.

**Why we're not doing it:** the licence is already paid for and now correctly wired in *both* secret
stores; the action is SHA-pinned; and `secrets-scan` is a **required** check on `main`, so a botched
swap breaks every PR until fixed. Running the binary directly would mean pinning its version and
checksum ourselves — trading one supply-chain decision for another rather than eliminating it. The
argument that the swap would "delete the two-secret-store trap" is **no longer load-bearing**: that
trap is understood, documented (BL-20), and fixed. It was never a reason to change tooling, only a
reason to understand the tooling — and now we do.

**Consequence:** **PR #50** (`gitleaks-action` 2→3) is a real major bump that must be reviewed on
its merits, not retired by deletion. It goes through Task 6's changelog review like the other three.

---

### BL-20 — Dependabot runs read a *different* secret store, a missing secret resolves to *empty*, and re-triggering as a human reads the other store
*(added 2026-07-14, sprint 35 — found the hard way; it produced a false "verified" claim that
reached `main` in PR #61)*

**Why:** three independent mechanisms compose into a trap where **the obvious way to test the fix is
the one way that cannot detect the bug.**

1. **Two stores, not one.** GitHub keeps **Actions** secrets and **Dependabot** secrets in separate
   stores (at both org and repo level). A workflow run triggered by `dependabot[bot]` can read *only*
   the Dependabot store; every other run reads *only* the Actions store. Same repo, same workflow,
   same `${{ secrets.X }}` expression — different store, decided by **who triggered the run**.
2. **A missing secret is not an error.** GitHub substitutes the **empty string** silently. So a
   secret that is absent, mis-scoped, or *misnamed* looks identical to one that is present, until
   whatever consumes it fails on its own terms (here: `missing gitleaks license`).
3. **Re-triggering changes the actor.** Closing and reopening a Dependabot PR — the natural way to
   refresh stale checks — makes **you** the triggering actor, so the re-run reads the **Actions**
   store and goes green. That green says nothing whatsoever about whether Dependabot can see the
   secret.

**How it actually bit us.** `secrets-scan` was red on Dependabot PRs #50–53. The org **Dependabot**
store did have a secret — named **`GITLEAKS_SECRETS`** — but the workflow reads
`secrets.GITLEAKS_LICENSE`. Name mismatch ⇒ empty ⇒ gitleaks refuses (an org repo requires a
licence). A human close+reopen turned all four green, and that green was reported as proof the
Dependabot secret worked. It wasn't: those runs had actor `Seuss27`, not `dependabot[bot]`, and were
reading the Actions store — where a repo-level `GITLEAKS_LICENSE` does exist. **The verification
changed the thing being verified.**

**The rules that fall out of this — the actual deliverable:**
- **Refresh a Dependabot PR's checks with `gh run rerun`, never close+reopen.** `run rerun` preserves
  the actor; close+reopen does not, and hands you a false pass. (This needs `actions: write` on the
  PAT — its absence is what forced the close+reopen in the first place, so the missing permission
  *caused* the wrong diagnosis.)
- **A green check on a Dependabot PR is only meaningful if the run's actor is `dependabot[bot]`.**
  Verify with `gh api repos/OWNER/REPO/actions/runs/<id> --jq .actor.login`.
- **Any secret the CI depends on must exist, with the same name, in BOTH stores** (or the workflow
  must tolerate its absence). Name equality across stores is invisible from the workflow file — the
  workflow refers to one name and cannot tell you which stores hold it.
- **`@dependabot recreate` / `@dependabot rebase`** re-trigger CI *as Dependabot*, and are the right
  tool when you specifically need a Dependabot-actored run.

**Related:** [BL-16] (a gate verified *required*, never *functional*), [BL-18] (an invariant that
reads as protective while the real protection comes from elsewhere), [BL-14] (Dependabot reads its
config only from the default branch — another "correct config, wrong place, silently inert").
This is the same family: **the alarm is green because it is measuring the wrong thing.** BL-16 said
the repo verifies its gates are *required*, never that they *work*; this says a *human* can verify a
gate the same wrong way.

**Shape (not designed yet):** mostly a documentation/discipline finding, but worth asking whether
`secrets-scan` should **fail loudly on an empty `GITLEAKS_LICENSE`** instead of letting
`gitleaks-action` discover it downstream — a one-line guard that converts a silent empty string into
a named failure, and would have made this a five-minute bug. The same reasoning applies to any
future secret the workflow depends on.

**Notes / where to look:** `.github/workflows/ci.yml` (`secrets-scan`, the `GITLEAKS_LICENSE` env
line). Live evidence: run `29338705025` (actor `dependabot[bot]`, `GITLEAKS_LICENSE:` empty, red) vs.
run `29340103433` after the rename (actor `dependabot[bot]`, `GITLEAKS_LICENSE: ***`, green) vs. the
misleading `#51` run (actor `Seuss27`, green, proving nothing).

---

### BL-21 — RESOLVED: `flows/bootstrap` now installs a per-repo protection ruleset, proven live
*(added 2026-07-14, from a review of the `glunk-works` org settings)*

**Status: RESOLVED 2026-07-15 (sprint 36).** The code fix landed across PRs #73 (the
`create_ruleset` verb + wiring) → #76 → #77 (S4–S9 + round-4 hardening), and was **proven
live** in sprint 36 Track B (§8). The org-level fix was confirmed unavailable (Free plan →
`403 "Upgrade to GitHub Team"`), so protection is installed **per repo, by the flow that
creates it** — which forced the visibility default to **public** (FD3: repo-level rulesets
are free only on public repos). `run_bootstrap` calls `repo_io.create_ruleset` **last**
(FD7), shipping `deletion` + `non_fast_forward` + `pull_request` on **both** `main` and
`develop` (FD5) with **zero** required checks (FD4). Per **FD9** the gate was proven
*functional*, not merely present: a live direct/force push and a branch deletion were each
**observed rejected** (`GH013`) on the real scratch repo — the admin token itself included
(empty `bypass_actors`). `create_ruleset` stayed orchestrator-only (FD6 — the github MCP
server is still exactly four verbs). Full evidence: `sprints/DEFERRED_VERIFICATION.md` §8.
Live verification surfaced three follow-ups, all in generated-repo territory: **[BL-28]**
(scaffold fails its own `ruff check`), **[BL-29]** (maintenance escalation crashes on a
missing `loop-engine/needs-human` label), **[BL-30]** (the maintenance gate targets `src`
but the scaffold puts tests in `tests/`).

**Why (original):** the factory's whole thesis is that integration branches are PR-gated and auto-merge is
impossible — loop-engine enforces this on *itself* via the `protected-integration-branches` ruleset,
and structurally by giving `repo_io` no merge verb at all. But `flows/bootstrap` hands a brand-new
repo to the world with **no ruleset**, so the repo it just created accepts direct pushes to `main`,
force-pushes, and deletion. The invariant holds inside the factory and evaporates at its output.
This is observable today: of the five repos in `glunk-works`, only `loop-engine` has a ruleset; the
other four (`bounty-infra`, `global-bootstrap`, `appsec-triage-agent`, `pm-agent-loop`) have none.

**The obvious fix is not available.** An **org-level** ruleset would cover every repo at birth
without touching the code — but it is a **GitHub Team** feature. On the org's current Free plan the
endpoint returns `403 "Upgrade to GitHub Team to enable this feature."` **Repo-level** rulesets *are*
free on public repos (loop-engine's is live proof), so the protection must be installed **per repo,
by the thing that creates the repo**. That makes this a code change, not a settings change.

**Shape (not designed yet):**
1. A new `repo_io` verb — roughly `create_ruleset(repo, ...)` — shelling `gh` like its four siblings.
   Note this **widens the github MCP server's pinned four-verb set to five** if it is exposed there;
   it likely should **not** be, since it is orchestrator-invoked only, exactly like the existing
   factory verbs (`build_github_provider()`, never the model's coder loop). Decide deliberately —
   the "four verbs, pairwise disjoint" assertion in `tests/tools/test_mcp_provider.py` is load-bearing.
2. Call it from `flows/bootstrap` **after** the `push_branch(main)` — the same ordering constraint
   that already forces `create_branch(develop, base=main)` to run post-push, because a ruleset
   targeting a ref that does not exist yet is not meaningful.
3. Decide the shipped default: at minimum `deletion` + `non_fast_forward` + `pull_request`. Required
   status checks are **repo-specific** and cannot be templated blindly — a generated repo has no
   `architect-review` check, and requiring a check that never reports is a merge deadlock, not a gate.

**The trap to avoid:** do **not** template loop-engine's own eight required checks into generated
repos. A required check that no workflow ever reports is permanently pending, and the repo can never
merge anything — the mirror-image of BL-11 (there, gates that looked required but blocked nothing;
here, gates that block everything and can never pass).

**Related:** [BL-11] (a required check is required only because the ruleset says so), [BL-16] (a gate
verified *required*, never *functional*). Same family, one step out: the factory verifies its *own*
gates and never asks whether its **output** has any.

**Blocked on:** nothing, but it is a design decision (the verb's shape + whether it touches the MCP
verb set), so it wants an Architect planning pass rather than a direct implementation task.

### BL-22 — Review what *triggers* the full test suite: a lot of runner time is spent re-proving the same thing
*(added 2026-07-14, from repo owner)*

**Why:** the suite is re-run constantly, and a measurable share of those runs cannot possibly learn
anything new. Measured 2026-07-14, not estimated:

| Measurement | Value |
| --- | --- |
| Tests | **555** |
| Suite wall time (local) | **289 s** (4m49s) |
| `test` job in CI | **~380 s**, consistently (365–398 s over the last 8 runs) |
| CI runs in the 7 days to 2026-07-14 | **29** |
| **10 slowest tests** | **~90 s — roughly 30% of the entire suite** |

**The clearest waste — docs-only PRs run everything.** PRs **#61, #64 and #66** this week changed
*markdown only* (`docs/backlog.md`, `.ai/next-steps.md`, `CLAUDE.md`, …) and each ran the full chain:
`lint` → `format-check` → **`test` (~380 s)** → `secrets-scan` → `dependency-audit` → `sbom`. Three
PRs, zero lines of Python, ~20 minutes of `test` alone. `architect-review` already knows how to
exempt docs PRs; `ci.yml` does not.

> ### ⚠️ The obvious fix is the one that has already burned this repo twice. Read this before touching `ci.yml`.
>
> The instinct is `paths-ignore:` on `ci.yml`. **Do not reach for it casually.** These are **required**
> checks on `main`, and a required check that does not run does not "pass" — it either:
> - **never reports at all**, and GitHub shows *"Expected — waiting"* **indefinitely**, leaving the PR
>   permanently unmergeable with no error anywhere — this is exactly **BL-12**; or
> - **reports `skipped`**, which can read as *satisfied* — exactly **BL-10**, the defect that made an
>   all-green checks page possible over a suite that never ran, and the reason `ci.yml` currently
>   carries **no `if:` on any job at all**.
>
> So the cheap optimization and the two most expensive CI bugs in this repo's history are **the same
> change**. Any proposal here must say explicitly how a skipped-or-absent required check still
> reports a *green check-run of the same name* — the standard answer is an always-running
> **aggregator job** (`if: always()`, explicitly inspecting `needs.*.result` rather than relying on
> `needs:` semantics) that is the required check, with the heavy jobs conditional behind it. That
> pattern is sound but subtle, and **BL-18** is a live reminder that `needs:`-based reasoning about
> `skipped` is easy to get wrong. Design it deliberately; do not bolt on a `paths-ignore`.

**Other threads worth pulling (none decided):**
- **~30% of the suite is 10 tests.** The slowest are MCP provider/server tests (`test_mcp_provider`,
  `test_github_server`, `test_issue_io_server`, `test_issue_provider` — 6.7–13.2 s *each*) that
  **spawn a real MCP server subprocess per test**, plus four `test_ralph_coder` tests at ~12 s each.
  Session-scoped fixtures that amortize server launch across tests could reclaim most of that without
  weakening a single assertion. This is likely the **highest-value, lowest-risk** change here — it
  makes the suite faster *everywhere* (local TDD included), rather than running it less often.
- **No parallelism.** No `pytest-xdist`; the suite is strictly serial. Much of the slow tail is
  subprocess-bound (MCP servers, `gh`-less `pytest` subprocesses), which parallelizes well. `-n auto`
  is worth measuring — but note the subprocess-spawning tests must be checked for shared-state
  collisions first.
- **`push: [main]` re-runs the whole chain on every merge.** Tempting to call redundant, and it is
  **not**: GitHub does *not* re-run a PR's checks when `main` moves underneath it, so a PR can merge
  green having been validated against a stale base. The post-merge run is the only thing that catches
  a semantic conflict between two PRs that were each green in isolation. **Evaluate it, don't assume
  it's waste** — but a merge queue is the principled alternative if the cost is judged too high.
- **`sbom` and `dependency-audit` run on every PR** even when `pyproject.toml` is untouched. Same
  path-filter trap as above — same aggregator requirement.
- `pr-title` ran **40** times in 7 days. It is seconds long and gates nothing; leave it alone.

**The frame the owner set, and it's the right one:** running the suite on every change is **essential
to TDD and is not the problem**. The goal is not "run the tests less" — it is to **stop paying for
runs that cannot fail** (markdown PRs) and to **make the run itself cheap** (fixture scoping,
parallelism), so that running it constantly stays affordable.

**Related:** [BL-10], [BL-12] (why the naive fix is dangerous), [BL-18] (`needs:`/`skipped` reasoning
is where this gets subtle), [BL-23] (its sibling: *are the tests worth running at all?*).

**Notes / where to look:** `.github/workflows/ci.yml` (`on:` triggers, the `needs:` chain),
`pyproject.toml` (`test = "pytest {args}"`; no xdist), `tests/tools/test_mcp_provider.py`,
`tests/tools/test_github_server.py`, `tests/personas/test_ralph_coder.py`. Reproduce the timings with
`hatch run test --durations=10`.

---

### BL-23 — Audit the tests themselves: are they still testing what they claim, and are they still valid?
*(added 2026-07-14, from repo owner — "some of those tests came from early in the development cycle
where the methodologies were not as well defined")*

**Why:** **555 tests across 67 files**, accumulated over 35 sprints. The earliest were written before
this project's conventions existed; the codebase underneath them has since been through a full
architectural migration (Phase 6 **deleted** the classic engine, tools, personas and Coder outright).
A test written against a design that no longer exists does not usually fail — it usually **passes
while proving nothing**, which is worse, because it is counted as coverage.

**This is not a hypothetical worry in this repo — it is a documented, repeated pattern.** In the last
month alone, four separate findings were all the same defect wearing different hats:
- **BL-16** — every CI gate is verified to be *required*, never to be *functional*. An inert gate
  passes every alarm **because** it is inert.
- **BL-18** — the "no `if:`, so nothing can be `skipped`" invariant is simply **not the mechanism**;
  the real protection comes from somewhere else entirely.
- **BL-20** — a green check that was green **because the verification changed the thing being
  verified**.
- **BL-15** — the AST write/encoding guards, which `CLAUDE.md` advertises as "checked by static tests,
  not just convention", classify `open()` receivers **by name** — so `import gzip as gz` walks
  straight through them. The guard is **weaker than advertised**, and nothing said so.

Every one of those is *a check that verified the wrong property while reporting success*. **BL-23 is
that same audit, turned on the test suite itself.** Given four confirmed instances at the CI layer,
the prior that the 555-test suite is free of them is not credible.

**What to actually look for (not designed yet):**
- **Tests that would still pass if the code were deleted.** The principled instrument is **mutation
  testing** (`mutmut`, `cosmic-ray`): mutate the source, and any mutant that survives is a line no
  test actually constrains. It is the only method that answers *"would this test fail if the code
  were wrong?"* rather than *"does this test pass?"*. Expensive to run on all 555 — scope it to the
  boundary guards and `core/` first.
- **Tests that pin the implementation rather than the behaviour.** 42 of 67 files use
  mocks/`monkeypatch`. Mock-*assertion* density is reassuringly low (**30** `assert_called` /
  `call_count` sites), but **BL-3 already flags** that "the mocked suite pins exact transport call
  counts" — a test that breaks when you refactor without changing behaviour is a tax, not a guard.
- **Orphans and vestiges.** Phase 6 deleted whole subsystems. Which tests now exercise a path that
  only still exists *because a test exercises it*?
- **Guards that are weaker than their docstring.** BL-15 is a proven instance. `CLAUDE.md` makes
  strong claims ("enforced by static tests, not just convention") for the module-boundary, subprocess-
  surface and write-owner guards — **each of those claims should be attacked, not assumed.** Try to
  defeat each guard deliberately; if you can, the guard is the finding.
- **Early-cycle tests (sprints 01–08)** predate the conventions; re-read them against today's
  Definition of Done rather than grandfathering them.

**Explicitly NOT the goal:** deleting tests to make the suite faster. That is **BL-22's** job, and
conflating the two would let "this test is slow" masquerade as "this test is invalid". A slow test
that catches real bugs stays. **The output of BL-23 is a verdict per test — keep / fix / delete —
with a reason**, not a smaller number.

**Related:** [BL-22] (its sibling: *how often should we run them?*), [BL-15] (a proven weak guard),
[BL-16] / [BL-18] / [BL-20] (the same failure mode, at the CI layer), [BL-1] (an in-loop review stage
would face this same question for generated code).

**Notes / where to look:** `tests/` (67 files, 555 tests), especially the guards `CLAUDE.md` leans on:
`tests/tools/test_subprocess_surfaces.py`, `tests/tools/test_state_io_boundary.py`,
`tests/tools/test_encoding_boundary.py`, `tests/tools/_ast_open.py` (BL-15's subject),
`tests/core/test_boundaries.py`, `tests/flows/test_boundaries.py`, `tests/trigger/test_boundaries.py`,
`tests/tools/test_mcp_provider.py`.

### BL-24 — `DEFERRED_VERIFICATION.md` §6: the trigger surface has never received a real webhook
*(added 2026-07-14, sprint 35 Task 6 — the home agreed with the repo owner for §6; **lowest
priority of the five**, and deliberately so)*

**Why:** sprint 23's coverage is entirely hermetic. `TestClient` deliveries against
`create_app(dispatcher=fake)` prove HMAC-verify → parse → dispatch end to end, but
`InProcessDispatcher` is only ever exercised with `runner.run_new` patched — **no real loop ever
runs, and no port is ever bound.** What has never happened: a real GitHub delivery reaching a real
listening server and driving a real default-loop run. The full protocol (stand up `uvicorn`,
register a real webhook on a scratch repo, deliver a signed `agent-action` label event and an
`/agent-run` comment, confirm the redelivery dedupe, confirm 23a's malformed-body path returns
`400` and not `500`) is written out in `sprints/DEFERRED_VERIFICATION.md` §6 — **not duplicated
here**, per that file's role as the register of record.

**Why it is a backlog item and not a sprint:** it needs a **tunnel and a publicly reachable
address** — neither the devcontainer nor the dev host has one — which is real setup for a surface
**nothing currently depends on**. `trigger/` is a live entrypoint, but no scheduled work routes
through it; the factory flows (`flows/maintenance`, `flows/bootstrap`) do not. So the check is
genuinely owed and genuinely not urgent, and saying so plainly is better than parking it in a
sprint that then slips.

**Do not read "lowest priority" as "optional."** The HMAC secret is an inbound credential
(`LOOP_ENGINE_WEBHOOK_SECRET`, an env var — a distinct credential class from the keyring-only
Anthropic key), and an unverified auth path on a public-facing surface is exactly the sort of thing
that is fine until the day it is catastrophic. It stays on this list until it is run.

**Sequence it with:** anything that gives the project a routable host — the same hosting question
that Sprint 36's daemon-bearing session raises. If that host ends up reachable, fold §6 in
opportunistically rather than standing the whole thing up twice.

**Notes / where to look:** `sprints/DEFERRED_VERIFICATION.md` §6 (the full protocol),
`src/loop_engine/trigger/` (`app.py`, `dispatch.py`), `tests/trigger/`.

> ### SUPERSEDED IN PRACTICE — not deleted (sprint 40, 2026-07-17, BL-2 pass 2)
> **Slack is now the live inbound path.** `slack_control/`'s Socket Mode daemon
> (`loop-engine slack-listen`) does what §6 was owed for — a real inbound trigger, authenticated,
> reaching a real `runner.run_new` — **without a tunnel or a routable address**, because the daemon
> dials *out*. That is exactly the dissolution BL-2's planning pass predicted, and it removes the
> "sequence it with anything that gives the project a routable host" dependency above: **that host
> is no longer coming, because nothing needs it.**
>
> **What this does and does not change:**
> - **`trigger/` is parked, not deleted, and §6 is not discharged.** FD1 chose *supersede, not
>   unify*: `slack_control/` shares no code with `trigger/`, so exercising Slack proves **nothing**
>   about `trigger/`'s HMAC-verify → parse → dispatch path. The webhook's auth path remains exactly
>   as unverified as this item says it is.
> - **The "fine until catastrophic" argument now cuts the other way.** An unverified auth path
>   matters because it is *public-facing* — but `trigger/` is not currently served anywhere, and now
>   likely never will be. The honest risk is no longer "unverified auth on a live surface"; it is
>   **dead code carrying an inbound credential** (`LOOP_ENGINE_WEBHOOK_SECRET`).
> - **The real decision is therefore no longer "verify it" but "keep or retire it."** Standing up a
>   tunnel to verify a surface we deliberately superseded is hard to justify; so is leaving a parked
>   inbound listener and its secret in the tree indefinitely. **Open question for the owner**
>   (deliberately not decided here): retire `trigger/` + `LOOP_ENGINE_WEBHOOK_SECRET` and close §6
>   as moot, or keep it as a second path and pay for the verification. **Until that is decided this
>   item stays open** — "superseded in practice" is not "closed," and quietly dropping it would be
>   the failure this item exists to prevent.

---

### BL-25 — Should the backlog and defect register live in GitHub Issues rather than this file?
*(added 2026-07-14, from repo owner — asked during sprint 36's planning pass)*

**Why it's a real question.** Filing a backlog item currently costs a **full pull request**: seven
required checks, including a **~380 s** test suite, to add markdown. BL-21, BL-22 and BL-23 each cost
one (PRs #65, #67). Issues would make filing free, give every item real state (open/closed, labels,
assignment), let a PR close an item by reference, and make the register **queryable** by the agent
(`gh issue list`) instead of grepping a 1223-line markdown file. It would also **dogfood the product**,
which already files GitHub issues as its human-escalation channel.

> ### ⚠️ The governing constraint: this repo's issue tracker is NOT a free surface — the product writes to it
> `tools/issue_io` files **runtime human-escalation issues** from live loop-engine runs. A dev backlog
> in the same tracker shares a namespace with **machine-generated issues from a running engine**.
>
> That is not hypothetical. **Finding R8** (V3, 2026-07-12) was exactly this: escalation issues for
> *managed* repos were filed against **`loop-engine` itself**, because `gh` derived its destination
> from the ambient CWD. The three issues in this repo's tracker (**#16, #19, #21** — all closed) are
> that bug's artifacts. R8 is fixed (`default_issue_filer` now names the repo explicitly), but the
> coupling is structural: **the register of defects would live in a table a buggy run can write to.**
> Labels can separate the namespaces — that is a deliberate choice to make, not a free win.

**The counter-argument for keeping `docs/backlog.md`, and it is stronger than it looks:**
- **The backlog is a cross-linked *argument*, not a ticket list.** `[BL-16]` is cited 4×, `[BL-10]`,
  `[BL-11]` and `[BL-18]` 3× each. BL-23's entire payload is *"these four findings are the same defect
  wearing different hats."* The value is in the linkage and the prose, not in the enumeration.
- **It is versioned with the code.** When a sprint plan cites BL-21, `git show` reveals what BL-21 said
  **at that commit**. Issues carry no per-commit snapshot, and the sprint plans lean on that property.
- **Churn is low** — 19 commits over the file's whole life, ~1–2 per sprint. The merge-conflict pain is
  real but rare, and already has a documented resolution (two branches appending = two additions).

**The likely answer (not decided — this wants a planning pass):** the pain the owner is feeling is
**real but misattributed**. "Every backlog item costs a full-CI PR" is **[BL-22]'s** problem, not the
tracker's — fix what triggers the suite and filing becomes cheap **without splitting the register of
record across two systems.** Two sources of truth is precisely the failure mode this repo keeps paying
for. Where issues are *clearly* right is the place the factory ships nothing today: **generated repos**
have no issue conventions at all, while the escalation ladder already terminates in a GitHub issue.

**A caution for whoever picks this up**, recorded because it happened *while filing this item*: the
first read of the tracker reported the three escalation issues as "still open, orphaned debris needing
cleanup." They were **closed**, and there is **no** open issue on this repo. `gh issue list --state all`
was run and its output described as if it were `--state open`. **Check the state field.** It is the same
defect family as [BL-16]/[BL-18]/[BL-20] — an observation asserted rather than made.

**Related:** [BL-22] (the cost that motivates this is actually its problem), [BL-16] (a check that
verified the wrong property while reporting success), [BL-1] (an in-loop review stage would also need
somewhere to file).

**Notes / where to look:** `docs/backlog.md` (1223 lines), `src/loop_engine/tools/issue_io/`,
`gh issue list --state all` on this repo (3 closed, 0 open), `docs/migration_roadmap.md` (finding R8).

---

### BL-26 — The factory births GitHub repos, but `global-bootstrap` is what makes a repo *real* — and nothing connects them
*(added 2026-07-14, from repo owner — "cycle back on global-bootstrap")*

**Why:** `flows/bootstrap` produces a repo containing a Python skeleton and the injected Global
Conventions `CLAUDE.md`. **That is all it produces.** Verified against `tools/scaffold/templates/`:

| A factory-born repo has | A repo that can actually *do* anything needs |
| --- | --- |
| `pyproject.toml`, `src/`, `tests/`, `README`, `.gitignore`, `CLAUDE.md` | ⬑ plus… |
| **no `.github/workflows/` at all** | a CI workflow (this is also sprint 36's **FD4**) |
| **no `backend.tf`** | an OpenTofu state backend pointing at the S3/DynamoDB backend |
| **no entry in `global-bootstrap`'s `projects` map** | an OIDC `aws_iam_role` to assume from Actions |
| **no IAM policy** | a hand-authored least-privilege workload policy |

So the factory's output is **inert**: it has no CI, no cloud identity, and no state backend. Meanwhile
the **Coder/IaC persona is meant to write infrastructure** — into repos that have none of the
substrate infrastructure needs. The factory creates a *GitHub* repo; `global-bootstrap` is what makes
it a *project*; **nothing joins the two.**

**What `global-bootstrap` actually does** (read 2026-07-14 — S3 state bucket, versioned + encrypted;
DynamoDB lock table; KMS-encrypted findings bucket; a GitHub OIDC provider): `main.tf` does
`for_each = var.projects` and per project mints an `aws_iam_role.github_actions_role` whose trust
condition is pinned to `repo:${org}/${repo_name}:ref:refs/heads/main`, plus a state-access policy.
`project_policies.tf` then **hand-writes a bespoke least-privilege workload policy per project.**

**So "add a repo" is TWO acts, and only one of them is mechanical:**
1. **Mechanical** — a `projects` map entry, which yields the OIDC role + state access automatically.
2. **A design decision** — the least-privilege workload policy, which depends on *what that project
   provisions*. This **cannot be templated blindly**, and that is not a defect: an auto-generated
   "least-privilege" policy that guesses is just a permissive policy with better branding. Whatever
   the factory does here must produce **either a correct scoped policy or no policy at all** — never
   a plausible one. (Same family as **[BL-21]**'s trap: do not template a gate you cannot honour.)

**Note the branch wrinkle before designing anything.** The OIDC trust is pinned to
`ref:refs/heads/main`, but `flows/bootstrap` creates **`develop`** as the integration branch and the
scaffolded `CLAUDE.md` tells generated repos to target `develop`, never `main`. Those are consistent
(deploys happen on `main`, after a merge) — but only if you notice. A generated repo whose workflow
tries to assume the role from a `develop` PR run will fail the OIDC condition, and the error will not
say why.

**Sequence it with:** sprint 36 (which fixes **[BL-21]** — a factory-born repo gets a ruleset — and
whose **FD4** deliberately deferred adding CI to the scaffold *because a generated repo has no CI to
require*). **BL-26 is what makes FD4 resolvable.** Do not fold it into 36; that sprint is scoped.

**Related:** [BL-21] (protection at birth — same "the invariant evaporates at the factory's output"
shape), [BL-27] (the registry that would have to be written to), [BL-1].

**Notes / where to look:** `src/loop_engine/flows/bootstrap/flow.py`,
`src/loop_engine/tools/scaffold/templates/`, `glunk-works/global-bootstrap`
(`main.tf`, `variables.tf`, `project_policies.tf`), sprint 36's FD4.

---

### BL-27 — `global-bootstrap`'s registry still points at the personal account; ONE unreadable variable decides whether that is harmless or a dangling-role hazard
*(added 2026-07-14, found while reading global-bootstrap for [BL-26]; **corrected the same day** by the repo owner — see the correction note)*

**Why:** `variables.tf`'s committed `projects` map lists `tri-loop-dev`, `bedrock-serverless-rag`,
`bounty-infra`, `resume-optimizer`. **All four exist — under `Seuss27/`, the repo owner's personal
account, not the `glunk-works` org.** The map is therefore **internally consistent but scoped to the
project's previous home.** The org's real repos (`loop-engine`, `pm-agent-loop`, `appsec-triage-agent`)
are **not registered at all**, and `bounty-infra` exists in **both** namespaces. The move from the
personal account to the org never carried the registry with it (global-bootstrap last pushed
**2026-06-26**).

> ### ⚠️ Everything hinges on `var.github_organization`, and it CANNOT be read from the repo
> `main.tf` mints, per project, an IAM role trusting
> `repo:${var.github_organization}/${each.value.repo_name}:ref:refs/heads/main`. That variable has
> **no default**, so its applied value lives outside the source. The two candidates give **opposite**
> answers, and both are plausible:
>
> | If `github_organization` = | Then the roles trust… | Consequence |
> | --- | --- | --- |
> | **`Seuss27`** | `Seuss27/tri-loop-dev`, … — **all four repos exist** | No dangling roles. The registry is merely **stale-by-namespace**: no `glunk-works` repo has an OIDC role, so no org repo can deploy. |
> | **`glunk-works`** | `glunk-works/tri-loop-dev`, … — **three do not exist** | **Dangling roles.** Whoever next creates a repo by one of those names in the org inherits its AWS permissions on `main` — and that is exactly the population holding the sprint-36 PAT, which now carries `administration=write` and can create org repos. |
>
> **This is undetermined, not dismissed.** Resolving it is one lookup against the live backend
> (`tofu state list` / the role's trust policy in the AWS console). **Do that before acting on *or*
> dropping the hazard.**

**And there is a live question underneath it either way:** `project_policies.tf` carries a bespoke
`bounty_infra_policy`, and the repo's most recent commits (2026-06-26) are active fixes to *that*
pipeline's IAM. But **`bounty-infra` exists in both namespaces.** Which one actually deploys? If the
org copy is the live one while the OIDC trust names the personal one (or vice versa), that pipeline
cannot assume its role — and the failure surfaces as an opaque OIDC rejection, not a useful error.

**The real finding — and it survives whichever way the variable resolves: `global-bootstrap`'s source
does not determine its deployed state.** `bootstrap_bucket_name` and `github_organization` have no
defaults and no committed tfvars (`.gitignore` does not even exclude one — there simply isn't any), so
the applied configuration is supplied entirely from outside the repo. **An IaC repo you cannot review
from its source is the substrate of this whole finding**, and the ambiguity above is not academic: two
readings of one absent value point at two different sets of real repositories.

**Close it in this order — any other order is guessing:** (a) establish what is actually applied;
(b) make the repo *say so* (commit a tfvars / pin the value), so the source is reviewable;
(c) *then* reconcile the project list and resolve the `bounty-infra` ambiguity.

> **Correction note, kept deliberately** *(the mistake is the lesson)*. This item was first filed
> claiming three **phantom repos** and probable dangling roles. That was **wrong**: all four exist
> under `Seuss27/`. The error was reading `${var.github_organization}` and **substituting the value I
> had been looking at** (`glunk-works`) for a value the repo never states — an inference reported as
> an observation. It is the same defect family as [BL-16]/[BL-18]/[BL-20], and it is preserved here
> because the corrected finding is *better* than the original: the hazard is not "phantom repos", it is
> **an unreadable variable that decides between two very different worlds.**

**Related:** [BL-26] (the registry the factory would need to write to), [BL-16] (a check — here, a
*record* — that reports on something other than what it claims).

**Notes / where to look:** `glunk-works/global-bootstrap` (`variables.tf` `projects`, `main.tf`
`aws_iam_role.github_actions_role` / `aws_iam_role_policy.pipeline_state_policy`, both `for_each =
var.projects`), `gh repo list glunk-works`, the real S3/DynamoDB tofu backend.

### BL-28 — A factory-scaffolded repo fails its own `ruff check` out of the box
*(added 2026-07-15, from sprint 36 live verification — `DEFERRED_VERIFICATION.md` §8)*

**Why:** the scaffold's `tools/scaffold/templates/python/pyproject.toml.tmpl` sets
`[tool.ruff.lint] select = ["E", "F", "I", "B", "S"]` but ships **no `per-file-ignores`**,
while `tools/scaffold/templates/python/tests/test_smoke.py.tmpl` is `def test_smoke(): assert
True`. `S101` (bandit: "use of `assert`") therefore fires on the scaffold's own smoke test, so a
brand-new generated repo **fails `ruff check`** immediately — observed live on
`factory-scratch-boot-20260715` (`pytest` and `ruff format --check` both passed; only lint
failed). The Global Conventions the factory injects mandate `ruff check` is green before a
commit, so the factory ships a repo that cannot meet its own Definition of Done on commit #1.

**Shape:** add a `[tool.ruff.lint.per-file-ignores]` entry to the template exempting `tests/*`
from `S101` (mirroring how loop-engine's own `pyproject.toml` handles it), and extend
`tests/tools/scaffold/test_writer.py` (or the §8 evidence) so a scaffolded tree passes `ruff
check` on its own. `src/` change (template) → needs its own sprint/PR + fresh-session
architect-review.

**Related:** [BL-21] (the sprint that surfaced it), [BL-30] (the other "generated repo can't
satisfy its own gate" finding).

### BL-29 — Maintenance escalation against a factory-born repo CRASHES: the `loop-engine/needs-human` label doesn't exist there
*(added 2026-07-15, from sprint 36 live verification — `DEFERRED_VERIFICATION.md` §7)*

**Why:** when the default loop escalates a question mid-run, `_pause_for_issue` →
`tools/issue_io.default_issue_filer` files a GitHub issue via `gh issue create … --label
loop-engine/needs-human`. On loop-engine itself that label exists; on a **factory-born**
managed repo it does **not** (bootstrap scaffolds files but provisions no labels), so `gh`
exits non-zero (`could not add label: 'loop-engine/needs-human' not found`) and the call raises
`MCPToolError` — **crashing the whole run** instead of pausing at `AWAITING_ISSUE`. Observed
live twice on `factory-scratch-boot-20260715`: the engine had already persisted the
`AWAITING_ISSUE` snapshot, but the issue never got filed and the process died. So the very
escalation path that exists to hand control to a human is **broken for exactly the repos the
factory manages** — a human is never actually asked. The §7 green PASS was only reachable after
manually `gh label create`-ing the label.

**Shape (decide deliberately):** either (a) `flows/bootstrap` provisions the
`loop-engine/needs-human` label at repo creation (the label becomes part of the factory's
output contract, alongside the ruleset), or (b) `default_issue_filer` creates-the-label-if-
missing / degrades to no `--label`, or (c) both. Note the failure mode is *worse than silent*:
the snapshot says `awaiting_issue` while no issue exists, so `resume --from-issue` has nothing
to resume from. `src/` change → own sprint/PR + fresh-session review.

**Related:** [BL-7]/[BL-9] (the escalation/issue path), [BL-21] (the sprint that surfaced it).

### BL-30 — The maintenance green gate runs `pytest src`, but the scaffold puts tests in `tests/`
*(added 2026-07-15, from sprint 36 live verification — `DEFERRED_VERIFICATION.md` §7)*

**Why:** `flows/maintenance` hard-codes `_TARGET_TEST_PATH = "src"`, so its green gate is
`pytest src`. But `tools/scaffold` ships the smoke test at `tests/test_smoke.py`, **not** under
`src/`. So a freshly-scaffolded repo, run through maintenance unchanged, has `pytest src` collect
**0 tests → exit 5 → GATE_FAILED**, and the flow could **never** open a green PR on it. The §7
green PASS only worked because the seeded and loop-written tests happened to live under `src/`.
Either the gate should target the repo root (or `tests/`), or the scaffold/conventions should
colocate tests under `src/` — decide which is the intended layout and make the two agree. The
in-loop Coder gate (`core/coder_gate.py`) keys off the same `src` assumption, so check both.

**Related:** [BL-28] (the other generated-repo-can't-pass-its-own-gate finding), [BL-21].

### BL-31 — MCP server cold-start is a fixed ~5s import penalty, paid per spawn — in tests AND every real coder session
*(added 2026-07-15, from sprint 37 BL-22 planning measurements)*

**Why:** measured in isolation this planning pass: `build_coder_tool_provider().__enter__()` costs
**~5.0s** (spawn the stdio subprocess + `session.initialize()` + `list_tools()`); teardown is a
cheap ~0.25s. The 5s is **import-bound** — a fresh server subprocess re-imports `loop_engine` plus
the MCP/pydantic/anthropic stack before it can answer `list_tools`. In the test suite this shows up
as ~20 tests paying the penalty (~40% of a 278s local run), which **sprint 37 addresses by reducing
the number of spawns** (Tasks 1-2). This item is the *other* half: reduce the per-spawn **cost**,
which sprint 37 explicitly left out of scope because it touches `src/` runtime and — unlike the test
work — **speeds every real coder session in production**, where each `_CoderToolBackend` open pays
the same 5s before the model can use a single tool.

**Shape (not decided):** profile what the server subprocess imports at startup; the likely lever is
**lazy-importing** the heavy stack in the server entry module (`mcp_servers/*_server`) so the
`list_tools` handshake doesn't drag in anthropic/langgraph/etc. that a read-only tool call never
needs. Measure spawn 5s → ?s. Watch for: the import cost may be structural to `loop_engine/__init__`
(a package-level import chain), in which case the fix is decoupling the server's import graph from
the orchestrator's, not just deferring within one module. `src/` change → own sprint/PR +
fresh-session review.

**Related:** [BL-22] (the sprint-37 parent — reduces spawn *count*; this reduces spawn *cost*).

### BL-32 — The static structural guards need an adversarial invariant-injection audit, not mutation testing

*(added 2026-07-15, filed from sprint 38 (BL-23 pass 1, `core/` mutation) FD1 — the natural next
BL-23 beat)*

**Why:** sprint 38 mutation-tested `core/`'s **behavioral** tests with `mutmut` (production: 61
keep, 86 fix, landed — see `sprints/38_test_validity_audit/`). That instrument is deliberately the
wrong tool for the repo's **static structural guards** — `tests/tools/test_subprocess_surfaces.py`,
`tests/tools/test_encoding_boundary.py` / `test_ast_open.py`, the `core/`↔`personas/` import-boundary
tests, `tests/tools/test_mcp_provider.py`'s verb-disjointness assertions — because those guards
assert on the **shape of the source tree** (AST scans, set algebra) rather than on runtime behavior.
No mutation operator in mutmut's catalog (arithmetic/boundary/keyword swaps, string-literal
wrapping, argument substitution) can generate the constructs these guards exist to catch: a sixth
`subprocess.run` call, a back-channel `core/`↔`personas/` import, an overlapping MCP verb set. A
green mutation run against them would report them well-covered while leaving their real weakness
completely unprobed — reproducing the exact BL-23 defect (a check that verifies the wrong property
while reporting success) **inside** the BL-23 audit itself. **BL-15 is the proof this isn't
hypothetical**: the write/encoding guards, advertised by `CLAUDE.md` as "checked by static tests, not
just convention", classify `open()` receivers **by name** — so `import gzip as gz` walks straight
through them, and nothing said so until BL-15 found it by deliberately trying to defeat the guard.

**What to actually do:** **adversarial invariant-injection** — a different instrument from mutation
testing. For each guard, deliberately construct the exact violating shape it exists to catch and
assert the guard goes **red**, not green:
- A **sixth** subprocess surface (a new `subprocess.run`/`Popen` call outside the five sanctioned
  ones) — does `test_subprocess_surfaces.py` catch it?
- An **aliased** file-write receiver (`import gzip as gz`, `from pathlib import Path as P`, or an
  `open()` called through an indirection) — does the encoding/write-owner guard catch it, or does it
  repeat BL-15's exact name-based blind spot elsewhere?
- A **back-channel import** from `core/` to a concrete persona module (bypassing `personas/base.py`)
  — does the module-boundary test catch it?
- An **overlapping MCP verb** across the `coder_tools`/`github`/`issue` server sets (breaking the
  pairwise-disjointness the servers currently guarantee) — does `test_mcp_provider.py` catch it?

Each of these should be tried as a **temporary, reverted-after-the-fact** injection against a
throwaway branch/worktree (never landed), confirming the guard fires — mirroring how BL-15 itself
was found. A guard that stays green under its own violating construct is the finding, exactly as
BL-15 was.

**Explicitly NOT the goal:** re-running mutmut against these files (FD1, sprint 38) — that would
just repeat the wrong-instrument mistake this item exists to avoid.

**Related:** [BL-23] (this item's parent — the `core/` behavioral pass that scoped these guards
*out* and filed this as the next beat), [BL-15] (the proven instance this audit generalizes).

### BL-33 — The boundary-guard AST walkers share BL-15's blind spots — a confirmed remediation list from a BL-32-style audit

*(added 2026-07-16, from the `/critic-gate` `guard-adversary` pass on PR #107 (BL-2 Slack notify, T1+T2))*

**Why:** running the BL-32 adversarial invariant-injection audit (via the `guard-adversary` subagent)
against the *new* `tests/tools/test_slack_io_boundaries.py` confirmed BL-32's thesis concretely — and
showed the blind spots are **not** unique to that file. The same AST-walker helpers
(`_direct_write_calls`, `_subprocess_surfaces`, `_imports_named_module` / the module-scope variant) are
copy-pasted across `tests/trigger/test_boundaries.py`, `tests/flows/test_boundaries.py`, and
`tests/tools/test_subprocess_surfaces.py`, so every one of these guards inherits the same holes. Four
were confirmed (the guard stays **green** under the violating construct it exists to catch):

- **Write guard (highest — BL-15 recurring):** flags `open` only when the receiver is a bare
  `ast.Name`, and `.write_text`/`.write_bytes` only as attributes. `io.open` / `gzip.open` / `os.open`
  (attribute-receiver) and `f.write(...)` walk straight through — BL-15's name-based `open()` blind
  spot, reproduced in the boundary-guard family.
- **Subprocess guard:** enumerates `.Popen` / bare `Popen` + a fixed `os` exec/system list; misses
  `os.popen`, `os.spawn*`, `os.posix_spawn*`, `os.fork`, and `subprocess.run`/`call`/`check_output` as
  *calls* (`os` is already imported, so no import line trips it either).
- **Leaf-import guard:** `from loop_engine.tools import slack_io` slips — `node.module` is
  `loop_engine.tools` and the imported *name* (`slack_io`) is never inspected. A real back-channel
  into a guarded package.
- **Module-scope guard:** "module scope" is defined as direct `tree.body` children only, so a
  top-level `try: import slack_sdk` (which executes at import time) slips — defeating the exact
  F7/FD4 deferred-import invariant the guard protects.

**What to do:** replace the per-file copy-pasted AST walkers with a **single shared, hardened guard
helper** — resolve `open`/`gzip.open`/`io.open`/`os.open` by qualified name and add
`write`/`writelines`/`truncate`; enumerate the full `os` process-creation surface + `subprocess`
module calls; inspect `ImportFrom` alias names; treat an import as deferred only when an enclosing
`FunctionDef`/`AsyncFunctionDef` exists on the path from the module root (not merely "not a
`tree.body` child"). Fixing one file leaves the siblings porous. Add a regression that the
`guard-adversary` audit goes red on each construct above before the fix and green after.

**Explicitly NOT:** widening PR #107's scope — the new `slack_io` guard is no weaker than its
siblings and catches the naive/common violations; this is a cross-cutting hardening of the shared
pattern, and belongs on its own PR.

**Confirmed again on a *sixth* sibling (2026-07-18, from the T5 `guard-adversary` pass on PR #136,
BL-2 pass 3).** `tests/slack_control/test_boundaries.py` inherits the identical holes: its write-call
matcher misses `.open()`-as-attribute and aliased-receiver calls, its subprocess denylist omits
`os.popen`/`os.posix_spawn`/`os.spawn*`, and `importlib.import_module` bypasses the name-based import
assertions. **Not exploited by PR #136's new code** (out of scope for T5) — this is the same shared
AST-walker copied into one more file, exactly the "fixing one file leaves the siblings porous" thesis
above, and the single shared hardened helper this item proposes subsumes it. No separate item needed.

**Related:** [BL-32] (the audit instrument this is the output of), [BL-15] (the original name-based
`open()` blind spot the write finding reproduces), BL-2 / sprints 39–41 (the diffs whose critic passes
surfaced it, most recently `tests/slack_control/test_boundaries.py`).

### BL-34 — The CI `test` job's "docs-only" pre-step has a defeated fail-safe: under `bash -e`, a failing `gh api` kills the step instead of falling back to running pytest

*(added 2026-07-17, observed live on PR #115 (BL-2 pass 2, T1) during a GitHub API outage)*

**Why:** the `test` job in `.github/workflows/ci.yml` opens with a "Determine whether this PR is
docs-only" step whose comment explicitly promises **"Fail SAFE: any detection error or empty result
runs pytest."** The logic is `changed=$(gh api "repos/$REPO/pulls/$PR/files" --paginate --jq …)`,
then `status=$?`, then `if [ "$status" -ne 0 ] || [ -z "$changed" ]; then echo "skip=false"; exit 0`.
But GitHub runs the step as `/usr/bin/bash -e {0}`, and the in-script `set -uo pipefail` does **not**
clear the inherited `-e` (errexit). So when `gh api` fails, the failing command substitution in the
assignment trips errexit and the step exits non-zero (`##[error]Process completed with exit code 1`)
**before** the `status=$?` fail-safe branch ever runs — the exact opposite of "fail safe." On PR #115
this made the whole `test` check go **red in ~14s** (no pytest run), which cascaded its `needs:`
dependents (`secrets-scan`/`dependency-audit`/`sbom`) to `skipped`. Root cause was a transient GitHub
REST outage returning an HTML 500 (`invalid character '<' looking for beginning of value` from `--jq`),
so it stays invisible in normal operation — but it means **a GitHub API blip can red a green PR**, and
worse, the failure *looks* like a real test failure until you read the job log.

**What to do:** make the fail-safe actually fail safe — decouple the `gh api` exit from errexit, e.g.
`changed=$(gh api … ) || status=$?` (so the assignment's failure is caught, not fatal), or wrap the
call in `set +e … set -e`, or add explicit `continue-on-error`-style handling. Keep the job's
**unconditional** `test` check-run guarantee intact (BL-10/BL-12): the step must still emit
`skip=false` and run pytest on any detection error. Add a regression that simulates a non-zero
`gh api` (stub it to exit 1) and asserts the step sets `skip=false` and exits 0. Consider whether the
same `bash -e` + command-substitution pattern hides elsewhere in the workflows.

**Explicitly NOT:** removing the docs-only fast-path (it correctly skips pytest for docs-only PRs and
that's worth keeping), and not a `test`-check-optionality change — the check stays required and
unconditional; only its internal fail-safe is broken.

**Fold in while here — extend the docs-only short-circuit to `dependency-audit` + `sbom` (added
2026-07-18).** On a docs-only PR **nothing about the dependency set or the SBOM changed**, yet
`dependency-audit` (`hatch run audit` = pip-audit) and `sbom` (`hatch run sbom` + artifact upload) run
their full work every time — pure waste, paid on **every** cursor sync / backlog / docs PR (this repo
opens a lot of them; a single sprint close-out opened two). The **safe** fix is the *same* report-but-skip
pattern the `test` job already uses: a per-job "is this docs-only?" pre-step, then `if:
steps.docs_only.outputs.skip != 'true'` on the expensive step, with **no job-level `if:`** so the required
check still reports green cheaply (never `paths-ignore`/job-`skip` — that strands the required check per
BL-12 or trips the `skipped`==success trap per BL-10/BL-18). **Do it together with the fail-safe fix
above, not before it** — copying today's `test` pre-step verbatim would replicate *this very bug* into two
more jobs. Watch `sbom`'s `upload-artifact` step (guard it too, or let it upload the checked-in
`sbom.json`, which is current when deps didn't change). Update `tests/test_ci_config.py` to assert the new
jobs stay unconditional (no job-level `if:`) and that their pre-step is fail-safe. It's a CI change into
the required-check chain, so it wants its own scoped PR + the fresh-eyes discipline even though it's
`architect-review`-exempt (non-`src/`).

**Resolved 2026-07-18.** The fail-safe now decouples the `gh api` exit from the inherited
errexit — `status=0; changed=$(gh api …) || status=$?` — so a detection failure falls through to
`skip=false` (run pytest) instead of killing the step; pinned by
`test_ci_docs_only_detection_is_errexit_safe`. The folded-in extension landed in the same PR: the
`test` job now exposes `outputs.docs_only`, and `dependency-audit` + `sbom` reuse it via
`needs.test.outputs.docs_only` on their expensive step (no copied bash, no local composite action —
which `test_all_workflow_actions_are_pinned_to_commit_shas` would reject). Both jobs stay
unconditional, so the required checks still report on docs-only PRs; pinned by
`test_dependency_audit_and_sbom_reuse_the_docs_only_detection`. **Hermetically pinned; the *skip
path* is not yet exercised live** — this PR itself is a code PR (touches `.github/`, `tests/`), so its
own CI runs the full chain; the first docs-only PR after merge is what exercises the skip. Watch that
first one (verification-ledger).

**Related:** BL-10 / BL-18 (the "a job can still report `skipped`" family and the unconditional-`test`
guarantee this must not break), BL-2 / sprint 40 T1 (the PR whose CI run surfaced it). Aligns with the
recurring theme in [github-workflow-traps]: *a check red/green for the wrong reason.*

### BL-35 — The `architect-review` gate strands a permanent red check-run on every `src/` PR: its own normal lifecycle blocks the merge it just approved

*(added 2026-07-17, observed live on PR #119 and confirmed retroactively on #107/#115/#117 — 4 of 4 `src/` PRs)*

**Why:** `.github/workflows/hitl-review.yml` fires on **both** `pull_request` (`opened`,
`synchronize`, `reopened`, `ready_for_review`) and `pull_request_review` (`submitted`, `dismissed`).
Both triggers are load-bearing and individually correct — without the review trigger, posting the
review the gate demands could never turn it green without a dummy push. But together they make the
**normal, intended lifecycle** of every `src/` PR emit *two* check-runs named `architect-review` on
the same head SHA: the `pull_request` run fails **correctly** (no review exists yet), then the
`pull_request_review` run passes once the review is posted. The `concurrency` +
`cancel-in-progress: true` block cannot help — the first run *completed* long before the second is
created, and `cancel-in-progress` only cancels in-flight runs. The stale red never self-supersedes,
so the gate blocks the very merge it just approved.

Forensics on **PR #119** (head `d70e9ce`), which is where this was finally run to ground rather than
waited out. GraphQL returned:

```
{"isDraft":false,"mergeStateStatus":"BLOCKED","mergeable":"MERGEABLE",
 "reviewDecision":null,"rollup":"FAILURE"}
```

- `reviewDecision: null` and the ruleset's `required_approving_review_count: 0` ⇒ **not** an approvals rule.
- `mergeable: MERGEABLE` ⇒ **not** a conflict; strict-mode/stale-base were both checked and excluded.
- `BLOCKED` survived **6 polls over ~60s** ⇒ **not** the familiar GitHub re-evaluation lag.
- `statusCheckRollup: FAILURE` was the blocker: the `03:09:50Z` run (`pull_request`, failed correctly —
  no review existed) sat beside the `11:19:22Z` run (`pull_request_review`, passed) on the same commit.
- `gh run rerun <stale_run_id>` → `CLEAN` on the next poll. The rerun is **truthful**: the review
  genuinely exists at that SHA, so re-evaluating the same condition is honest, not a bypass.

**It is structural, not a one-off.** All four `src/` PRs of sprints 39–40 carry two `architect-review`
check-runs on their head SHA, and in each the *earlier-created* run id has the *later* `completed_at` —
the signature of a manual rerun:

| PR | head | rerun completed | note |
| --- | --- | --- | --- |
| #107 | `b42e52f` | 14:04:33Z | merged **14:04:51Z** — 18s later |
| #115 | `13149da5` | 23:54:08Z | matches the session's "poll and rerun" at 23:52 |
| #117 | `490fb1cc` | 02:22:39Z | |
| #119 | `d70e9ce` | 11:22:36Z | the forensic case above |

The ruleset (`18847725`) has `bypass_actors: []` and `enforcement: active`, and there is no classic
branch protection, so **none of these could have merged without the rerun**. This is a 100% tax on code
PRs — roughly 7 minutes of re-diagnosis on #119 alone, and it recurs every sprint.

**Open uncertainty — do not build a fix on an assumed rule.** GitHub's exact dedupe semantics for
multiple same-name check-runs on one SHA are **not** pinned down by this evidence, and the record is
genuinely contradictory: #107 *still* carries a `failure` `architect-review` check-run on its head
commit and merged anyway, while #119 with one red and one green was hard-blocked. Any fix must be
verified against the live API rather than reasoned from a presumed latest-per-name rule. Note this also
**corrects** [github-workflow-traps] item #5, which claimed GitHub "supersedes by latest-run-per-name
once it catches up" — #119 disproves that: it never self-cleared.

**What to do (options considered 2026-07-17, none chosen — owner deferred):**

1. **Auto-heal.** After the review-triggered run passes, have it `gh run rerun` the stale failing run
   on the same SHA. Removes the tax with no reliance on human memory. **Cost:** `hitl-review.yml` gains
   `actions: write` — a permission escalation on the security gate itself, which is the surface you'd
   least want widened. Weigh that against the tax honestly.
2. **Codify the workaround in `/pr-checks`.** No CI change, no new permission. Teach the skill the
   stale-red signature (`BLOCKED` + rollup `FAILURE` + a superseded `architect-review` red on head) and
   have it offer the rerun. Keeps the one-command tax but removes the re-diagnosis.
3. **Draft-first.** Open the PR as a draft (the gate's existing `if: draft == false` emits no check-run),
   post the fresh-session review on the draft, then `gh pr ready` — the gate fires once, finds the
   review, and goes green first time. No CI or permission change. **Cost:** relies on remembering
   `--draft`; a forgotten flag silently reinstates the trap.

**Explicitly NOT:**
- **Do not make the `pull_request` run `skip` for `src/` PRs.** GitHub treats a **skipped** required
  check as **successful** — that is precisely the BL-10 / BL-18 trap — so this would convert the repo's
  strongest gate into a green-for-the-wrong-reason hole. The worst available outcome.
- **Do not add a `paths:` filter** to the `pull_request` trigger. A required check that *never reports*
  leaves docs-only PRs blocked forever on "Expected"; the always-run + `exit 0` docs exemption exists
  for exactly this reason.
- **Do not add a `name:` override** to the job (BL-11 / FD5): it renames the check-run and strands the
  ruleset's requirement, which `tests/test_ci_config.py` pins against.
- Not a relaxation of the gate. The `pull_request` run's failure is **correct** and must stay — the
  defect is that it lingers after being superseded, not that it happens.

**Related:** BL-11 (the ruleset and its required-check contexts), BL-10 / BL-18 (the `skipped` != `failure`
family this fix must not fall into), BL-6 (a separate machine identity — the real fix for the shared-identity
constraint that forces the header/attestation design in the first place), BL-25 (whether the backlog belongs
in GitHub Issues). Aligns with the recurring theme in [github-workflow-traps], inverted: here a check is
**red for a stale reason** rather than green for a wrong one.

### BL-36 — Low-priority cleanups deferred from the BL-2 sprint-41 Architect reviews (escalation round-trip)
*(added 2026-07-18, T6 — collecting the non-blocking notes from the fresh-session Architect reviews of
sprint 41's T3 (#131) and T4 (#133) PRs, so they aren't lost now that BL-2 is complete)*

**Why:** each of these was raised as an explicitly **non-blocking** note during a sprint-41 review and
merged unfixed by design — none blocks correctness, but each is a small quality/robustness improvement
worth doing when the area is next touched. Grouped rather than filed one-per-item because they are all
small and share the BL-2 escalation surface.

**Items:**

1. **`_ANSWER_LINE_RE` is duplicated verbatim** across `tools/issue_io/github.py:23` and
   `tools/slack_io/escalation.py:30` (identical `re.compile(r"^\s*(\d+)\s*[:.)]\s*(.+?)\s*$")`). The two
   escalation transports parse the human's numbered-answer lines with byte-identical regexes; a shared
   constant (a small pure `answers` helper both import) would keep them from drifting. Low — they are
   correct today and both are unit-tested.
2. **The oversized-digit `int()` guard is missing from the issue path.** `slack_io.parse_thread_answers`
   wraps `int(match.group(1))` in a `try/except ValueError` so an adversarial huge digit-run (tripping
   `sys.get_int_max_str_digits`) is treated as a non-matching line, not a crash;
   `issue_io.parse_issue_answers` (`github.py:153`) does the bare `int(match.group(1))` with no guard. The
   issue body is less adversarial than a Slack reply (it comes back through `gh`), so this is lower-risk,
   but the asymmetry is worth closing — ideally by item 1's shared helper, which would carry the guard to
   both.
3. **No aggregate message-length cap on the Slack escalation post.** `render_question_message` caps each
   question's length, but a run paused on *many* questions could still assemble a body past Slack's
   ~40k-char `chat.postMessage` limit. A total-length cap (truncate-with-elision past N questions/chars)
   would make the post robust to a pathological question count. Low — real pauses carry a handful of
   questions.
4. **`cli.resume` lost its early `--loop` validation** (T4-review note). After the T4 refactor to call
   `runner.resume_run`, an unknown `--loop` name now fails **late** with a raw `KeyError` after the issue
   read, rather than early with a clean message. Restore an upfront validation of the loop name (or have
   `_resolve_loop` raise a typed error the CLI renders as `typer.BadParameter`).
5. **`_resolve_loop` / the named-loop registry is duplicated** across `cli.py:32` and `runner.py:40`
   (T4-review note). Both define their own `_resolve_loop`; the two should share one source of truth
   (lift it into `runner` or a small `loops` helper and have `cli` import it) so the loop registry can't
   diverge between the CLI and the programmatic entrypoints.

**Notes / where to look:** `src/loop_engine/tools/slack_io/escalation.py`,
`src/loop_engine/tools/issue_io/github.py`, `src/loop_engine/cli.py`, `src/loop_engine/runner.py`. Full
review reasoning is on PRs #131 and #133 (`gh pr view <n> --comments`).

**Related:** [BL-2] (the sprint whose reviews surfaced these), [BL-9] (the other "issue-path cleanup"
grouping — items here are the Slack-era siblings).

### BL-37 — The Slack inbound surface (command + escalation round-trip) has never been exercised live
*(added 2026-07-18, T6 — flagged while closing BL-2: "complete and hermetically verified" is not "proven live")*

**Why:** every green check on the Slack **inbound** work is hermetic. Pass 2's `/agent-run` command
(sprint 40) and pass 3's escalation round-trip (sprint 41) are tested only against a **fake `WebClient`
and a fake listener**, with **synthetic `events_api`/`slash_commands` envelopes** hand-built in the
tests. **No real Socket Mode session has ever fired** — not one live `/agent-run`, not one live thread
reply folded back. The docs describe Slack as "the live inbound path," but that is the *design intent*
(the surface now meant to be live), not an executed smoke. This is the exact shape of **[BL-24]** — a
surface verified structurally but never run — one door over.

**What a live smoke catches that the hermetic suite structurally cannot:**
- **Real `events_api` payload shape.** `daemon.py` reads `payload["event"]["channel"]` / `thread_ts` /
  `bot_id` / `subtype` / `text`. If a real Slack `message.channels` delivery nests those differently,
  the daemon silently drops the reply — and every fake in the suite is built to the *assumed* shape, so
  the suite cannot disprove the assumption. **Highest-value unknown.**
- **App-config correctness.** Whether the T6 operator step (`message.channels` event subscription +
  `channels:history` bot scope) actually causes thread replies to be delivered. A missing subscription/
  scope is invisible to every test and is the single most likely real-world failure.
- **Connection liveness.** That the daemon's outbound Socket Mode WebSocket stays up and
  `SocketModeClient` reconnect/backoff behaves under a real connection.
- **Self-trigger + channel-scope under real payloads** (the bot's own post carries a real `bot_id`; a
  foreign-channel message carries a real `channel`).

**Why it is NOT a `live-verify` V-run.** That subagent is scoped to disposable-scratch-repo **factory**
flows (§5 github verbs / §7 maintenance / §8 bootstrap / §1 cost smoke) and **explicitly excludes**
inbound trigger surfaces (§6 webhook is out for needing live infra). A Slack smoke needs a configured
Slack app, a long-lived `slack-listen` daemon, a run engineered to actually **pause** on an escalation,
a **human posting the thread reply**, and real Anthropic spend — an **operator-run manual smoke**, not
an automatable V-run. Runbook: **`docs/slack_escalation_live_smoke.md`**.

**Shape (not urgent, needs explicit authorization — real money + real Slack side effects):** run the
runbook once in the same real-key host session as BL-3's caching/§1 cost smoke (they share the scarce
prerequisite: a real key and real spend). Capture the evidence the runbook lists; record the discharge
(or any finding) back here. Until then BL-2 stands as **complete + hermetically verified, live smoke
deferred**.

**Related:** [BL-2] (the surface this verifies), [BL-24] (the analogous never-run-live `trigger/`
webhook — same "structurally verified, never exercised" shape), [BL-3] (the real-key host session to
fold this into), [BL-7] (the PM-can't-escalate gap — relevant to *engineering* a run that reaches a
human escalation).
