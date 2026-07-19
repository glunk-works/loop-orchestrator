import pytest
from pydantic import ValidationError

from loop_orchestrator.tools.llm.pricing import (
    ModelRates,
    UnknownModelError,
    cost_usd,
    estimate_cost_usd,
)


def test_cost_usd_matches_rate_table_for_plain_input_output() -> None:
    # claude-sonnet-5: $3/MTok input, $15/MTok output.
    assert cost_usd("claude-sonnet-5", 1_000_000, 0) == pytest.approx(3.00)
    assert cost_usd("claude-sonnet-5", 0, 1_000_000) == pytest.approx(15.00)
    assert cost_usd("claude-sonnet-5", 20_000, 20_000) == pytest.approx(0.36)


def test_cost_usd_includes_cache_write_and_read_components() -> None:
    # Cache writes at 1.25x input ($3.75/MTok), reads at 0.1x ($0.30/MTok).
    assert cost_usd("claude-sonnet-5", 0, 0, cache_creation_tokens=1_000_000) == pytest.approx(3.75)
    assert cost_usd("claude-sonnet-5", 0, 0, cache_read_tokens=1_000_000) == pytest.approx(0.30)
    assert cost_usd(
        "claude-sonnet-5",
        10_000,
        5_000,
        cache_creation_tokens=100_000,
        cache_read_tokens=200_000,
    ) == pytest.approx(0.03 + 0.075 + 0.375 + 0.06)


def test_estimate_prices_max_tokens_at_the_output_rate() -> None:
    # 2000 input tokens at $3/MTok + 8192 max_tokens at $15/MTok.
    assert estimate_cost_usd("claude-sonnet-5", 2_000, 8_192) == pytest.approx(
        0.006 + 8_192 * 15 / 1_000_000
    )


def test_cost_usd_matches_rate_table_for_claude_opus_4_8() -> None:
    # claude-opus-4-8: $5/MTok input, $25/MTok output.
    assert cost_usd("claude-opus-4-8", 1_000_000, 0) == pytest.approx(5.00)
    assert cost_usd("claude-opus-4-8", 0, 1_000_000) == pytest.approx(25.00)
    assert cost_usd("claude-opus-4-8", 20_000, 20_000) == pytest.approx(0.60)


def test_cost_usd_includes_cache_write_and_read_components_for_claude_opus_4_8() -> None:
    # Cache writes at 1.25x input ($6.25/MTok), reads at 0.1x ($0.50/MTok).
    assert cost_usd("claude-opus-4-8", 0, 0, cache_creation_tokens=1_000_000) == pytest.approx(6.25)
    assert cost_usd("claude-opus-4-8", 0, 0, cache_read_tokens=1_000_000) == pytest.approx(0.50)
    assert cost_usd(
        "claude-opus-4-8",
        10_000,
        5_000,
        cache_creation_tokens=100_000,
        cache_read_tokens=200_000,
    ) == pytest.approx(0.05 + 0.125 + 0.625 + 0.10)


def test_estimate_prices_max_tokens_at_the_output_rate_for_claude_opus_4_8() -> None:
    # 2000 input tokens at $5/MTok + 8192 max_tokens at $25/MTok.
    assert estimate_cost_usd("claude-opus-4-8", 2_000, 8_192) == pytest.approx(
        0.01 + 8_192 * 25 / 1_000_000
    )


def test_cost_usd_matches_rate_table_for_claude_haiku_4_5() -> None:
    # claude-haiku-4-5: $1/MTok input, $5/MTok output.
    assert cost_usd("claude-haiku-4-5", 1_000_000, 0) == pytest.approx(1.00)
    assert cost_usd("claude-haiku-4-5", 0, 1_000_000) == pytest.approx(5.00)
    assert cost_usd("claude-haiku-4-5", 20_000, 20_000) == pytest.approx(0.12)


def test_cost_usd_includes_cache_write_and_read_components_for_claude_haiku_4_5() -> None:
    # Cache writes at 1.25x input ($1.25/MTok), reads at 0.1x ($0.10/MTok).
    assert cost_usd("claude-haiku-4-5", 0, 0, cache_creation_tokens=1_000_000) == pytest.approx(
        1.25
    )
    assert cost_usd("claude-haiku-4-5", 0, 0, cache_read_tokens=1_000_000) == pytest.approx(0.10)
    assert cost_usd(
        "claude-haiku-4-5",
        10_000,
        5_000,
        cache_creation_tokens=100_000,
        cache_read_tokens=200_000,
    ) == pytest.approx(0.01 + 0.025 + 0.125 + 0.02)


def test_estimate_prices_max_tokens_at_the_output_rate_for_claude_haiku_4_5() -> None:
    # 2000 input tokens at $1/MTok + 8192 max_tokens at $5/MTok.
    assert estimate_cost_usd("claude-haiku-4-5", 2_000, 8_192) == pytest.approx(
        0.002 + 8_192 * 5 / 1_000_000
    )


def test_unknown_model_raises_instead_of_pricing_at_zero() -> None:
    with pytest.raises(UnknownModelError):
        cost_usd("claude-nonexistent-9", 10, 10)
    with pytest.raises(UnknownModelError):
        estimate_cost_usd("claude-nonexistent-9", 10, 10)


def test_model_rates_rejects_negative_rates() -> None:
    with pytest.raises(ValidationError):
        ModelRates(
            input_usd_per_mtok=-1.0,
            output_usd_per_mtok=15.0,
            cache_write_usd_per_mtok=3.75,
            cache_read_usd_per_mtok=0.30,
        )


def test_model_rates_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ModelRates(
            input_usd_per_mtok=3.0,
            output_usd_per_mtok=15.0,
            cache_write_usd_per_mtok=3.75,
            cache_read_usd_per_mtok=0.30,
            discount=0.5,
        )
