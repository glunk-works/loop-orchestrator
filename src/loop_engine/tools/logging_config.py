import json
import logging

_COST_LOGGER_NAME = "loop_engine.cost"


def get_cost_logger() -> logging.Logger:
    return logging.getLogger(_COST_LOGGER_NAME)


def log_stage_completion(stage_name: str, tokens_used: int, cost_usd: float) -> None:
    get_cost_logger().info(
        json.dumps(
            {
                "stage_name": stage_name,
                "tokens_used": tokens_used,
                "cost_usd": cost_usd,
            }
        )
    )
