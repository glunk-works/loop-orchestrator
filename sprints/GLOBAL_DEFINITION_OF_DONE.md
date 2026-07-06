# GLOBAL DEFINITION OF DONE

Every sprint in this directory is complete only when all of the following gates pass, in addition to that sprint's own Acceptance Criteria:

- **Tests:** `hatch run test` exits zero. Every new Pydantic-validated I/O boundary introduced by the sprint has at least one test proving invalid input is rejected.
- **Linting:** `hatch run ruff check .` exits zero, including the `S` (bandit-equivalent security) and `B` (bugbear) rule sets. No `# noqa` suppression is added without an inline justification comment on the same line.
- **Formatting:** `hatch run ruff format --check .` exits zero.
- **No hardcoded secrets:** no API key, token, or credential literal appears in any source file, config file, test fixture, or `state/` snapshot. `gitleaks detect --source . --config .gitleaks.toml` reports zero findings. The LLM API key is retrieved exclusively via `keyring` from `src/loop_engine/tools/llm/client.py` — no other module imports `keyring` — with one documented exception: a double-gated env var pair (`LOOP_ENGINE_ALLOW_ENV_CREDENTIAL=1` and `LOOP_ENGINE_CI_API_KEY`, both required together) scoped to CI/automation contexts where mounting an encrypted keyring file is impractical. See `docs/architecture_definition.md` §4.
- **Dependency vulnerability scan:** `hatch run audit` (pip-audit against the OSV/PyPI advisory databases) exits zero; any dependency added or upgraded in the sprint is pinned to a version with no known critical or high CVE at merge time; the repository's Dependabot alerts show zero open critical/high alerts after merge.
- **SBOM:** `sbom.json` (CycloneDX format) is regenerated via `hatch run sbom` and committed whenever `pyproject.toml` dependencies change.
- **CI pipeline status:** `.github/workflows/ci.yml` runs `lint`, `format-check`, `test`, `secrets-scan`, `dependency-audit`, and `sbom` jobs, and all report green on the sprint's final commit.
- **Module boundary enforcement:** `src/loop_engine/core/` imports no concrete persona module — only `src/loop_engine/personas/base.py`. `src/loop_engine/tools/state_io/` is the only module that writes to `state/`, `docs/`, or `sprints/`.
- **State schema integrity:** any change touching `State` keeps `schema_version` accurate and keeps the model's `extra="forbid"` configuration intact.
