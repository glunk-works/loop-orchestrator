import pytest

from loop_engine.personas.coder_iac.mode import (
    CODER_ENV_VAR,
    RALPH_MAX_ITERS_ENV_VAR,
    coder_mode,
    ralph_max_iterations,
    use_ralph_coder,
)


def test_coder_mode_defaults_to_classic(monkeypatch) -> None:
    monkeypatch.delenv(CODER_ENV_VAR, raising=False)
    assert coder_mode() == "classic"
    assert use_ralph_coder() is False


def test_coder_mode_selects_ralph(monkeypatch) -> None:
    monkeypatch.setenv(CODER_ENV_VAR, "ralph")
    assert coder_mode() == "ralph"
    assert use_ralph_coder() is True


def test_coder_mode_is_case_insensitive_and_stripped(monkeypatch) -> None:
    monkeypatch.setenv(CODER_ENV_VAR, "  RALPH  ")
    assert coder_mode() == "ralph"


def test_unknown_coder_mode_raises(monkeypatch) -> None:
    monkeypatch.setenv(CODER_ENV_VAR, "wiggum")
    with pytest.raises(ValueError, match="not a valid Coder mode"):
        coder_mode()


def test_ralph_max_iterations_default(monkeypatch) -> None:
    monkeypatch.delenv(RALPH_MAX_ITERS_ENV_VAR, raising=False)
    assert ralph_max_iterations() == 30


def test_ralph_max_iterations_override(monkeypatch) -> None:
    monkeypatch.setenv(RALPH_MAX_ITERS_ENV_VAR, "7")
    assert ralph_max_iterations() == 7


@pytest.mark.parametrize("bad", ["0", "-3", "notanint"])
def test_ralph_max_iterations_rejects_bad_values(monkeypatch, bad) -> None:
    monkeypatch.setenv(RALPH_MAX_ITERS_ENV_VAR, bad)
    with pytest.raises(ValueError):
        ralph_max_iterations()
