# V3 record — fill-in template

Paste this over the existing `## V3 — forced issue-escalation round-trip — NOT STARTED`
section in `sprints/DEFERRED_VERIFICATION.md` once the host session runs, replacing the
three-line placeholder. `[FILL]` marks what only the host run can supply; everything else
is already established and can stand as written.

Style matches the V1/V2 records: a blockquoted `RESULT` block, then Config / Outcome /
Independently verified / Consequence, then any findings as their own named subsections.

Lands via the sprint-27 PR alongside Task 8 (a V3 PASS is what unblocks Tasks 8 and 9;
Task 9 then deletes this whole file, so this record is the gate evidence, not a permanent
artifact).

---

## V3 — forced issue-escalation round-trip — **[FILL: PASS | PASS (qualified) | FAIL]**

Host session [FILL: date], Opus/Architect. Harnesses: `scratch/v3a_verbs.py` (verb-level,
no LLM) and `scratch/v3b_engine.py` + `v3b_forcing_input.md` (engine-level). Plan:
`scratch/v3_run_plan.md`. Disposable scratch repo `[FILL: owner/repo]`, deleted afterward.

Run in two layers so a defect in the verb layer costs nothing: **V3a** proves the MCP
`create_issue`/`read_issue` verbs and the `mcp_issue_filer`/`mcp_read_issue` adapters
against a real `gh` and a real GitHub Issue (§9 bullets 1–3, zero budget); **V3b** proves
the engine's `issue_filer` write seam and `cli`'s reader seam under a real forced pause
(§9 bullet 4 + the R1–R7 wiring).

### V3a — verb-level round-trip — **[FILL: PASS | FAIL]**

- **Provider launch (B3/R7).** `build_issue_provider()` launched the `issue` server and
  exposed exactly `{create_issue, read_issue}`. [FILL: confirm on host — this already
  passed locally under `hatch run` on 2026-07-11, so R7 is a latent fragility, not a
  blocker.]
- **Real `create_issue` through the server.** Issue `[FILL: #N]` created on the scratch
  repo, carrying the `loop-engine/needs-human` label; the returned `IssueRef`'s
  number/url agree with `gh issue view`.
