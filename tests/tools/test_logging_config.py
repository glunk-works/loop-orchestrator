import json
import logging

from loop_engine.core.engine import Loop, Stage, run_loop
from loop_engine.core.gates import ArtifactGate
from loop_engine.core.state import State
from loop_engine.personas.base import BasePersona


class StubPersona(BasePersona):
    def __init__(self, key: str) -> None:
        self._key = key

    def run(self, state: State, llm_client, findings=None) -> State:
        llm_client.tokens_used += 10
        return state.model_copy(update={"artifacts": {**state.artifacts, self._key: "done"}})


class StubClient:
    def __init__(self, budget_tokens: int) -> None:
        self.budget_tokens = budget_tokens
        self.tokens_used = 0

    def remaining(self) -> int:
        return self.budget_tokens - self.tokens_used


def _initial_state() -> State:
    return State(schema_version=2, run_id="run-1", stage_history=[], artifacts={})


def test_run_loop_emits_json_log_line_per_stage(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.chdir(tmp_path)
    loop = Loop(
        stages=[Stage(persona=StubPersona(k), gate=ArtifactGate(k)) for k in ("a", "b", "c")]
    )

    with caplog.at_level(logging.INFO, logger="loop_engine.cost"):
        run_loop(loop, _initial_state(), StubClient(budget_tokens=1000))

    records = [r for r in caplog.records if r.name == "loop_engine.cost"]
    assert len(records) == 3

    for record in records:
        payload = json.loads(record.message)
        assert set(payload) == {"stage_name", "tokens_used", "cost_usd"}
        assert payload["tokens_used"] == 10
