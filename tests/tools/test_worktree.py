"""Phase 3a worktree isolation. Uses a real git repo in tmp_path so the
`git worktree` subprocess surface is exercised end to end."""

import asyncio
import subprocess
from pathlib import Path

import pytest

from loop_orchestrator.tools.state_io import writer as state_writer
from loop_orchestrator.tools.state_io.writer import state_root
from loop_orchestrator.tools.worktree.manager import (
    WorktreeError,
    branch_name,
    cleanup,
    create,
    origin_cwd,
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
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "worktree")
    # state_root is a module global; ensure a clean baseline per test.
    state_writer.set_state_root(None)
    return tmp_path


def test_flag_off_by_default(monkeypatch):
    monkeypatch.delenv("LOOP_ORCHESTRATOR_ISOLATION", raising=False)
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
    monkeypatch.setenv("LOOP_ORCHESTRATOR_WORKTREE_ROOT", str(repo / "custom_wt"))
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
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "none")
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


def test_origin_cwd_is_the_main_checkout_while_inside_the_worktree(repo):
    """The invariant the issue filer leans on (R8): inside a worktree the process
    CWD is the worktree — whose remote is loop-orchestrator itself — while `origin_cwd()`
    is still the checkout the orchestrator was launched from."""
    assert origin_cwd() == repo  # outside a worktree: just the CWD

    with worktree_run("run020") as wt:
        assert Path.cwd() == wt.resolve()
        assert origin_cwd().resolve() == repo.resolve()
        assert origin_cwd().resolve() != Path.cwd()

    assert origin_cwd() == repo  # restored on exit


def test_nested_worktree_run_restores_the_prior_origin_not_none(repo):
    """F6: exiting an inner `worktree_run` must restore whatever
    `_ORIGIN_CWD`/`_STATE_ROOT` held before it -- via `ContextVar.reset(token)`
    -- not clobber to `None`. With the plain-global version this replaced,
    the inner exit's `_set_origin_cwd(None)` left the outer context's
    `origin_cwd()` falling back to `Path.cwd()`, which by then is the OUTER
    worktree (not the real origin) -- a distinguishable wrong answer, not
    just a theoretical one."""
    create("run032")

    with worktree_run("run032") as outer_wt:
        outer_origin = origin_cwd()
        outer_state_root = state_root()
        assert outer_origin == repo

        with worktree_run("run033") as inner_wt:
            assert origin_cwd().resolve() == outer_wt.resolve()
            assert inner_wt != outer_wt

        # Restored to what was active before the inner run -- not None
        # (which would fall back to Path.cwd(), now wrongly == outer_wt).
        assert origin_cwd() == outer_origin
        assert state_root() == outer_state_root
        assert Path.cwd() == outer_wt


def test_origin_cwd_context_does_not_leak_into_a_worker_thread(repo):
    """F3: `_ORIGIN_CWD` is a `ContextVar`, not a plain module global --
    `asyncio.to_thread` (what `InProcessDispatcher` uses to run each loop)
    copies the calling context into its worker thread, so a `set()` made
    from inside that thread cannot cross back into the caller's context,
    and the caller's own value is unaffected by whatever the thread does."""
    create("run034")
    assert origin_cwd() == repo

    def in_thread() -> Path:
        with worktree_run("run034", reuse=True):
            return origin_cwd().resolve()

    async def main() -> Path:
        return await asyncio.to_thread(in_thread)

    result = asyncio.run(main())

    assert result == repo.resolve()
    # The calling (outer) context's origin is untouched by the thread's own
    # set/reset -- there was nothing to leak back.
    assert origin_cwd() == repo


def test_origin_cwd_is_the_cwd_when_isolation_is_off(repo, monkeypatch):
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "none")
    with worktree_run("run021") as wt:
        assert wt is None
        # No worktree, so the CWD *is* the intended tree (e.g. a flows/ clone).
        assert origin_cwd() == Path.cwd()


def test_missing_worktree_error_names_the_isolation_mismatch_cause(repo):
    """R10, the direction V3 actually hit: paused under ISOLATION=none (which
    creates no worktree), resumed under a worktree-bearing mode. Reporting only
    'pruned' sent that session hunting for a tree that never existed."""
    with pytest.raises(WorktreeError) as exc:
        with worktree_run("neverpaused", reuse=True):
            pass

    message = str(exc.value)
    assert "pruned" in message
    assert "LOOP_ORCHESTRATOR_ISOLATION=none" in message
    assert "same isolation mode" in message


def test_resume_under_none_errors_when_paused_run_has_a_worktree(repo, monkeypatch):
    """R10: the converse of `test_resume_reuse_errors_when_worktree_missing`
    — a run paused under a worktree-isolated mode left a real worktree on
    disk; resuming under `none` must not silently passthrough against the
    wrong tree."""
    create("run007")
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "none")

    with pytest.raises(WorktreeError, match="isolation"):
        with worktree_run("run007", reuse=True):
            pass


def test_resume_under_none_passthrough_when_no_worktree_exists(repo, monkeypatch):
    """A run that was never worktree-isolated resumes fine under `none` —
    the R10 guard only fires when a worktree actually exists."""
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "none")
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
    from loop_orchestrator.core.state import State
    from loop_orchestrator.tools.state_io.writer import write_artifact, write_state_snapshot

    state = State(schema_version=1, run_id="run010", stage_history=[], artifacts={})
    with worktree_run("run010") as wt:
        artifact = write_artifact("body", "docs/thing.md").resolve()
        snapshot = write_state_snapshot(state, run_id="run010", stage_index=0, stage_name="pm")
        snapshot = snapshot.resolve()

    assert wt.resolve() in artifact.parents  # artifact in the worktree
    assert (repo / "state" / "run010" / "00_pm.json").resolve() == snapshot
    assert repo.resolve() in snapshot.parents  # snapshot in the main checkout
    assert wt.resolve() not in snapshot.parents
