"""Hermetic end-to-end proof of the bootstrap flow's full chain: real
`tools/scaffold` + real `tools/git_io` against a `tmp_path` git repo and a
local bare remote, with `repo_io` (create/clone/create_branch) faked. No
real GitHub create, clone, or network -- proves the skeleton actually lands
in the tree, `main` is really pushed, and `create_branch` fires with
`base="main"` after the push."""

import subprocess
from pathlib import Path

import pytest

from loop_engine.flows.bootstrap import BootstrapRequest, BootstrapStatus, run_bootstrap
from loop_engine.tools import git_io, scaffold
from loop_engine.tools.repo_io import RepoRef


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def empty_clone(tmp_path, monkeypatch):
    """A bare `remote.git` standing in for the real GitHub remote, and an
    empty `demo/` working tree on an *unborn* HEAD -- standing in for what
    `clone_repo` hands back right after `gh repo create` + `gh repo clone`
    of a brand-new, commit-less repo. Named `scratch` (not `main`) to mirror
    the real-world case where the cloner's `init.defaultBranch` may not be
    `main` -- `checkout_branch(tree, "main")` must still work on it."""
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "-b", "main", str(remote))

    working = tmp_path / "demo"
    working.mkdir()
    _git(working, "init", "-b", "scratch")
    _git(working, "config", "user.email", "t@t.test")
    _git(working, "config", "user.name", "T")
    _git(working, "remote", "add", "origin", str(remote))

    monkeypatch.chdir(tmp_path)
    return tmp_path


class _FakeRepoIO:
    """Fakes only the `gh`-shelling verbs; `clone_repo` hands back the
    already-prepared empty working tree instead of really cloning."""

    def __init__(self, dest: str) -> None:
        self._dest = dest
        self.repo = RepoRef(slug="glunk-works/demo", url="https://github.com/glunk-works/demo")
        self.create_repository_calls: list[tuple] = []
        self.create_branch_calls: list[tuple] = []
        self.create_ruleset_calls: list[tuple] = []

    def create_repository(self, name, *, org=None, private=True):
        self.create_repository_calls.append((name, org, private))
        return self.repo

    def clone_repo(self, slug, dest, *, depth=None):
        return self._dest

    def create_branch(self, owner, repo, branch, *, base=None):
        self.create_branch_calls.append((owner, repo, branch, base))
        return f"refs/heads/{branch}"

    def create_ruleset(self, owner, repo, *, branches, name="protect-integration-branches"):
        self.create_ruleset_calls.append((owner, repo, tuple(branches)))
        return 1


def _bare_remote_heads(remote: Path) -> str:
    return subprocess.run(
        ["git", "ls-remote", "--heads", str(remote)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_bootstrap_writes_skeleton_pushes_main_and_creates_develop_after_push(
    empty_clone,
) -> None:
    repo_io = _FakeRepoIO(dest="demo")
    request = BootstrapRequest(name="demo", clone_dest="demo")

    result = run_bootstrap(request, repo_io=repo_io, git_io=git_io, scaffold=scaffold)

    assert result.status == BootstrapStatus.CREATED
    assert result.repo == repo_io.repo
    assert result.default_branch == "main"
    assert result.integration_branch == "develop"
    assert result.ruleset_installed is True

    tree = empty_clone / "demo"
    for rel in (
        "pyproject.toml",
        "src/demo/__init__.py",
        "tests/test_smoke.py",
        "README.md",
        ".gitignore",
        "CLAUDE.md",
    ):
        assert (tree / rel).is_file(), f"missing {rel}"

    remote_heads = _bare_remote_heads(empty_clone / "remote.git")
    assert "refs/heads/main" in remote_heads

    assert repo_io.create_branch_calls == [("glunk-works", "demo", "develop", "main")]
    assert repo_io.create_ruleset_calls == [("glunk-works", "demo", ("main", "develop"))]


def test_no_open_pr_or_merge_verb_reachable_end_to_end() -> None:
    from loop_engine.tools import repo_io as real_repo_io

    assert not hasattr(real_repo_io, "merge_pull_request")
    assert not any("merge" in name.lower() for name in real_repo_io.__all__)
    assert "open_pr" not in {"create_repository", "clone_repo", "create_branch"}
