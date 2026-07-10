"""Unit-level coverage for `run_maintenance`'s chain and gating, with every
collaborator faked — no real clone, loop, or push. See
`test_integration.py` for the hermetic end-to-end (real git_io) proof."""

import pytest
from pydantic import ValidationError

from loop_engine.core.state import RunStatus, State
from loop_engine.flows.maintenance import (
    MaintenanceRequest,
    MaintenanceStatus,
    run_maintenance,
)
from loop_engine.tools.repo_io import PullRef


class _FakeRepoIO:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.open_pr_result = PullRef(number=7, url="https://github.com/acme/widgets/pull/7")

    def clone_repo(self, slug, dest, *, depth=None):
        self.calls.append(("clone_repo", slug, dest))
        return dest

    def open_pr(self, owner, repo, *, head, base, title, body):
        self.calls.append(("open_pr", owner, repo, head, base, title, body))
        return self.open_pr_result


class _FakeGitIO:
    def __init__(self, *, has_changes: bool = True) -> None:
        self.calls: list[tuple] = []
        self._has_changes = has_changes

    def checkout_branch(self, tree, branch):
        self.calls.append(("checkout_branch", tree, branch))

    def has_changes(self, tree):
        # Deliberately NOT recorded in `calls`: it's a read-only query, and the
        # ordering assertions below track the *write* sequence only.
        return self._has_changes

    def commit_all(self, tree, message):
        self.calls.append(("commit_all", tree, message))

    def push_branch(self, tree, branch, *, remote="origin"):
        self.calls.append(("push_branch", tree, branch, remote))


def _fake_run_step(calls, *, status=RunStatus.COMPLETED):
    def run_step(human_input, tree_path, *, budget_usd, loop_name):
        calls.append(("run_step", human_input, tree_path, budget_usd, loop_name))
        return State(
            schema_version=2,
            run_id="r1",
            status=status,
            stage_history=[],
            artifacts={},
        )

    return run_step


def _request(**overrides) -> MaintenanceRequest:
    defaults = dict(
        repo_full_name="acme/widgets",
        human_input="Bump the lockfile",
        branch="maint/bump-lockfile",
    )
    return MaintenanceRequest(**{**defaults, **overrides})


def test_green_gate_drives_full_chain_in_order_and_returns_opened_pr() -> None:
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO()
    step_calls: list = []
    run_step = _fake_run_step(step_calls)

    def run_tests(tree):
        return 0, "ok"

    request = _request()
    result = run_maintenance(
        request, run_step=run_step, repo_io=repo_io, git_io=git_io, run_tests=run_tests
    )

    assert result.status == MaintenanceStatus.OPENED_PR
    assert result.pull == repo_io.open_pr_result

    # clone -> checkout_branch -> run_step -> [gate] -> commit_all -> push_branch -> open_pr
    assert repo_io.calls[0] == ("clone_repo", "acme/widgets", "widgets")
    assert git_io.calls[0] == ("checkout_branch", "widgets", "maint/bump-lockfile")
    assert step_calls[0] == (
        "run_step",
        "Bump the lockfile",
        "widgets",
        request.budget_usd,
        "default",
    )
    assert git_io.calls[1][0] == "commit_all"
    assert git_io.calls[1][1] == "widgets"
    assert git_io.calls[2] == ("push_branch", "widgets", "maint/bump-lockfile", "origin")
    assert repo_io.calls[1] == (
        "open_pr",
        "acme",
        "widgets",
        "maint/bump-lockfile",
        "develop",
        repo_io.calls[1][5],
        repo_io.calls[1][6],
    )


def test_red_gate_returns_gate_failed_and_calls_no_git_writes_or_pr() -> None:
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO()
    run_step = _fake_run_step([])

    def run_tests(tree):
        return 1, "FAILED"

    request = _request()
    result = run_maintenance(
        request, run_step=run_step, repo_io=repo_io, git_io=git_io, run_tests=run_tests
    )

    assert result.status == MaintenanceStatus.GATE_FAILED
    assert result.pull is None
    assert not any(call[0] == "commit_all" for call in git_io.calls)
    assert not any(call[0] == "push_branch" for call in git_io.calls)
    assert not any(call[0] == "open_pr" for call in repo_io.calls)


def test_incomplete_inner_run_returns_run_incomplete_and_ships_nothing() -> None:
    # A run that paused for a human (AWAITING_ISSUE) must not reach the gate,
    # a git write, or a PR — even if its partial tree would pass pytest.
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO()
    run_step = _fake_run_step([], status=RunStatus.AWAITING_ISSUE)
    gate_calls: list = []

    def run_tests(tree):
        gate_calls.append(tree)
        return 0, "ok"

    result = run_maintenance(
        _request(), run_step=run_step, repo_io=repo_io, git_io=git_io, run_tests=run_tests
    )

    assert result.status == MaintenanceStatus.RUN_INCOMPLETE
    assert result.pull is None
    assert gate_calls == []  # gate never runs on an incomplete run
    assert not any(call[0] == "commit_all" for call in git_io.calls)
    assert not any(call[0] == "push_branch" for call in git_io.calls)
    assert not any(call[0] == "open_pr" for call in repo_io.calls)


def test_completed_run_with_no_changes_returns_no_changes_and_ships_nothing() -> None:
    # A completed run that produced no diff is a clean no-op: no gate, no
    # commit (which would fail on an empty index), no push, no PR.
    repo_io = _FakeRepoIO()
    git_io = _FakeGitIO(has_changes=False)
    run_step = _fake_run_step([])
    gate_calls: list = []

    def run_tests(tree):
        gate_calls.append(tree)
        return 0, "ok"

    result = run_maintenance(
        _request(), run_step=run_step, repo_io=repo_io, git_io=git_io, run_tests=run_tests
    )

    assert result.status == MaintenanceStatus.NO_CHANGES
    assert result.pull is None
    assert gate_calls == []
    assert not any(call[0] == "commit_all" for call in git_io.calls)
    assert not any(call[0] == "push_branch" for call in git_io.calls)
    assert not any(call[0] == "open_pr" for call in repo_io.calls)


def test_maintenance_request_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        _request(unknown_field="nope")


def test_maintenance_request_defaults_base_to_develop() -> None:
    request = _request()
    assert request.base == "develop"


def test_maintenance_request_dest_defaults_to_repo_name() -> None:
    request = _request(repo_full_name="acme/widgets")
    assert request.dest == "widgets"


def test_maintenance_request_dest_honors_clone_dest_override() -> None:
    request = _request(clone_dest="somewhere-else")
    assert request.dest == "somewhere-else"


def test_flow_module_imports_no_keyring_and_writes_no_files_directly() -> None:
    import ast
    from pathlib import Path

    module_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src/loop_engine/flows/maintenance/flow.py"
    )
    tree = ast.parse(module_path.read_text())
    disallowed_writes = {"open", "write_text", "write_bytes"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "keyring" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "keyring"
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in disallowed_writes
            if isinstance(func, ast.Attribute):
                assert func.attr not in disallowed_writes
