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
