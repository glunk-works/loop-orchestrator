# Dev-workflow protocol: model routing + session handoff

This repo is built with two models, split to keep each session lean and single-model
(the fix for hitting session limits — long Opus sessions accumulate huge context).
Work is externalized into `.ai/` so a fresh session can rehydrate cheaply instead of
inheriting a bloated context window.

## The two state layers (do not conflate)

- **`.ai/`** — *this* dev-workflow's state (how Claude Code sessions hand off).
  - `.ai/next-steps.md` (git-tracked) — the human-readable cursor: current phase/sprint, status, next action, which model to use, HITL-gate state. A **thin pointer** into the roadmap + the active sprint file; not a second copy of them.
  - `.ai/state.json` (git-ignored) — the machine cursor (`current_sprint_id`, `sprint_status`, `assigned_model`, `last_commit`, `next_action`, `pointers`).
  - `.ai/context/` (git-tracked) — heavy reference loaded on demand (`modules.md`, `conventions.md`, this file).
  - `.ai/archive/` (git-ignored) — retired sprint snapshots.
- **`.agent/STATE.md` + `.agent/MEMORY.md`** — the loop-engine **product's** runtime Ralph state, written when the engine itself runs. Nothing in the dev workflow writes these.

The deep, authoritative history stays in `docs/migration_roadmap.md`; `.ai/` never
duplicates it, only points at the current cursor within it.

## Model routing

- **Architect = Opus.** Decide *what* to build or *whether* a diff is correct: architecture, design, sprint/phase planning (one question at a time, HITL gates), HITL review of a coding diff, boundary calls, non-trivial debugging, roadmap/memory updates.
- **Coder = Sonnet.** Execute an already-defined spec: implement a sprint task, write/adjust tests, mechanical refactors, run the green gate (`hatch run lint/format/test/audit/sbom`), fix lint.

Phase 1 (now) is **manual, persona-driven** routing — you or the orchestrator pick the
model. Automated routing (a proxy/router) is explicitly out of scope until the
thresholds are proven.

## Switch points across a sprint

```
OPUS (plan)    design/plan the sprint -> write sprint_plan.md + roadmap -> /handoff
   |                                                                          |
   v   (fresh session, /model sonnet)                                         |
SONNET (code)  /resume -> branch sprint/NN-slug -> implement + tests -> green
   |           gate -> /critic-gate (QA-critic pass) -> commit -> push        |
   |           -> /handoff                                                    |
   |                                                                          |
   v   *** NEW SESSION (context empty), then /model opus ***                  |
   |   /model alone does NOT clear context — a reviewer holding the authoring |
   |   context proofreads its own reasoning instead of re-deriving it.        |
OPUS (review)  /resume -> /code-review the diff -> HITL gate -> update roadmap
   |           -> open PR (base: main) -> STOP                                |
   |                                                                          |
   v                                                                          |
HUMAN          review the PR -> merge = approval -> /archive-sprint, plan next
```

Each box is its own **short, single-model session**. The expensive planning context
never carries into the coding session, and vice-versa — that is the token saving.

- **Primary path: session handoff** (above). Use it at every sprint boundary.
- **Secondary path: in-session subagent.** For a small, well-scoped coding task that
  doesn't warrant a full session switch, an Opus session may dispatch the Sonnet
  **`coder`** subagent (`.claude/agents/coder.md`) via the Agent tool. The subagent's
  result returns into the Opus context, so prefer the handoff path for anything large.

## Integration gate: every sprint lands via a pull request

**A merged PR is the human approval.** Nothing reaches the integration branch
without it. Claude commits and pushes freely on a sprint branch, opens the PR, and
**never merges** — the same posture the engine enforces on managed repos, where
`tools/repo_io` deliberately exposes no merge verb.

- **Branch per sprint:** `sprint/NN-slug`, cut from `main`.
- **PR base is `main`.** Every sprint PR merges into the repo default branch. A PR base
  may be any branch that exists on the remote — it does not have to be the default —
  but `main` is the one this repo uses.

  > **Historical note — the `feat/mcp-langgraph-migration` era (sprints 26–35, now over).**
  > While the MCP/LangGraph migration was in flight, `main` was deliberately left
  > untouched: every sprint branch was cut from, and every sprint PR based on,
  > `feat/mcp-langgraph-migration` instead, keeping 113 commits of in-progress
  > migration work off the default branch until it was whole. Sprint 35's Task 5
  > landed that branch on `main` as **one deliberate merge commit** (PR #58, merge
  > commit `d2135e7`, 2026-07-14) — never squashed, since squashing would have
  > collapsed the entire migration's history into a single commit. That was the
  > **one-time exception** to this repo's squash-merge convention, and it is spent:
  > `allow_merge_commit` was turned back off immediately afterwards (BL-13 closed),
  > so the merge-commit button no longer exists on any PR. **If you find a merge
  > commit in `main`'s history, that is why — and there should be exactly one.**
  > The rules above ("cut from `main`", "base is `main`") are now simply true, with
  > no window or exception attached.

