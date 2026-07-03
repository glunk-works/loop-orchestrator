from pathlib import Path
from types import SimpleNamespace

import pytest

from loop_engine.core.engine import InvalidStateTransitionError, run_loop
from loop_engine.core.state import StageRecord, State
from loop_engine.personas.base import BasePersona


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _initial_state(run_id: str = "run-1") -> State:
    return State(schema_version=1, run_id=run_id, stage_history=[], artifacts={})


class AppendArtifactPersona(BasePersona):
    def __init__(self, key: str) -> None:
        self._key = key

    def run(self, state: State, llm_client) -> State:
        artifacts = {**state.artifacts, self._key: "done"}
        return state.model_copy(update={"artifacts": artifacts})


class CorruptingPersona(BasePersona):
    def run(self, state: State, llm_client) -> State:
        record = StageRecord(
            stage_name="corrupt", tokens_used=1, cost_usd=0.0, completed_at="2026-07-02T00:00:00Z"
        )
        state.stage_history.append(record)
        state.stage_history[0].tokens_used = -5  # bypasses construction-time validation
        return state


class NeverCalledPersona(BasePersona):
    def run(self, state: State, llm_client) -> State:
        raise AssertionError("this persona must never be invoked")


def _stub_llm_client(tokens_used: int = 0, budget_tokens: int = 10_000) -> SimpleNamespace:
    return SimpleNamespace(_tokens_used=tokens_used, budget_tokens=budget_tokens)


def test_run_loop_executes_personas_in_order_and_merges_state() -> None:
    personas = [AppendArtifactPersona("a"), AppendArtifactPersona("b"), AppendArtifactPersona("c")]

    final_state = run_loop(personas, _initial_state(), _stub_llm_client())

    assert final_state.artifacts == {"a": "done", "b": "done", "c": "done"}


def test_run_loop_raises_invalid_state_transition_error_naming_persona() -> None:
    with pytest.raises(InvalidStateTransitionError, match="CorruptingPersona"):
        run_loop([CorruptingPersona()], _initial_state(), _stub_llm_client())


def test_run_loop_writes_snapshot_after_each_stage() -> None:
    personas = [AppendArtifactPersona("a"), AppendArtifactPersona("b"), AppendArtifactPersona("c")]

    run_loop(personas, _initial_state("run-2"), _stub_llm_client())

    expected_names = [
        "00_AppendArtifactPersona",
        "01_AppendArtifactPersona",
        "02_AppendArtifactPersona",
    ]
    for name in expected_names:
        assert (Path("state") / "run-2" / f"{name}.json").exists()


def test_run_loop_aborts_before_second_stage_when_budget_already_exhausted() -> None:
    from loop_engine.tools.llm.client import BudgetExceededError

    class BudgetConsumingPersona(BasePersona):
        def run(self, state: State, llm_client) -> State:
            llm_client._tokens_used = llm_client.budget_tokens
            return state

    personas = [BudgetConsumingPersona(), NeverCalledPersona()]
    client = _stub_llm_client(tokens_used=0, budget_tokens=100)

    with pytest.raises(BudgetExceededError):
        run_loop(personas, _initial_state("run-3"), client)
