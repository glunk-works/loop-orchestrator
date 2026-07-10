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

## Definition of Done
A unit of work is done only when: formatting + lint + the full test suite pass; new validated boundaries have negative-input tests; dependencies are pinned and CVE-clean with the SBOM regenerated; no unjustified `# noqa`; and no secrets in any committed file. For managed repos the repo's own `sprints/GLOBAL_DEFINITION_OF_DONE.md` (if present) extends, never relaxes, this bar.
