from pydantic import ValidationError

from loop_engine.core.state import State
from loop_engine.personas.base import BasePersona
from loop_engine.tools.llm.client import BudgetExceededError, LLMClient
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

        state = persona.run(state, llm_client)

        try:
            state = State.model_validate(state.model_dump())
        except ValidationError as exc:
            raise InvalidStateTransitionError(
                f"{stage_name} returned an invalid State: {exc}"
            ) from exc

        write_state_snapshot(
            state,
            run_id=state.run_id,
            stage_index=stage_index,
            stage_name=stage_name,
        )

    return state
