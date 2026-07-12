"""Phase 3a worktree isolation. Uses a real git repo in tmp_path so the
`git worktree` subprocess surface is exercised end to end."""

import subprocess
from pathlib import Path

import pytest

from loop_engine.tools.state_io import writer as state_writer
from loop_engine.tools.worktree.manager import (
    WorktreeError,
    branch_name,
    cleanup,
    create,
    prune_all,
    use_worktree_isolation,
    worktree_path,
    worktree_run,
)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A tmp git repo with one commit, made the CWD, isolation flag on."""
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t.test")
    _git(tmp_path, "config", "user.name", "T")
    (tmp_path / "seed.txt").write_text("seed")
    _git(tmp_path, "add", "seed.txt")
    _git(tmp_path, "commit", "-m", "seed")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "worktree")
    # state_root is a module global; ensure a clean baseline per test.
    state_writer.set_state_root(None)
    return tmp_path


def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("LOOP_ENGINE_ISOLATION", raising=False)
    assert use_worktree_isolation() is False


def test_create_makes_worktree_under_root_on_branch(repo):
    path = create("run001")
    assert path == worktree_path("run001")
    assert path.parent == (repo / ".worktrees").resolve()
    assert path.is_dir()
    assert (path / "seed.txt").is_file()  # checked out from HEAD
    listed = subprocess.run(
        ["git", "worktree", "list"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    assert branch_name("run001") in listed


def test_create_is_idempotent(repo):
    first = create("run001")
    second = create("run001")
    assert first == second


def test_worktree_root_env_override(repo, monkeypatch):
    monkeypatch.setenv("LOOP_ENGINE_WORKTREE_ROOT", str(repo / "custom_wt"))
    path = create("run002")
    assert path.parent == (repo / "custom_wt").resolve()


def test_worktree_run_chdirs_in_and_restores(repo):
    origin = Path.cwd()
    with worktree_run("run003") as wt:
        assert Path.cwd() == wt.resolve()
        assert wt != origin
    assert Path.cwd() == origin


def test_worktree_run_restores_cwd_on_exception(repo):
    origin = Path.cwd()
    with pytest.raises(RuntimeError):
        with worktree_run("run004"):
            assert Path.cwd() != origin
            raise RuntimeError("boom")
    assert Path.cwd() == origin


def test_worktree_run_passthrough_when_flag_off(repo, monkeypatch):
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "none")
    origin = Path.cwd()
    with worktree_run("run005") as wt:
        assert wt is None
        assert Path.cwd() == origin
    assert not (repo / ".worktrees").exists()


def test_resume_reuse_errors_when_worktree_missing(repo):
    with pytest.raises(WorktreeError, match="does not exist"):
        with worktree_run("nevercreated", reuse=True):
            pass


def test_resume_reuse_enters_existing_worktree(repo):
    created = create("run006")
    with worktree_run("run006", reuse=True) as wt:
        assert wt.resolve() == created.resolve()


def test_resume_under_none_errors_when_paused_run_has_a_worktree(repo, monkeypatch):
    """R10: the converse of `test_resume_reuse_errors_when_worktree_missing`
    — a run paused under a worktree-isolated mode left a real worktree on
    disk; resuming under `none` must not silently passthrough against the
    wrong tree."""
    create("run007")
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "none")

    with pytest.raises(WorktreeError, match="isolation"):
        with worktree_run("run007", reuse=True):
            pass


def test_resume_under_none_passthrough_when_no_worktree_exists(repo, monkeypatch):
    """A run that was never worktree-isolated resumes fine under `none` —
    the R10 guard only fires when a worktree actually exists."""
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "none")
    origin = Path.cwd()

    with worktree_run("run008", reuse=True) as wt:
        assert wt is None
        assert Path.cwd() == origin


def test_create_rejects_traversal_run_id(repo):
    with pytest.raises(ValueError, match="run_id"):
        create("../../etc")
    assert not (repo / ".worktrees").exists()


def test_cleanup_removes_worktree_and_branch(repo):
    create("run007")
    cleanup("run007")
    assert not worktree_path("run007").exists()
    listed = subprocess.run(
        ["git", "worktree", "list"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    assert "run007" not in listed


def test_prune_all_removes_every_run_worktree(repo):
    create("run008")
    create("run009")
    removed = prune_all()
    assert set(removed) == {"run008", "run009"}
    assert not worktree_path("run008").exists()
    assert not worktree_path("run009").exists()


def test_snapshots_land_in_main_checkout_artifacts_in_worktree(repo):
    """The core D2 invariant: under a worktree, artifacts follow the chdir into
    the worktree; state snapshots stay anchored to the main checkout."""
    from loop_engine.core.state import State
    from loop_engine.tools.state_io.writer import write_artifact, write_state_snapshot

    state = State(schema_version=1, run_id="run010", stage_history=[], artifacts={})
    with worktree_run("run010") as wt:
        artifact = write_artifact("body", "docs/thing.md").resolve()
        snapshot = write_state_snapshot(state, run_id="run010", stage_index=0, stage_name="pm")
        snapshot = snapshot.resolve()

    assert wt.resolve() in artifact.parents  # artifact in the worktree
    assert (repo / "state" / "run010" / "00_pm.json").resolve() == snapshot
    assert repo.resolve() in snapshot.parents  # snapshot in the main checkout
    assert wt.resolve() not in snapshot.parents
