# Deferred verification — checks that need a real host, key, or network

Every check here is **still owed**: none has been performed. They are the checks
the hermetic test suite structurally cannot make — they need a real Anthropic key,
a real authenticated `gh`, a daemon-bearing host that can bind a port, or real
side effects on GitHub. `hatch run test` passing says nothing about any of them.

This file **outlives the migration.** It began as the sprint 09–14 smoke-run list
and is now the project's standing register of unmet proof obligations; it is not a
Phase 6 artifact and does not close with it.

> **Phase 6 (sprint 27) retired the sections it actually discharged.** The
> flip-block host runs **V1/V2/V3 all PASSED**, and their results — the evidence,
> the qualifications, and findings R8/R9/R10 + F-GATE-SANDBOX / F-TOOLLOOP-CAP /
> F-CODER-NO-LINT / F-RALPH-OVERSPEC-TEST / F-RALPH-FALSE-COMPLETION — now live in
> `docs/migration_roadmap.md`'s Phase 6 row and decisions log, which is the record
> of point. Retired from this file:
>
> - **§2 (Agentic Coder end-to-end)** — **moot.** Phase 6 deleted the classic
>   agentic Coder; the code path it validated no longer exists.
> - **§3 (Ralph convergence + cost)** — **superseded by V2 PASS** (host re-attempt
>   #8, 2026-07-11: terminal `COMPLETED`, 8/8 tasks, zero escalations, $2.24/$5.00).
> - **§4 (Declarative personas parity)** — **superseded by V1 PASS.**
> - **§9 (Issue-server round-trip)** — **superseded by V3 PASS** (2026-07-12).
>
> **Section numbers are deliberately NOT renumbered.** `docs/backlog.md` (BL-3)
> cites §1, and several archived sprint plans cite §3/§6/§9; renumbering would
> silently redirect every one of those. The gaps are the point.

Sections still open: **§1, §6.** (**§5, §7 and §8 were PERFORMED live in sprint 36**
against a real disposable scratch repo in `glunk-works`; their observed results are
recorded in place below, and they are retired rather than deleted because the findings
they surfaced — [BL-28], [BL-29], [BL-30] — are not yet fixed.)

> **Sprint 36 corrected FD1's stale premise.** §5/§8 below used to assert "this
> devcontainer has no `gh` auth and no network" and all three demanded "a
> daemon-bearing host". **Measured false, 2026-07-14/15:** `gh auth status` is green
> here (`Seuss27`, fine-grained PAT with `administration=write`), the network resolves,
> and the Anthropic key is in the keyring. What §5/§7/§8 actually needed was
> *authenticated `gh` + network + a disposable scratch repo* — **none of which is a
> daemon**. "Daemon-bearing" was inherited from §6, the only section that must bind a
> port GitHub can reach; §6 stays open. That stale premise is what deferred these three
> for 25 sprints.

> ## Every open section now has a scheduled owner (sprint 35, Task 6 — agreed with the repo owner, 2026-07-14)
>
> "After the merge" had been the answer for five sprints, and **an obligation with no
> scheduled home is an obligation nobody owns** (FD4). So each one now names its destination.
> These are commitments, not suggestions — if a destination slips, move it explicitly rather
> than letting it drift back to "later".
>
> | Section | Destination | Why there |
> | --- | --- | --- |
> | **§5** `github_server` live verbs | **Sprint 36 — ✅ PERFORMED 2026-07-15** | All three needed the *same* thing: authenticated `gh`, network, and a disposable scratch repo they create and destroy (not a daemon — FD1). They shared the setup and one scratch-repo lifecycle. |
> | **§7** maintenance flow live | **Sprint 36 — ✅ PERFORMED 2026-07-15** | ⬑ |
> | **§8** bootstrap flow live | **Sprint 36 — ✅ PERFORMED 2026-07-15** | ⬑ |
> | **§1** caching + USD smoke | **Folded into [BL-3]** (prompt-caching review) | §1 needs a real Anthropic key and real spend; BL-3 needs *the same session*. BL-3 cannot assess caching without live `Cache R` data — and §1 **is** that data. Running them apart means paying for two key-bearing sessions to learn one thing. §1 is now BL-3's evidence-gathering step, not a standalone check. |
> | **§6** live webhook | **[BL-24]** — lowest priority | Needs a tunnel and a publicly reachable address (neither host nor devcontainer has one), and it validates a surface nothing currently depends on. Real, but not urgent. |
>
> **Why §5/§7/§8 are together, and why they matter most.** They are the only checks in this
> file with *real side effects on GitHub*, and together they are the checks that decide
> whether **the factory actually works** — the product's central claim, still unverified
> against real GitHub after 25 sprints. Every other guarantee in this repo is hermetic and
> says nothing about it.

## 1. Caching + USD budget smoke (validates Sprints 10–12)

```bash
hatch run loop-engine run --input <small requirements doc> --budget 0.50
hatch run loop-engine cost-summary --run-id <run_id>
```

Expected observations:

- `cost-summary` shows nonzero, plausible `Cost (USD)` per stage (rate table live,
  no longer the 0.0 placeholder).
- With a spec large enough that the Architect/Coder prefix exceeds Sonnet 5's
  ~2048-token minimum cacheable size, `Cache R` is nonzero on Coder rows (sprints
  2..N) and on any gate-revision retry.
- **If every `Cache R` is 0**, a silent cache invalidator crept in: diff the system
  blocks between two calls — they must be byte-identical (state-derived content
  only; findings/sprint plans belong in the user turn).
- Note: recorded cost uses standard Sonnet 5 rates ($3/$15 per MTok); through
  2026-08-31 real spend is at introductory rates ($2/$10), so `cost_usd` slightly
  overstates the bill until then (see `tools/llm/pricing.py`).


## 5. `github_server` live launch + factory verbs (validates Sprint 22b) — ✅ PERFORMED (sprint 36, 2026-07-15)

**Result: PASS.** The first authenticated MCP-fronted `gh` round-trip ever ran, via
`build_github_provider()` (the real `github` stdio server subprocess), against a
disposable private scratch repo `glunk-works/factory-scratch-s5-20260715` (since
deleted, Task 7). Observed:

- **FD6 at runtime:** the provider exposed exactly `{create_repository, clone_repo,
  create_branch, open_pr}` — `create_ruleset` **absent**, no merge verb present.
- **`create_repository`** — created a real private repo; `gh repo view` confirmed
  `visibility=PRIVATE` and the returned `RepoRef.url` resolved.
- **`clone_repo`** — the working tree landed; **both** a `../`-traversal `dest` and a
  symlink-escaping `dest` were rejected **before** any `gh` call (`Invalid clone
  destination … must not contain '..' segments` / `… escapes the run tree`), with no
  directory created.
- **`create_branch`** — created a remote ref off the default branch (no `base`) **and**
  off an explicit `base=main`; both confirmed via `gh api repos/{o}/{r}/branches`.
- **`open_pr`** — after pushing a commit to the feature branch with plain `git`, opened
  PR #1; the returned `PullRef.url` resolved (`state=OPEN`). No merge verb exists to
  auto-merge it.

No findings. (An initial seed commit on `main` was pushed with plain `git` first, since
a repo created by `gh repo create` is empty and `create_branch` needs a base ref.)

## 6. Trigger surface live webhook → real run (validates Sprint 23)

Sprint 23's coverage is entirely hermetic: `TestClient` deliveries against
`create_app(dispatcher=fake)` prove HMAC verify → parse → dispatch end to end,
but `InProcessDispatcher` is only ever exercised with `runner.run_new` patched
(no real loop ever runs in CI), and no port is bound. What none of that shows
is a real GitHub delivery reaching a real, listening server and driving a real
default-loop run. Run on a daemon-bearing host (this devcontainer cannot bind
a port reachable from GitHub):

- **Stand up the server.** No `uvicorn` pin shipped in 23 (deferred with
  hosting) — install it ad hoc for this check (`pip install uvicorn`) and run:
  ```bash
  LOOP_ENGINE_WEBHOOK_SECRET=<real random secret> \
    uvicorn loop_engine.trigger.app:app --host 0.0.0.0 --port 8000
  ```
- **Register a real webhook** on a disposable scratch repo pointed at the
  host's reachable address (tunnel it — e.g. `ngrok` — if the host has no
  public IP), content type `application/json`, secret matching
  `LOOP_ENGINE_WEBHOOK_SECRET`, subscribed to the `issues` and
  `issue_comment` events.
