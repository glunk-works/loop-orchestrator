import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_declares_hatch_scripts() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    scripts = data["tool"]["hatch"]["envs"]["default"]["scripts"]
    assert scripts["test"] == "pytest {args}"
    assert scripts["lint"] == "ruff check ."
    assert scripts["format"] == "ruff format ."
    assert scripts["sbom"] == "cyclonedx-py environment -o sbom.json"
    assert scripts["audit"].startswith("pip-audit --skip-editable")


def test_pyproject_declares_ruff_security_rules() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    assert data["tool"]["ruff"]["line-length"] == 100
    selected = set(data["tool"]["ruff"]["lint"]["select"])
    assert {"E", "F", "I", "B", "S"} <= selected


def test_gitleaks_config_extends_default_ruleset_only() -> None:
    data = tomllib.loads((REPO_ROOT / ".gitleaks.toml").read_text())
    assert data == {"extend": {"useDefault": True}}


def test_state_directory_is_gitignored() -> None:
    (REPO_ROOT / "state").mkdir(exist_ok=True)
    result = subprocess.run(  # noqa: S603 -- fixed argv, no untrusted input
        ["git", "check-ignore", "state/"],  # noqa: S607 -- git resolved via PATH by design
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_dependabot_config_defines_daily_pip_updates() -> None:
    text = (REPO_ROOT / ".github" / "dependabot.yml").read_text()
    assert 'package-ecosystem: "pip"' in text
    assert 'directory: "/"' in text
    assert 'interval: "daily"' in text


def test_ci_workflow_defines_required_jobs_in_order() -> None:
    text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    jobs = ["lint:", "format-check:", "test:", "secrets-scan:", "dependency-audit:", "sbom:"]
    positions = [text.index(job) for job in jobs]
    assert positions == sorted(positions)
    assert "hatch run audit" in text


def test_lint_job_gates_on_pr_title_to_fail_fast() -> None:
    """A failing `pr-title` must stop the heavy chain instead of racing it in
    parallel — `lint` (and everything chained after it via `needs:`) has to
    wait on `pr-title` and only proceed on success or (on `push`, where
    `pr-title` doesn't run at all) skip."""
    text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    lint_section = text[text.index("\n  lint:") : text.index("\n  format-check:")]
    assert "needs: pr-title" in lint_section
    assert "needs.pr-title.result == 'success'" in lint_section
    assert "needs.pr-title.result == 'skipped'" in lint_section
