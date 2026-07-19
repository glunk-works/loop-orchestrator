"""Per-model pricing: the sole source of $/token truth for budget and cost.

Rates are standard list prices in USD per million tokens. claude-sonnet-5
carries introductory pricing ($2/$10 per MTok) through 2026-08-31; this table
encodes the standard rates, so recorded cost slightly overstates real spend
until then.
"""

from pydantic import BaseModel, ConfigDict, Field

_TOKENS_PER_MTOK = 1_000_000


class UnknownModelError(KeyError):
    """No pricing entry for the requested model.

    Raised instead of pricing at $0 — a silently unpriced model would make
    every call free from the budget's point of view and disable the cap.
    """


class ModelRates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_usd_per_mtok: float = Field(ge=0)
    output_usd_per_mtok: float = Field(ge=0)
    cache_write_usd_per_mtok: float = Field(ge=0)
    cache_read_usd_per_mtok: float = Field(ge=0)


RATES: dict[str, ModelRates] = {
    "claude-sonnet-5": ModelRates(
        input_usd_per_mtok=3.00,
        output_usd_per_mtok=15.00,
        # Cache writes bill at 1.25x the input rate; cache reads at 0.1x.
        cache_write_usd_per_mtok=3.75,
        cache_read_usd_per_mtok=0.30,
    ),
    "claude-opus-4-8": ModelRates(
        input_usd_per_mtok=5.00,
        output_usd_per_mtok=25.00,
        cache_write_usd_per_mtok=6.25,
        cache_read_usd_per_mtok=0.50,
    ),
    "claude-haiku-4-5": ModelRates(
        input_usd_per_mtok=1.00,
        output_usd_per_mtok=5.00,
        cache_write_usd_per_mtok=1.25,
        cache_read_usd_per_mtok=0.10,
    ),
}


def _rates_for(model: str) -> ModelRates:
    try:
        return RATES[model]
    except KeyError as exc:
        raise UnknownModelError(
            f"No pricing entry for model {model!r}; add it to "
            "loop_orchestrator.tools.llm.pricing.RATES before using it."
        ) from exc


def cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    """Actual cost of a completed call, from the API's own usage numbers."""
    rates = _rates_for(model)
    return (
        input_tokens * rates.input_usd_per_mtok
        + output_tokens * rates.output_usd_per_mtok
        + cache_creation_tokens * rates.cache_write_usd_per_mtok
        + cache_read_tokens * rates.cache_read_usd_per_mtok
    ) / _TOKENS_PER_MTOK


def estimate_cost_usd(model: str, estimated_input_tokens: int, max_tokens: int) -> float:
    """Pre-flight worst-case cost of a call that has not happened yet.

    max_tokens is priced at the output rate and input at the uncached rate —
    deliberately conservative: the budget must abort *before* the breaching
    call, never after.
    """
    rates = _rates_for(model)
    return (
        estimated_input_tokens * rates.input_usd_per_mtok + max_tokens * rates.output_usd_per_mtok
    ) / _TOKENS_PER_MTOK
