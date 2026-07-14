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

Sections still open: **§1, §5, §6, §7, §8.**

> ## Every open section now has a scheduled owner (sprint 35, Task 6 — agreed with the repo owner, 2026-07-14)
>
> "After the merge" had been the answer for five sprints, and **an obligation with no
> scheduled home is an obligation nobody owns** (FD4). So each one now names its destination.
> These are commitments, not suggestions — if a destination slips, move it explicitly rather
> than letting it drift back to "later".
>
> | Section | Destination | Why there |
> | --- | --- | --- |
> | **§5** `github_server` live verbs | **Sprint 36 — live factory verification** | All three need the *same* thing: a daemon-bearing host, authenticated `gh`, network, and a disposable scratch repo they create and destroy. They share the setup and one scratch-repo lifecycle. |
> | **§7** maintenance flow live | **Sprint 36** | ⬑ |
> | **§8** bootstrap flow live | **Sprint 36** | ⬑ |
> | **§1** caching + USD smoke | **Folded into [BL-3]** (prompt-caching review) | §1 needs a real Anthropic key and real spend; BL-3 needs *the same session*. BL-3 cannot assess caching without live `Cache R` data — and §1 **is** that data. Running them apart means paying for two key-bearing sessions to learn one thing. §1 is now BL-3's evidence-gathering step, not a standalone check. |
> | **§6** live webhook | **[BL-21]** — lowest priority | Needs a tunnel and a publicly reachable address (neither host nor devcontainer has one), and it validates a surface nothing currently depends on. Real, but not urgent. |
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


## 5. `github_server` live launch + factory verbs (validates Sprint 22b)

The `mcp_servers/github_server` re-front is verified hermetically: real-server
discovery (`list_tools`, offline — no `gh`/network) asserts exactly
`{create_repository, clone_repo, create_branch, open_pr}`; the `tools/repo_io`
delegate's argv-building and stdout parsing are verified with `_run_gh` mocked;
and the bidirectional coder⟂github consumer-scope guard
(`tests/tools/test_mcp_provider.py`) is proven with the real committed
`loop_engine.mcp.json`. What none of that exercises is a **real, authenticated
`gh`** round-trip — this devcontainer has no `gh` auth and no network. Run on a
daemon-bearing host with `gh auth status` green:

```bash
python -m loop_engine.mcp_servers.github_server &  # or launch via build_github_provider()
```

Exercise each of the four verbs against a disposable scratch repo/org:

- `create_repository` — creates a real (private) repo; confirm the returned
  `RepoRef.url` resolves.
- `clone_repo` — clones it to a validated `dest`; confirm the working tree lands
  and a traversal/symlink-escaping `dest` is still rejected pre-`gh`-call.
- `create_branch` — creates a remote ref off the repo's default branch (no
  `base` given) and off an explicit `base`; confirm both via `gh api
  repos/{owner}/{repo}/branches`.
- `open_pr` — push a commit to the new branch (out of scope for `repo_io` itself
  — do this with plain `git`/`gh` in the test harness), then `open_pr` and
  confirm the returned `PullRef.url` resolves and **no merge verb exists** to
  auto-merge it.

Clean up the scratch repo afterward — this check has real side effects on
GitHub, unlike every other check in this file.

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

## 7. Maintenance flow live clone → run → gate → push → PR (validates Sprint 24)

Sprint 24's coverage is entirely hermetic: `tests/flows/maintenance/test_flow.py`
fakes every collaborator to prove call order/gating, and
`test_integration.py` exercises real `tools/git_io` against a `tmp_path` repo
+ a local bare remote — but `repo_io.clone_repo`/`open_pr` and the loop run
are always faked; no real `gh repo clone`, no real default-loop run with
`gh` auth + network, and no real push/PR happen in CI. Run on a daemon-bearing
host with `gh` authenticated and network access:

- **Clone a real disposable scratch repo** via
  `flows.maintenance.run_maintenance` with all collaborators at their real
  defaults (`repo_io`, `git_io`, `runner.run_in_tree`, `coder_tools.run_pytest`)
  — confirm the clone lands at the request's `dest` and `git_io.checkout_branch`
  actually cuts the branch in that real tree.
- **Confirm the inner run absorbs the target's own `CLAUDE.md` +
  `.agent/STATE.md`** — seed the scratch repo with both before the run and
  confirm the default loop's personas see them (cwd is the clone, per
  `run_in_tree`).
