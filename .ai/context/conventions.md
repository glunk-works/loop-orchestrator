# Global Conventions (portable skill repository)

Referenced from the lean root `CLAUDE.md`. This is the engine's **global
directive/skill repository**: repo-agnostic ground rules the personas load as
conventions, and the block the bootstrapping/maintenance workflows inject into
every managed `glunk-works` repo. Keep it self-contained — no references to
files that only exist in *this* repo — so it stays valid when copied elsewhere.

## Python conventions
- **Formatting is not negotiable:** `ruff format` (line length 100) is the single source of truth; never hand-format against it. Lint with `ruff check` under rule sets `E, F, I, B, S` (pycodestyle, pyflakes, isort, bugbear, bandit). Import order is isort-managed — do not hand-order.
- **No `# noqa` without an inline justification** on the same line (`# noqa: RULE — reason`). A bare `# noqa` fails review.
- Target `python >= 3.12`. Full type hints on public functions; prefer `X | None` over `Optional[X]`, `list`/`dict` over `typing.List`/`Dict`.
- **No hardcoded secrets anywhere** — not in source, tests, or committed state/snapshot files. Credentials come from the OS keyring (or the documented double-gated CI fallback), never CLI flags or plain env vars.
- Every Pydantic-validated I/O boundary needs a test proving invalid input is rejected. Pin dependencies to CVE-free versions and regenerate the SBOM whenever deps change.

## OpenTofu / IaC conventions
- Format with `tofu fmt`; every change must pass `tofu validate` with exit 0 (this is the deterministic gate — no LLM judges IaC).
- One concern per module; expose inputs via `variables.tf`, outputs via `outputs.tf`, pin provider **and** module versions (no floating `latest`).
- Remote, locked state only — never commit `.tfstate` or `.terraform/`. No secrets in `.tf` or `.tfvars`; source them from the secret manager at plan/apply time.
- Name resources `snake_case`; tag every resource with owner + managing-repo so the factory can attribute drift.

## Commit / PR conventions

- Commits are small, self-contained, and green (`ruff check` + `ruff format --check` + the test suite all pass before committing). Sign commits.
- PRs target the integration branch (`develop`), never `main`/`master` directly, and never auto-merge — human review or remote CI validation is always required before merge.
- A change touching a versioned state schema must bump its `schema_version` and extend the migration path in the same commit.

### Message grammar: Conventional Commits

```
type(scope): imperative subject, lower-case, no trailing period
                                            <- 72 chars max
<blank>
Body: why the change exists and what it trades off. Wrap at 80.
Not a restatement of the diff — the diff is already in the commit.
<blank>
Sprint: 31
Finding: F-RALPH-FALSE-COMPLETION
Co-Authored-By: ...
```

- **`type`** is one of: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`,
  `revert`. There is deliberately **no `style`** — the formatter owns formatting, so a
  style-only commit should not exist.
- **`scope`** is the module the change lives in, drawn from the repo's *enforced module
  boundaries* (in this engine: `core`, `personas/ralph`, `tools/mcp`, `tools/git_io`,
  `flows`, `trigger`, `mcp_servers`, `ci`, …). The commit vocabulary and the
  architectural vocabulary are deliberately the same words — if a change doesn't fit one
  scope, that is a signal it is really two commits.
- **`!` marks a breaking change** (`feat(core)!:`). For a versioned-state repo this has a
  precise meaning: a `State` shape break, which must carry a `schema_version` bump and a
  migration-path extension **in the same commit** (see above). The `!` makes that
  visible in one line of `git log`.
- **The type prefix is not a licence for a vague subject.** `fix(personas/ralph): fix bug`
  is worse than no convention at all. The subject still has to say what changed:
  `fix(personas/ralph): gate task completion on successful edit application`.
- **Trailers link a commit to the project's own ID space** — `Sprint: NN`,
  `Finding: <ID>`, `Closes: #N`. This is what makes "which commit closed this finding?"
  a `git log --grep` instead of an archaeology session.

### PR titles use the same grammar — and are the enforced surface

The merge is a squash, so **the PR title becomes the commit subject on the integration
branch**. It is therefore the only message that must be well-formed, and the only one
worth a CI check (`pr-title` job). Commits *within* a branch may be messy WIP; the
history that survives is the PR title. Enforcing every WIP commit buys nothing and adds
friction mid-sprint.

### Branch names

`sprint/NN-slug` for planned sprint work; `feat|fix|chore|docs/slug` for one-offs.
The prefix matches the commit `type` the branch will land as.

### Merge method: squash by default, merge-commit for integration → main

- **Squash-merge every ordinary PR.** The sprint (not the individual task commit) is the
  atomic unit: it is reviewed, archived, and attributed to a finding as one thing, and
  you would never want to revert half of it. Squashing also means **every commit on the
  integration branch is known-green** — WIP commits inside a branch are never CI'd on
  their own, only the PR head is. Keep the squash *message* set to the branch's commit
  messages, so per-task rationale and the `Sprint:`/`Finding:` trailers survive in the
  body and stay greppable.
- **Set the squash *title* source to the PR title, not "PR title or commit details."**
  With the default, a **single-commit PR silently uses the commit subject instead**,
  bypassing the CI-validated PR title entirely. The `pr-title` gate is only real once
  this is set.
- **Merge-commit (never squash) the long-lived integration branch into `main`.** Squashing
  that PR would collapse the entire multi-sprint effort into one commit and destroy the
  history. This is the one deliberate exception to the default.
- **Enable "automatically delete head branches."** A squash-merged branch is dead (its
  original commits are still "unmerged" against the new squashed commit and will
  conflict). Auto-deletion makes that structural rather than remembered — you cannot push
  to a branch that no longer exists.

## Issue + label taxonomy

- **No title prefixes.** `[BUG] thing is broken` is noise — the label already says `bug`,
  and the prefix wastes the most scannable characters in the UI. Issue titles are plain
  imperative statements, same as a commit subject.
- **Labels carry structure on three orthogonal axes**, not one flat list. A label picked
  from each axis answers a different question, and mashing them together (the common
  failure) makes filtering useless:
  - **type** — `bug`, `feature`, `chore`, `docs`: what kind of work.
  - **`area/*`** — `area/core`, `area/personas`, `area/tools`, `area/flows`, `area/ci`:
    *the same vocabulary as the commit scopes*, so an issue and the commit that closes it
    are filterable by the same word.
  - **`status/*`** — `status/blocked`, `status/needs-human`: where it is.
- **Machine-emitted labels stay namespaced under the emitting system**
  (`loop-engine/needs-human`). This is the load-bearing rule: a namespace makes "did a
  human or a robot put this here?" answerable at a glance, without a separate identity
  for the machine. Never let an automated writer apply an un-namespaced label.

## Definition of Done
A unit of work is done only when: formatting + lint + the full test suite pass; new validated boundaries have negative-input tests; dependencies are pinned and CVE-clean with the SBOM regenerated; no unjustified `# noqa`; and no secrets in any committed file. For managed repos the repo's own `sprints/GLOBAL_DEFINITION_OF_DONE.md` (if present) extends, never relaxes, this bar.
