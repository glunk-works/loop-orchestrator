import re
import subprocess
import tomllib
from pathlib import Path

import yaml

_COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")

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


def test_dependabot_config_defines_pip_and_github_actions_updates() -> None:
    """Structural, not substring: a config that dropped either ecosystem must
    fail this test. Without the github-actions entry, Task 1's SHA pins freeze
    at their current commits and can never receive a security patch — trading
    a loud staleness risk (a Dependabot PR) for a silent one (a frozen CVE)."""
    data = yaml.safe_load((REPO_ROOT / ".github" / "dependabot.yml").read_text())
    updates = {entry["package-ecosystem"]: entry for entry in data["updates"]}
    assert set(updates) == {"pip", "github-actions"}
    assert updates["pip"]["directory"] == "/"
    assert updates["pip"]["schedule"]["interval"] == "daily"
    assert updates["github-actions"]["directory"] == "/"
    assert updates["github-actions"]["schedule"]["interval"] == "weekly"


def _pr_title_pattern() -> re.Pattern[str]:
    """The Conventional Commits regex `pr-title.yml` actually enforces, read from
    the workflow rather than restated here — a copy would let the two drift, which
    is the whole failure this guards."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "pr-title.yml").read_text()
    match = re.search(r"pattern='(?P<pattern>[^']+)'", workflow)
    assert match is not None, "pr-title.yml no longer declares a `pattern='...'`"
    return re.compile(match.group("pattern"))


def test_dependabot_titles_would_satisfy_the_required_pr_title_check() -> None:
    """`pr-title` is a REQUIRED check, and Dependabot's default subject
    ("Bump X from A to B" — capital B, no type) does not match its Conventional
    Commits regex. So without a `commit-message.prefix`, every Dependabot PR is
    born failing a required check and can never merge: the update mechanism runs,
    opens PRs, and none of them can land. That is not hypothetical — it is how
    #50-53 sat blocked, and it is BL-14's shape (a control present and inert).

    Asserting the prefix keys exist would be too weak: it would pass on a prefix
    like `build`, which is a perfectly ordinary Conventional Commits type but is
    NOT in this repo's allowed set, so the title would still be rejected. So this
    reconstructs the subject Dependabot will actually emit and runs it through
    pr-title.yml's own regex."""
    data = yaml.safe_load((REPO_ROOT / ".github" / "dependabot.yml").read_text())
    updates = {entry["package-ecosystem"]: entry for entry in data["updates"]}
    pattern = _pr_title_pattern()

    for ecosystem, entry in updates.items():
        commit_message = entry.get("commit-message")
        assert commit_message is not None, (
            f"{ecosystem}: no commit-message.prefix, so Dependabot emits "
            f"'Bump X from A to B', which fails the required pr-title check"
        )
        # `include: "scope"` is what supplies the "(deps)" / "(deps-dev)" scope.
        assert commit_message.get("include") == "scope"

        # The subject Dependabot generates: "<prefix>(<scope>): bump X from A to B".
        # The lower-case "bump" is Dependabot's own behaviour once a prefix is set.
        for prefix_key, scope in (
            ("prefix", "deps"),
            ("prefix-development", "deps-dev"),
        ):
            prefix = commit_message.get(prefix_key)
            if prefix is None:
                continue  # prefix-development is optional (github-actions has no dev deps)
            title = f"{prefix}({scope}): bump some-dependency from 1.2.3 to 4.5.6"
            assert pattern.match(title), (
                f"{ecosystem}: Dependabot would emit {title!r}, which pr-title.yml rejects"
            )

    # The negative: the default (prefix-less) subject must genuinely fail, or this
    # test proves nothing about why the prefix is needed.
    assert not pattern.match("Bump actions/checkout from 4.3.1 to 7.0.0")


def test_all_workflow_actions_are_pinned_to_commit_shas() -> None:
    """A tag is a mutable pointer: whoever controls the upstream repo can
    repoint it at arbitrary code that then runs in this repo's CI. Walks every
    workflow file (not just ci.yml) and every `uses:` (job- and step-level) so
    a newly added workflow with a floating tag fails too, not just today's
    four pinned actions."""
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    for path in sorted(workflows_dir.glob("*.yml")):
        cfg = _load_workflow(path.name)
        for job_id, job in cfg["jobs"].items():
            uses_values = [job["uses"]] if "uses" in job else []
            uses_values += [step["uses"] for step in job.get("steps", []) if "uses" in step]
            for uses in uses_values:
                ref = uses.split("@", 1)[1]
                assert _COMMIT_SHA.match(ref), f"{path.name}:{job_id} uses floating ref {uses!r}"


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
    """FD5: branch protection matches required checks by check-run name, not by
    workflow file. That name is `jobs.<id>.name` when present and falls back to
    the job id only when it is absent — so a `name:` override renames the check
    run just as surely as renaming the job does. Either drift and the required
    check never arrives, hanging every future PR on a check that cannot resolve."""
    cfg = _load_workflow("pr-title.yml")
    assert "pr-title" in cfg["jobs"]
    assert "name" not in cfg["jobs"]["pr-title"]


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


def test_hitl_review_src_detection_does_not_pipe_into_grep_q() -> None:
    """The src/-detection must not pipe a paginating `gh` into `grep -q`.

    `grep -q` exits at its first match, closing the pipe; a `gh --paginate` with
    pages still to write then dies of SIGPIPE (141), and under the step's
    `pipefail` that 141 becomes the pipeline's exit status. The `if !` then reads
    the failure as "no src/ changes" and the gate exempts itself — green, with no
    review. It only triggers once the file list is long enough that gh is still
    writing when grep quits, so the gate silently weakens as the diff grows, and
    is least trustworthy on the largest PRs. Found on PR #58 (the migration
    merge, 197 files): the gate reported "No src/ changes" over 66 changed src/
    files. Capture into a variable, then match — no pipe, no SIGPIPE.
    """
    text = (REPO_ROOT / ".github" / "workflows" / "hitl-review.yml").read_text()
    flat = " ".join(text.split())
    assert "| grep -q" not in flat, (
        "hitl-review.yml pipes into `grep -q`; a paginating producer upstream of "
        "it dies of SIGPIPE and `pipefail` turns that into a silent exemption"
    )
    # The shape that replaced it: capture first, match second.
    assert 'changed=$(gh api "repos/$REPO/pulls/$PR/files"' in text
    assert "grep -q '^src/' <<<\"$changed\"" in text
