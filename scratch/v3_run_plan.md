# V3 run plan — forced issue-escalation host round-trip

Drafted 2026-07-11 (Opus/Architect). Untracked (`scratch/`), like the V2 harness.
Gates sprint-27 **Task 8** (issue-path flip onto MCP + findings R1–R7) and **Task 9**
(delete `DEFERRED_VERIFICATION.md`, close Phase 6).

Obligation is `sprints/DEFERRED_VERIFICATION.md` §9 (four bullets) plus the engine-level
seam wiring. Human-operated: real `gh` auth, real Anthropic budget, real GitHub side
effects.

---

## 0. Pre-flight blockers (do these before spending anything)

### B1 — The issue lands in whatever repo the cwd resolves to. **CONFIRMED: this has already happened three times.**

`tools/issue_io/github.py::create_issue` shells `gh issue create` with **no `--repo`
flag**; `gh` infers the target repo from the cwd's git remote. `build_issue_provider()`
→ `build_provider_for(["issue"])` builds `StdioServerParameters(cwd=spec.cwd)`, and
`loop_engine.mcp.json` declares the issue server with `"cwd": null` — so the server
subprocess **inherits the launching process's cwd**.

**This is not hypothetical.** Issues **#16, #19, #21** on `glunk-works/loop-engine` are
real loop-engine escalation issues filed by earlier host sessions, straight onto the
project repo.

**The mechanism, exactly** (worth understanding — it decides the harness design):
`worktree_run` calls `set_state_root(origin)` then **`os.chdir(worktree)`**, where the
worktree is `loop-engine/.worktrees/<run_id>`. So with isolation **on**, an in-process
`gh` call inherits a cwd *inside loop-engine* → the issue lands on loop-engine. With
`LOOP_ENGINE_ISOLATION=none`, `worktree_run` is a **no-op passthrough with no chdir** and
cwd stays put.

An **MCP-launched** server, by contrast, keeps the cwd it was **launched with**. So the
harness enters `build_issue_provider()` *before* `worktree_run` chdirs — pinning the
server (and therefore `gh`) to the scratch clone regardless of what the orchestrator does
afterward. The MCP path incidentally *fixes* B1; the classic in-process path is the one
that leaks.

**Mitigation:** every V3 step runs with cwd **inside the disposable scratch clone**, and
both harnesses hard-refuse to proceed if `gh repo view` resolves to `*/loop-engine`.

```bash
cd "$SCRATCH_CLONE" && gh repo view --json nameWithOwner   # MUST print the scratch repo
```

**Candidate finding (R8) for Task 8:** the issue verbs have no explicit repo target — the
destination of a human-escalation issue is implicit cwd coupling, and under isolation it
resolves to the *orchestrator's own repo* rather than the managed one. Not an MCP
regression (classic `file_question_issue` has the identical property), and under
`flows/maintenance` cwd is pinned to the managed clone, which is plausibly the *intended*
semantics — but as #16/#19/#21 show, the failure mode is real and silent.

### B2 — The label must pre-exist in the scratch repo.

`create_issue` passes `--label loop-engine/needs-human`; `gh` fails hard on an unknown
label. Create it at setup:

```bash
gh label create 'loop-engine/needs-human' --description 'loop-engine escalation' --color B60205
```

### B3 — R7 launch risk: **CLEARED, no action needed.**

`loop_engine.mcp.json` launches the issue server with `"command": "python"`. If the
provider were entered from a process whose PATH `python` cannot import `loop_engine`, the
server would die at startup and V3 would fail for a reason unrelated to the issue path —
and R7 (use `sys.executable`) is scheduled to land **in Task 8**, which is itself gated on
V3. Circular.

