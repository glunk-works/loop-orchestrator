"""Isolation-aware `run_gate_pytest`: in-process on none/worktree, dispatched
through the sandboxed coder-tools server on container/sandbox. Mirrors
`test_coder_tool_backend.py`'s fake-provider pattern (mocks
`sandbox_runtime_mode` + `build_coder_tool_provider` directly rather than
spawning a real stdio server)."""

from pathlib import Path

import pytest

from loop_engine.tools.coder_tools.run_tests import PYTEST_NO_TESTS_COLLECTED
from loop_engine.tools.mcp import provider as mcp_provider
from loop_engine.tools.mcp.provider import run_gate_pytest


class _FakeProvider:
    def __init__(self, result_text: str) -> None:
        self._result_text = result_text
        self.entered = 0
        self.exited = 0
        self.calls: list[tuple[str, dict]] = []

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, *exc):
        self.exited += 1

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return self._result_text


@pytest.fixture
def _tree(tmp_path):
    (tmp_path / "src").mkdir()
    return tmp_path


def test_delegates_to_in_process_run_pytest_when_unsandboxed(monkeypatch, _tree) -> None:
    monkeypatch.setattr(mcp_provider, "sandbox_runtime_mode", lambda: None)
    monkeypatch.setattr(mcp_provider, "run_pytest", lambda path: (0, "1 passed"))

    def _unexpected_provider(cwd=None):
        raise AssertionError("no provider should be built when unsandboxed")

    monkeypatch.setattr(mcp_provider, "build_coder_tool_provider", _unexpected_provider)

    assert run_gate_pytest("src", cwd=_tree) == (0, "1 passed")


def test_dispatches_through_sandbox_provider_when_containerized(monkeypatch, _tree) -> None:
    fake = _FakeProvider("pytest exit code: 0\n\n1 passed in 0.01s")
    monkeypatch.setattr(mcp_provider, "sandbox_runtime_mode", lambda: "container")
    monkeypatch.setattr(mcp_provider, "build_coder_tool_provider", lambda cwd=None: fake)

    exit_code, output = run_gate_pytest("src", cwd=_tree)

    assert (exit_code, output) == (0, "1 passed in 0.01s")
    assert fake.entered == 1
    assert fake.exited == 1
    assert fake.calls == [("run_tests", {"path": "src"})]


def test_nonzero_exit_round_trips_through_sandbox_provider(monkeypatch, _tree) -> None:
    fake = _FakeProvider("pytest exit code: 1\n\nFAILED src/test_x.py")
    monkeypatch.setattr(mcp_provider, "sandbox_runtime_mode", lambda: "container")
    monkeypatch.setattr(mcp_provider, "build_coder_tool_provider", lambda cwd=None: fake)

    assert run_gate_pytest("src", cwd=_tree) == (1, "FAILED src/test_x.py")


@pytest.mark.parametrize("mode", [None, "container"])
def test_missing_tree_short_circuits_without_building_a_provider(
    monkeypatch, tmp_path, mode
) -> None:
    monkeypatch.setattr(mcp_provider, "sandbox_runtime_mode", lambda: mode)

    def _unexpected_provider(cwd=None):
        raise AssertionError("a missing tree must short-circuit before any provider is built")

    def _unexpected_run_pytest(path):
        raise AssertionError("pytest must not run for a missing tree")

    monkeypatch.setattr(mcp_provider, "build_coder_tool_provider", _unexpected_provider)
    monkeypatch.setattr(mcp_provider, "run_pytest", _unexpected_run_pytest)

    exit_code, output = run_gate_pytest("src", cwd=tmp_path)

    assert exit_code == PYTEST_NO_TESTS_COLLECTED
    assert output == "no src/ tree was produced"


def test_cwd_is_passed_through_to_the_sandbox_provider(monkeypatch, _tree) -> None:
    fake = _FakeProvider("pytest exit code: 0\n\nok")
    seen_cwd = {}

    def _capture_provider(cwd=None):
        seen_cwd["cwd"] = cwd
        return fake

    monkeypatch.setattr(mcp_provider, "sandbox_runtime_mode", lambda: "container")
    monkeypatch.setattr(mcp_provider, "build_coder_tool_provider", _capture_provider)

    run_gate_pytest("src", cwd=_tree)

    assert seen_cwd["cwd"] == _tree
    assert isinstance(_tree, Path)
