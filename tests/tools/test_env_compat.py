"""`tools/env_compat.getenv_compat` — the LOOP_ENGINE_* → LOOP_ORCHESTRATOR_*
back-compat shim added with the sprint-42 package rename.

The rename flipped the runtime env-var prefix; the shim lets a deployment that
still sets the legacy `LOOP_ENGINE_*` names keep working (with a one-time
deprecation warning) until its environment is updated. These tests pin that
contract so the fallback isn't silently dropped."""

import warnings

import pytest

from loop_orchestrator.tools import env_compat
from loop_orchestrator.tools.env_compat import getenv_compat


@pytest.fixture(autouse=True)
def _reset_warn_cache():
    """The warn-once cache is module-global; clear it between tests."""
    env_compat._warned.clear()
    yield
    env_compat._warned.clear()


def test_new_name_wins(monkeypatch):
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "container")
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "worktree")
    assert getenv_compat("LOOP_ORCHESTRATOR_ISOLATION") == "container"


def test_falls_back_to_legacy_name(monkeypatch):
    monkeypatch.delenv("LOOP_ORCHESTRATOR_ISOLATION", raising=False)
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "container")
    with pytest.warns(DeprecationWarning, match="LOOP_ENGINE_ISOLATION is deprecated"):
        assert getenv_compat("LOOP_ORCHESTRATOR_ISOLATION") == "container"


def test_default_when_neither_set(monkeypatch):
    monkeypatch.delenv("LOOP_ORCHESTRATOR_ISOLATION", raising=False)
    monkeypatch.delenv("LOOP_ENGINE_ISOLATION", raising=False)
    assert getenv_compat("LOOP_ORCHESTRATOR_ISOLATION") is None
    assert getenv_compat("LOOP_ORCHESTRATOR_ISOLATION", "none") == "none"


def test_legacy_warning_emitted_once(monkeypatch):
    monkeypatch.delenv("LOOP_ORCHESTRATOR_ISOLATION", raising=False)
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "container")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        getenv_compat("LOOP_ORCHESTRATOR_ISOLATION")
        getenv_compat("LOOP_ORCHESTRATOR_ISOLATION")
    assert sum(issubclass(w.category, DeprecationWarning) for w in caught) == 1


def test_empty_string_value_is_returned_not_defaulted(monkeypatch):
    """An explicitly-empty new-name value must not trigger the legacy fallback."""
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ISOLATION", "")
    monkeypatch.setenv("LOOP_ENGINE_ISOLATION", "container")
    assert getenv_compat("LOOP_ORCHESTRATOR_ISOLATION", "none") == ""
