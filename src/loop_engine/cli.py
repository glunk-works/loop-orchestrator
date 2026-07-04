import uuid
from pathlib import Path
from typing import Annotated

import typer

from loop_engine.core.engine import run_loop
from loop_engine.core.state import State
from loop_engine.loops.default.loop import DEFAULT_LOOP
from loop_engine.personas.base import BasePersona
from loop_engine.tools.llm.client import LLMClient

app = typer.Typer()

NAMED_LOOPS: dict[str, list[BasePersona]] = {"default": DEFAULT_LOOP}

DEFAULT_BUDGET_TOKENS = 100_000


@app.callback()
def main() -> None:
    """loop-engine: run a named persona loop against shared State."""


@app.command()
def run(
    loop: Annotated[str, typer.Option("--loop")] = "default",
    input: Annotated[Path | None, typer.Option("--input")] = None,
    budget: Annotated[int, typer.Option("--budget")] = DEFAULT_BUDGET_TOKENS,
    resume_from: Annotated[Path | None, typer.Option("--resume-from")] = None,
) -> None:
    selected_loop = NAMED_LOOPS[loop]

    if resume_from is not None:
        initial_state = State.model_validate_json(resume_from.read_text())
        remaining_loop = selected_loop[len(initial_state.stage_history) :]
    else:
        human_input = input.read_text() if input is not None else ""
        initial_state = State(
            schema_version=1,
            run_id=uuid.uuid4().hex,
            stage_history=[],
            artifacts={"human_input": human_input},
        )
        remaining_loop = selected_loop

    llm_client = LLMClient(budget_tokens=budget)
    run_loop(remaining_loop, initial_state, llm_client)


@app.command(name="cost-summary")
def cost_summary(run_id: Annotated[str, typer.Option("--run-id")]) -> None:
    run_dir = Path("state") / run_id
    total_tokens = 0
    total_cost = 0.0

    typer.echo(f"{'Stage':<40}{'Tokens':>10}{'Cost (USD)':>14}")
    for snapshot_path in sorted(run_dir.glob("*.json")):
        state = State.model_validate_json(snapshot_path.read_text())
        if not state.stage_history:
            continue
        record = state.stage_history[-1]
        total_tokens += record.tokens_used
        total_cost += record.cost_usd
        typer.echo(f"{record.stage_name:<40}{record.tokens_used:>10}{record.cost_usd:>14.4f}")

    typer.echo(f"{'TOTAL':<40}{total_tokens:>10}{total_cost:>14.4f}")


if __name__ == "__main__":
    app()
