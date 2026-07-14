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

### BL-17 — Retire `feat/**`: drop it from the ruleset's targets, then delete the branch
*(added 2026-07-14, sprint 35 Task 5 — deferred by the repo owner, who was away from a terminal
when the migration merged; it is the one step of Task 5 left unexecuted)*

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
