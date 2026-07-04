from datetime import UTC, datetime

from pydantic import ValidationError

from loop_engine.core.state import StageRecord, State
from loop_engine.personas.base import BasePersona
from loop_engine.tools.llm.client import BudgetExceededError, LLMClient
from loop_engine.tools.logging_config import log_stage_completion
from loop_engine.tools.state_io.writer import write_state_snapshot


class InvalidStateTransitionError(Exception):
    pass


def run_loop(loop: list[BasePersona], initial_state: State, llm_client: LLMClient) -> State:
    state = initial_state

    for stage_index, persona in enumerate(loop):
        stage_name = type(persona).__name__

        if llm_client._tokens_used >= llm_client.budget_tokens:
            write_state_snapshot(
                state,
                run_id=state.run_id,
                stage_index=stage_index,
                stage_name="budget_exceeded",
            )
            raise BudgetExceededError(
                f"Budget already exhausted before stage {stage_index} ({stage_name})."
            )

        tokens_before = llm_client._tokens_used
        state = persona.run(state, llm_client)
        tokens_used_this_stage = llm_client._tokens_used - tokens_before

        try:
            state = State.model_validate(state.model_dump())
        except ValidationError as exc:
            raise InvalidStateTransitionError(
                f"{stage_name} returned an invalid State: {exc}"
            ) from exc

        # cost_usd is a placeholder until a per-model $/token rate table is
        # added; no such rate exists anywhere in this codebase or the specs.
        stage_record = StageRecord(
            stage_name=stage_name,
            tokens_used=tokens_used_this_stage,
            cost_usd=0.0,
            completed_at=datetime.now(UTC).isoformat(),
        )
        state = state.model_copy(update={"stage_history": [*state.stage_history, stage_record]})

        write_state_snapshot(
            state,
            run_id=state.run_id,
            stage_index=stage_index,
            stage_name=stage_name,
        )
        log_stage_completion(
            stage_name=stage_record.stage_name,
            tokens_used=stage_record.tokens_used,
            cost_usd=stage_record.cost_usd,
        )

    return state
