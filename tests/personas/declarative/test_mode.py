import pytest

from loop_engine.personas.declarative.mode import (
    PERSONAS_ENV_VAR,
    persona_mode,
    use_declarative_personas,
)


def test_persona_mode_defaults_to_classic_when_unset(monkeypatch) -> None:
    monkeypatch.delenv(PERSONAS_ENV_VAR, raising=False)
    assert persona_mode() == "classic"
    assert use_declarative_personas() is False


def test_persona_mode_empty_or_whitespace_is_classic(monkeypatch) -> None:
    monkeypatch.setenv(PERSONAS_ENV_VAR, "   ")
    assert persona_mode() == "classic"


def test_persona_mode_classic_explicit(monkeypatch) -> None:
    monkeypatch.setenv(PERSONAS_ENV_VAR, "classic")
    assert persona_mode() == "classic"
    assert use_declarative_personas() is False


def test_persona_mode_declarative_is_case_insensitive(monkeypatch) -> None:
    monkeypatch.setenv(PERSONAS_ENV_VAR, "DECLARATIVE")
    assert persona_mode() == "declarative"
    assert use_declarative_personas() is True


def test_persona_mode_unknown_value_raises(monkeypatch) -> None:
    monkeypatch.setenv(PERSONAS_ENV_VAR, "yaml")
    with pytest.raises(ValueError, match="not a valid persona mode"):
        persona_mode()
