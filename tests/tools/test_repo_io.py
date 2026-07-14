import json
import subprocess
from unittest.mock import patch

import pytest

from loop_engine.tools.repo_io import (
    PullRef,
    RepoNotResolvableError,
    RepoRef,
    clone_repo,
    create_branch,
    create_repository,
    create_ruleset,
    open_pr,
    resolve_repo_slug,
)


def test_create_repository_builds_argv_and_parses_url() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = "https://github.com/acme/widget\n"
        ref = create_repository("widget", org="acme", private=True)

    assert ref == RepoRef(slug="acme/widget", url="https://github.com/acme/widget")
    run_gh.assert_called_once_with(["repo", "create", "acme/widget", "--private"])


def test_create_repository_defaults_to_public_flag_omitted_org() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = "https://github.com/me/widget\n"
        ref = create_repository("widget", private=False)

    assert ref.slug == "me/widget"
    run_gh.assert_called_once_with(["repo", "create", "widget", "--public"])


def test_clone_repo_builds_argv_and_returns_dest() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = ""
        result = clone_repo("acme/widget", "workspaces/widget")

    assert result == "workspaces/widget"
    run_gh.assert_called_once_with(["repo", "clone", "acme/widget", "workspaces/widget"])


def test_clone_repo_with_depth_appends_git_flag() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = ""
        clone_repo("acme/widget", "workspaces/widget", depth=1)

    run_gh.assert_called_once_with(
        ["repo", "clone", "acme/widget", "workspaces/widget", "--", "--depth", "1"]
    )


@pytest.mark.parametrize("dest", ["/etc/passwd", "../escape", "a/../../b"])
def test_clone_repo_rejects_traversal_dest_before_any_gh_call(dest) -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        with pytest.raises(ValueError, match="Invalid clone destination"):
            clone_repo("acme/widget", dest)
    run_gh.assert_not_called()