- **Deliver a real signed `agent-action` label event** — label an issue
  `agent-action` — and confirm: GitHub's webhook UI shows a `202` response;
  the server log shows `run starting for <repo>#<issue>`; a `state/<run_id>/`
  directory appears with the run's snapshots; the run actually executes the
  default loop against the issue's title+body as `human_input`.
- **Deliver a real `/agent-run` comment** on a second issue and confirm the
  same, plus that a redelivery (GitHub's "Redeliver" button) while the first
  run is still active is dropped (no second run), per the in-memory dedupe.
- Tear down the tunnel/server and delete the scratch webhook afterward.
- **(23a) Also confirm the bad-body path**: a delivery whose content type is
  misconfigured as `application/x-www-form-urlencoded` (so the raw body is
  not valid JSON) but still correctly signed should observe a `400` response
  in GitHub's webhook UI, not a `500`.

## 7. Maintenance flow live clone → run → gate → push → PR (validates Sprint 24) — ✅ PERFORMED (sprint 36, 2026-07-15)

**Result: PASS, with the red path qualified.** Run via `flows.maintenance.run_maintenance`
with all collaborators at their real defaults against the bootstrapped scratch repo
`glunk-works/factory-scratch-boot-20260715` (§8's output — FD8; since deleted, Task 7).

- **Clone + branch (real):** `repo_io.clone_repo` landed the tree at the request's
  `dest` and `git_io.checkout_branch` cut the feature branch in it.
- **Absorption (confirmed):** with `.agent/STATE.md` seeded onto `main`, the loop's own
  reader (`read_scratchpad`, cwd-relative) saw `active_task="§7 absorption probe: seeded
  by Task 6 setup"` inside the clone; `CLAUDE.md` (scaffolded) and `.agent/STATE.md` were
  both present in the tree the loop ran in — cwd was the clone, per `run_in_tree`.
- **Green path (PASS):** a real default-loop run (`run_id d881ad80…`, terminal
  `COMPLETED`, 4 stages, **$1.4645 / $5.00**) produced changes; the real green gate
  (`pytest src`) passed; the flow committed, pushed `maint-green` to the real remote, and
  opened **PR #2** against `develop` (`state=OPEN`, `base=develop`, `PullRef.url`
  resolved). **Left unmerged** (no merge verb exists — `repo_io` exposes none).
- **`run_in_tree` never opened `worktree_run`** even with `LOOP_ENGINE_ISOLATION=worktree`
  set: no `.worktrees/` appeared under the clone or the run tree; artifacts landed in the
  clone.
- **Red path (gate PASS, loop qualified):** with a deliberately failing `src/` test
  merged onto `main`, the flow's gate behavior was verified — real `pytest src` red →
  `GATE_FAILED` → **no commit, no push, no PR** (no `maint-red` branch on the remote).
  The *real-loop* red attempt could not run: the Anthropic account hit **credit
  exhaustion** mid-sprint (`BadRequestError 400 "credit balance is too low"`), which also
  produces no PR but proves nothing about the gate — so the gate's red behavior was
  proven deterministically instead (real clone/branch/gate/push-suppression; only the
  credit-blocked LLM loop stubbed as "completed + changed the tree").

**Findings (open):**
- **[BL-29] — escalation against a factory-born repo crashes.** Two real-loop green
  attempts (a task needing a repo-root `CONTRIBUTING.md`, and a docs task the Coder
  over-implemented with a broken `src/` test) each *escalated* legitimately, but
  `default_issue_filer`'s `gh issue create --label loop-engine/needs-human` **failed**
  because bootstrap never provisions that label on a managed repo — the run **raised**
  (`MCPToolError`) instead of pausing, *after* the `AWAITING_ISSUE` snapshot had already
  persisted. The green PASS above was obtained only after manually creating the label and
  giving the loop a crisp, self-contained coding task.
- **[BL-30] — the green gate targets `src`, but the scaffold puts tests in `tests/`.** A
  freshly-scaffolded repo, unchanged, would have `pytest src` collect **0 tests → exit 5
  → GATE_FAILED**; the green PASS only worked because the seeded/loop-written tests lived
  under `src/`.

## 8. Bootstrap flow live create → clone → scaffold → push `main` → create `develop` → protect (validates Sprint 25 + BL-21) — ✅ PERFORMED (sprint 36, 2026-07-15)

**Result: PASS, and BL-21's gate proven functional (FD9).** `flows.bootstrap.run_bootstrap`
ran with all collaborators at their real defaults against the disposable public scratch
repo `glunk-works/factory-scratch-boot-20260715` (since deleted, Task 7). The
`BootstrapResult` was `status=created`, `ruleset_installed=true`, `ruleset_id=18965237`.

- **Create → clone → scaffold → commit → push → `develop`:** `create_repository` made a
  real **public** repo (default flipped per FD3) whose `RepoRef.url` resolved; the skeleton
  (`pyproject.toml`, `src/<pkg>/__init__.py`, `tests/test_smoke.py`, `README.md`,
  `.gitignore`, `CLAUDE.md`) landed with names substituted; `gh api …/branches` confirmed
  `main` (scaffold as first commit, repo default) and `develop` **based on `main`'s exact
  pushed SHA** (equal SHAs — `develop` could only be created after the push, FD7). No PR
  opened; no merge verb reachable.
- **Ruleset (BL-21):** `gh api …/rulesets/18965237` showed `enforcement=active`, empty
  `bypass_actors`, rules exactly `deletion` + `non_fast_forward` + `pull_request`,
  targeting **both** `refs/heads/main` and `refs/heads/develop`, and **zero**
  `required_status_checks` (FD4 — a scaffolded repo ships no CI; a required check that
  never reports would deadlock merges).
- **FD9 — the gate REJECTS (observed, not inferred):** deliberate writes were attempted
  and observed to fail:
  - direct push to `main` **and** `develop` → `GH013 … Changes must be made through a pull request`;
  - force-push `main` → `GH013` (pull_request rule);
  - delete `develop` → `GH013 … Cannot delete this branch` (the `deletion` rule);
  - delete `main` → refused as the repo's default branch.
  Notably the `administration=write` admin token with empty `bypass_actors` was **itself**
  blocked — repository rulesets do not auto-exempt admins.
- **Not deadlocked (FD4 from the other side):** the repo **can** still merge a PR — the
  §7 fixture seeds and PR #2 merged/opened normally through `develop`/`main`.

**Finding (open):** **[BL-28] — a factory-scaffolded repo fails its own `ruff check`.** The
scaffold's `pyproject.toml` selects the `S` (bandit) rule set but ships no
`per-file-ignores` for `tests/`, so its own `tests/test_smoke.py` (`assert True`) trips
`S101`. `pytest` and `ruff format --check` pass; only lint fails.

(The org question was already closed in sprint 35; the wheel-ships-templates check was
already done in the Sprint 25 session — neither needed re-doing here.)


---

Delete a section once its check has been performed and any findings are fixed.
Delete **this file** only when no section remains — not before: the sections are
the only record that these things were never verified against a real host.
