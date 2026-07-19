<!--
TITLE: `type(scope): imperative subject` — lower-case, no trailing period, <= 72 chars.
Types: feat|fix|docs|test|refactor|perf|chore|ci|revert. `!` = breaking (State schema).
The merge is a squash, so this title BECOMES the commit subject. CI enforces it.
-->

## Summary

<!-- What does this PR do and why? -->

## Related issue

<!-- Closes #123 -->

## Test plan

<!-- How did you verify this works? -->

## Definition of Done checklist

- [ ] `hatch run test` passes, no skipped tests
- [ ] Every new/modified Pydantic-validated I/O path has a test proving invalid input is rejected
- [ ] `hatch run ruff check .` is clean (incl. `S`/`B` rule sets); any `# noqa` has a one-line justification
- [ ] `hatch run ruff format --check .` is clean
- [ ] No secret/credential value appears in code, fixtures, logs, or committed JSON — `gitleaks detect --source . --config .gitleaks.toml` is clean
- [ ] The LLM API key is retrieved exclusively via `keyring` from `src/loop_orchestrator/tools/llm/client.py` — no other module imports `keyring`
- [ ] Any new/upgraded dependency is pinned to a version with no known critical/high CVE
- [ ] `sbom.json` regenerated via `hatch run sbom` and committed if dependencies changed
- [ ] `src/loop_orchestrator/core/` imports no concrete persona module (only `personas/base.py`); `tools/state_io/` is the only writer to `state/`, `docs/`, `sprints/`
- [ ] Any change touching `State` keeps `schema_version` accurate and `extra="forbid"` intact
- [ ] CI is green on this PR

## Deviations

<!-- Anything implemented differently than planned, with justification. "None" if none. -->
