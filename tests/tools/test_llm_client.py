from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from loop_orchestrator.tools.llm.client import (
    BudgetExceededError,
    InvalidMessageSequenceError,
    LLMClient,
    MissingCredentialError,
    ToolLoopExceededError,
    TruncatedResponseError,
)


def _tool_use_response(tool_use_id: str, name: str, tool_input: dict) -> SimpleNamespace:
    return SimpleNamespace(
        usage=SimpleNamespace(input_tokens=10, output_tokens=10),
        content=[
            SimpleNamespace(type="text", text="calling a tool"),
            SimpleNamespace(type="tool_use", id=tool_use_id, name=name, input=tool_input),
        ],
        stop_reason="tool_use",
    )


def _mock_response(
    input_tokens: int,
    output_tokens: int,
    text: str = "hello",
    stop_reason: str = "end_turn",
) -> SimpleNamespace:
    return SimpleNamespace(
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        content=[SimpleNamespace(text=text)],
        stop_reason=stop_reason,
    )


def test_missing_credential_raises_when_keyring_returns_none(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: None)

    with pytest.raises(MissingCredentialError):
        LLMClient(budget_usd=1.0)


def test_keyring_get_password_called_exactly_once_across_two_calls(monkeypatch) -> None:
    mock_get_password = MagicMock(return_value="fake-api-key")
    monkeypatch.setattr("keyring.get_password", mock_get_password)

    client = LLMClient(budget_usd=10.0)
    client._anthropic.messages.create = MagicMock(return_value=_mock_response(10, 10))

    client.call("first prompt", model="claude-sonnet-5")
    client.call("second prompt", model="claude-sonnet-5")

    assert mock_get_password.call_count == 1


