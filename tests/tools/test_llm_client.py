from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_engine.tools.llm.client import (
    BudgetExceededError,
    LLMClient,
    MissingCredentialError,
)


def _mock_response(input_tokens: int, output_tokens: int, text: str = "hello") -> SimpleNamespace:
    return SimpleNamespace(
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        content=[SimpleNamespace(text=text)],
    )


def test_missing_credential_raises_when_keyring_returns_none(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: None)

    with pytest.raises(MissingCredentialError):
        LLMClient(budget_tokens=1000)


def test_keyring_get_password_called_exactly_once_across_two_calls(monkeypatch) -> None:
    mock_get_password = MagicMock(return_value="fake-api-key")
    monkeypatch.setattr("keyring.get_password", mock_get_password)

    client = LLMClient(budget_tokens=10_000)
    client._anthropic.messages.create = MagicMock(return_value=_mock_response(10, 10))

    client.call("first prompt", model="claude-sonnet-5")
    client.call("second prompt", model="claude-sonnet-5")

    assert mock_get_password.call_count == 1


def test_call_increments_tokens_used_by_actual_response_usage(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_tokens=10_000)
    client._anthropic.messages.create = MagicMock(return_value=_mock_response(50, 25))

    client.call("a prompt", model="claude-sonnet-5")

    assert client._tokens_used == 75


def test_budget_exceeded_raises_and_skips_underlying_call(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_tokens=1)
    mock_create = MagicMock(return_value=_mock_response(50, 25))
    client._anthropic.messages.create = mock_create

    with pytest.raises(BudgetExceededError):
        client.call("a very long prompt that estimates well over budget", model="claude-sonnet-5")

    mock_create.assert_not_called()


def test_ci_env_fallback_used_when_both_gate_variables_set(monkeypatch) -> None:
    mock_get_password = MagicMock(return_value="keyring-key-should-not-be-used")
    monkeypatch.setattr("keyring.get_password", mock_get_password)
    monkeypatch.setenv("LOOP_ENGINE_ALLOW_ENV_CREDENTIAL", "1")
    monkeypatch.setenv("LOOP_ENGINE_CI_API_KEY", "env-fallback-key")

    client = LLMClient(budget_tokens=1000)

    assert client._api_key == "env-fallback-key"
    mock_get_password.assert_not_called()


def test_ci_env_fallback_ignored_without_opt_in_flag(monkeypatch) -> None:
    mock_get_password = MagicMock(return_value="keyring-key")
    monkeypatch.setattr("keyring.get_password", mock_get_password)
    monkeypatch.delenv("LOOP_ENGINE_ALLOW_ENV_CREDENTIAL", raising=False)
    monkeypatch.setenv("LOOP_ENGINE_CI_API_KEY", "env-fallback-key")

    client = LLMClient(budget_tokens=1000)

    assert client._api_key == "keyring-key"
    mock_get_password.assert_called_once()


def test_ci_env_fallback_ignored_when_opt_in_flag_not_exact_match(monkeypatch) -> None:
    mock_get_password = MagicMock(return_value="keyring-key")
    monkeypatch.setattr("keyring.get_password", mock_get_password)
    monkeypatch.setenv("LOOP_ENGINE_ALLOW_ENV_CREDENTIAL", "true")
    monkeypatch.setenv("LOOP_ENGINE_CI_API_KEY", "env-fallback-key")

    client = LLMClient(budget_tokens=1000)

    assert client._api_key == "keyring-key"
    mock_get_password.assert_called_once()