- **CI runs on the PR.** `.github/workflows/ci.yml` triggers on `pull_request:` with
  no branch filter, and on `push:` to `main` and `feat/**` (the latter is what let CI
  build on `feat/mcp-langgraph-migration` during the migration; it becomes dead
  weight once that branch is retired in Task 5 and should be stripped from both
  `ci.yml` and the `protected-integration-branches` ruleset then) — so a sprint
  branch pushed *without* a PR gets **no CI at all**. The PR is what turns the
  lint → format → test → gitleaks → sbom gate on for sprint work; the local
  `hatch run` green gate is a pre-check, not the gate of record.
- **Claude does not merge, and does not force-push a pushed branch** without asking.
- A PR gates *integration*, not *committing* — local commits on a sprint branch are
  still free and expected.
- **A squash-merged branch is dead — never push to it again.** The squash puts a *new*
  commit on the base with the same content, so the branch's original commits are still
  "unmerged" and re-applying them conflicts. Start a fresh branch off the updated base
  and cherry-pick anything that didn't land. This bites hard because of the next rule.
- **A conflicted PR runs no CI, silently.** GitHub cannot build the `refs/pull/N/merge`
  ref when a PR is not mergeable, so `pull_request` workflows never start — and *zero
  checks* is visually almost identical to *checks still queuing*. If a PR shows no
  checks after a minute, check `mergeable` before assuming CI is slow:
  `gh api repos/<owner>/<repo>/pulls/<N> -q '.mergeable_state'`.

### The QA-critic pass runs Coder-side, before the Architect review (`/critic-gate`)

After the green gate and before `/handoff`, the implementation session runs **`/critic-gate`**:
a read-only critic pass over the diff that catches the cheap, mechanical, boundary-shaped
defects Sonnet-side, so the fresh-session Opus review spends its attention on judgment — and
so nothing ships with *no* critic having looked (the sprint 27 Task 8 failure below is
exactly what one standing critic pass defends against). The session orchestrates it: a
subagent cannot spawn subagents, so the **session** spawns coder and critics as siblings.

**The gate proposes; the human picks — it does not auto-fan-out.** Each critic is real spend
(mostly Opus subagents) and `architect`/`security-critic` overlap, so `/critic-gate` works out
which critics a diff *warrants* from the table below, presents that list with a reason each,
and spawns **only** what the human confirms (or the critics named explicitly in the call). A
light change may want one critic; a trust-boundary change may want the full set.

> **`/critic-gate` is defense-in-depth that runs EARLIER — it is NOT the `architect-review`
> CI gate and never satisfies it.** The fresh-session Architect review still happens after
> `/handoff`, unchanged (next section). Two properties keep the pass honest: the critics are
> **separate subagents** (fresh context — not `/model`-switching and self-reviewing), and
> they are **read-only** (they *find*; the coder *fixes* — so a critic can't wave its own
> problem through).

Propose by what the diff touches — don't offer critics that have nothing to look at:

| Diff touches… | propose |
| --- | --- |
| any `src/` | **`security-critic`** (taint / trust-boundary) **+ `architect`** (correctness pre-review) |
| a guard surface (new subprocess/write/import/MCP verb) | **also `guard-adversary`** (`isolation: "worktree"`) |
| a test-validity sprint (BL-23) | **`mutation-triage`** (sharded, N in parallel) |
| load-bearing docs / roadmap / CLAUDE.md | **`docs-consistency`** |

#### The agent catalog (spawn via the Agent tool by `subagent_type`)

All live in `.claude/agents/`. A definition loads at session start; name it here so a
`/resume`'d session knows to reach for it (the same pattern that puts `coder` in the loop).

- **`coder`** (Sonnet, read/write) — implement one defined sprint task; the secondary
  in-session path when a full handoff is overkill.
- **`architect`** (Opus, read-only) — correctness + structural-invariant review; the
  `/critic-gate` pre-review and a `/code-review` fan-out target. **Not** the CI gate.
- **`security-critic`** (Opus, read-only) — threat-model SAST / taint-flow on a `src/` diff.
- **`guard-adversary`** (Opus, worktree) — BL-32: adversarial invariant-injection audit of
  the static structural guards; run when a diff touches a guard surface, or as its own beat.
- **`mutation-triage`** (Sonnet, read-only) — BL-23: triage a shard of mutmut survivors into
  keep/fix/delete; spawn N in parallel on a test-validity sprint.
- **`live-verify`** (Opus, worktree) — a DEFERRED_VERIFICATION V-run against a disposable
  scratch repo. **Requires explicit per-run authorization** (real GitHub side effects + spend).
- **`docs-consistency`** (Opus, read-only) — cross-check load-bearing prose against ground
  truth; run before a roadmap-heavy PR or at archive time.

### The Architect's HITL review is a posted GitHub review, not just prose

