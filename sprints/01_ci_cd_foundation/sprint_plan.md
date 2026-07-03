### FILEPATH: /sprints/01_ci_cd_foundation/sprint_plan.md

**Sprint Goal:** Establish the repository scaffold, dependency/environment management, and automated security tooling gates before any application code is written.

**Dependencies:** None

**Security Considerations:** This sprint establishes the enforcement mechanisms for supply-chain security — secrets scanning, dependency vulnerability scanning, SBOM generation, and security-focused linting. The threat surface is a misconfigured CI gate that allows secrets or vulnerable dependencies to merge silently. Every gate must fail the build (non-zero exit) on violation, not just report to a log file.

**Risks & Blockers:** Access to create and configure `glunk-works/loop-engine` on GitHub is required for Dependabot and CI configuration; this is an external dependency outside this sprint's direct control.

**Tasks:**

- **Task 1: Repository Scaffold and Package Layout**
  - **Description:** Create the directory tree `src/loop_engine/{core,personas,loops,tools}/` and `tests/{core,personas,loops,tools}/` with an `__init__.py` in every package directory. Create `pyproject.toml` declaring the project name `loop-engine`, Python requirement `>=3.12`, and `hatchling` as the build backend.
  - **Target Files:** `pyproject.toml`, `src/loop_engine/__init__.py`, `src/loop_engine/core/__init__.py`, `src/loop_engine/personas/__init__.py`, `src/loop_engine/loops/__init__.py`, `src/loop_engine/tools/__init__.py`, `tests/__init__.py`, `tests/core/__init__.py`, `tests/personas/__init__.py`, `tests/loops/__init__.py`, `tests/tools/__init__.py`
  - **Acceptance Criteria:** `hatch run python -c "import loop_engine"` exits zero. `hatch env show` lists the default environment without error.

- **Task 2: Hatch Script Configuration**
  - **Description:** Add a `[tool.hatch.envs.default.scripts]` section to `pyproject.toml` defining `test = "pytest {args}"`, `lint = "ruff check ."`, and `format = "ruff format ."`. Add `pytest` and `ruff` as pinned dev dependencies under `[tool.hatch.envs.default]`.
  - **Target Files:** `pyproject.toml`
  - **Acceptance Criteria:** `hatch run test`, `hatch run lint`, and `hatch run format` each execute without a "script not found" error.

- **Task 3: Ruff Security and Style Configuration**
  - **Description:** Add `[tool.ruff]` and `[tool.ruff.lint]` sections to `pyproject.toml` enabling rule sets `E`, `F`, `I`, `B` (bugbear), and `S` (bandit-equivalent security rules). Set `line-length = 100`.
  - **Target Files:** `pyproject.toml`
  - **Acceptance Criteria:** `hatch run ruff check .` run against the empty scaffold exits zero.

- **Task 4: Gitleaks Secrets Scanning Configuration**
  - **Description:** Add a `.gitleaks.toml` configuration file at the repo root using the default gitleaks ruleset with no custom allowlist entries.
  - **Target Files:** `.gitleaks.toml`
  - **Acceptance Criteria:** `gitleaks detect --source . --config .gitleaks.toml` run against the repository exits zero with no findings.

- **Task 5: State Directory Exclusion**
  - **Description:** Create `.gitignore` at the repo root excluding `state/`, `__pycache__/`, `*.pyc`, `.venv/`, and `dist/`.
  - **Target Files:** `.gitignore`
  - **Acceptance Criteria:** `git check-ignore state/` exits zero once a `state/` directory exists locally.

- **Task 6: CI Pipeline Definition**
  - **Description:** Create `.github/workflows/ci.yml` defining, in order, jobs `lint` (`hatch run ruff check .`), `format-check` (`hatch run ruff format --check .`), `test` (`hatch run test`), `secrets-scan` (gitleaks via `gitleaks/gitleaks-action`), and `sbom` (generate `sbom.json` and upload it as a workflow artifact). Each job fails the workflow run on non-zero exit.
  - **Target Files:** `.github/workflows/ci.yml`
  - **Acceptance Criteria:** A pull request opened against the repository triggers all five jobs and the workflow reports a single aggregate status check.

- **Task 7 (Security): Dependabot and SBOM Automation**
  - **Description:** Create `.github/dependabot.yml` configuring a `pip` package-ecosystem update check on a daily schedule for directory `/`. Add `cyclonedx-bom` as a pinned dev dependency and a hatch script `sbom = "cyclonedx-py environment -o sbom.json"`.
  - **Target Files:** `.github/dependabot.yml`, `pyproject.toml`
  - **Acceptance Criteria:** `hatch run sbom` produces a valid CycloneDX-format `sbom.json` at the repo root. `.github/dependabot.yml` validates against GitHub's Dependabot v2 schema.

---
