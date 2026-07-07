import json
import logging

_COST_LOGGER_NAME = "loop_engine.cost"


def get_cost_logger() -> logging.Logger:
    return logging.getLogger(_COST_LOGGER_NAME)


def log_stage_completion(
    stage_name: str,
    tokens_used: int,
    cost_usd: float,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
) -> None:
    get_cost_logger().info(
        json.dumps(
            {
                "stage_name": stage_name,
                "tokens_used": tokens_used,
                "cost_usd": cost_usd,
                "cache_creation_input_tokens": cache_creation_input_tokens,
                "cache_read_input_tokens": cache_read_input_tokens,
            }
        )
    )
