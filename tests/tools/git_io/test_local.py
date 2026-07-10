"""Real git repo in tmp_path so the `tools/git_io` local-git subprocess
surface (fourth sanctioned surface) is exercised end to end against a local
bare remote — no network, no `gh`."""

import subprocess
from pathlib import Path

import pytest

from loop_engine.tools.git_io import (
    GitIOError,
    checkout_branch,
    commit_all,
    has_changes,
    push_branch,
)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A tmp working clone (`repo/`) with a local bare remote (`remote.git`),
    CWD pinned to `tmp_path` so `repo` is a valid relative tree argument."""
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "-b", "main", str(remote))

    working = tmp_path / "repo"
    working.mkdir()
    _git(working, "init", "-b", "main")
    _git(working, "config", "user.email", "t@t.test")
    _git(working, "config", "user.name", "T")
    (working / "seed.txt").write_text("seed")
    _git(working, "add", "seed.txt")
    _git(working, "commit", "-m", "seed")
    _git(working, "remote", "add", "origin", str(remote))
    _git(working, "push", "origin", "main")

    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_checkout_branch_creates_and_switches(repo):
    checkout_branch("repo", "feature")
    current = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo / "repo",
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert current == "feature"


def test_commit_all_commits_working_tree(repo):
    checkout_branch("repo", "feature")
    (repo / "repo" / "new.txt").write_text("hello")
    commit_all("repo", "add new.txt")
    log = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=repo / "repo",
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "add new.txt" in log
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo / "repo",
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status.strip() == ""


def test_push_branch_lands_branch_on_bare_remote(repo):
    checkout_branch("repo", "feature")
    (repo / "repo" / "new.txt").write_text("hello")
    commit_all("repo", "add new.txt")
    push_branch("repo", "feature")

    listed = subprocess.run(
        ["git", "branch", "-r"],
        cwd=repo / "repo",
        capture_output=True,
        text=True,
        check=True,
    )
    remote_refs = subprocess.run(
        ["git", "ls-remote", "--heads", str(repo / "remote.git")],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "refs/heads/feature" in remote_refs
    assert listed.returncode == 0


def test_has_changes_reflects_working_tree_state(repo):
    checkout_branch("repo", "feature")
    assert has_changes("repo") is False
    (repo / "repo" / "new.txt").write_text("hello")
    assert has_changes("repo") is True
    commit_all("repo", "add new.txt")
    assert has_changes("repo") is False


def test_non_zero_git_op_raises_git_io_error_with_stderr(repo):
    with pytest.raises(GitIOError, match="checkout"):
        checkout_branch("repo", "main")  # already on main; -b main fails


@pytest.mark.parametrize(
    "bad_tree",
    ["/abs/path", "repo/../escape", "../outside"],
)
def test_invalid_tree_argument_raises_value_error(repo, bad_tree):
    with pytest.raises(ValueError):
        checkout_branch(bad_tree, "feature")


def test_git_io_imports_no_keyring():
    import ast
    from pathlib import Path as P

    module_path = P(__file__).resolve().parent.parent.parent.parent / (
        "src/loop_engine/tools/git_io/local.py"
    )
    tree = ast.parse(module_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "keyring" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "keyring"


def test_git_io_makes_no_direct_file_write_call():
    import ast
    from pathlib import Path as P

    module_path = P(__file__).resolve().parent.parent.parent.parent / (
        "src/loop_engine/tools/git_io/local.py"
    )
    tree = ast.parse(module_path.read_text())
    disallowed = {"open", "write_text", "write_bytes"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            assert func.id not in disallowed
        if isinstance(func, ast.Attribute):
            assert func.attr not in disallowed