**Resolved empirically (2026-07-11, costs nothing — a provider enter does tool discovery
only, no `gh` call):** under `hatch run`, the server launches and exposes exactly
`{create_issue, read_issue}`. **R7 does not block V3 and stays in Task 8 as planned.**
It remains a real latent fragility (it works only because hatch's env python is on PATH),
which is why it is still a finding — just not a blocker. `v3a_verbs.py` step 0 re-checks
it on the host anyway.

---

## 1. Shape: V3 splits into V3a (free) and V3b (real budget)

§9's first three bullets are about the **verbs and adapters**. They need a real `gh`, a
real issue, and the real server subprocess — but **no LLM at all**. Only the fourth
concern (the engine's `issue_filer`/reader seams under a real pause) needs a real run.

Splitting them means a bug in the verb layer is found for **$0**, before any budget is
committed to V3b.

---

## 2. Auth — the current PAT is **not** sufficient. Read this before setup.

Current state (probed 2026-07-11): a **fine-grained** PAT (`github_pat_11…`), account
`Seuss27`, `ADMIN` on `glunk-works/loop-engine`.

Fine-grained PATs are pinned to a **selected repository list fixed at creation time**.
That produces a chicken-and-egg that blocks V3 outright:

1. It almost certainly cannot **create** a repo (that needs `Administration: write` on the
   `glunk-works` org, not on a repo).
2. **Even if it could**, a brand-new scratch repo would **not be in the token's selected-repo
   list** — so the token could not create labels, file issues, or read them on the very repo
   it just made. V3 does nothing but file and read issues, so this is fatal.

`gh repo delete` is the other verb most likely missing: it needs `delete_repo` (classic) or
`Administration: write` (fine-grained).

### Option A — **recommended.** Update the existing PAT; add no new permission classes.

Create **and** delete the scratch repo **by hand in the GitHub UI**, so the token never
needs `Administration` at all. Then edit the existing fine-grained PAT's *repository access*
to add the scratch repo, with:

| Permission | Level | Why |
|---|---|---|
| Metadata | Read | mandatory for any fine-grained PAT |
| Contents | Read | `gh repo clone` of the scratch repo |
| Issues | Read & Write | `create_issue`, `read_issue`, comments, **and labels** |

Nothing else. No `Administration`, no `Contents: write` — **V3 never pushes** (the Coder
runs in loop-engine's own worktree; the scratch clone exists only to anchor `gh`'s repo
resolution and to hold `state/` snapshots). This keeps the everyday token's blast radius
essentially unchanged and is the least-privilege path.

### Option B — an **additional**, short-lived token, if you want setup/teardown scripted.

A *second* fine-grained PAT: repository access **All repositories** in `glunk-works`,
permissions `Administration: RW` (create + delete) + `Contents: RW` + `Issues: RW`. Export
it as `GH_TOKEN` for the V3 session only — `GH_TOKEN` overrides `gh`'s stored auth for that
process tree, so the everyday token is untouched — then **revoke it immediately after
cleanup**.

```bash
export GH_TOKEN="github_pat_…"   # V3 session only; revoke after §5
```

Choose B only if you want the harness to create/delete the scratch repo itself. It trades a
short window of broad privilege for automation; A trades a little manual clicking for never
holding repo-delete power. **Prefer A.**

### Option C — a classic PAT with `repo` + `delete_repo`. **Don't.**

Simplest and works everywhere, but it is broad, long-lived, and grants write on *every* repo
the account can see. There is no reason to take that for a two-issue verification.

---

## 2b. Setup (once)

Under **Option A**: create the repo in the UI, add it to the PAT's repo list, then:

```bash
export SCRATCH_REPO="glunk-works/loop-engine-v3"     # the repo you made in the UI
gh repo clone "$SCRATCH_REPO" ~/v3-scratch
cd ~/v3-scratch
gh label create 'loop-engine/needs-human' --color d73a4a \
    --description 'loop-engine paused: questions need a human answer'
gh repo view --json nameWithOwner        # B1 check — MUST print the scratch repo
```

Under **Option B**, replace the first two lines with `gh repo create … --private --clone`.

Both harnesses re-assert the B1 check themselves and refuse to run if cwd resolves to
`*/loop-engine`.

---

## 3. V3a — verb-level round-trip (no LLM, $0). Clears §9 bullets 1–3.

**Harness: `scratch/v3a_verbs.py`.** Run with cwd = the scratch clone (B1); it refuses
otherwise.

```bash
cd ~/v3-scratch
hatch run python /workspace/scratch/v3a_verbs.py     # from the loop-engine hatch env
```


- **V3a.0 — provider launch smoke (B3).** Enter `build_issue_provider()`, list tools.
  Assert exactly `{create_issue, read_issue}`. A launch failure here is R7; stop and
  pre-land it.
- **V3a.1 — real `create_issue` through the server.** Dispatch `create_issue` with a
  throwaway title/body/label. Confirm a real issue exists, capture its number/URL, and
  confirm it carries the `loop-engine/needs-human` label.
- **V3a.2 — real `read_issue` through the server.** Post an ` ```answers ` comment on
  that issue, dispatch `read_issue` through the same provider, and assert the returned
  JSON's `state`/`body`/`comments` **equal what `gh issue view --json state,body,comments`
  reports directly**. This is the bullet that proves the server round-trips `gh`'s JSON
  faithfully rather than the monkeypatched shape the unit tests assert.
- **V3a.3 — adapters against the real server.** Build a real `State` + `Question` list,
  file via `mcp_issue_filer(provider)`, read back via `mcp_read_issue(provider, n)`, and
  assert the resulting `IssueRef` and the `parse_issue_answers` map are **identical to
  what classic `file_question_issue`/`read_issue_answers` produce against the same
  issue**. (Run classic against a second scratch issue and compare structurally — the
  issue *numbers* will differ.)

Pass criterion: all four green, evidence captured to `scratch/v3a_evidence/`.

---

## 4. V3b — engine-level round-trip (real budget). Clears the seam wiring.

### The forcing mechanism

`loops/default/loop.py` gives the PM stage `resolvers=[]`, `escalate_on_exhaustion=True`,
`max_revisions=4`. So a **PM-stage escalation pauses immediately at stage 0**: the ladder
iterates an empty resolver list, `unresolved_questions(state)` stays non-empty, and
`_pause_for_issue` fires. That is the cheapest reachable pause in the whole pipeline —
and it never reaches the Coder.

Two triggers, in order:

1. **Preferred (honest): an unsatisfiable requirements doc.** Write an input the
   `CriticGate` cannot accept in 4 revise cycles — internally contradictory, with a
   material decision genuinely absent (not merely terse; the PM will happily invent
   detail to fill a gap, but it cannot resolve a contradiction). Exhaustion →
   `_exhaustion_escalation` → empty ladder → issue.
2. **Fallback (deterministic): a forced-escalate PM gate stub** in the harness Loop.
   Everything V3 must prove — the MCP provider, the real `gh`, the real issue, both seams
   — stays real; only the *trigger* is synthetic, and the gate's judgment is already
   covered hermetically. Use this if trigger 1 converges twice.

**Budget guard:** run with `--budget 1.00`. A PM that converges anyway then dies at
`BUDGET_EXCEEDED` (exit 3) somewhere downstream rather than burning a full pipeline —
a cheap "the doc didn't force it" signal.

### Isolation — the sprint plan is over-strict here

Sprint 27's security consideration (5) says V3 "executes model-generated code on the host
→ MUST run under `LOOP_ENGINE_ISOLATION=container`". On the **pause leg** that is vacuous:
a run that pauses at the PM stage generates and executes **no code**. It bites on the
**resume leg**, which continues Architecture → Sprint Breakdown → Coder.

- **Pause leg:** `LOOP_ENGINE_ISOLATION=none` is sufficient and honest.
- **Resume leg:** `LOOP_ENGINE_ISOLATION=container`, mandatory — it reaches the Coder.

### Steps

**Harness: `scratch/v3b_engine.py`** (+ the forcing input `scratch/v3b_forcing_input.md`),
not the bare CLI: the MCP filer/reader are capability-only today (no flag selects them, by
design), so the harness injects what Task 8 will make the default — `issue_filer=
mcp_issue_filer(provider)` into the engine, and `cli._issue_reader` for the read seam. Cwd =
the scratch clone throughout (B1); it refuses otherwise. Two phases, because a human answers
in between.

```bash
cd ~/v3-scratch

# 1. pause — isolation=none is sufficient: a PM-stage pause executes NO model code
LOOP_ENGINE_ISOLATION=none hatch run python /workspace/scratch/v3b_engine.py pause \
    --input /workspace/scratch/v3b_forcing_input.md --budget 1.00

# 2. answer the printed issue with exactly ONE ```answers block

# 3. resume — isolation=container is MANDATORY: this leg reaches the Coder
LOOP_ENGINE_ISOLATION=container hatch run python /workspace/scratch/v3b_engine.py resume \
    --budget 5.00
```

Add `--force-gate` to the `pause` phase for the deterministic trigger (below).

- **V3b.1 — pause.** `run_graph_loop(..., issue_filer=mcp_issue_filer(provider))` on the
  forcing input. Assert: terminal status `AWAITING_ISSUE`, exit code 2, `state.pending_issue`
  populated, an `AWAITING_ISSUE` snapshot on disk, and **a real GitHub issue on the scratch
  repo** whose body carries the `Snapshot:` line and the numbered questions.
- **V3b.2 — answer.** Post an ` ```answers ` comment answering each filed question by
  number.
- **V3b.3 — resume.** Monkeypatch `cli._issue_reader` to `mcp_read_issue` bound to a live
  provider, then invoke `resume --from-issue <N>`. Assert: the answers are parsed, the
  snapshot is located from the issue body, `apply_answers_to_questions` marks the questions
  `resolved_by: human:<N>`, the PM folds them in, and the run **proceeds past the stage it
  paused on** rather than re-pausing.
- **V3b.4 — carry to a terminal state** under `container`, budget ~$5. A `COMPLETED` run is
  the strongest evidence; `BUDGET_EXCEEDED` after the resume demonstrably took effect is
  acceptable — V3's obligation is the issue seam, not another happy-path proof (V1 already
  did that).

Pass criterion: V3b.1–V3b.3 green, evidence to `scratch/v3b_evidence/`.

### Watch for (these become Task 8 findings if they fire)

- **R2 is live on this path.** `cli.resume` threads no `issue_filer` into its inner
  `run_graph_loop`, so if the resumed run escalates *again*, the second issue is filed
  through the **classic** `gh` path, not MCP — a silent seam gap. If V3b's resume re-pauses,
  you will see it directly.
- **R5** (resume abort-path crash) triggers on an issue closed with no answers — don't do
  that accidentally mid-run.
- **R6** (first-block-only answer parse) — post exactly one ` ```answers ` block per comment.

---

## 5. Cleanup (mandatory — real side effects)

Deleting the scratch repo deletes every issue in it, so that is the whole teardown.

- **Option A:** delete the repo in the GitHub UI, then remove it from the PAT's repository
  list (restoring the token to exactly its pre-V3 access).
- **Option B:** `gh repo delete "$SCRATCH_REPO" --yes`, then **revoke the temporary PAT**.

Then confirm B1 did not bite — that no *new* escalation issue was filed on the project repo:

```bash
gh issue list --repo glunk-works/loop-engine --label 'loop-engine/needs-human' --state all
```

**Expected: exactly #16, #19, #21** (the pre-existing ones from earlier host sessions).
Anything newer means B1 fired during V3 — close it, and record it as evidence for R8.

---

## 6. Recording the result

Append a **V3** section to `sprints/DEFERRED_VERIFICATION.md` alongside V1/V2 — PASS /
PASS(qualified) / FAIL, with the observations, the issue URLs (now dead), the cost, and
any new findings (R8 from B1, plus anything V3b turns up). That record is what unblocks
Tasks 8 and 9.

---

## 7. Incidental: V3 is the first host run on the post-collapse build

V1 and V2 ran **before** `1217f79` — on flag-*selected* paths. V3 is the first host
verification against the collapsed one-path build. The collapse is meant to be
behavior-identical, so this is not a new obligation — but if V3 trips on something V1/V2
did not, the collapse is the first place to look.
