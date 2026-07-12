import subprocess
import tomllib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_workflow(filename: str) -> dict:
    path = REPO_ROOT / ".github" / "workflows" / filename
    return yaml.safe_load(path.read_text())


def _trigger_types(cfg: dict, event: str) -> list[str]:
    # yaml.safe_load parses the bare `on:` key as the boolean True (YAML 1.1
    # truthy) rather than the string "on" — cfg["on"] raises KeyError.
    triggers = cfg.get("on") or cfg[True]
    return triggers[event]["types"]


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


def test_no_job_in_ci_workflow_can_report_skipped() -> None:
    """BL-10: a job with a satisfied `needs:` chain and no `if:` cannot report
    `skipped`, and a skipped job reads as satisfied to everything downstream of
    it. A PR used to be able to reach an all-green checks page having never run
    lint or the test suite because a gate keyed on `pr-title` reported
    `skipped` on the wrong event. Pinning the absence — no `if:`, no `needs:`
    on `pr-title` — closes the whole class, not just today's wiring."""
    cfg = _load_workflow("ci.yml")
    for job_id, job in cfg["jobs"].items():
        assert "if" not in job, f"{job_id} carries an `if:` — it can now be skipped"
        needs = job.get("needs", [])
        needs_list = [needs] if isinstance(needs, str) else needs
        assert "pr-title" not in needs_list, f"{job_id} still needs pr-title"


def test_ci_workflow_pull_request_trigger_excludes_edited() -> None:
    """FD2: `edited` shares ci.yml's cancelling concurrency group with `opened`
    and `synchronize`, so a title/body edit mid-run cancels an in-flight (or
    already-green) run of the heavy chain. That path is closed only by never
    triggering the heavy chain on `edited` at all."""
    cfg = _load_workflow("ci.yml")
    assert "edited" not in _trigger_types(cfg, "pull_request")


def test_pr_title_workflow_defines_the_frozen_job_id() -> None:
    """FD5: branch protection matches required checks by check-run name, which
    is the job id, not the workflow file. If the job id here drifts from
    `pr-title`, the required check never arrives and every future PR hangs."""
    cfg = _load_workflow("pr-title.yml")
    assert "pr-title" in cfg["jobs"]


def test_pr_title_workflow_trigger_types_reopen_the_check() -> None:
    """Without `edited`, a bad title could only be cleared by a dummy push —
    the trap this workflow exists to fix. `synchronize` guarantees a
    check-run on every head SHA, which a required check depends on to ever
    resolve."""
    cfg = _load_workflow("pr-title.yml")
    types = _trigger_types(cfg, "pull_request")
    assert "edited" in types
    assert "synchronize" in types


def test_pr_title_job_gates_nothing() -> None:
    """This job is deliberately standalone: it must not gate, and must not be
    gated by, anything else — that coupling is what BL-10 was."""
    cfg = _load_workflow("pr-title.yml")
    assert "needs" not in cfg["jobs"]["pr-title"]


def test_claude_md_documents_the_human_abort_exit_code() -> None:
    """The CLI's exit codes are a contract a supervising script reads; a
    deliberate human abort must be documented and distinct from a crash (1)."""
    from loop_engine.cli import ABORTED_BY_HUMAN_EXIT_CODE

    text = (REPO_ROOT / "CLAUDE.md").read_text()
    assert f"{ABORTED_BY_HUMAN_EXIT_CODE} aborted by the human" in text
    assert ABORTED_BY_HUMAN_EXIT_CODE not in (0, 1, 2, 3)


def test_hitl_review_gate_exists_and_requires_the_architect_header() -> None:
    """The Architect review is enforced by CI, not just by prose in
    workflow.md. Sprint 27 Task 8 shipped a green PR whose R8 fix silently
    missed every fresh-run path precisely because the review that would have
    caught it was skipped and nothing noticed."""
    wf = REPO_ROOT / ".github" / "workflows" / "hitl-review.yml"
    assert wf.is_file(), "the HITL review gate workflow must exist"
    text = wf.read_text()

    # The header the review body must carry (Claude and the owner share one
    # GitHub identity; the header is what marks a review as the automated one).
    assert "**Opus/Architect HITL review (automated)**" in text
    # Scoped to code: docs/sprint-plan/.ai-cursor PRs need no architecture review.
    assert "^src/" in text
    # Must review THIS diff — a review of an earlier commit is not a review of
    # the code being merged.
    assert "commit_id" in text and "HEAD_SHA" in text
    # The review must run in a session that did not write the diff: a reviewer
    # holding the authoring context proofreads its own reasoning. CI cannot see a
    # session boundary, so the reviewer attests to it — which at least makes
    # self-review a knowing false statement rather than a silent default.
    assert "Fresh-session review: this session did not author the diff." in text
    # The failure guidance must not teach the anti-pattern it exists to prevent:
    # if it mentions /model opus at all, it must say that alone is not enough.
    flat = " ".join(text.split())
    assert "does NOT clear the context" in flat
    assert "/handoff" in flat
    # Without the review event the check could never turn green without a dummy
    # push — the same trap ci.yml's `edited` trigger exists to avoid.
    assert "pull_request_review" in text


def test_hitl_review_gate_is_not_inside_the_cancel_in_progress_ci_workflow() -> None:
    """`ci.yml` cancels in-progress runs on new events for the same ref. If the
    review gate lived there, posting a review would cancel an in-flight test
    run — so it is deliberately a separate workflow."""
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "cancel-in-progress: true" in ci
    assert "pull_request_review" not in ci