- **Real `read_issue` through the server.** With an ` ```answers ` comment posted, the
  server's returned JSON was **[FILL: byte-identical / NOT identical]** to
  `gh issue view --json state,body,comments` run directly. *This is the bullet the
  hermetic suite structurally cannot cover — every Sprint-26 test saw a monkeypatched
  shape, never `gh`'s real payload.*
- **Adapters vs classic.** The same `State`/`Question` pair filed through
  `mcp_issue_filer(provider)` and through classic `file_question_issue` produced issues
  **[FILL: identical / differing]** in title/body/labels, and `mcp_read_issue` +
  classic `read_issue_answers` returned the same answers map for the same issue.
- Evidence: `scratch/v3a_evidence/`. Cost: **$0** (no LLM).

### V3b — engine-level round-trip — **[FILL: PASS | FAIL]**

- **Config.** Pause leg: `LOOP_ENGINE_ISOLATION=none`, budget `$1.00`, injected
  `issue_filer=mcp_issue_filer(provider)`. Resume leg: `LOOP_ENGINE_ISOLATION=container`
  (`LOOP_ENGINE_DEV_IMAGE=loop-engine-dev:latest`), budget `$[FILL]`, injected
  `cli._issue_reader = mcp_read_issue(provider, …)`.
  *Note the asymmetry, and why it is correct:* sprint 27's security consideration (5)
  requires `container` on the grounds that V3 "executes model-generated code". **The pause
  leg executes none** — it pauses at the PM stage, upstream of the Coder. The **resume**
  leg does reach the Coder, and there `container` is mandatory.
- **Trigger.** [FILL: the unsatisfiable requirements doc (PM `CriticGate` exhaustion) |
  `--force-gate` (deterministic always-ESCALATE PM gate)]. Both exploit the same
  structural fact: the PM stage has `resolvers=[]` and `escalate_on_exhaustion=True`, so a
  PM escalation has no automated resolver above it and `_pause_for_issue` fires at stage 0
  — the cheapest reachable pause in the pipeline.
- **Pause.** `run_id=[FILL]` reached terminal **`AWAITING_ISSUE`** (exit 2), wrote an
  `AWAITING_ISSUE` snapshot, and filed **real issue `[FILL: #N]`** on the scratch repo
  **through the MCP server** — with `state.pending_issue` populated and `[FILL: N]`
  question(s) in the engine's unresolved order. Cost: `$[FILL]`.
- **Answer.** One ` ```answers ` comment, one `N: answer` line per filed question.
- **Resume.** `cli.resume --from-issue [FILL]` read the issue **through the MCP reader**,
  parsed the answers, located the snapshot from the issue body, marked the questions
  `resolved_by: human:[FILL]`, folded them in via the PM, and re-entered at
  `[FILL: stage]`. The run advanced **past** the stage it paused on and reached terminal
  `[FILL: COMPLETED (exit 0) | BUDGET_EXCEEDED (exit 3) after the resume demonstrably took
  effect]`. Cost: `$[FILL]`.
- **Re-pause?** [FILL: The resumed run did NOT escalate again — R2 was not exercised live.
  | The resumed run RE-PAUSED, and the second issue landed on `[FILL: repo]` — **R2 firing
  live**: `cli.resume` threads no `issue_filer` into its inner `run_graph_loop`, so the
  second filing went through the classic in-process `gh` path, which under `container`
  inherits the worktree cwd inside loop-engine. See R8 below.]
- Evidence: `scratch/v3b_evidence/`.

### Independently verified (not merely trusting the harness's self-report)

[FILL — mirror V2's discipline. At minimum:]
- `gh issue view [N] --json state,body,comments` on each filed issue matches the evidence
  files captured through MCP.
- The `AWAITING_ISSUE` snapshot's `pending_issue.number`/`url` match the real issue.
- The post-resume snapshot's `questions[].resolved_by == "human:[N]"` and `stage_history`
  advances past the paused stage index.

### Finding R8 (new, from V3 drafting) — the issue verbs have no explicit repo target

**Confirmed pre-existing, not an MCP regression; surfaced while planning V3.**
`issue_io.create_issue` shells `gh issue create` with **no `--repo`**, so `gh` resolves
the destination from the **cwd's** git remote. Under isolation, `worktree_run` does
`os.chdir(loop-engine/.worktrees/<run_id>)` — so an **in-process** `gh` call resolves to
**the orchestrator's own repo**. That is how issues **#16, #19, #21** came to be filed on
`glunk-works/loop-engine` by earlier host sessions: real escalation issues for managed-repo
runs, landing on the project repo, silently.

An **MCP-launched** server instead keeps the cwd it was *launched* with, so the MCP path
incidentally **fixes** this when the provider is entered before the chdir (which is what
both V3 harnesses do). The classic in-process path is the one that leaks.

Route into **Task 8** alongside R1–R7: the destination of a human-escalation issue should
be **explicit** (a repo argument threaded to the verb), not implicit cwd coupling. Under
`flows/maintenance` the cwd-pinned-to-the-clone behavior is plausibly the *intended*
semantics — which is the argument for making it explicit rather than accidental.

### Consequence

[FILL — on PASS:]
**V3's obligation is discharged.** Sprint 27's **Task 8** (issue-path flip onto MCP,
carrying findings R1–R7 **+ R8**) and **Task 9** (delete this file, close Phase 6) are
**unblocked**.

[FILL — on FAIL:] Per the sprint's own rule, a failed V-run means *"the path isn't proven —
don't flip yet"*, **not** "keep a break-glass" (FD2). Record the defect, fix it, re-run V3,
then flip.
