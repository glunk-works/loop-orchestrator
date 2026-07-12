# loop-engine — Backlog

Post-migration / out-of-band ideas that are **not** part of the current
`docs/migration_roadmap.md` phases. Captured here so they aren't lost; each is a
candidate to promote into a phase/sprint plan later. Nothing here is scheduled or
committed to a design yet.

> Scope note: `docs/migration_roadmap.md` remains the authoritative record for the
> in-flight MCP + LangGraph + isolation migration. This file is for *product*
> ideas beyond it.

## Open items

### BL-1 — In-loop code review of the Coder's output (Architect / QA persona + gate)
*(added 2026-07-10, from repo owner)*

The default loop is `PM → Architecture → Agile Sprint Breakdown → Coder/IaC`, and
each stage passes a content **gate** (accept / revise / escalate). Today the
Coder's implementation output is gated only by its own `CoderGate` /
`RalphCoderGate` (green-test gate) — there is **no dedicated review of the sprint's
code by an Architect or QA persona** inside the loop. The only architect-level
review is the *dev-workflow* HITL step (a human Opus session reviewing a diff),
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

### BL-3 — Review the prompt-caching implementation (correctness + improvement)
*(added 2026-07-10, from repo owner)*

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
owner's own account. So when Claude opens a PR and posts an Architect HITL review on
it, GitHub renders it as *the owner reviewing their own PR*. Today this is patched by
convention: every posted review is prefixed `**Opus/Architect HITL review
(automated)**` so authorship is unambiguous in the text (`.ai/context/workflow.md`).
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
