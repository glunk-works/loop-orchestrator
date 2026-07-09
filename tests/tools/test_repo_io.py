from unittest.mock import patch

import pytest

from loop_engine.tools.repo_io import (
    PullRef,
    RepoRef,
    clone_repo,
    create_branch,
    create_repository,
    open_pr,
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