def test_clone_repo_rejects_symlink_escape(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / "outside_target"
    outside.mkdir(exist_ok=True)
    (tmp_path / "escape_link").symlink_to(outside)

    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        with pytest.raises(ValueError, match="escapes the run tree"):
            clone_repo("acme/widget", "escape_link")
    run_gh.assert_not_called()


def test_clone_repo_rejects_symlinked_parent_with_nonexistent_target(tmp_path, monkeypatch) -> None:
    """The realistic clone case: the target itself does not exist yet, but a
    *parent* component is a symlink escaping the run tree. `Path.resolve()`
    resolves the symlinked prefix even for a non-existent tail, so this must be
    rejected — the validator does not gate the check on `path.exists()`."""
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / "outside_target"
    outside.mkdir(exist_ok=True)
    (tmp_path / "escape_link").symlink_to(outside)

    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        with pytest.raises(ValueError, match="escapes the run tree"):
            clone_repo("acme/widget", "escape_link/repo")
    run_gh.assert_not_called()


def test_create_branch_with_explicit_base_resolves_sha_then_creates_ref() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.side_effect = ["abc123\n", ""]
        ref = create_branch("acme", "widget", "feature-x", base="develop")

    assert ref == "refs/heads/feature-x"
    assert run_gh.call_count == 2
    first_args = run_gh.call_args_list[0].args[0]
    assert first_args == [
        "api",
        "repos/acme/widget/git/ref/heads/develop",
        "--jq",
        ".object.sha",
    ]
    second_args = run_gh.call_args_list[1].args[0]
    assert second_args == [
        "api",
        "--method",
        "POST",
        "repos/acme/widget/git/refs",
        "-f",
        "ref=refs/heads/feature-x",
        "-f",
        "sha=abc123",
    ]


def test_create_branch_without_base_resolves_default_branch_first() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.side_effect = ["main\n", "def456\n", ""]
        ref = create_branch("acme", "widget", "feature-y")

    assert ref == "refs/heads/feature-y"
    assert run_gh.call_count == 3
    assert run_gh.call_args_list[0].args[0] == [
        "api",
        "repos/acme/widget",
        "--jq",
        ".default_branch",
    ]
    assert run_gh.call_args_list[1].args[0] == [
        "api",
        "repos/acme/widget/git/ref/heads/main",
        "--jq",
        ".object.sha",
    ]


def test_open_pr_builds_argv_and_parses_number() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = "https://github.com/acme/widget/pull/42\n"
        ref = open_pr(
            "acme", "widget", head="feature-x", base="develop", title="Add x", body="does x"
        )

    assert ref == PullRef(number=42, url="https://github.com/acme/widget/pull/42")
    run_gh.assert_called_once_with(
        [
            "pr",
            "create",
            "--repo",
            "acme/widget",
            "--head",
            "feature-x",
            "--base",
            "develop",
            "--title",
            "Add x",
            "--body",
            "does x",
        ]
    )


def test_create_ruleset_posts_to_the_rulesets_endpoint_via_stdin_input() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = json.dumps({"id": 18847726})
        ruleset_id = create_ruleset("glunk-works", "widget", branches=["main", "develop"])

    assert ruleset_id == 18847726
    args, kwargs = run_gh.call_args
    assert args[0] == [
        "api",
        "--method",
        "POST",
        "repos/glunk-works/widget/rulesets",
        "--input",
        "-",
    ]
    body = json.loads(kwargs["input_data"])
    assert body["target"] == "branch"
    assert body["enforcement"] == "active"
    assert body["bypass_actors"] == []


def test_create_ruleset_targets_both_main_and_develop() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = json.dumps({"id": 1})
        create_ruleset("glunk-works", "widget", branches=["main", "develop"])

    body = json.loads(run_gh.call_args.kwargs["input_data"])
    assert body["conditions"]["ref_name"]["include"] == [
        "refs/heads/main",
        "refs/heads/develop",
    ]


def test_create_ruleset_declares_exactly_three_rule_types() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = json.dumps({"id": 1})
        create_ruleset("glunk-works", "widget", branches=["main", "develop"])

    body = json.loads(run_gh.call_args.kwargs["input_data"])
    rule_types = {rule["type"] for rule in body["rules"]}
    assert rule_types == {"deletion", "non_fast_forward", "pull_request"}


def test_create_ruleset_declares_no_required_status_checks() -> None:
    """FD4's trap, named explicitly: a generated repo ships no CI, so a
    required status check in the shipped ruleset would be a permanent merge
    deadlock. This must never be reintroduced, even incidentally."""
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = json.dumps({"id": 1})
        create_ruleset("glunk-works", "widget", branches=["main", "develop"])

    body = json.loads(run_gh.call_args.kwargs["input_data"])
    rule_types = {rule["type"] for rule in body["rules"]}
    assert "required_status_checks" not in rule_types


def test_resolve_repo_slug_shells_gh_repo_view() -> None:
    """Repo introspection lives here, not in `issue_io` — but its caller is the
    issue filer, which needs an explicit destination instead of `gh`'s implicit
    CWD resolution (finding R8)."""
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = "acme/repo\n"
        slug = resolve_repo_slug()

    run_gh.assert_called_once_with(
        ["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd=None
    )
    assert slug == "acme/repo"


def test_resolve_repo_slug_resolves_against_the_given_cwd() -> None:
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.return_value = "acme/other\n"
        resolve_repo_slug("/orchestrator/checkout")

    assert run_gh.call_args.kwargs["cwd"] == "/orchestrator/checkout"


def test_resolve_repo_slug_raises_a_typed_error_when_gh_fails() -> None:
    """F4: a caller (`default_issue_filer`) needs to catch this without
    itself importing `subprocess` -- `repo_io` stays the sole owner of that
    surface, so a raw `CalledProcessError` must not cross this module's
    boundary."""
    with patch("loop_engine.tools.repo_io.github._run_gh") as run_gh:
        run_gh.side_effect = subprocess.CalledProcessError(
            1, ["gh", "repo", "view"], stderr="not a git repository"
        )
        with pytest.raises(RepoNotResolvableError):
            resolve_repo_slug("/not/a/repo")
