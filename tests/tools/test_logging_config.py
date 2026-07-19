import json
import logging

from loop_orchestrator.core.engine import Loop, Stage
from loop_orchestrator.core.gates import ArtifactGate
from loop_orchestrator.core.graph_engine import run_graph_loop
from loop_orchestrator.core.state import State
from loop_orchestrator.personas.base import BasePersona


class StubPersona(BasePersona):
    def __init__(self, key: str) -> None:
        self._key = key

    def run(self, state: State, llm_client, findings=None) -> State:
        llm_client.tokens_used += 10
        llm_client.cost_used += 0.01
        return state.model_copy(update={"artifacts": {**state.artifacts, self._key: "done"}})


class StubClient:
    def __init__(self, budget_usd: float) -> None:
        self.budget_usd = budget_usd
        self.tokens_used = 0
        self.cost_used = 0.0
        self.cache_creation_tokens_used = 0
        self.cache_read_tokens_used = 0

    def remaining(self) -> float:
        return self.budget_usd - self.cost_used


def _initial_state() -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts={})


def test_run_loop_emits_json_log_line_per_stage(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    loop = Loop(
        stages=[Stage(persona=StubPersona(k), gate=ArtifactGate(k)) for k in ("a", "b", "c")]
    )

    with caplog.at_level(logging.INFO, logger="loop_orchestrator.cost"):
        run_graph_loop(loop, _initial_state(), StubClient(budget_usd=10.0))

    records = [r for r in caplog.records if r.name == "loop_orchestrator.cost"]
    assert len(records) == 3

    for record in records:
        payload = json.loads(record.message)
        assert set(payload) == {
            "stage_name",
            "tokens_used",
            "cost_usd",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
        }
        assert payload["tokens_used"] == 10
