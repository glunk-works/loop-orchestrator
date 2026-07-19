"""Hermetic end-to-end proof of the maintenance flow's full chain: real
`git_io` against a `tmp_path` git repo + a local bare remote, with `repo_io`
(clone/open_pr) and the loop run faked. No real GitHub clone, no real loop,
no real network -- proves the green path actually pushes and opens a PR,
and the red path touches neither."""

import subprocess
from pathlib import Path

import pytest

from loop_orchestrator.core.state import RunStatus, State
from loop_orchestrator.flows.maintenance import (
    MaintenanceRequest,
    MaintenanceStatus,
    run_maintenance,
)
from loop_orchestrator.tools import git_io
from loop_orchestrator.tools.repo_io import PullRef


def _completed_state() -> State:
    return State(
        schema_version=2, run_id="r1", status=RunStatus.COMPLETED, stage_history=[], artifacts={}
    )


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def target_repo(tmp_path, monkeypatch):
    """A `remote.git` bare repo standing in for the real GitHub remote, and
    a `repo/` working tree standing in for `clone_repo`'s output -- already
    remoted to `origin` -- so real `git_io` pushes land somewhere real."""
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


class _FakeRepoIO:
    """Fakes only the `gh`-shelling verbs; `clone_repo` hands back the
    already-prepared working tree instead of really cloning."""

    def __init__(self) -> None:
        self.open_pr_calls: list[dict] = []

    def clone_repo(self, slug, dest, *, depth=None):
        return dest

    def open_pr(self, owner, repo, *, head, base, title, body):
        self.open_pr_calls.append(
            {"owner": owner, "repo": repo, "head": head, "base": base, "title": title, "body": body}
        )
        return PullRef(number=42, url=f"https://github.com/{owner}/{repo}/pull/42")


def _run_step(human_input, tree, *, budget_usd, loop_name):
    (Path(tree) / "change.txt").write_text("a change from the inner run")
    return _completed_state()


def _run_step_no_change(human_input, tree, *, budget_usd, loop_name):
    """A completed inner run that writes nothing into the clone."""
    return _completed_state()


def _bare_remote_heads(remote: Path) -> str:
    return subprocess.run(
        ["git", "ls-remote", "--heads", str(remote)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_green_gate_pushes_to_bare_remote_and_opens_pr_against_develop(target_repo) -> None:
    repo_io = _FakeRepoIO()
    request = MaintenanceRequest(
        repo_full_name="acme/widgets",
        human_input="Apply routine maintenance",
        branch="maint/routine",
        clone_dest="repo",
    )

    result = run_maintenance(
        request,
        run_step=_run_step,
        repo_io=repo_io,
        git_io=git_io,
        run_tests=lambda tree: (0, "1 passed"),
    )

    assert result.status == MaintenanceStatus.OPENED_PR
    assert result.pull is not None
    assert result.pull.number == 42

    remote_heads = _bare_remote_heads(target_repo / "remote.git")
    assert "refs/heads/maint/routine" in remote_heads

    assert len(repo_io.open_pr_calls) == 1
    call = repo_io.open_pr_calls[0]
    assert call["head"] == "maint/routine"
    assert call["base"] == "develop"
    assert call["owner"] == "acme"
    assert call["repo"] == "widgets"


def test_red_gate_leaves_remote_untouched_and_opens_no_pr(target_repo) -> None:
    repo_io = _FakeRepoIO()
    request = MaintenanceRequest(
        repo_full_name="acme/widgets",
        human_input="Apply routine maintenance",
        branch="maint/routine-red",
        clone_dest="repo",
    )

    result = run_maintenance(
        request,
        run_step=_run_step,
        repo_io=repo_io,
        git_io=git_io,
        run_tests=lambda tree: (1, "1 failed"),
    )

    assert result.status == MaintenanceStatus.GATE_FAILED
    assert result.pull is None

    remote_heads = _bare_remote_heads(target_repo / "remote.git")
    assert "refs/heads/maint/routine-red" not in remote_heads
    assert not repo_io.open_pr_calls


def test_completed_run_with_no_diff_pushes_nothing_and_does_not_crash(target_repo) -> None:
    # Real git_io against a real tree: a completed run that changed nothing
    # must return NO_CHANGES without ever reaching `commit_all` (which would
    # raise GitIOError on an empty index) and without pushing or opening a PR.
    repo_io = _FakeRepoIO()
    request = MaintenanceRequest(
        repo_full_name="acme/widgets",
        human_input="Apply routine maintenance",
        branch="maint/noop",
        clone_dest="repo",
    )

    result = run_maintenance(
        request,
        run_step=_run_step_no_change,
        repo_io=repo_io,
        git_io=git_io,
        run_tests=lambda tree: (0, "1 passed"),
    )

    assert result.status == MaintenanceStatus.NO_CHANGES
    assert result.pull is None
    remote_heads = _bare_remote_heads(target_repo / "remote.git")
    assert "refs/heads/maint/noop" not in remote_heads
    assert not repo_io.open_pr_calls


def test_open_pr_is_the_terminal_github_call_no_merge_verb_reachable() -> None:
    """`repo_io` exposes no merge verb at all -- auto-merge can never be
    reached through this flow, regardless of gate outcome."""
    from loop_orchestrator.tools import repo_io as real_repo_io

    assert not hasattr(real_repo_io, "merge_pull_request")
    assert not any("merge" in name.lower() for name in real_repo_io.__all__)