**It is a CI gate** (`.github/workflows/hitl-review.yml`): any PR touching `src/` fails
the `architect-review` check until a review carrying the header + attestation below is
posted **against that PR's current head commit**. Docs / sprint-plan / `.ai/`-cursor PRs
are exempt (no runtime behavior to get wrong). A review of an *earlier* commit does not
count — push first, then review the final diff.

This is a check rather than a convention because the convention failed. Sprint 27's Task 8
shipped as a fully green PR (#32) whose R8 fix covered `cli.py` and silently left every
fresh-run path — `runner.run_new`, the trigger surface, `flows/maintenance` — still filing
escalation issues against the wrong repo. The suite passed, CI passed, and the review that
would have caught it was simply never run. It was caught only by a review done *after* the
merge (findings in PR #34). A rule that lives only in prose is a rule that gets skipped.

#### The review runs in a FRESH session — this is the point, not a detail

> **`/model opus` mid-session is NOT a review session.** Switching model does not clear
> context. The reviewer still holds every assumption the author made, so it re-reads its own
> reasoning and agrees with it. That is not a review; it is a proofread.

The required sequence — the same `/handoff` boundary the model split already uses:

```
SONNET (code)   implement -> green gate -> /critic-gate -> push -> open PR -> /handoff
                                   ↓
                        *** NEW SESSION. Context empty. ***
                                   ↓
OPUS (review)   /resume -> /code-review the diff -> post review -> HITL gate
```

`/resume` rehydrates from `.ai/` — the externalized cursor — **not** from a memory of having
written the code. That is exactly what makes the review adversarial: the reviewer must
re-derive intent from the sprint plan and the diff, the way a stranger would, and a claim the
author found obvious has to survive being read cold.

Both prior reviews violated this and it shows: #32's review was done by `/model opus` inside
the authoring session, and #34 was authored by Opus and would have been self-reviewed. The
gate now requires the reviewer to attest:

```
*Fresh-session review: this session did not author the diff.*
```

CI cannot observe a session boundary. The attestation does not prove one — it makes
reviewing your own work a *knowing false statement* rather than something that quietly
happens. That is as far as a check can go; real attribution needs a separate machine
identity (**BL-6**).

Two distinct artifacts — do not conflate them:

- **The PR *description*** says what the change is and why (scope, links to the
  `sprint_plan.md`). It is authored, editable prose.
- **The PR *review*** is the Opus/Architect verdict on the diff, posted with
  `gh pr review --comment`. It is a timestamped, threadable event — a real audit
  record that survives edits to the description, and that cannot be mistaken for the
  human's approval.

Rules:

- **`--comment` only. Never `--approve`, never `--request-changes`.** The merge is the
  human's approval; a Claude-issued approval would be a gate approving itself. This is
  also enforced by GitHub: the `gh` token authenticates as **`Seuss27`**, the same
  identity that opens the PR, and GitHub forbids approving your own PR.
- **Prefix every posted review with `**Opus/Architect HITL review (automated)**`.**
  Because Claude and the repo owner share the `Seuss27` identity, a posted review
  otherwise renders as the owner reviewing their own PR. The header is what makes
  authorship unambiguous. (A separate machine identity would make attribution *real*
  rather than declared — tracked as **BL-6** in `docs/backlog.md`.)
- **Inline comments for line-anchored defects; the summary body for the scope verdict.**
  `/code-review --comment` posts findings inline on the diff — right for concrete bugs.
  But most of the Architect review is *not* line-anchored ("does this honor the sprint
  plan's locked FD1/FD2/FD3?", "is the scope exactly these files?"); that judgment
  belongs in the review summary.

Nothing here changes on-branch commit hygiene: commits stay signed, and the green
gate still runs locally before the push.

## The skills

- **`/critic-gate`** — run in the implementation session **after the green gate, before
  `/handoff`**. Proposes which read-only critics the diff warrants (the table above) and
  spawns only what you confirm — no auto-fan-out — then aggregates findings for the coder to
  fix and iterates to clean. Defense-in-depth that runs *earlier* — **not** the
  `architect-review` CI gate, which still runs fresh after handoff.
- **`/resume`** — run at the **start** of a session. Reads `.ai/state.json` +
  `.ai/next-steps.md` + the pointed sprint_plan + roadmap NEXT ACTION, states the exact
  pick-up point, and adopts the assigned persona/model. (Distinct from the
  `loop-engine resume` CLI subcommand — different namespace.)
- **`/handoff`** — run **before** switching model/session. Serializes the current cursor
  to `.ai/state.json`, regenerates `.ai/next-steps.md` (what was done, what's next, which
  model next), and reminds you to commit if the tree is dirty. Does **not** archive.
- **`/archive-sprint`** — run **only** when a sprint is HITL-approved **and** committed.
  Moves its `next-steps.md` snapshot into `.ai/archive/`, advances `.ai/state.json` to
  the next sprint, and seeds a fresh `.ai/next-steps.md`.