- **Green path:** seed the scratch repo so its `src/` test suite passes,
  confirm the flow pushes the branch to the real remote (`git ls-remote
  --heads` against the real GitHub remote) and opens a real PR against
  `develop` (confirm `PullRef.url` resolves) — and that no merge verb is ever
  reachable (`repo_io` exposes none).
- **Red path:** seed the scratch repo so its test suite fails, confirm
  **nothing** is pushed and no PR is opened.
- **Confirm `run_in_tree` never opens `worktree_run`** even with
  `LOOP_ENGINE_ISOLATION=worktree` set on the host — the loop's artifacts
  should land in the clone, not `.worktrees/<run_id>`.
- Clean up the scratch repo (and any opened PR/branch) afterward — this check
  has real side effects on GitHub, unlike every other check in this file.

## 8. Bootstrap flow live create → clone → scaffold → push `main` → create `develop` (validates Sprint 25)

Sprint 25's coverage is entirely hermetic: `tests/tools/scaffold/test_writer.py`
proves `write_skeleton` against a `tmp_path` tree (incl. the `pkg_name`
sanitization/traversal negative tests and the `CLAUDE.md` byte-identity guard),
`tests/flows/bootstrap/test_flow.py` fakes every collaborator to prove the
chain's call order, and `tests/flows/bootstrap/test_integration.py` exercises
real `tools/scaffold` + real `tools/git_io` against a `tmp_path` repo + a local
bare remote — but `repo_io.create_repository`/`clone_repo`/`create_branch` are
always faked; no real `gh repo create`, no real clone, no real push, and no
real `develop` branch creation happen in CI. Run on a daemon-bearing host with
`gh` authenticated and network access.

> **The org question is CLOSED (sprint 35, Task 6).** This section used to warn that
> `glunk-works` "may not exist yet" and to confirm access or substitute a scratch org.
> It exists, and is the org this repo itself lives in — verified live via
> `gh api orgs/glunk-works`. No substitute org is needed. **Still create and destroy a
> disposable scratch *repo* inside it** — that part was never about the org.

- **Run `flows.bootstrap.run_bootstrap`** with all collaborators at their real
  defaults (`repo_io`, `git_io`, `tools/scaffold`) against a disposable scratch
  repo name — confirm `create_repository` actually creates a private repo,
  `clone_repo` lands a real empty working tree, and the returned `RepoRef.url`
  resolves.
- **Confirm the skeleton is really there.** In the real clone, confirm
  `pyproject.toml`, `src/<pkg_name>/__init__.py`, `tests/test_smoke.py`,
  `README.md`, `.gitignore`, and `CLAUDE.md` all exist with the repo/package
  name substituted, and that a real `pytest`/`ruff check`/`ruff format --check`
  pass against the scaffolded skeleton on its own (proving the bundled
  templates are actually coherent, not just individually unit-tested).
- **Confirm the empty-clone branch mechanics.** Verify the fresh clone's
  initial branch name (whatever the host's `init.defaultBranch` is) and that
  `checkout_branch(tree, "main")` still succeeds and produces a `main` branch
  regardless of that starting name.
- **Confirm the push + `develop` ordering against the real remote.** After the
  run, confirm (via `gh api repos/{owner}/{repo}/branches`) that both `main`
  (with the scaffold as its first commit, and set as the repo's default
  branch) and `develop` (based on `main`'s pushed SHA) exist, and that
  `develop` could only have been created after the push (confirm by timestamp
  or by re-running against a repo where the push is deliberately blocked and
  observing `create_branch` fails against a nonexistent base ref).
- **Confirm no PR is opened and no merge verb is reachable** — `repo_io`
  exposes none, and bootstrap never calls `open_pr`.
- ~~Confirm the wheel actually ships the templates~~ — already verified in the
  25 implementation session (no `gh`/network needed for this one): `hatch
  build -t wheel` + inspecting the archive confirms
  `loop_engine/tools/scaffold/templates/` (including the non-`.py` `CLAUDE.md`
  and `.tmpl` files) ships via hatchling's **default** `packages` file
  selection — no `force-include` needed (an explicit `force-include` entry
  was tried first and **conflicts** with the default inclusion, raising
  hatchling's duplicate-path build error; removed).
- Clean up the scratch repo afterward — this check has real side effects on
  GitHub, unlike every other check in this file.


---

Delete a section once its check has been performed and any findings are fixed.
Delete **this file** only when no section remains — not before: the sections are
the only record that these things were never verified against a real host.
