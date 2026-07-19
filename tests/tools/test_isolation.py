"""The single reader of LOOP_ORCHESTRATOR_ISOLATION and its derived predicates."""

import pytest

from loop_orchestrator.tools.isolation import (
    isolation_mode,
    sandbox_runtime_mode,
    worktree_needed,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "none"),
        ("", "none"),
        ("none", "none"),
        ("worktree", "worktree"),
        ("container", "container"),
        ("sandbox", "sandbox"),
        ("  WORKTREE  ", "worktree"),  # stripped + lowercased
    ],
)
def test_isolation_mode_values(monkeypatch, value, expected) -> None:
    if value is None:
        monkeypatch.delenv("LOOP_ORCHESTRATOR_ISOLATION", raising=False)
    else:
        monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", value)
    assert isolation_mode() == expected


def test_unknown_isolation_mode_raises(monkeypatch) -> None:
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "vm")
    with pytest.raises(ValueError, match="invalid LOOP_ORCHESTRATOR_ISOLATION"):
        isolation_mode()


@pytest.mark.parametrize(
    ("value", "needed"),
    [(None, False), ("none", False), ("worktree", True), ("container", True), ("sandbox", True)],
)
def test_worktree_needed(monkeypatch, value, needed) -> None:
    if value is None:
        monkeypatch.delenv("LOOP_ORCHESTRATOR_ISOLATION", raising=False)
    else:
        monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", value)
    assert worktree_needed() is needed


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("none", None),
        ("worktree", None),
        ("container", "container"),
        ("sandbox", "sandbox"),
    ],
)
def test_sandbox_runtime_mode(monkeypatch, value, expected) -> None:
    if value is None:
        monkeypatch.delenv("LOOP_ORCHESTRATOR_ISOLATION", raising=False)
    else:
        monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", value)
    assert sandbox_runtime_mode() == expected