def test_call_increments_tokens_used_by_actual_response_usage(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    client._anthropic.messages.create = MagicMock(return_value=_mock_response(50, 25))

    client.call("a prompt", model="claude-sonnet-5")

    assert client._tokens_used == 75


def test_budget_exceeded_raises_and_skips_underlying_call(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    # max_tokens=1024 alone estimates ~$0.015 at the output rate; a tiny
    # budget guarantees the pre-flight check rejects before any transport call.
    client = LLMClient(budget_usd=0.000001)
    mock_create = MagicMock(return_value=_mock_response(50, 25))
    client._anthropic.messages.create = mock_create
    # Near the cap the pre-flight refines via count_tokens; stub it so the
    # unit test never attempts the network.
    client._anthropic.messages.count_tokens = MagicMock(
        return_value=SimpleNamespace(input_tokens=500)
    )

    with pytest.raises(BudgetExceededError):
        client.call("a very long prompt that estimates well over budget", model="claude-sonnet-5")

    mock_create.assert_not_called()


def test_truncated_response_raises_instead_of_returning_partial_text(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    client._anthropic.messages.create = MagicMock(
        return_value=_mock_response(50, 1024, text="half a docu", stop_reason="max_tokens")
    )

    with pytest.raises(TruncatedResponseError):
        client.call("a prompt", model="claude-sonnet-5")

    # The tokens were still spent and must still be accounted for.
    assert client.tokens_used == 1074


def test_remaining_reports_budget_left_in_dollars(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    client._anthropic.messages.create = MagicMock(return_value=_mock_response(50, 25))
    client.call("a prompt", model="claude-sonnet-5")

    # 50 input at $3/MTok + 25 output at $15/MTok.
    expected_cost = (50 * 3 + 25 * 15) / 1_000_000
    assert client.remaining() == pytest.approx(10.0 - expected_cost)
    assert client.cost_used == pytest.approx(expected_cost)


def test_call_records_cache_usage_when_present(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    response = _mock_response(50, 25)
    response.usage.cache_creation_input_tokens = 4000
    response.usage.cache_read_input_tokens = 6000

    client = LLMClient(budget_usd=10.0)
    client._anthropic.messages.create = MagicMock(return_value=response)

    result = client.call("a prompt", model="claude-sonnet-5")

    assert result.cache_creation_input_tokens == 4000
    assert result.cache_read_input_tokens == 6000
    assert client.cache_creation_tokens_used == 4000
    assert client.cache_read_tokens_used == 6000
    # All token classes count toward tokens_used (total processed).
    assert client.tokens_used == 50 + 25 + 4000 + 6000
    expected_cost = (50 * 3 + 25 * 15 + 4000 * 3.75 + 6000 * 0.30) / 1_000_000
    assert result.cost_usd == pytest.approx(expected_cost)
    assert client.cost_used == pytest.approx(expected_cost)


def test_call_treats_absent_cache_fields_as_zero(monkeypatch) -> None:
    # Responses (and test doubles) that predate caching lack the cache usage
    # fields entirely; behavior must be identical to zeroes.
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    client._anthropic.messages.create = MagicMock(return_value=_mock_response(50, 25))

    result = client.call("a prompt", model="claude-sonnet-5")

    assert result.cache_creation_input_tokens == 0
    assert result.cache_read_input_tokens == 0
    assert client.cache_creation_tokens_used == 0
    assert client.cache_read_tokens_used == 0
    assert client.tokens_used == 75


def test_system_blocks_render_with_cache_control_on_last_block_only(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    mock_create = MagicMock(return_value=_mock_response(50, 25))
    client._anthropic.messages.create = mock_create

    client.call(
        "the volatile user prompt",
        model="claude-sonnet-5",
        system_blocks=["stable template", "stable artifact"],
    )

    system = mock_create.call_args.kwargs["system"]
    assert [block["text"] for block in system] == ["stable template", "stable artifact"]
    assert "cache_control" not in system[0]
    assert system[1]["cache_control"] == {"type": "ephemeral"}
    assert mock_create.call_args.kwargs["messages"] == [
        {"role": "user", "content": "the volatile user prompt"}
    ]


def test_no_system_kwarg_when_system_blocks_omitted(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    mock_create = MagicMock(return_value=_mock_response(50, 25))
    client._anthropic.messages.create = mock_create

    client.call("a prompt", model="claude-sonnet-5")

    assert "system" not in mock_create.call_args.kwargs


def test_count_tokens_not_invoked_far_from_budget(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    client._anthropic.messages.create = MagicMock(return_value=_mock_response(50, 25))
    mock_count = MagicMock()
    client._anthropic.messages.count_tokens = mock_count

    client.call("a prompt", model="claude-sonnet-5")

    mock_count.assert_not_called()


def test_count_tokens_refines_the_estimate_near_budget(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    # max_tokens=1024 estimates ~$0.0154; a $0.02 budget puts the call inside
    # the 50%-of-remaining guard band. The heuristic alone would pass, but the
    # counted number (2000 input tokens -> +$0.006) must be what's used.
    client = LLMClient(budget_usd=0.0157)
    mock_create = MagicMock(return_value=_mock_response(50, 25))
    client._anthropic.messages.create = mock_create
    mock_count = MagicMock(return_value=SimpleNamespace(input_tokens=2_000))
    client._anthropic.messages.count_tokens = mock_count

    with pytest.raises(BudgetExceededError):
        client.call("hi", model="claude-sonnet-5")

    mock_count.assert_called_once()
    mock_create.assert_not_called()


def test_count_tokens_failure_falls_back_to_heuristic(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    # Inside the guard band with a budget the heuristic estimate clears: a
    # count_tokens outage must not become a new failure mode.
    client = LLMClient(budget_usd=0.02)
    mock_create = MagicMock(return_value=_mock_response(50, 25))
    client._anthropic.messages.create = mock_create
    client._anthropic.messages.count_tokens = MagicMock(side_effect=RuntimeError("api down"))

    result = client.call("hi", model="claude-sonnet-5")

    assert result.text == "hello"
    mock_create.assert_called_once()


def test_call_messages_passes_messages_through_verbatim(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    mock_create = MagicMock(return_value=_mock_response(50, 25))
    client._anthropic.messages.create = mock_create

    messages = [
        {"role": "user", "content": "attempt-1 instruction"},
        {"role": "assistant", "content": "the previous artifact"},
        {"role": "user", "content": "the findings"},
    ]
    result = client.call_messages(messages, model="claude-sonnet-5")

    assert mock_create.call_args.kwargs["messages"] == messages
    assert result.text == "hello"
    assert client.tokens_used == 75


def test_call_messages_rejects_trailing_assistant_turn_without_transport_call(
    monkeypatch,
) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    mock_create = MagicMock(return_value=_mock_response(50, 25))
    client._anthropic.messages.create = mock_create

    with pytest.raises(InvalidMessageSequenceError):
        client.call_messages(
            [
                {"role": "user", "content": "u"},
                {"role": "assistant", "content": "a prefill"},
            ],
            model="claude-sonnet-5",
        )

    mock_create.assert_not_called()


def test_run_tool_loop_executes_tools_until_end_turn(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    mock_create = MagicMock(
        side_effect=[
            _tool_use_response("tu_1", "read_file", {"path": "sprints/01/plan.md"}),
            _mock_response(10, 10, text="finished implementation"),
        ]
    )
    client._anthropic.messages.create = mock_create
    executed: list[tuple[str, dict]] = []

    def execute(name: str, tool_input: dict) -> str:
        executed.append((name, tool_input))
        return "file contents here"

    result = client.run_tool_loop(
        [{"role": "user", "content": "implement the sprint"}],
        model="claude-sonnet-5",
        tools=[{"name": "read_file", "input_schema": {"type": "object"}}],
        execute=execute,
    )

    assert result.text == "finished implementation"
    assert executed == [("read_file", {"path": "sprints/01/plan.md"})]

    # Second request carries the assistant turn plus ALL tool results in one
    # user message with matching tool_use_ids.
    second_messages = mock_create.call_args_list[1].kwargs["messages"]
    assert second_messages[-2]["role"] == "assistant"
    tool_result_message = second_messages[-1]
    assert tool_result_message["role"] == "user"
    assert tool_result_message["content"] == [
        {"type": "tool_result", "tool_use_id": "tu_1", "content": "file contents here"}
    ]


def test_run_tool_loop_surfaces_executor_errors_as_is_error_results(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    mock_create = MagicMock(
        side_effect=[
            _tool_use_response("tu_1", "read_file", {"path": "../etc/passwd"}),
            _mock_response(10, 10, text="recovered"),
        ]
    )
    client._anthropic.messages.create = mock_create

    def execute(name: str, tool_input: dict) -> str:
        raise ValueError("path escapes the run tree")

    result = client.run_tool_loop(
        [{"role": "user", "content": "go"}],
        model="claude-sonnet-5",
        tools=[{"name": "read_file", "input_schema": {"type": "object"}}],
        execute=execute,
    )

    # The loop continued (didn't crash) and the model saw the failure.
    assert result.text == "recovered"
    tool_result = mock_create.call_args_list[1].kwargs["messages"][-1]["content"][0]
    assert tool_result["is_error"] is True
    assert "path escapes the run tree" in tool_result["content"]


def test_run_tool_loop_debits_budget_per_iteration(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    # Each mocked response costs (200k in + 200k out) = $0.6 + $3.0 = $3.6.
    # Budget $3: iteration 1 overspends it, so iteration 2's ledger check
    # raises BudgetExceededError after exactly one transport call.
    client = LLMClient(budget_usd=3.0)
    mock_create = MagicMock(
        return_value=SimpleNamespace(
            usage=SimpleNamespace(input_tokens=200_000, output_tokens=200_000),
            content=[
                SimpleNamespace(type="tool_use", id="tu_1", name="grep", input={"pattern": "x"})
            ],
            stop_reason="tool_use",
        )
    )
    client._anthropic.messages.create = mock_create
    client._anthropic.messages.count_tokens = MagicMock(
        return_value=SimpleNamespace(input_tokens=400_000)
    )

    with pytest.raises(BudgetExceededError):
        client.run_tool_loop(
            [{"role": "user", "content": "go"}],
            model="claude-sonnet-5",
            tools=[{"name": "grep", "input_schema": {"type": "object"}}],
            execute=lambda name, tool_input: "ok",
        )

    assert mock_create.call_count == 1


def test_run_tool_loop_iteration_cap_raises_dedicated_error(monkeypatch) -> None:
    monkeypatch.setattr("keyring.get_password", lambda *_args: "fake-api-key")

    client = LLMClient(budget_usd=10.0)
    client._anthropic.messages.create = MagicMock(
        side_effect=lambda **_kwargs: _tool_use_response("tu_x", "grep", {"pattern": "x"})
    )

    with pytest.raises(ToolLoopExceededError):
        client.run_tool_loop(
            [{"role": "user", "content": "go"}],
            model="claude-sonnet-5",
            tools=[{"name": "grep", "input_schema": {"type": "object"}}],
            execute=lambda name, tool_input: "ok",
            max_iterations=3,
        )

    assert client._anthropic.messages.create.call_count == 3


def test_ci_env_fallback_used_when_both_gate_variables_set(monkeypatch) -> None:
    mock_get_password = MagicMock(return_value="keyring-key-should-not-be-used")
    monkeypatch.setattr("keyring.get_password", mock_get_password)
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ALLOW_ENV_CREDENTIAL", "1")
    monkeypatch.setenv("LOOP_ORCHESTRATOR_CI_API_KEY", "env-fallback-key")

    client = LLMClient(budget_usd=1.0)

    assert client._api_key == "env-fallback-key"
    mock_get_password.assert_not_called()


def test_ci_env_fallback_ignored_without_opt_in_flag(monkeypatch) -> None:
    mock_get_password = MagicMock(return_value="keyring-key")
    monkeypatch.setattr("keyring.get_password", mock_get_password)
    monkeypatch.delenv("LOOP_ORCHESTRATOR_ALLOW_ENV_CREDENTIAL", raising=False)
    monkeypatch.setenv("LOOP_ORCHESTRATOR_CI_API_KEY", "env-fallback-key")

    client = LLMClient(budget_usd=1.0)

    assert client._api_key == "keyring-key"
    mock_get_password.assert_called_once()


def test_ci_env_fallback_ignored_when_opt_in_flag_not_exact_match(monkeypatch) -> None:
    mock_get_password = MagicMock(return_value="keyring-key")
    monkeypatch.setattr("keyring.get_password", mock_get_password)
    monkeypatch.setenv("LOOP_ORCHESTRATOR_ALLOW_ENV_CREDENTIAL", "true")
    monkeypatch.setenv("LOOP_ORCHESTRATOR_CI_API_KEY", "env-fallback-key")

    client = LLMClient(budget_usd=1.0)

    assert client._api_key == "keyring-key"
    mock_get_password.assert_called_once()
