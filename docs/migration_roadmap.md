# Migration Roadmap — MCP / LangGraph / Isolated Factory

Working roadmap + status for the migration to `migration_architecture_plan.md`.
This is the **resume point**: a new session should read this file first, then
`git log` the branch. Target requirements live in `migration_architecture_plan.md`;
this file tracks *how far we've got and what's next*.

- **Branch:** `feat/mcp-langgraph-migration` (cut from `origin/main`). Nothing
  merges to `main` until the whole migration works end to end.
- **Workflow:** one phase at a time; each phase ends with a green commit
  (`hatch run lint`/`format`/`test` + `audit`/`sbom`) and a **hard stop for
  human review** before the next phase starts. Earlier behavior stays runnable
  behind flags so any phase boundary is checkout-able.

## Status

| Phase | State | Commit |
|---|---|---|
| **▣ THE LANDING — `feat/mcp-langgraph-migration` → `main`** | ✅ **DONE (2026-07-14, sprint 35).** The migration is **on the default branch**. PR #58 merged as a **merge commit** (two parents, **113 commits preserved, never squashed**); the merged tree came out **byte-for-byte** the tree the preflight predicted (`4aad78e`). `allow_merge_commit` disabled straight after — the exception is **spent**, the repo is squash-only, and there should be **exactly one** merge commit in `main`'s history. `feat/**` dropped from the ruleset and the branch **deleted** (BL-17), with `main`'s protection re-verified afterwards and independently confirmed by `ruleset-drift.yml`. **The two-branch topology that generated BL-12/BL-13/BL-14 no longer exists.** Plan: `sprints/35_migration_merge/sprint_plan.md` (FD1–FD7) | **`d2135e7`** (merge) |
| 1 — State & skill externalization + LangGraph engine | ✅ complete, reviewed | `ee89718` |
| 2 — MCP tooling (coder tools as MCP server) | ✅ complete, reviewed | `7368411` |
| 3a — Execution isolation (per-run git worktrees) | ✅ built behind flag, reviewed | `951e377` |
| 3b — Execution isolation (disposable container/sandbox) — **inert seam** | ✅ built behind flag, reviewed (docker/podman primary, bwrap secondary). Sandboxed gate pytest **closed in code by sprint 28** (`386c660`): both Coder gates' verification pytest now routes through the MCP container sandbox via `tools/mcp.run_gate_pytest`, `_raise_if_sandboxed` deleted — only the real `docker run` daemon-host e2e remains deferred, carried by sprint 27's V1(complete)/V2. Plans: `sprints/18_execution_isolation_container/`, `sprints/28_gate_pytest_sandbox/` | `cdc7c8f` → `386c660` |
| 4 · part 1 — Ralph-loop Coder (`AgenticNode`) | ✅ built behind flag, reviewed; 4 review findings hardened in 4a (below). Plan: `sprints/19_ralph_coder/sprint_plan.md` | `195f7b7` |
| 4 · part 1a — Ralph hardening (review findings #6 (a)–(d)) | ✅ complete, reviewed; 3 HITL-review findings resolved (see "Sprint-19a HITL-review settlements"). Plan: `sprints/19a_ralph_hardening/sprint_plan.md` | `d675d5d` → review-fixes |
| 4 · part 2 — Declarative generators (`GeneratorNode`) + PM critic-gate | ✅ complete, reviewed; HITL-review findings resolved via sprint 21 review-fixes. 394 tests green. Plans: `sprints/20_declarative_generators/`, `sprints/21_declarative_review_fixes/` | `cf48b0c` → `aceb23a` → `03818d9` |
| 5 — Autonomous triggers + multi-repo factory | 🟨 22a + 22b + 23 + 23a + 24 + 25 complete, reviewed, archived. Sprint 25 (bootstrap flow capability slice) landed the second sanctioned file-write surface (`tools/scaffold`), HITL-reviewed by Opus and approved. Next: plan Phase 6 (collapse the flags). Plans: `sprints/22a_mcp_multiserver_discovery/`, `sprints/22b_native_github_server/`, `sprints/23_trigger_surface/`, `sprints/23a_trigger_review_fixes/`, `sprints/24_maintenance_flow/`, `sprints/25_bootstrap_flow/` | `457f675` → `71f1692` → `d0e118d` → `7b46227` → `5bc3811` → `5ff8c02` → `e0406d8` → `212beeb` → `6172ad1` → `f8d388a` → `79b535d` |
| 6 — Collapse the flags (decommission the migration scaffolding) | 🟩 **DONE (2026-07-12).** Planning pass locked 2026-07-10; Sprint 26 (`issue_io`→MCP unification, capability+seams) — implemented, green, **HITL-reviewed by Opus and approved (2026-07-10)**; review findings R1–R7 routed into the host-gated flip block (see the Sprint 26 HITL-review subsection + `DEFERRED_VERIFICATION.md` §9), archived. Flip block planned in `sprints/27_phase6_flip_block/`; its Phase-3b-completion prerequisite **sprint 28 (gate-pytest sandbox) is complete, green, HITL-reviewed by Opus and approved (2026-07-10, `386c660`), and archived** — unblocking sprint 27's host V-runs. **Sprint 29 (Coder host-run hardening) is complete, green, HITL-reviewed by Opus and approved (2026-07-11, `b0be361`/`10f27d3`):** it closed the two Coder-convergence gaps the V2 re-attempt surfaced — **F-TOOLLOOP-CAP** (graceful `ToolLoopExceededError` + inner cap 12→40) and **F-CODER-NO-LINT** (the `run_lint` ruff tool, a fifth sanctioned subprocess surface). **Sprint 30 (Ralph test-scope guardrails) is complete, green, HITL-reviewed by Opus and approved (2026-07-11, `551338a`/`f934fda`):** V2 re-attempt #6 surfaced a third convergence gap, **F-RALPH-OVERSPEC-TEST** (Ralph authored out-of-spec tests asserting private/underscore internals, then escalated on their self-caused failures instead of self-fixing); sprint 30 closed it with a prompt-only fix (locked FD1/FD2 — test-scope + self-fix-before-escalate directives added to the Coder/Ralph prompts, no gate-guard). **Sprint 31 (Ralph completion integrity) is complete, green, HITL-reviewed by Opus and approved (2026-07-11, `e5d9d98`/`9c32cbf`):** V2 re-attempt #7 confirmed sprint 30's fix holds but surfaced a fourth gap, **F-RALPH-FALSE-COMPLETION** (`RalphCoderPersona` marked a task done on "no open question" alone, never checking that `apply_file_blocks` actually applied the edit — so one malformed edit block baked a permanent `## Edit Application Failures` marker into the report and wedged the Coder gate before pytest); sprint 31 closed it with a bookkeeping fix in `personas/coder_iac/ralph.py` only (locked FD1/FD2/FD3 — completion gated on no-questions **and** no-edit-failures, the failure kept distinct from an escalation and simply retried; no `core/coder_gate.py` change). **V2 is now PASS (host re-attempt #8, 2026-07-11):** a real container-sandboxed Ralph run reached terminal `COMPLETED` under the full production config — 8/8 manifest tasks, zero escalations, $2.24/$5.00, independently re-verified (pytest 15 passed, ruff clean, every spec case + error path exercised); sprint 31's fix held, so FD1 did not fire. **Sprint 27's subtractive flag deletions are DONE (2026-07-11):** Task 0 tagged `pre-phase6-classic`; Tasks 1–4 deleted all four migration flags and their classic paths (`ec8b0e5` ENGINE, `adb20b3` TOOLS, `56c3824` PERSONAS, `3ea8106` CODER); Task 6 (the `loop.py` collapse) fell out of them — a `build_default_loop()` that cannot read a flag cannot branch on one; Task 7 reconciled the docs. **Task 5 (the `artifacts` strip) is DEFERRED to its own sprint (decision FD3)** — its premise was false: deleting `run_loop` does not make the engine the sole `artifacts` reader, because the readers were always the personas and gates, so the strip is a behavior-changing refactor rather than a deletion. **V3 is PASS (qualified, 2026-07-12)** — the forced issue-escalation host round-trip: V3a (verb-level, $0) and V3b (engine-level) both proved the issue path against a real `gh`, real GitHub issues, and the real `issue` MCP server subprocess; it surfaced findings **R8** (the issue verbs had no explicit repo target — escalation issues for managed repos were being filed on loop-engine itself), **R9** (the PM stage cannot escalate a requirements contradiction) and **R10** (a run cannot be paused and resumed under different isolation modes). **Task 8 (the issue-path flip onto MCP) landed (`8a8b59f`, PR #30), and its R8 fix was completed by Task 10 (`796610a`, PR #34)** — the first cut threaded `cwd` from `cli.py` alone and every fresh-run path kept leaking, so the destination decision moved *into* `default_issue_filer` (resolving `worktree.origin_cwd()`, no `repo=None` fallback anywhere). Task 10 also closed the review's F1–F7: `resume --snapshot` is now repo/issue-authoritative from the snapshot's own `pending_issue.url`, `_ORIGIN_CWD`/`_STATE_ROOT` are `ContextVar`s restored by token, `InProcessDispatcher` serializes runs, and `_pause_for_issue` persists before filing. **HITL-reviewed by Opus and approved (2026-07-12, fresh session, PR #34).** **Task 9 (this row's close) pruned rather than deleted `sprints/DEFERRED_VERIFICATION.md`** — its premise was false in the same way Task 5's was: the file held five checks (§1, §5, §6, §7, §8) that were **never performed**, so deleting it would have silently discarded the project's only record of them. The Phase-6 sections it *had* discharged (§2 moot, §3/§4/§9 superseded by V1/V2/V3) were retired and their results folded into this row; the file survives as the standing register of unmet proof obligations and **outlives the migration**. **Phase 6 is therefore complete: four flags deleted, one path (LangGraph engine + MCP tool dispatch + declarative `GeneratorNode` personas / PM `CriticGate` + Ralph Coder); classic recoverable at the `pre-phase6-classic` tag; `LOOP_ENGINE_ISOLATION` survives as genuine runtime config; V1/V2/V3 all PASS.** ✅ **Task 5's dangling ⚠ is now DISCHARGED (sprint 32, 2026-07-12) — inverted, not executed as written: `artifact_refs` was stripped, `State.artifacts` survives as the permanent source of truth (FD1, superseding FD3 below).** **Sprint 32 is complete, green, HITL-reviewed by Opus and approved (2026-07-12, fresh session, PR #39, squash `3db3237`)** — `schema_version` 3→4 with an explicit pop of the retired key; the 8 artifact-reader modules came out **byte-identical** to the pre-sprint base, which is the tell that the inversion held. Its review raised eight non-blocking findings (two worth folding in: `publish_artifacts`' new per-stage disk read vs. its "does no I/O" docstring, and its unencoded `Path.read_text()` read-back) and, more consequentially, surfaced **BL-10** — a `ci.yml` hole under which #39's own test suite had **never run** (a 78-char title failed `pr-title`, which skipped `lint`, which cascaded to skip the entire heavy chain; a title edit fires `edited`, which `lint` deliberately ignores, so it could never recover). Recovered by close+reopen (`reopened` preserves the head SHA, so the commit-pinned `architect-review` stayed green); logged in PR #40 (`46458af`), **not fixed**. Plans: `sprints/26_issue_io_mcp_unification/`, `sprints/27_phase6_flip_block/`, `sprints/28_gate_pytest_sandbox/`, `sprints/29_coder_host_run_hardening/`, `sprints/30_ralph_test_scope/`, `sprints/31_ralph_completion_integrity/` | `3a9bc30` → `b7e2496` → `386c660` → `b0be361` → `10f27d3` → `551338a` → `f934fda` → `e5d9d98` → `9c32cbf` → `ec8b0e5` → `adb20b3` → `56c3824` → `3ea8106` → `8a8b59f` (Task 8, PR #30) → `796610a` (Task 10, PR #34) → `ddd28a8` (Task 9 — Phase 6 closed, PR #37) |

Phases 1–3b are detailed and executed (3b's daemon-host e2e is deferred, not
lost — see its plan). Phase 4's planning pass is done and it **split into two
separately-gated sub-phases, Ralph-Coder-first** (see the Phase 4 section and
decisions log below). Part 1 (Ralph Coder, `195f7b7`) is built + reviewed, and
its four review findings are hardened in **part 1a** (`sprints/19a_ralph_hardening/`).
**Part 2** (`GeneratorNode` + PM critic-gate, `sprints/20_declarative_generators/`)
is **built behind `LOOP_ENGINE_PERSONAS=declarative`** (default `classic`),
**reviewed, and its review findings resolved** (sprint 21 review-fixes, `03818d9`).
## ✅ THE MIGRATION IS LANDED — this roadmap is now history, not a plan (2026-07-14)

**Sprint 35 (`35_migration_merge`) is COMPLETE. `feat/mcp-langgraph-migration` is on `main`, and the branch is retired.** PR #58 merged as merge commit **`d2135e7`** — **two parents, 113 commits preserved, never squashed** — and `main`'s resulting tree came out **byte-for-byte the tree the Task 3 preflight predicted** (`4aad78e`), which is the tell that FD1 held to the end. The one-time merge-commit exception is **spent**: `allow_merge_commit` went back to `false` immediately after, so the repo is squash-only and **there should be exactly one merge commit in `main`'s history — that one.** `feat/**` was then dropped from the ruleset's targets and the branch **deleted** (BL-17), after proving `b669482` was an ancestor of `main` and re-verifying `main`'s protection *afterwards* — independently confirmed by a `ruleset-drift.yml` run.

**The two-branch era is over.** Sprint branches are cut from `main`; PRs are based on `main`. The topology that generated BL-12, BL-13 and BL-14 in a single week **no longer exists** — the *generator* is gone, not just the instances (see `docs/backlog.md`).

**✅ Sprint 36 — live factory verification — DONE (2026-07-15).** `DEFERRED_VERIFICATION.md` **§5** (`github_server` verbs), **§7** (maintenance flow) and **§8** (bootstrap flow) were run **live against real GitHub** — the first time the factory's central claim was verified with real side effects. Track A (#73/#76/#77) fixed and hardened BL-21's `create_ruleset`; Track B (#79, squash `212cc56`) executed the three sections against one disposable scratch-repo lifecycle. §8's ruleset was proven **functional, not merely present** (FD9 — direct/force/delete pushes on `main` and `develop` all observed rejected, the `administration=write` admin token itself blocked); §7's green path opened a real PR against `develop`, and a real loop was shown to converge a red suite to green. **BL-21 closed.** Findings filed: **BL-28** (scaffold fails its own `ruff check`), **BL-29** (maintenance escalation crashes on a missing `loop-engine/needs-human` label), **BL-30** (green gate targets `src` but the scaffold puts tests in `tests/`). FD1's stale "no `gh` auth / daemon-bearing host" premise was corrected in `DEFERRED_VERIFICATION.md`; **§1 → BL-3, §6 → BL-24** remain the only open sections.

**✅ Sprint 37 — test-suite velocity (BL-22) — DONE (2026-07-15).** Four tasks landed as separate squash-merged PRs, each green on the full required-check set (`architect-review` exempt — none touched `src/`): **T1** (`0066701`, PR #82) stubbed `build_coder_tool_provider` in `tests/personas/test_ralph_coder.py` so the ralph unit tests stop spawning a real MCP server (~75s file → ~5s; suite 278s → 174.58s); **T2** (`2b9292f`, PR #83) moved the direct-spawner MCP test files' provider fixtures to **module scope** — chosen over the plan's literal "session" wording to avoid an autouse-cwd fixture leaking across later-collected files (suite → ~86–89s, no flake); **T3** (`e993861`, PR #86) added a **step-level** `if:` short-circuit in `ci.yml`'s `test` job that skips `hatch run test` only when every changed file is docs (`**/*.md`, `.ai/**`, `sprints/**`, `docs/**`), fails safe on any API error, SIGPIPE-safe capture-then-match — deliberately **not** `paths-ignore` and **not** an aggregator job (avoids the BL-10/BL-12 "green for the wrong reason" trap; a skipped step still reports the job green), verified live on throwaway docs-only + code-touching PRs (both correct polarity, closed unmerged); **T4** (`deb7c99`, PR #87) landed `pytest-xdist==3.8.0` as a **new** `test-parallel` hatch script (`-n auto --dist=loadscope`), NOT wired into the default `test` script (protects the single-file fast path) — `loadscope` was required, not optional, because xdist's default distribution scatters a module's tests across workers and T2's module-scoped fixtures don't amortize that way (one transient >120s stall observed before switching). **CI full suite now ~54s** on a real GitHub runner (4 workers, 573 passed), down from the ~380s the sprint started from — roughly 7×. Sprint-37 planning also filed **BL-31** (reduce the MCP per-spawn ~5s cold-start itself), deferred as its own `src/`-touching unit. **No HITL gate — all four PRs were `src/`-exempt.**

**✅ Sprint 38 — test-validity audit, `core/` mutation pass 1 (BL-23) — DONE (2026-07-15).** Three tasks landed as separate squash-merged PRs: **T1** (PR #90) stood up `mutmut` (pinned dev dep, `[tool.mutmut]` scoped to `src/loop_engine/core/` against `tests/core/`) and captured the baseline — 693 mutants, 147 survivors, ~35s wall-clock (`sprints/38_test_validity_audit/mutation_baseline.md`); **T2** (PR #92) triaged all 147 survivors into `audit_report.md` with FD3's mandatory full-suite cross-check (distinguishing mislocated coverage from genuinely-uncovered from equivalent), parallelized across `git worktree` checkouts (~110min sequential → ~15min); **T3** (PR #94) landed every `fix` verdict as an added/strengthened `tests/core/` test — **no `src/` change was needed anywhere**, since every row that looked like a genuine defect (the `has_artifact(state, None)` masking gap, the token/cost/cache delta subtraction-vs-addition bug) turned out on inspection to be mislocated coverage, not an actual bug. Landing T3 also **corrected 3 of the 89 originally `fix`-triaged mutants to `keep — equivalent`** (proven by call-graph analysis while landing that group's own fix, not just "no test happened to catch it" — FD5's bar), so the report's final tally is **61 keep, 86 fix, 0 delete** (was 58/89 pre-correction); `hatch run mutate`'s residual survivor count (61) matches the corrected report exactly, verified per-file against the report's named rows, not just the total. Both planning-pass follow-ups resolved: **BL-32 filed** (PR #95) — the deferred adversarial invariant-injection audit of the static structural guards, since mutmut's operator catalog cannot generate the constructs those guards exist to catch (FD1); and the **gate-vs-script decision landed on "stay on-demand"** (owner call, given the real ~35–50s runtime came in far below the sprint plan's feared "minutes-to-hours" — no `ci.yml` gate added). **No HITL gate — all PRs were `src/`-exempt** (test-only or docs-only throughout).

**✅ Sprint 39 — BL-2 pass 1 of 3, outbound Slack notify — DONE (2026-07-16).** Direction resolved notify-first (FD1); `tools/slack_io` wraps the official `slack_sdk`, not an MCP server (FD2); credentials are env vars `LOOP_ENGINE_SLACK_BOT_TOKEN`/`LOOP_ENGINE_SLACK_CHANNEL`, not keyring (FD3); `core/graph_engine.py`'s `run_graph_loop` emits through the `core/notify` `Notifier` seam, fail-open at the call site, gated on a `resuming: bool` flag rather than `start_index` (FD4). **T1+T2** (PR #107) added the `core/notify` contract + `tools/slack_io` transport/formatter; **T3** (PR #112) wired the two emit points into `run_graph_loop`; **T4** (this PR) is the docs-only close-out. Full detail: `docs/backlog.md`'s BL-2 entry.

**▶ NEXT ACTION: plan BL-2 pass 2 or 3 (Slack control plane, inbound surface).** BL-2's outbound pass is done; **BL-24**'s never-verified inbound trigger surface, and whether Slack's inbound direction supersedes/parallels/waits behind it, are still open — see `docs/backlog.md`'s BL-2 entry (the `SCHEDULED` planning note, still applicable to the remaining two passes) for the open questions. Post-migration work is backlog-driven from `docs/backlog.md`; the migration itself is done. BL-23 is a multi-pass program — pass 2 (the BL-32 adversarial-guard audit, or extending mutation testing beyond `core/`) is a later beat, not blocking BL-2.

**Sprint 35's other outcomes**, each recorded in `docs/backlog.md`: the two non-blocking findings from #39's review landed as Task 1 (PR #57). The four Dependabot majors (#50–53) **merged** — they were not four upgrades but **one deadline**, the Node 20 → Node 24 runtime migration, with GitHub removing Node 20 on **2026-09-16**; since `secrets-scan` is a *required* check, `gitleaks-action@v2` dying would have made **every PR unmergeable** on a known date. Driving them to green exposed two structural CI faults (**BL-20**: Dependabot runs read a *different* secret store, and re-triggering as a human silently reads the other one — a green that proves nothing; and Dependabot's default PR title fails the required `pr-title` check by construction, fixed in `dependabot.yml`). Sprint 35 also found and fixed a live gate defect — `architect-review` was **exempting itself on large PRs** (a paginating `gh` piped into `grep -q` → SIGPIPE → `pipefail` → read as "no `src/` changes" → green), filed as **BL-16**. `sprints/DEFERRED_VERIFICATION.md`'s five never-run checks each now have a **named, scheduled owner** (Task 6, FD4): §5/§7/§8 → sprint 36, §1 → folded into BL-3, §6 → BL-24. `.ai/next-steps.md` remains the live cursor.

> Phase 6 is done and the migration is collapsed to one path. One standing obligation
> survives it: **`sprints/DEFERRED_VERIFICATION.md`** — five checks (§1, §5, §6, §7, §8)
> that have **never been run** because they need a real key, a real authenticated `gh`, or a
> daemon-bearing host that can bind a port. It is not a migration task, but it is real.
> A green `hatch run test` says nothing about it. (**FD3** — the `artifacts` strip, above
> — is discharged: sprint 32 inverted it; see FD1 there.)

**The flag era is over.** Sprint 27 Tasks 0–4 + 6 + 7 landed the subtractive deletions:
all four migration flags and the classic paths they selected are gone (`ec8b0e5`,
`adb20b3`, `56c3824`, `3ea8106`), `build_default_loop()` is one unbranched wiring, and
the classic engine/tools/personas/Coder are recoverable at the **`pre-phase6-classic`**
tag. Only `LOOP_ENGINE_ISOLATION` (+ `LOOP_ENGINE_RALPH_MAX_ITERS`) survive, both genuine
runtime config. **Task 5 (the `State.artifacts` strip) as originally planned is
superseded — sprint 32 (2026-07-12) inverted it: `artifact_refs` was stripped instead,
`State.artifacts` survives as the permanent source of truth (FD1 below, superseding FD3).**

**Host V2 is PASS — the flip block's last gate is discharged.** Re-attempt **#8**
(2026-07-11, Opus/Architect host session) observed a real container-sandboxed Ralph
run reaching terminal **`COMPLETED`** under the full production config
(`ENGINE=langgraph` + `TOOLS=mcp` + `PERSONAS=declarative` + `CODER=ralph` +
`ISOLATION=container`): `run_id=0c8fdb89949c49578f891fe78f3373b4`, **8/8 manifest
tasks** checked off across 3 sprints, **zero escalations**, **`$2.2433` of `$5.00`**
(well inside budget, vs run #3's `BUDGET_EXCEEDED`). Independently re-verified in the
produced worktree: `pytest -q` → 15 passed, `ruff check`/`ruff format --check` clean,
and both functions exercised against every spec case + error path. Sprint 31's fix
**held** — the run-#7 edit-application wedge did not recur, so **FD1 does not fire**
and stays closed. (One invalid attempt, #8a, escalated on a mis-seeded target tree —
a staging error, not a product defect; see `DEFERRED_VERIFICATION.md` §V2.)

With V1 **PASS(qualified)** for `ENGINE`/`TOOLS`/`PERSONAS` and V2 now **PASS** (it
also discharges V1's one deferred tail — the Coder-ACCEPT → terminal `COMPLETED`
transition under the new engine), sprint 27's subtractive deletions are **unblocked**.
The flip block itself is planned
(`sprints/27_phase6_flip_block/`): the
four flag deletions + `artifacts` strip + `loop.py` collapse + the issue-path
default-flip/classic-deletion (which now also carries Sprint 26's HITL findings
R1–R7), all gated on those host V-runs passing. **Sprint 28** (gate-pytest sandbox,
the Phase-3b-completion prerequisite) is **complete, green, HITL-reviewed by Opus
and approved (2026-07-10, `386c660`), and archived** — `_raise_if_sandboxed`
deleted, gate pytest now routes through the MCP container sandbox. Sprint 26
(`issue_io`→MCP unification) is **complete, green, HITL-reviewed by Opus and
approved (2026-07-10, `3a9bc30`/`b7e2496`), and archived**. Sprint 25
(`sprints/25_bootstrap_flow/sprint_plan.md`) is **complete, all 6 tasks green,
HITL-reviewed by Opus and approved (`79b535d`), and archived**: a new `tools/scaffold` module (`write_skeleton`,
validated via `repo_io._validate_clone_dest`, `pkg_name` sanitized to a safe Python
identifier) — the **second** sanctioned file-write surface, moving the invariant from
one to two (`CLAUDE.md` + `tests/tools/test_state_io_boundary.py` updated together,
mirroring how sprint 24 moved the subprocess-surface count three→four); bundled
package-data templates (`kind="python"` only; a `kind="iac"` set is deferred behind
the seam) plus a byte-identical `templates/CLAUDE.md` sync-guard against
`.ai/context/conventions.md`; the new `src/loop_engine/flows/bootstrap/` package
(a sibling of `flows/maintenance`) chaining `repo_io.create_repository` →
`repo_io.clone_repo` → `git_io.checkout_branch(main)` → `scaffold.write_skeleton` →
`git_io.commit_all`/`push_branch(main)` → `repo_io.create_branch(develop, base=main)`
(load-bearing ordering — `create_branch` must follow the push); **no** inner loop,
**no** green gate, **no** `open_pr` (a brand-new repo has nothing to review into —
auto-merge stays impossible); a `flows/` boundary test provably enumerating
`flows/bootstrap`; and a hermetic end-to-end proof (real `scaffold` + real `git_io`
against a `tmp_path` repo seeded on a non-`main` initial branch, proving the
unborn-HEAD handling, + a local bare remote, `repo_io` faked). No new dependency
(`sbom.json` unchanged); the four sanctioned subprocess surfaces are unchanged
(`scaffold` writes files, it does not shell out); live `create_repository`→clone→
scaffold→push→`create_branch` verification is deferred to a daemon-bearing host
(`sprints/DEFERRED_VERIFICATION.md`; `glunk-works` org access remains an open
hosting question). Sprint 24 (maintenance flow) is
**implemented, HITL-reviewed, review-fixed, and archived** (`6172ad1` → `f8d388a`).
Sprint 24 (`sprints/24_maintenance_flow/sprint_plan.md`) is **implemented,
all 6 tasks green**: a new `tools/git_io` module (local-git `checkout_branch`/
`commit_all`/`push_branch` against a cloned tree, mirroring `tools/worktree`'s
`_git` posture, validated via `repo_io._validate_clone_dest`) — the **fourth**
sanctioned subprocess surface, moving the invariant from three to four (`CLAUDE.md`
+ `tests/tools/test_subprocess_surfaces.py` updated together); `runner.run_in_tree`
(same loop-build as `run_new` but cwd pinned to the clone, deliberately **not**
opening `worktree_run` — the clone is its own isolation boundary); the new
`src/loop_engine/flows/maintenance/` package chaining `repo_io.clone_repo` →
`git_io.checkout_branch` → `run_in_tree` → a green gate (`coder_tools.run_pytest`
against the clone) → **green-only** `git_io.commit_all`/`push_branch` +
`repo_io.open_pr` (base defaults to `develop`); a `flows/` boundary test (no
`keyring`, no direct file write, no subprocess surface of its own — `git_io` is
*called*, not introduced); and a hermetic green/red end-to-end proof (real
`git_io` against a `tmp_path` repo + local bare remote, `repo_io`/the loop faked).
**Capability slice only** — no CLI subcommand, no trigger wiring, no bootstrap
flow; auto-merge stays impossible (no merge verb, `open_pr` terminal). No new
dependency (`sbom.json` unchanged); live clone→push→PR verification deferred to
a daemon-bearing host (`sprints/DEFERRED_VERIFICATION.md`). **HITL-reviewed by
Opus; 2 findings fixed** (`f8d388a`): the flow now (1) requires the inner run's
returned `State` to be `COMPLETED` before the gate (a `FAILED_STAGE`/
`BUDGET_EXCEEDED`/`AWAITING_ISSUE` run → `run_incomplete`, so a human-paused
tree is never shipped as a PR) and (2) probes `git_io.has_changes` before
committing (an empty-diff run → `no_changes`, dodging `commit_all`'s empty-index
failure). 497 tests green. Sprint 23 (trigger
surface — a FastAPI webhook that turns a GitHub `agent-action` label or
`/agent-run` comment into a real `runner.run_new` default-loop run via an
injectable `RunDispatcher` seam) is **implemented, all 6 tasks green**
(`sprints/23_trigger_surface/sprint_plan.md`, `5ff8c02`), **HITL-reviewed**,
and its 3 dispatch/webhook findings **fixed in 23a (`212beeb`) and re-reviewed
clean** (see "Sprint-23a HITL-review settlements" below). It is a capability slice mirroring 22b's posture: dispatch is
**in-process** (a worker-thread `InProcessDispatcher`, so the sanctioned
subprocess-surface count stays **three**, unchanged), FastAPI is pinned as
loop-engine's first web runtime dependency while `uvicorn`/hosting stays
deferred (hermetic `TestClient` coverage only, `httpx` dev-only), the webhook
secret is an env var (`LOOP_ENGINE_WEBHOOK_SECRET`, HMAC over the raw body,
fail-closed) — not a keyring credential — and it does **not** chain into the
factory verbs (no `tools/repo_io` call, no clone/branch/PR) — that's Sprint
24's job. Sprint 22b (native `github_server` + `tools/repo_io` delegate +
committed `loop_engine.mcp.json` github entry + `build_github_provider()`) is
**complete, HITL-reviewed and approved** (`7b46227`, review-fix `5bc3811`) —
the system's second MCP server and its first credentialed one. The review
raised one finding — `_validate_clone_dest` gated its symlink-escape check on
`path.exists()`, letting the normal clone case (non-existent target under a
symlinked parent) escape the run tree — **fixed** in `5bc3811` with a
regression test; a low-severity nit (bare `python` vs `sys.executable` in the
committed config) was deferred, still open. The "cloning target repos
introduces a new git subprocess surface" open item flagged during 22a is
**settled gh-only**: all four factory verbs ride the existing `gh`
executable, so `repo_io` is a second `gh` consumer and adds **no** fourth
subprocess surface (the genuine local-git surface — `git push` inside a
cloned tree — is deferred to Sprint 24's maintenance flow, which is also
where the trigger surface's `RunRequest` will eventually chain into the
factory verbs). See the "Phase 5 planning pass" + "sprint decomposition"
subsections below for the locked decisions.
All Phase-4 sub-phases are now built, reviewed, and their review findings
resolved (part 1a reviewed 2026-07-09). Phase 6
(below) is the tracked teardown that keeps the feature flags from calcifying
into permanent bloat.

## Decisions log (locked)

- **Adopt LangGraph literally** — the pre-existing engine was a bespoke
  `while`-loop, not LangGraph. Now a `StateGraph` in `core/graph_engine.py`,
  selected by `LOOP_ENGINE_ENGINE=langgraph`; classic `run_loop` is still the
  default. Both drive the shared `execute_stage()` primitive (parity-tested).
- **Doc stages keep deterministic structural validators**; exit-code gates
  apply only to code stages. "No LLM Critic" = no LLM *judge* (already true).
  The PM's *revision loop* is what Phase 4 retires — its checks survive as a
  structural gate.
- **1c used the "dual-field" path (not the full strip):** `State` gained
  `artifact_refs` (path + sha256) alongside the inline `artifacts` body-dict
  (schema v3); `tools/artifact_store.mirror_to_disk` populated refs at snapshot
  time. **Resolved by sprint 32 (2026-07-12, FD1): inverted, not completed as
  planned.** `artifact_refs` had no readers and was deleted; `State.artifacts`
  is the permanent source of truth, not a transitional field, and no artifact
  body is ever read back off disk (`schema_version` 4).
- **Phase 2 scope:** built only the coder-tools MCP server (the sole
  LLM-callable tool set). **Deferred:** state-io/github MCP servers (they're
  orchestrator-invoked, not model tools) and full `loop_engine.mcp.json`-file-driven
  multi-server discovery (the `list_tools` runtime-discovery mechanism is in
  place, pointed at a default server).
- **Phase 4 planning pass (locked):**
  - **Persona config format = YAML (PyYAML).** The declarative persona config
    (`GeneratorNode`, part 2) lives in per-persona YAML parsed by a node
    loader. This adds PyYAML as a *pinned* dependency → SBOM regen + `pip-audit`
    must clear it (a first-class task in the part-2 plan). Loop *wiring* stays
    Python ("loops are just Python"); only persona **config** goes declarative.
  - **Two node archetypes, not one-generic-vs-four-custom.** A misfit persona
    is holding control flow that belongs in a gate or edge. (1) `GeneratorNode`
    — single-shot generate + optional section-merge revision + optional
    `resolve_via_document` resolver — drives **Architecture, Sprint Breakdown,
    and PM**; its only varying logic is a small registry of shared services
    (output-adapters `markdown`/`sprint_blocks`/`json_object`, revision-style
    `section_merge`/`full_reextract`, `untrusted` input-wrapper). (2)
    `AgenticNode` (tool loop) — drives the **Coder**. Guiding principle:
    *personas generate, gates accept, the graph routes.*
  - **PM collapses onto `GeneratorNode` once its critic *loop* is retired.**
    The `MAX_REVISION_CYCLES` loop inside `PMPersona.run` is misplaced control
    flow → it becomes a structural `CriticGate` (the `critic.review()` *checks*
    survive; the engine's existing revise loop drives re-extraction). PM's
    `fold_answers` is a resume-time resolver *service*, not forward-path node
    logic. (Part 2.)
  - **Coder = a Ralph loop** (project owner's call). One **task** of work per
    invocation from a **fresh context**; the worktree filesystem + the `.agent/`
    ledger (`STATE.md` task checklist / `MEMORY.md` lessons, built Phase 1,
    underused) are its progress + cross-iteration memory; the exit-code gate is
    its termination condition. Implemented as **Strategy A — reuse
    `execute_stage`'s revise loop** (no new `StateGraph` topology): incremental
    idempotent `run()`, a coverage-aware gate (green is necessary, not
    sufficient — *every manifest task* must be checked off), and the Coder
    stage's `max_revisions` raised to the Ralph iteration cap. The engine's
    existing identical-findings→escalate is the no-progress guard; the USD
    budget is the hard cost governor. Behind `LOOP_ENGINE_CODER=ralph`; a
    behavior change, so **flag-gated, not parity-claimed** (only the default
    `classic` path and cross-engine equivalence are parity-tested).
  - **Sprints ARE the right input for Ralph — keep the planner, add a manifest.**
    The Agile Sprint Breakdown already decomposes work into sprints → tasks →
    acceptance-criteria: exactly the discrete, dependency-ordered,
    independently-verifiable checklist a Ralph loop needs. So `AgileSprintBreakdownPersona`
    and its prompt stay unchanged; it *additionally* emits a **structured
    `task_manifest`** (`[{id, sprint_path, title, description, acceptance_criteria,
    target_files, deps}]`), **deterministically parsed from its own `**Task N:**`
    markdown — no new LLM call**, `sprint_plans` byte-identical. Ralph's increment
    unit is a **task** (dependency-respecting), and per-task "done" = *its
    acceptance-criteria test passes* — which closes the "report-presence is a
    proxy for done" gap. `.agent/STATE.md` holds the authoritative task checklist;
    `implementation_reports` stays sprint-keyed prose. The manifest is a new
    Pydantic boundary (negative-input test) but its *validation gate* + the Ralph
    persona are wired **only under `LOOP_ENGINE_CODER=ralph`**, so the default
    Sprint-Breakdown/Coder acceptance behavior is untouched.
  - **Sequencing: Ralph Coder first (part 1, sprint 19), declarative generators
    + PM critic-gate second (part 2, sprint 20).** De-risk the higher-uncertainty
    piece first; each part is its own green commit + HITL gate.
- **Phase 4 · part 2 build (locked, owner-confirmed 2026-07-08):**
  - **Persona config = PyYAML (owner reaffirmed over stdlib dataclasses).**
    Pinned `PyYAML==6.0.3` (CVE-clean); SBOM regenerated + `pip-audit` green.
    Loader is `yaml.safe_load`-only (asserted by test) — a hostile `!!python/*`
    tag fails to load rather than instantiating.
  - **PM escalation-shape change accepted as in-bounds (owner call).** Retiring
    the internal critic loop into a stateless `CriticGate` means a non-converging
    PM files **one combined** `execute_stage` escalation question (naming every
    blank/vague field) instead of N per-field questions. Documented, flag-gated,
    **NOT parity-claimed** on that path; the gate stays stateless (no loop state
    smuggled back). `fold_answers` on resume is unaffected (folds the free-text
    answer, never needed per-field granularity). Likewise the declarative
    multi-cycle path drops the `revision_history` trail (empty on the happy path
    in both modes — byte-parity holds there).
  - **Parity-preserving deviations from the plan's config sketch (documented):**
    (a) Architecture's config sets `extract_open_questions: false` — its markdown
    artifact *is* what the stage gate reads, so the gate extracts Open Questions
    exactly as classic; having the node also add them would diverge the produced
    `State`. Sprint Breakdown keeps it `true` (its gate sees only the parsed-JSON,
    so the node must lift questions). (b) Two config fields beyond the sketch:
    `prompt_style` (`cached` for Architecture/Sprint; `inline` for PM, matching
    the classic PM single-user-prompt call byte-for-byte) and `static_fields`
    (baseline keys like PM's `revision_history: []` so the clean-path JSON is
    byte-identical). (c) PM prompt files are numbered `00_pm_*` (PM is the first
    stage; `01_` is already `01_architecture_review_prompt.md`). (d) The on-disk
    `prompts/02`/`prompts/03` were regenerated to be **byte-identical to the
    personas' embedded `PROMPT_TEMPLATE`** (they previously differed only by
    line-wrapping) — required so the declarative node's `system_blocks` equal the
    classic persona's; a parity test now pins file==embedded both ways.
  - **`CriticGate` lives in `personas/pm/critic_gate.py`, not `core/`.** The
    import-boundary test forbids `core` importing any persona module but `base`,
    and the gate reuses `critic.review`; so it uses the `ManifestArtifactGate`
    pattern (a gate under `personas/` that imports `core.gates`). Core never
    imports it (the loop wiring does).
  - **Stage identity via thin subclasses.** The engine keys escalation counters
    and question `origin_stage` off `type(persona).__name__`; three identical
    `GeneratorNode` instances would collide. `ArchitectureGenerator` /
    `SprintBreakdownGenerator` / `PMGenerator` are one-line identity subclasses
    (all logic stays in `GeneratorNode`) giving each stage its own name.
- **Sprint-21 HITL-review settlements (owner-confirmed 2026-07-09):**
  - **Classic PM escalate-on-exhaustion is intentional, not inert.** The PM
    stage's `max_revisions=4` + `escalate_on_exhaustion=True` are live on the
    *classic* path too: its `ArtifactGate` returns REVISE on a
    missing/empty/invalid `project_spec`, so a non-converging classic PM now
    escalates to a human issue instead of hard-failing (`FAILED_STAGE`). The
    earlier "inert for classic — its gate never REVISEs" comment was wrong; a
    corrected comment + a pinning test
    (`test_classic_default_loop_pm_stage_escalates_on_exhaustion`) replace it.
    Deliberately *not* scoped to declarative — escalating a dead-end PM (its
    only resolver is the human) beats hard-failing on both paths.
  - **`key_merge` findings-accumulation accepted as in-bounds non-parity
    (review finding #4).** The engine accumulates findings across revision
    cycles — its *uniform* contract for every revise loop (`section_merge`,
    `full_reextract`, Coder/Ralph all share it); `_revise_key_merge` dedups only
    exact duplicates, so a 2nd+ PM revision's followup prompt can re-list a field
    already fixed in an earlier cycle. Classic's retired internal loop fed only
    the *latest* critic pass. Accepted, **NOT parity-claimed** (parity is the
    single-cycle happy path; multi-cycle is a declared replacement): a
    latest-only fix would be a special-case carve-out on shared infra (an
    engine-wide accumulation change → broad blast radius, or gate re-derivation
    inside the persona → boundary violation), both worse than the redundancy —
    and `key_merge` passes the *current artifact* alongside the findings, so a
    re-listed already-fixed field is reconciled against the spec, not a
    misdirection.
- **Sprint 23 trigger-surface decisions (locked 2026-07-09, Opus/Architect,
  23 planning pass):**
  - **Deliverable boundary = capability slice, real run against the existing
    default loop.** The webhook dispatches a genuine `run_new`/`run_loop`
    (or `run_graph_loop`) run of the **default** loop, `human_input` = the
    issue's title+body. Ships app + parser + dispatcher + shared runner +
    FastAPI dep + hermetic tests + docs. Does **not** deploy (no `uvicorn`/hosting
    decision) and does **not** wire the maintenance/bootstrap flow (Sprint 24+
    remain the callers that chain `tools/repo_io`).
  - **Dispatch = an injectable `RunDispatcher` seam, one in-process
    implementation; no fourth subprocess surface.** `InProcessDispatcher` runs
    the loop **in-process** on a worker thread (`asyncio.to_thread`), never as a
    `loop-engine run` subprocess. The "exactly three sanctioned subprocess
    surfaces" invariant is unchanged — the dispatched loop's own
    worktree/`gh`/pytest calls are those existing surfaces reached from a new
    caller, not a new surface.
  - **Web dependency = FastAPI (pinned); `uvicorn` deferred with hosting.**
    FastAPI is a pinned **runtime** dependency (loop-engine's first web
    dependency); the ASGI app is tested hermetically via `TestClient`.
    `uvicorn` is **not** pinned — the ASGI runner/port-binding decision lands
    with deployment. `httpx` (for `TestClient`) is a **dev/test** dependency
    only.
  - **Webhook auth = HMAC over the raw body, secret from an env var,
    fail-closed.** `X-Hub-Signature-256` (HMAC-SHA256 over the raw request
    bytes, `hmac.compare_digest`) is mandatory. The shared secret is
    `LOOP_ENGINE_WEBHOOK_SECRET`; unset → the app refuses to construct/start
    (fail-closed, never falls open). Not a keyring credential — `trigger/`
    imports no `keyring`.
  - **Trigger grammar = two bare-verb triggers; requirements = issue
    title+body (unified).** An `issues`/`labeled` event with label
    `agent-action`, or an `issue_comment`/`created` event whose first
    non-empty line is `/agent-run` — both carry no payload of their own;
    `human_input = issue["title"] + "\n\n" + issue["body"]`. Everything else,
    including `ping`, is a 2xx no-op.
  - **Placement = new top-level `src/loop_engine/trigger/` package;
    orchestrator-level caller** (sibling to `cli.py`, not a `tools/` module,
    not an MCP server). Enforced boundary: no `keyring`, no direct file
    write, no subprocess surface (`tests/trigger/test_boundaries.py`). No CLI
    `serve` subcommand in 23 — the deliverable is the importable ASGI `app`
    + the dispatcher.
- **Sprint-23a HITL-review settlements (owner-confirmed 2026-07-09):** the
  Sprint 23 trigger-surface diff (`62a3de2`) was HITL-reviewed; 3 findings on
  the dispatch/webhook robustness path, all fixed in 23a
  (`sprints/23a_trigger_review_fixes/sprint_plan.md`):
  - **`InProcessDispatcher` task retention.** `dispatch` discarded the
    `asyncio.create_task` result with nothing else holding a strong
    reference, so the event loop's weak reference let the run be
    GC-cancelled mid-flight — silently dropping the run **and** permanently
    wedging its `(repo, issue)` key in `_active` (every future dispatch for
    that issue dropped as a phantom duplicate). Fixed by retaining each task
    in an instance-level `self._tasks: set[asyncio.Task]`, added on create
    and dropped via `task.add_done_callback(self._tasks.discard)` — the
    `(repo, issue)` dedupe on `self._active` is unchanged; the task set is
    purely a liveness fix.
  - **Webhook `400` on an authenticated-but-unparseable body.** `await
    request.json()` raised uncaught on a signed-but-non-JSON body (e.g. a
    webhook misconfigured as `application/x-www-form-urlencoded`), producing
    an HTTP `500` and violating the module's own "never 500 on a malformed
    delivery" contract. Fixed by parsing the already-read raw body via
    `json.loads`, guarded by `except ValueError: return Response(status_code=400)`.
    Deliberately `400`, not `204`: the sender is authenticated (HMAC passed)
    but sent a body the app cannot parse — a real misconfiguration the
    operator should see surfaced red in GitHub's webhook UI. A well-formed
    but unrelated/`ping` delivery still returns `204` via the existing
    `parse_event → None` path; the two are not collapsed.
  - **Dispatcher run failures now logged.** `_run`'s `try/finally` had no
    `except`, so a `runner.run_new` exception propagated out of the
    un-awaited task with only asyncio's default "Task exception was never
    retrieved" noise at GC time. Fixed with
    `except Exception: logger.exception("run failed for %s#%s", *key)`
    before the `finally` — swallowed (fire-and-forget; the webhook already
    returned `202`), logging only the `(repo, issue)` key, never the
    payload or secret.
  - No new dependency, subprocess, credential, or file-write surface; the
    sanctioned-subprocess-surface count stays **three**; no `State`-schema
    change.
- **Sprint-19a HITL-review settlements (owner-confirmed 2026-07-09):** the
  Ralph-hardening pass (`d675d5d`) was reviewed; 3 findings, all fixed (flag-scoped
  to `LOOP_ENGINE_CODER=ralph`):
  - **`_upsert_task_section` orphaning (correctness).** Its terminator matched any
    `\n### `, so a model report body's own `### ` subheadings truncated the match
    mid-body and orphaned the tail — leaking stale content (including a resolved
    `## Edit Application Failures`, which could wedge the gate) across re-runs and
    defeating the idempotency finding (c) added. Fixed to key only off the section
    headers this module writes (`### Task ` / `### Regression fix`); pinned by a
    `### `-in-body test.
  - **`_repair` false-success ledger.** An escalating repair (one that raised Open
    Questions instead of fixing the suite) recorded a "Repaired…" memory lesson and
    a `### Regression fix` claim. Now branches its outcome on `new_questions` like
    `_task_increment`.
  - **Dependency name-matching precision (owner chose to tighten).** Bare
    single-word sprint names (`api`, `beta`) matched from incidental prose ("the
    public api"), reintroducing a milder version of the false-dep problem finding
    (b) fixed. Tightened to *distinctive* (underscore-bearing) tokens only — the
    full `NN_name` dir or a multi-word name; single words must be referenced by
    full dir or `Sprint N`/`#N`. Changed the deliberately-tested `beta`→sprint
    contract (test updated to a distinctive `data_layer` name + a false-positive
    negative test).
- **Sprint 24 maintenance-flow decisions (locked 2026-07-09, Opus/Architect,
  24 planning pass):**
  - **Deliverable boundary = capability slice, real run against the existing
    default loop over a real clone.** The flow clones a real target repo and
    dispatches a genuine `run_loop`/`run_graph_loop` of the **default** loop
    with cwd inside the clone. Ships `tools/git_io` + `runner.run_in_tree` +
    the `flows/maintenance` package + hermetic tests + a boundary test +
    docs. Does **not** add a CLI subcommand, does **not** wire the trigger
    surface to dispatch this flow, and does **not** build the bootstrap flow
    (piece 4) — those are Sprint 25+.
  - **Git-write surface = a new dedicated `tools/git_io` module; the fourth
    sanctioned subprocess surface.** Local git writes (`checkout -b`, `add`,
    `commit`, `push`) in the cloned tree are the flow-forced surface deferred
    from 22b. It lives in its own module — not bolted onto `tools/repo_io`
    (remote `gh` API) or `tools/worktree` (the orchestrator's own per-run
    isolation; the target clone is a foreign tree). Mirrors
    `worktree._git`'s posture exactly and validates the tree path by reusing
    `repo_io._validate_clone_dest`. The "exactly three sanctioned subprocess
    surfaces" invariant becomes **four** — `CLAUDE.md` and
    `tests/tools/test_subprocess_surfaces.py` updated together. `git push`
    rides `gh`'s clone-established credential helper — no new credential path.
  - **Execution model = an injectable run-step seam, wired to a new
    `runner.run_in_tree`; absorb = run in the clone's cwd.** The concrete run
    step is `run_in_tree`: default loop, cwd pinned to the clone, deliberately
    **not** opening `worktree_run` (the clone is itself the isolation
    boundary; `run_new`'s orchestrator-worktree wrapper would chdir into the
    wrong tree under `LOOP_ENGINE_ISOLATION`). "Absorb `CLAUDE.md` +
    `.agent/STATE.md`" = cwd inside the clone so the existing readers pick
    them up — no new absorb code.
  - **Green gate = `coder_tools`' pytest on the clone; push + PR are
    green-only; red ⇒ no push, no PR.** After the inner run, the flow runs
    the target's test suite through the existing sanctioned
    `coder_tools.run_tests` pytest surface against the clone. Green →
    `git_io.commit_all` → `git_io.push_branch` → `repo_io.open_pr`. Red →
    a failing status, no commit/push/PR. `open_pr`'s base defaults to
    `develop`, overridable. Auto-merge stays impossible — no merge verb
    exists and `open_pr` is the terminal GitHub call.
  - **Placement = new top-level `src/loop_engine/flows/` package (sibling of
    `trigger/`, `cli.py`); orchestrator-level caller.** Enforced boundary,
    asserted by `tests/flows/test_boundaries.py`: imports no `keyring`,
    writes no files directly, and introduces no subprocess surface of its
    own — it *calls* `tools/git_io`, the one permitted new surface.
  - No new dependency (`sbom.json` unchanged); no `State`-schema change; the
    local-git surface deferred from 22b is now landed.
  - **HITL-review settlement (Opus/Architect, 2026-07-10, `f8d388a`):** the
    green gate is a *quality* gate, not a *completion* gate — so the flow now
    guards **two** additional preconditions before any git write. (1)
    **Completion guard:** the inner run's returned `State` must be `COMPLETED`;
    a `FAILED_STAGE`/`BUDGET_EXCEEDED`/`AWAITING_ISSUE` run short-circuits to a
    new `run_incomplete` status. Rationale: a partial or human-paused tree can
    still pass pytest; without this guard an `AWAITING_ISSUE` pause (a run that
    escalated a question to a human) would be silently converted into a
    merge-ready PR. (2) **No-change guard:** a completed run that produced no
    diff short-circuits to a new `no_changes` status via a read-only
    `git_io.has_changes` probe (`git status --porcelain`) — this both models a
    clean no-op honestly and dodges `commit_all`'s `git commit` failing on an
    empty index (which previously raised an uncaught `GitIOError`). Both guards
    are covered by fake-collaborator unit tests + a real-`git_io` integration
    test; 497 tests green.

## Feature flags introduced

- `LOOP_ENGINE_ENGINE=langgraph` → LangGraph engine (default: classic `run_loop`).
- `LOOP_ENGINE_TOOLS=mcp` → Coder dispatches tools via the MCP provider
  (default: in-process `CODER_TOOLS`/`_execute_tool`).
- `LOOP_ENGINE_ISOLATION=worktree` → per-run git worktree; the CLI chdir's the
  run into it (default: no isolation, runs in the checkout). Worktree base dir
  overridable via `LOOP_ENGINE_WORKTREE_ROOT` (default `.worktrees/`).
- `LOOP_ENGINE_CODER=ralph` → the Ralph-loop Coder (one increment per
  invocation, self-loop via `execute_stage`) instead of the classic per-sprint
  Coder (default `classic`). *(Phase 4 · part 1 — planned, sprint 19.)*
- `LOOP_ENGINE_RALPH_MAX_ITERS` → Ralph iteration cap = the Coder stage's
  `max_revisions` under `ralph` mode (default `30`). *(Phase 4 · part 1.)*
- `LOOP_ENGINE_PERSONAS=declarative` → the three document personas (PM,
  Architecture, Sprint Breakdown) become config-driven `GeneratorNode`s and the
  PM stage gate becomes `CriticGate` (default `classic` keeps the persona
  classes byte-identical). Composes with `LOOP_ENGINE_CODER`. *(Phase 4 · part 2.)*

## What exists now (key modules)

- `core/engine.py` — `execute_stage()` (shared per-stage primitive) + classic `run_loop`.
- `core/graph_engine.py` — LangGraph `StateGraph` engine; `tests/core/test_graph_engine.py` guards parity.
- `core/state.py` — schema v4, `migrate_state_payload` (v1/v2/v3→v4).
- `tools/artifact_store.py` — `publish_artifacts`, `has_artifact`.
- `tools/agent_state/` + `.agent/STATE.md`/`.agent/MEMORY.md` — semantic-state layer.
- `mcp_servers/coder_tools_server.py` — stdio MCP server (read/execute-only).
- `tools/mcp/` — `MCPToolProvider` (discovery + dispatch on a background event loop); Phase 3b `container_server_params`/`sandbox_server_params` + preflight (inert).
- `tools/isolation.py` — single reader of `LOOP_ENGINE_ISOLATION` (`none|worktree|container|sandbox`) + `IsolationUnavailableError`.
- `personas/declarative/` — Phase 4 · part 2. `mode.py` (single reader of `LOOP_ENGINE_PERSONAS`), `config.py` (`GeneratorConfig` + `yaml.safe_load` loader), `services.py` (the shared-services registry: input-wrappers / output-adapters / revision-styles / `resolve_via_document`), `node.py` (`GeneratorNode` + the three identity subclasses `ArchitectureGenerator`/`SprintBreakdownGenerator`/`PMGenerator`), `configs/*.yaml`. Prompts externalized to `prompts/` (byte-identical to the personas' embedded templates).
- `personas/pm/critic_gate.py` — `CriticGate`, the PM critic *checks* re-expressed as a structural stage gate (core-safe home, like `ManifestArtifactGate`).
- `CLAUDE.md` — expanded with a portable "Global Conventions" skill section.

---

## Phase 3 — Execution Isolation *(planned — see `docs/phase3_execution_isolation_plan.md`)*

Detailed buildable spec lives in **`docs/phase3_execution_isolation_plan.md`**.
Summary + the decisions that resolved the earlier open questions:

- **Split into 3a (build now) + 3b (spec the seam, defer the build).** Forced by
  the environment: the devcontainer has **no `docker`/`podman`** and is itself an
  unprivileged container. DinD needs `--privileged`; DooD mounts the host socket
  (host-root-equivalent) into a process that already runs untrusted model code
  in-process — that *enlarges* the surface. So no DinD/DooD here.
- **3a — worktree isolation:** a `tools/worktree/` manager (`git worktree` per
  run, a new sanctioned subprocess surface) + a `worktree_run(run_id)` context
  manager that **`chdir`s** into the worktree for the run. Rooting is by chdir
  (not root-threading) because everything already keys off `Path.cwd()` — this
  needs ~zero signature changes, converges the MCP `cwd` param and the in-process
  tool path, and auto-tightens the existing traversal/symlink checks to the
  worktree. Gated by `LOOP_ENGINE_ISOLATION=worktree` (default off).
- **Snapshots stay in the main checkout** (state_io grows a `state_root()` the
  context manager pins to the orchestrator home); only the artifact tree
  (`src/`/`docs/`/`sprints/`/`.agent/`) follows the chdir into the worktree. So
  `publish_artifacts`'s `docs/artifacts/<run_id>/…` lands in the worktree — the
  chdir-following behavior this rooting choice was designed to preserve is
  exactly why sprint 32 kept the write as publication rather than deleting it
  (cross-cutting #1, resolved).
- **3b — container/sandbox:** preserved as a drop-in via the MCP provider seam
  (only the server *launch params* change: `docker`/`podman` on a daemon-bearing
  host, or `bwrap`/`nsjail` daemon-free). Reuses the `dev` Dockerfile stage;
  mounts worktree only. Spec + flag stub now, no executing code until a runtime
  is chosen and verified.
- **Honest caveat:** 3a is blast-radius isolation, **not** a security sandbox —
  on the default tools path untrusted code still runs in-process. The security
  boundary is 3b.

## Phase 4 — Flattening Orchestration *(planned; split into part 1 + part 2)*

Planning pass complete — the open questions below are resolved in the decisions
log above. Phase 4 is two separately-gated sub-phases, **Ralph-Coder-first**.

**Reality check that shaped the plan** (the earlier sketch was stale):
- Prompts already exist as `prompts/0N_*.md` but are *embedded verbatim* in each
  persona and pinned by a header **parity test** — not loaded from disk. PM has
  no prompt file (ported from pm-agent-loop, pinned by phrase).
- The code-stage exit-code gate **already exists** (`CoderGate` ACCEPTs only on
  pytest exit 0) and `execute_stage` **already runs a bounded revise loop**
  feeding gate findings back. So "error-loop until green" is largely already the
  shared primitive — Phase 4 reshapes the Coder *around* it rather than adding a
  new conditional edge.

### Part 1 — Ralph-loop Coder (`AgenticNode`) — sprint 19 *(detailed plan ready)*

See `sprints/19_ralph_coder/sprint_plan.md`. Two moves in one sprint: (1) the
Sprint Breakdown additionally emits a deterministic `task_manifest` (its prompt
+ `sprint_plans` unchanged); (2) the Coder becomes a Ralph loop that works the
manifest down **one task per invocation** from a fresh context, tracking
progress as a `.agent/STATE.md` checklist, driven to completion by
`execute_stage`'s existing revise loop + a **coverage-aware** exit-code gate
(green + *every task checked off*). Per-task "done" = its acceptance-criteria
test passes. Behind `LOOP_ENGINE_CODER=ralph` (default `classic`); flag-gated,
not parity-claimed. Termination is hard-bounded (iteration cap
`LOOP_ENGINE_RALPH_MAX_ITERS`, no-progress escalation via identical-findings,
USD budget as governor).

### Part 2 — Declarative generators (`GeneratorNode`) + PM critic-gate — sprint 20 *(built behind flag)*

Built behind `LOOP_ENGINE_PERSONAS=declarative` (default `classic`). See
`sprints/20_declarative_generators/sprint_plan.md` and the Phase 4 · part 2
decisions above.

- **`GeneratorNode`:** one YAML-driven node (prompt file, model, max_tokens,
  consumes/produces, input-context+wrap, output-adapter, revision-style,
  optional resolver) replaces the per-class boilerplate of **Architecture,
  Sprint Breakdown, and PM**. The genuinely-varying logic is a registry of
  **shared services** in `services.py` (input-wrappers `none`/`untrusted`;
  output-adapters `markdown`/`sprint_blocks`/`json_object`; revision-styles
  `section_merge`/`key_merge`/`full_reextract`; `resolve_via_document`), each
  factored from the classic persona code so the accept-path output is
  byte-identical. Pinned PyYAML; SBOM regenerated, audit green.
- **PM critic-gate:** the `MAX_REVISION_CYCLES` loop inside `PMPersona.run` is
  retired; `critic.review()` is re-expressed as a structural `CriticGate` the
  engine's revise loop drives (its identical-findings→escalate is the
  no-progress detector). `fold_answers` stays a resume-time resolver service on
  `PMPersona`, outside the node. Parity on the clean-extraction path; a
  documented, flag-gated escalation-shape change otherwise (see decisions).
- **Verification:** unit-level against the fake-LLM harness (byte-parity of
  Architecture/Sprint artifacts + `task_manifest`, PM clean-path `project_spec`,
  `system_blocks`/revision-message equality, `untrusted` wrapper bytes,
  `CriticGate` decisions, cross-engine `run_loop`≡LangGraph). Live-run
  parity/cost deferred to `sprints/DEFERRED_VERIFICATION.md` §4.

## Phase 5 — Autonomous Triggers & Multi-Repo Factory *(planning underway)*

**Scope (four separable pieces, dependency-ordered):**
- **(1) github MCP server** — the deferred cross-cutting #2; both flows below need it.
- **(2) Trigger surface** — FastAPI webhook server; trigger a graph run on an issue
  labeled `agent-action` or a slash command in an issue comment.
- **(3) Maintenance flow** — clone + feature-branch worktree → absorb target repo's
  `CLAUDE.md` + `.agent/STATE.md` → on green gate, push branch and open a PR against
  `develop`. **Auto-merge stays prohibited.**
- **(4) Bootstrap flow** — `create_repository` in `glunk-works` → scaffold
  (`hatch new` / OpenTofu boilerplate) in a fresh worktree → inject global `CLAUDE.md`
  → commit/push.

### Phase 5 planning pass (locked 2026-07-09, Opus/Architect)

- **Foundation-first: the github MCP server is the first slice** (piece 1), built
  before the trigger/flows. Both flows stack on it; it is the lowest-risk, best-understood
  piece.
- **Native re-front, not the official GitHub MCP server.** Build `mcp_servers/github_server`
  mirroring `coder_tools_server`: it delegates to a `tools/` module (never calls `gh`
  directly), so the "only the GitHub-owning `tools/` module talks to GitHub" boundary
  holds. Rationale: this repo enforces *exact* tool-set invariants by static test —
  a native server can assert "exposes exactly `{create_repository, clone_repo,
  create_branch, open_pr}`"; the official server is a large, evolving, ~60-tool surface
  (incl. `merge_pull_request`, contradicting "auto-merge prohibited") that we don't
  control and can't fake offline in CI. We pay more code for the enforced-minimal,
  testable boundary the migration exists to protect.
- **Credential = `gh` CLI's own auth** (as `tools/issue_io` already does) — no new secret
  path, nothing touches the `tools/llm/client.py`-only-imports-keyring invariant. Infisical
  (available) is an **orthogonal** secrets-provider decision, **deferred** until the factory
  host needs non-interactive PAT auth. Note: a github server is nonetheless the system's
  **first credentialed MCP server** (unlike credential-free `coder_tools_server`).
- **Tool surface = factory verbs only** — `{create_repository, clone_repo, create_branch,
  open_pr}`. The existing `issue_io` escalation verbs (create/read/comment) **stay on their
  current direct path** (don't destabilize `resume --from-issue`); unify onto MCP in Phase 6.
- **Full `loop_engine.mcp.json`-driven multi-server discovery** (pays down cross-cutting #3), not a
  bespoke second provider. Two design constraints, both locked: **(a) consumer split** —
  the provider feeds the **model's** coder tool loop only; github verbs are
  **orchestrator-invoked** and must never enter that loop, so discovery is
  **consumer-scoped** (each consumer builds a provider for the servers *it* names).
  **(b) heterogeneous launch profiles** — coder-tools is sandboxed/no-network (runs
  untrusted model code, runtime-computed launch); github runs un-sandboxed with
  network + `gh` auth (trusted first-party code, static `loop_engine.mcp.json` spec). `loop_engine.mcp.json`
  is **optional** with a built-in `coder_tools` default so absence is byte-identical to today.
- **Config filename = `loop_engine.mcp.json` at repo root** *(revised 2026-07-09, Opus/Architect,
  during 22a implementation)*. The planning pass originally named this file `.mcp.json`, but
  repo-root `.mcp.json` is **already** Claude Code's own project MCP config (`{"mcpServers":
  {"github": …}}`, the devcontainer's hosted-github wiring, committed `65ed47c`) — a different
  schema and purpose, and a filename Claude Code reserves by convention. loop-engine takes a
  distinct, product-namespaced file (`loop_engine.mcp.json`) for its own stdio launch specs; the
  two never mix. (`.ai/mcp.json` was rejected: `.ai/` is the dev-workflow layer, not product
  runtime.)

### Phase 5 sprint decomposition (Phase 4 split precedent)

- **Sprint 22a — `loop_engine.mcp.json` multi-server discovery** *(implemented, all 5
  tasks green: `sprints/22a_mcp_multiserver_discovery/sprint_plan.md`)*. Pure client-side
  refactor of `tools/mcp` — config-driven, N-server, consumer-scoped provider. **No** new
  server / subprocess / credential / file-write surface (confirmed — no dependency added,
  SBOM unchanged). Load-bearing gate: **coder-tools parity**, held (existing
  `test_mcp_provider.py` isolation assertions pass unchanged). `MCPToolProvider` already
  did multi-session routing; the gap — discovery + scoping — is closed by
  `load_mcp_config`/`build_provider_for` and proven by `tests/tools/test_mcp_multiserver.py`
  (two-server discovery/routing) and `test_mcp_provider.py::test_extra_config_server_never_reaches_coder_provider`
  (consumer-scope guard).
  **HITL gate after 22a before 22b.**
- **Sprint 22b — native `github_server` + `tools/repo_io` delegate + `loop_engine.mcp.json` entry**
  *(implemented, all 5 tasks green: `sprints/22b_native_github_server/sprint_plan.md`;
  HITL-reviewed and approved, `7b46227` → review-fix `5bc3811`)*. Ships the
  server (factory verbs), the GitHub-owning
  delegate module (new `tools/repo_io` sibling to `issue_io`; issue_io untouched), a
  **committed** repo-root `loop_engine.mcp.json` github stanza (the first real instance
  of that file), and the consumer-scoped `build_github_provider()` orchestrator helper
  — plus hermetic tests and the bidirectional coder⟂github scope guard
  (`tests/tools/test_mcp_provider.py`). **Open design item from 22a planning, now
  settled gh-only:** all four verbs ride the existing `gh` executable (`create_branch`
  via `gh api …/git/refs`, a remote ref) — `repo_io` is a **second `gh` consumer**, not
  a new subprocess surface; the "exactly three sanctioned surfaces" invariant holds,
  only its `gh` clause widens. The genuine local-git surface (`git push` inside a
  cloned tree) isn't needed by these four verbs and is deferred to Sprint 24's
  maintenance flow. **Capability slice only** — no production flow caller (no CLI
  subcommand, no loop wiring); Sprint 23 (trigger surface) dispatches only the
  existing default loop and deliberately does not chain these verbs either —
  Sprint 24 is the first caller. First real
  network+`gh`-auth server launch; live verification deferred to a daemon-bearing host
  (`sprints/DEFERRED_VERIFICATION.md`).
- **Sprint 23 — trigger surface** *(implemented, all 6 tasks green:
  `sprints/23_trigger_surface/sprint_plan.md`; HITL-reviewed — its 3 findings
  fixed in Sprint 23a (`212beeb`) and re-reviewed clean, see "Sprint-23a
  HITL-review settlements")*.
  Ships `src/loop_engine/runner.py` (the shared `run_new` run-starter,
  factored out of `cli.run` so both the CLI and the dispatcher call one
  source of truth) and the new `src/loop_engine/trigger/` package: `parse.py`
  (`RunRequest` + the locked trigger grammar), `dispatch.py` (`RunDispatcher`
  seam + `InProcessDispatcher`, worker-thread dispatch, in-memory dedupe),
  `app.py` (the FastAPI ASGI app — HMAC-verify raw body → parse → dispatch).
  **Capability slice, real run against the existing default loop** — no
  `tools/repo_io` call, no clone/branch/PR, no deploy (no `uvicorn` pin, no
  hosting decision, no CLI `serve` subcommand). Coverage is entirely
  hermetic (`TestClient` + injected fake dispatcher + patched `runner.run_new`
  + a package boundary static test asserting no `keyring`, no direct file
  write, no subprocess surface); live webhook→real-run verification is
  deferred to a daemon-bearing host (`sprints/DEFERRED_VERIFICATION.md` §6).
  FastAPI is loop-engine's first web runtime dependency (`httpx` dev-only for
  `TestClient`); `sbom.json` regenerated, `hatch run audit` green.
- **Sprint 24 — maintenance flow** *(implemented, all 6 tasks green:
  `sprints/24_maintenance_flow/sprint_plan.md`; HITL review pending)*. Ships
  `tools/git_io` (the deferred local-git subprocess surface — `checkout_branch`/
  `commit_all`/`push_branch` against a cloned tree — re-opened, flow-forced,
  as the genuine **fourth** sanctioned surface, not bolted onto `repo_io`=`gh`
  or `worktree`=orchestrator-own isolation), `runner.run_in_tree` (the default
  loop, cwd pinned to the clone, deliberately **not** `worktree_run`), and the
  new `src/loop_engine/flows/maintenance/` package chaining `repo_io.clone_repo`
  → `git_io.checkout_branch` → `run_in_tree` → a green gate
  (`coder_tools.run_pytest` against the clone) → **green-only**
  `git_io.commit_all`/`push_branch` + `repo_io.open_pr` (base `develop`, red ⇒
  no git write, no PR). **Capability slice** — no CLI subcommand, no trigger
  wiring, no bootstrap flow. Coverage is hermetic: a `flows/` boundary test
  (no `keyring`, no direct write, no subprocess surface of its own) plus a
  real-`git_io`-against-`tmp_path` green/red end-to-end proof; live
  clone→push→PR is deferred to a daemon-bearing host
  (`sprints/DEFERRED_VERIFICATION.md`). No new dependency, `sbom.json` unchanged.
- **Sprint 25 — bootstrap flow** *(complete, all 6 tasks green:
  `sprints/25_bootstrap_flow/sprint_plan.md`; HITL-reviewed by Opus and
  approved `79b535d`, archived)*. Ships
  `tools/scaffold` (the deferred second file-write surface — `write_skeleton`
  writing bundled package-data templates into a validated foreign clone tree,
  `pkg_name` sanitized to a safe Python identifier — moving the file-write
  invariant one→two, mirroring how 24 moved the subprocess invariant three→four),
  bundled `kind="python"` templates + a byte-identical `templates/CLAUDE.md`
  sync-guard against `.ai/context/conventions.md`, and the new
  `src/loop_engine/flows/bootstrap/` package chaining `repo_io.create_repository`
  → `repo_io.clone_repo` → `git_io.checkout_branch(main)` →
  `scaffold.write_skeleton` → `git_io.commit_all`/`push_branch(main)` →
  `repo_io.create_branch(develop, base=main)` (ordering load-bearing: the base
  ref must exist remotely before `create_branch` reads its SHA). **Skeleton
  only** — no inner loop, no LLM run/budget, no green gate, no `open_pr`, no
  CLI subcommand, no trigger wiring, no IaC template set (deferred behind the
  `kind` seam). Coverage is hermetic: a `flows/` boundary test provably
  enumerating `flows/bootstrap`, plus a real-`scaffold`+real-`git_io`-against-
  `tmp_path` end-to-end proof (seeded on a non-`main` initial branch, proving
  the unborn-HEAD handling) against a local bare remote, `repo_io` faked; live
  `create_repository`→clone→scaffold→push→`create_branch` is deferred to a
  daemon-bearing host (`sprints/DEFERRED_VERIFICATION.md`; `glunk-works` org
  access remains an open hosting question). No new dependency, `sbom.json`
  unchanged; the four sanctioned subprocess surfaces are unchanged.

**Still-open questions (deferred to their sprints, not the github foundation):**
where the trigger server is hosted (`uvicorn`, deferred with deployment); org
access to `glunk-works`; how runs are queued/rate-limited durably (23 ships
only best-effort in-memory dedupe behind the `RunDispatcher` seam). **Settled
in 23:** the webhook auth model — HMAC-SHA256 over the raw body,
`LOOP_ENGINE_WEBHOOK_SECRET` env var, fail-closed.

## Phase 6 — Collapse the flags (decommission the scaffolding)

### Phase 6 planning pass (locked 2026-07-10, Opus/Architect)

- **LD1 — Scope = the `issue_io`→MCP unification is the verification-independent
  first slice.** The four flag deletions, the `artifacts` strip, and the
  `loop.py` flag-branch collapse are all host-gated or downstream of a
  deletion, so they are a **later block**, not Sprint 26. Building a server +
  provider + seams + hermetic tests needs no host — doing it first, offline,
  is the correct sequencing. The roadmap already scoped the issue-verb
  unification into Phase 6 (see cross-cutting follow-up #2 below) and
  `next-steps.md` flagged "CLI unification onto MCP (`resume --from-issue`)"
  as a prerequisite gating parts of the collapse.
- **LD2 — Unification scope = FULL, both read and write sides** (user-confirmed).
  Both `cli.py`'s `resume --from-issue` (read) and `core/engine.py`'s
  escalation-ladder issue filing (write) get MCP-backed adapters + injectable
  seams.
- **LD3 — Runtime posture = capability + seams now; classic stays the DEFAULT;
  default-flip + classic deletion deferred to the host-gated block**
  (user-confirmed). Mirrors 22b's github posture exactly: the MCP route is
  proven as a capability, but the classic direct `gh` calls remain what
  actually runs until the MCP↔`gh` round-trip is live-verified on a
  daemon-bearing host.
- **LD4 — Server = a thin `gh` shell over primitive args; domain
  rendering/parsing stays pure lib in `tools/issue_io`.** `State`/`Question`
  never cross the MCP boundary — only strings/JSON, matching `github_server`'s
  posture.
- **LD5 — Injection mechanism = an `issue_filer` collaborator threaded like
  `llm_client`.** Added to `execute_stage`/`_pause_for_issue` and forwarded
  by both `run_loop` and `run_graph_loop` (one seam covers both engines, since
  `run_graph_loop` is built on the same `execute_stage` primitive).
- **LD6 — No new subprocess surface, no new dependency, no `State` change, no
  keyring.** The issue server delegates to `tools/issue_io`'s already-sanctioned
  `gh` surface; the server subprocess is `stdio_client`-spawned (not a fifth
  surface, per the existing Phase 3b precedent); `mcp` is already a dependency.

### Sprint 26 — `issue_io` → MCP unification (implemented)

Landed the third native MCP server (`mcp_servers/issue_io_server.py`, mirroring
`github_server.py`) exposing exactly `{create_issue, read_issue}`;
`build_issue_provider()` + `mcp_issue_filer`/`mcp_read_issue` client adapters
(`tools/issue_io/mcp_client.py`); the `tools/issue_io` pure/`gh` split
(`render_question_issue`/`create_issue` on the write side,
`parse_issue_answers`/`read_issue` on the read side — `file_question_issue`/
`read_issue_answers` remain behavior-preserving thin wrappers); the injectable
`issue_filer` write seam threaded through `execute_stage`/`_pause_for_issue`/
`run_loop`/`run_graph_loop` (default `None` resolves to the classic
`file_question_issue` via module-global lookup at call time, so existing
`monkeypatch.setattr("loop_engine.core.engine.file_question_issue", ...)`
tests keep working unmodified — binding the classic filer as a literal
default-argument value would have snapshotted it at import time and broken
that monkeypatch pattern); an analogous injectable read seam in `cli.py`'s
`resume --from-issue` (`_resolve_issue_reader()`, same module-global pattern);
and the three-way pairwise-disjoint tool-set assertion in
`tests/tools/test_mcp_provider.py`. Sanctioned subprocess surfaces stay
**four**; no new dependency (`sbom.json` unchanged); no new feature flag; no
`State` change; no new `keyring` import. **Capability + seams only** — the
classic direct `issue_io` calls remain the runtime default per LD3; nothing
flipped, nothing deleted. Live MCP↔`gh` round-trip verification (real
`create_issue`/`read_issue` through the server subprocess with real `gh` auth)
is deferred to a daemon-bearing host, recorded in
`sprints/DEFERRED_VERIFICATION.md`, gating together with the eventual
default-flip and classic-path deletion (both still part of the host-gated
block below). Plan: `sprints/26_issue_io_mcp_unification/sprint_plan.md`.

**HITL review (Opus/Architect, 2026-07-10) — APPROVED.** Diff reviewed at high
effort (8-angle `/code-review` + manual trace). No default-path defect: suite
green, conventions/boundary posture intact (keyring-free, four subprocess
surfaces, three-way disjoint verb sets, no `State` change). Findings are
forward-looking seam asymmetries + test gaps + two pre-existing traps carried
into touched code — **none block approval**, all deferred (nothing on the
default path). The seam-shaped findings **fold into the host-gated flip block
below** (they are exactly the seams that block exercises), not a new sprint:

- **R1 (fix at flip) — `mcp_read_issue` is not a drop-in reader adapter.**
  `mcp_issue_filer(provider)` returns a closure matching the `IssueFiler` seam,
  but `mcp_read_issue(provider, issue_number)` is a raw 2-arg fn, not a factory
  matching the reader seam's `Callable[[int], dict]` — the `mcp_client.py`
  module docstring's "signature-compatible … drop into the reader seam" claim
  is false for the read side. Wiring `cli._issue_reader = mcp_read_issue` by
  analogy to the filer raises `TypeError` at resume time. Make it a
  `mcp_issue_reader(provider) -> Callable[[int], dict]` factory before the flip.
- **R2 (fix at flip) — `resume` never forwards `issue_filer` to the engine.**
  `cli.resume` injects the *read* seam but its `_select_engine()(...)` call omits
  `issue_filer`; once the reader is MCP-backed, a resumed run that re-escalates
  would read-via-MCP but write new issues via classic `gh`. Thread the write
  seam through resume in the same change that flips the reader.
- **R3 (fix at flip) — two injection mechanisms for one capability.** Write seam
  = threaded param; read seam = process-wide module global (`_issue_reader`).
  The global can't carry a per-run provider (multi-repo-factory hazard). Unify
  on the threaded-collaborator shape when wiring the flip.
- **R4 (test, fold into flip) — injected-filer coverage is partial.** The
  injected-`issue_filer` tests exercise only the unresolved-after-ladder
  `_pause_for_issue` site; the escalation-cap and replan-cap sites are covered
  only by the default-path stub, so a dropped `issue_filer` there passes green.
  Add injected-filer cases at all three pause sites.
- **R5 (pre-existing, worth fixing) — `resume` crashes on the documented abort
  path.** Closing the issue without answers (the documented abort) makes
  `parse_issue_answers` raise `IssueClosedWithoutAnswersError`, uncaught in
  `cli.resume` → raw traceback + exit 1 instead of a clean abort. The Sprint 26
  pure/`gh` split also dropped the issue number from that exception's message.
  Catch it and exit cleanly; restore the issue number to the message.
- **R6 (pre-existing, worth fixing) — first-block-only answer parse.**
  `parse_issue_answers` uses `_ANSWERS_BLOCK_RE.search` (first ```answers block
  per comment only); a human "Quote reply" that echoes the bot's own example
  block silently drops the real answers below it → `resume` reports "no answers
  yet". Switch to `finditer` over all blocks in a comment.
- **R7 (host-gated nit) — committed MCP stanzas launch bare `python`.**
  `loop_engine.mcp.json`'s `issue`/`github` stanzas exec `python` (not the active
  interpreter), so the servers fail to spawn on a `python3`-only host — unlike
  the `coder_tools` built-in default which uses `sys.executable`. Resolve when
  the live round-trip check (`DEFERRED_VERIFICATION.md` §9) runs on the host.

Lower-severity (recorded, no action required): the MCP `read_issue` path
triple-round-trips the comment JSON (parse→dump→parse, once-per-resume,
non-default path); `test_render_..._byte_for_byte` is near-tautological and
doesn't pin MCP-path body parity; the `_FakeProvider` test double is hand-rolled
in four files with no shared fixture.

*(sketch — the remaining, host-gated block)*

**Why this phase exists.** Every phase adds a feature flag so earlier behavior
stays runnable and each phase boundary is checkout-able — the right call *during*
an unmerged migration. But the flags are **temporary scaffolding, not permanent
optionality**; left unmanaged they calcify into a combinatorial matrix of
untested cross-products, doubled maintenance, and a confusing surface. Phase 6
is the tracked teardown so that never happens: the migration ends with **one
path**, not N. It runs last, after every new path is proven end-to-end on a
daemon-bearing host (the same host the deferred 3b/Ralph verification needs).

**Not all flags are scaffolding — classify before deleting:**

| Flag | Fate | Sunset criterion |
|---|---|---|
| `LOOP_ENGINE_ENGINE=langgraph` | ✅ **DELETED** (`ec8b0e5`, sprint 27 Task 1) | Gated on V1. `run_loop`, `use_langgraph_engine`, `ENGINE_ENV_VAR` and both `_select_engine()` indirections are gone; `run_graph_loop` is called directly. The classic-vs-graph parity harness collapsed into `test_engine.py` (one engine ⇒ nothing to compare), keeping only genuinely graph-specific routing coverage. **Public API break:** `loop_engine.run_loop` → `loop_engine.run_graph_loop`. |
| `LOOP_ENGINE_TOOLS=mcp` | ✅ **DELETED** (`adb20b3`, sprint 27 Task 2) | Gated on V1. `use_mcp_tools`, `_TOOLS_ENV_VAR`, the in-process `CODER_TOOLS`/`_execute_tool` dispatch, and the now-orphaned hand-written tool-schema dicts (`READ_TOOL_SCHEMAS`, `RUN_TESTS_TOOL_SCHEMA`, `RUN_LINT_TOOL_SCHEMA` — FastMCP derives the server's schemas from the function signatures) are gone. Retires the "container isolation requires `TOOLS=mcp`" refusal: with no in-process path, the sandboxing guarantee is structural, not conditional. |
| `LOOP_ENGINE_CODER=ralph` | ✅ **DELETED** (`3ea8106`, sprint 27 Task 4) | Gated on V2 (PASS, re-attempt #8). `CODER_ENV_VAR`, `coder_mode`, `use_ralph_coder`, `CoderIacPersona`, `CoderGate` and `_last_reported_sprint` are gone; `ralph_max_iterations()` survives (genuine runtime config). Three paths `RalphCoderGate` *shares* with the deleted `CoderGate` were only covered by `CoderGate`'s tests (edit-failure short-circuit, no-tests-collected, content-gate deferral) and were **ported**, not lost. |
| `LOOP_ENGINE_PERSONAS=declarative` | ✅ **DELETED** (`56c3824`, sprint 27 Task 3) | Gated on V1. `use_declarative_personas`, `PERSONAS_ENV_VAR`, `PMPersona`, `ArchitecturePersona`, `AgileSprintBreakdownPersona` and their embedded templates are gone; `prompts/` is the sole source of truth. **Kept** what the declarative path still calls: `pm.persona.fold_answers` (+ `_wrap_untrusted_artifact`/`_parse_extraction_response`) and `agile_sprint_breakdown.persona._parse_sprint_blocks`. Their only direct coverage lived in the deleted persona tests and was **re-homed** onto the surviving code, not dropped. |
| `LOOP_ENGINE_ISOLATION` | ✅ **KEPT** (genuine runtime config) | Not old-vs-new: `none` for local dev, `container` for the factory host. Stays permanently. (So does `LOOP_ENGINE_RALPH_MAX_ITERS` — the Ralph self-loop bound, config rather than scaffolding.) |

**Also collapses here:**
- The **dual-field `artifacts`/`artifact_refs` strip** (cross-cutting #1) —
  **resolved by sprint 32, inverted (FD1 below):** `artifact_refs` is what
  dropped, not the inline bodies. `State.artifacts` stays as the permanent
  source of truth; `schema_version` bumped 3 → 4 with `migrate_state_payload`
  extended to pop the retired key.
- Any **flag-branching in `loops/default/loop.py`** (Ralph-vs-classic stage
  wiring, manifest-gate selection) collapses to the single surviving wiring.

- **FD3 — SUPERSEDED by sprint 32's FD1 (2026-07-12): the direction was inverted.** `artifact_refs` is what got stripped, not `State.artifacts` — see FD1 below. Text preserved as originally locked; the deferral reasoning was correct, only the assumed direction was wrong. **The `artifacts` strip is a REFACTOR, not a deletion; deferred out of the flip block** *(locked 2026-07-11, Opus/Architect, sprint 27 execution pass; user-confirmed)*. Task 5 as planned rested on a false premise: *"with `run_loop` deleted, the LangGraph engine is the sole reader of `State.artifacts`, so the inline bodies drop."* The engine was never the reader. **Every persona and every gate indexes `state.artifacts[...]` directly** (`architecture/persona.py`, `coder_iac/ralph.py`, `declarative/services.py`, `core/gates.py`, `core/coder_gate.py`, `agile_sprint_breakdown/manifest.py`), and `artifact_refs` is currently a **write-only mirror**: `mirror_to_disk` populates it at snapshot time, the only thing reading it is `has_artifact` (an existence check), and `get_artifact` — the function that would actually load a body from disk — **has zero callers**. So deleting `run_loop` changes nothing about who reads `artifacts`. Stripping the field means rewriting ~8 persona/gate/service modules to read through `artifact_store`, which is (a) **additive behavior change** — disk I/O in the hot path of the exact code V1/V2 just verified — in a block whose charter is *"only removes scaffolding — no new behavior"*, and (b) hazardous in the `run_in_tree`/`flows/maintenance` case, where artifact paths are cwd-relative (`docs/artifacts/<run_id>/<key>`) and the run is chdir'd into a foreign clone. **Consequence:** sprint 27 stays purely subtractive (Tasks 0–4, 6, 7); the strip becomes its own sprint with a real design pass (make `artifact_store` the read path, settle the cwd/clone question, then bump `schema_version` 3→4 and extend `migrate_state_payload`). Nothing else is blocked — Task 6 gated on Tasks 3+4, not 5.

- **FD1 (sprint 32) — The direction is INVERTED: `artifact_refs` is stripped, `State.artifacts` survives** *(locked 2026-07-12, Opus/Architect, sprint 32 planning pass; user-confirmed)*. `get_artifact` (the only disk-read path) had zero production callers and nothing in `src/` reads `docs/artifacts/` back — `artifact_refs` was a write-only mirror. `State.artifacts` has ~14 read sites across 8 persona/gate/service modules and feeds the prompt-cache prefix directly. A snapshot's self-containment is also load-bearing (finding R10): stripping the inline bodies would turn a snapshot into dangling pointers after a prune/foreign-clone/cross-CWD resume. Full reasoning: `sprints/32_artifact_refs_strip/sprint_plan.md` FD1.
- **FD2 (sprint 32) — The artifact bodies ARE the prompt-cache prefix; routing them through disk is a cache hazard with no upside.** `Path.read_text()`'s universal-newline translation would silently break cache-hit byte-identity for a body carrying `\r\n`. Actual token savings live in backlog BL-3 (prompt composition), orthogonal to storage location — this sprint saves zero tokens, by design. Full reasoning: sprint plan FD2.
- **FD3 (sprint 32) — The disk write is PUBLICATION, not externalization, and is KEPT.** `docs/artifacts/` is not gitignored and `flows/maintenance` commits the whole tree, so the bodies ship as documentation in the managed repo's PR. `mirror_to_disk` is renamed `publish_artifacts` and demoted to a pure side effect (returns `None`, mutates no state); the write itself survives. Full reasoning: sprint plan FD3.
- **FD4 (sprint 32) — Removing a field under `extra="forbid"` is a BREAKING schema change: `schema_version` 3 → 4, `migrate_state_payload` pops the retired `artifact_refs` key.** Every prior bump was additive-with-a-default; this one required an explicit pop, tested against a payload with a *populated* ref (an empty-dict fixture would pass a broken pop-less migration and hide the bug). Full reasoning: sprint plan FD4.

**Discipline:** each deletion is its own dedicated, green commit (flip default →
remove the dead path + its tests/flag in one reviewable change), never bundled
with feature work. A path is only deleted *after* its replacement is verified on
a host — Phase 6 removes proven-redundant scaffolding, it does not take the
migration's remaining risk.

**Open questions — RESOLVED 2026-07-10 (Opus/Architect flip-planning pass, user-confirmed); planned in `sprints/27_phase6_flip_block/sprint_plan.md`:**
- **FD1 — Verification bar = per-flag *criterion*, batched *execution*.** Each flag keeps its own sunset criterion, but the runs are batched where paths co-occur: **one big end-to-end factory run** clears `ENGINE`+`TOOLS`+`PERSONAS` together (they're on the happy path and mutually exercised in the target production config; parity-checked against the classic baseline), with **two carve-outs** that a happy-path run structurally cannot exercise — **Ralph** (§3: a dedicated multi-sprint convergence/cost run, no parity oracle) and the **issue path** (§9: a forced pause-for-issue round-trip + R1–R4 seam wiring). Consequence: **deletion in `run_loop`-first dependency order** (`ENGINE` → `TOOLS` → `PERSONAS` → `CODER=ralph` → issue-path flip), since the `artifacts` strip and `loop.py` collapse are downstream of `run_loop` deletion. Rationale: isolated per-flag verification is both wasteful (re-provision host + re-burn real budget for paths that always run together) and weaker (never proves the interacting combined config that is the one-path end state).
- **FD2 — No flag survives as a break-glass; git is the recovery mechanism.** Full deletion for all four sunsettable flags — an escape hatch kept live is a path kept untested (and for `ENGINE`, one that keeps `State` fat by blocking the `artifacts` strip), re-creating the exact calcification Phase 6 exists to remove. The "what if Ralph regresses" anxiety is answered by **tagging the pre-deletion commit** (`pre-phase6-classic`): the classic paths live in history, recoverable via `git revert` of a deletion commit — no permanently-live, permanently-untested branch. `PERSONAS` classic prompt *content* is separately preserved (promoted to `prompts/` as sole source of truth; only the redundant `run()` bodies + embedded templates are deleted). `LOOP_ENGINE_ISOLATION` stays — genuine runtime config (`none`/`container`), not a break-glass.

## Cross-cutting follow-ups (don't lose these)

1. **Drop the inline `artifacts` body-dict** once the LangGraph engine is the
   sole reader (completes the 1c "strip" — makes state truly thin). **Now scoped
   into Phase 6** — it can only happen after `run_loop` is deleted.
2. **state-io + github MCP servers** (deferred from Phase 2) — ✅ the github one
   **delivered as a capability** in 22b (`mcp_servers/github_server.py` +
   `tools/repo_io`, exactly `{create_repository, clone_repo, create_branch,
   open_pr}`); Sprint 23 (trigger surface) dispatches the default loop only
   and deliberately did not chain it. **✅ Sprint 24 (maintenance flow) is now
   the first production caller** — `flows/maintenance.run_maintenance` chains
   `clone_repo` → `git_io.checkout_branch` → the default loop → a green gate
   → `git_io.commit_all`/`push_branch` → `open_pr`, gated on green tests.
3. **Full `loop_engine.mcp.json`-driven multi-server discovery** — ✅ mechanism
   generalized to N servers via `loop_engine.mcp.json` (22a: `load_mcp_config` +
   `build_provider_for`, proven by `tests/tools/test_mcp_multiserver.py`'s
   two-server discovery/routing test); `loop_engine.mcp.json`-declared static
   servers — ✅ the first (`github`) landed with 22b, **committed** at the repo
   root.
4. **Ralph cap-exhaustion → escalate, not fail.** Part-1 v1 hard-fails
   (`FAILED_STAGE` snapshot) when the Ralph loop hits its iteration cap while
   still making progress; a nicer behavior is to file a human issue ("did not
   converge") instead. Deferred so `execute_stage` stays generic for now. **Still
   open** — the Phase 4a repair increment (#6a) also terminates at the cap via
   `FAILED_STAGE`, so this deferral now covers the repair path too.
5. **Real Ralph-run convergence/cost is unverified on this branch** (no LLM key
   + no container runtime here) — deferred to a live host run, recorded in
   `sprints/DEFERRED_VERIFICATION.md`. Now includes the **self-healing** repair
   path (#6a): whether a real regression-repair increment converges at acceptable
   cost is part of the deferred live verification.
6. **Ralph code-review findings (`195f7b7`) — ✅ addressed in the Phase 4a
   hardening pass** (`sprints/19a_ralph_hardening/sprint_plan.md`), a dedicated
   green commit before sprint 20. All four are flag-scoped to `LOOP_ENGINE_CODER=ralph`:
   - **(a, most substantive) Ralph can't fix a cross-task test regression.** ✅
     `RalphCoderGate` now emits a distinct `RALPH_REGRESSION_PREFIX` finding when
     *every* manifest task is checked off but the suite is red; `RalphCoderPersona`
     routes that (no selectable task + regression finding) to a **repair increment**
     — one fresh-context tool loop scoped to fixing the regression, marking no task,
     upserting a single `### Regression fix` report section — instead of the
     escalate-when-blocked dead-end. The persona distinguishes this from an
     all-blocked-deps state purely by the gate's finding prefix (never by sniffing
     pytest output). Residual: cap-exhaustion still routes through `FAILED_STAGE`
     (see #4). Fix stayed persona/gate-local — no `execute_stage` change.
   - **(b) Spurious cross-sprint deps from incidental digits.** ✅
     `manifest._dependency_sprint_paths` no longer matches bare `\d+`; it matches
     sprint-qualified number tokens (`Sprint 3`, `#3`) or a sprint directory/name
     token (`01_ci_cd_foundation` / `ci_cd_foundation`) appearing whole in the
     `Dependencies:` field. The order-safe "nothing matched ⇒ immediately-preceding
     sprint" fallback is retained (strictly more conservative — can only remove
     spurious edges).
   - **(c) Duplicate report sections.** ✅ Report sections are now **upserted** by
     task id (`_upsert_task_section`): a re-run task (or repeated repair) replaces
     its `### Task <id>:`/`### Regression fix` block rather than appending a
     duplicate.
   - **(d) Only `findings[-1]` reaches the model.** ✅ The persona partitions
     carried findings into resolution answers (shared `RESOLUTION_FINDING_PREFIX`)
     and gate status, and composes the prompt from **all** resolution answers plus
     the **latest** status line — so a resolution answer survives every
     post-re-entry iteration while the prompt stays bounded and current.

## How to run / verify

```bash
hatch run test            # full suite (215 after P1, 226 after P2, 246 after P3a, 279 after P3b, 385 after P4·part2)
hatch run lint && hatch run format && hatch run audit && hatch run sbom
LOOP_ENGINE_ENGINE=langgraph    hatch run test tests/core/test_graph_engine.py
LOOP_ENGINE_TOOLS=mcp           hatch run test tests/tools/test_mcp_provider.py
LOOP_ENGINE_PERSONAS=declarative hatch run test tests/personas/declarative tests/loops/test_declarative_pipeline.py
```
